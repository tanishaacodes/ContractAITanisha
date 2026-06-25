"""
Multi-Modal Contract Understanding – Feature 8
===============================================
POST /api/multimodal/voice/     — voice/audio transcription → contract extraction → full analysis
POST /api/multimodal/document/  — scanned image/PDF → text extraction + clause detection → full analysis
POST /api/multimodal/email/     — email text → structured contract data → full analysis

All three modalities produce the same downstream analysis format:
  analysis.final_score, analysis.decision, analysis.risk_summary,
  analysis.cfo_result, analysis.legal_risks, analysis.negotiation_results
"""

import json
import re
import logging
import tempfile
import os
import requests

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')


# ─────────────────────────────────────────────
# LLM helpers
# ─────────────────────────────────────────────

def _call_ollama(prompt: str, temperature: float = 0.3) -> str:
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "qwen2.5:0.5b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=50,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "")
        return ""
    except Exception as exc:
        logger.warning("Ollama call failed: %s", exc)
        return ""


def _parse_json_from_llm(text: str, fallback: dict) -> dict:
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return fallback


# ─────────────────────────────────────────────
# Shared text analysis helpers
# ─────────────────────────────────────────────

CONTRACT_KEYWORDS = [
    "agreement", "contract", "party", "parties", "obligation", "payment",
    "termination", "liability", "indemnity", "warranty", "confidential",
    "governing law", "dispute", "jurisdiction", "force majeure", "penalty",
    "delivery", "service", "goods", "consideration", "effective date",
]

CLAUSE_TYPE_KEYWORDS = {
    "Payment Terms":      ["payment", "invoice", "due date", "remittance", "amount"],
    "Termination":        ["termination", "terminate", "cancellation", "notice period"],
    "Liability":          ["liability", "liable", "damages", "loss", "consequential"],
    "Indemnification":    ["indemnify", "indemnification", "hold harmless"],
    "Confidentiality":    ["confidential", "non-disclosure", "NDA", "proprietary"],
    "Force Majeure":      ["force majeure", "act of god", "unforeseeable", "beyond control"],
    "Governing Law":      ["governing law", "jurisdiction", "courts of"],
    "Warranty":           ["warranty", "warrants", "guarantee", "representation"],
    "Dispute Resolution": ["dispute", "arbitration", "mediation", "resolution"],
}


def _detect_clause_types(text: str) -> list:
    text_lower = text.lower()
    return [
        ct for ct, kws in CLAUSE_TYPE_KEYWORDS.items()
        if any(kw.lower() in text_lower for kw in kws)
    ]


def _extract_key_terms(text: str) -> list:
    text_lower = text.lower()
    found = [kw.replace("_", " ").title() for kw in CONTRACT_KEYWORDS if kw in text_lower]
    entities = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text)
    for entity in entities[:10]:
        if entity not in found and len(entity) > 3:
            found.append(entity)
    return list(dict.fromkeys(found))[:20]


def _detect_contract_type(text: str) -> str:
    t = text.lower()
    if "supply" in t or "goods" in t:
        return "Supply Agreement"
    if "software" in t or "license" in t:
        return "Software License"
    if "employment" in t or "employee" in t:
        return "Employment Agreement"
    if "service" in t:
        return "Service Agreement"
    return "General Commercial Agreement"


def _extract_contract_value(text: str) -> float:
    """Extract first numeric monetary amount found in text."""
    patterns = [
        r'(?:USD|usd|\$)\s*([\d,]+(?:\.\d{2})?)',
        r'([\d,]+(?:\.\d{2})?)\s*(?:USD|dollars?)',
        r'(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d{2})?)',
    ]
    for pat in patterns:
        for m in re.findall(pat, text, re.IGNORECASE):
            try:
                val = float(m.replace(',', ''))
                if val >= 1000:          # ignore tiny numbers
                    return val
            except (ValueError, TypeError):
                pass
    return 100_000.0


# ─────────────────────────────────────────────
# Downstream analysis pipeline
# ─────────────────────────────────────────────

def _run_downstream_analysis(extracted_text: str, contract_value: float = None) -> dict:
    """
    Pipe extracted text through the full orchestrator pipeline:
      risk scoring → CFO Monte Carlo → negotiation engine → scoring → recommendations
    Returns a lightweight subset of the full result.
    """
    try:
        from api.orchestrator import run_full_analysis
        value = contract_value or _extract_contract_value(extracted_text)
        result = run_full_analysis(
            contract_id=None,
            jurisdiction="india",
            contract_value=value,
            duration_months=12,
            raw_clauses=None,
            raw_text=extracted_text,
        )
        return {
            "analysis_id":          result.get("analysis_id"),
            "final_score":          result.get("final_score"),
            "decision":             result.get("decision"),
            "risk_summary":         result.get("risk_summary", {}),
            "cfo_result":           result.get("cfo_result", {}),
            "legal_risks":          result.get("legal_risks", [])[:6],
            "negotiation_results":  result.get("negotiation_results", [])[:3],
            "recommendations":      result.get("recommendations", [])[:6],
            "score_breakdown":      result.get("score_breakdown", {}),
            "clauses":              result.get("clauses", []),
        }
    except Exception as exc:
        logger.warning("Downstream analysis failed: %s", exc)
        return {"error": str(exc)}


# ─────────────────────────────────────────────
# Voice: Whisper transcription
# ─────────────────────────────────────────────

def _transcribe_audio(tmp_path: str) -> tuple:
    """
    Attempt transcription in order:
      1. OpenAI Whisper API  (if OPENAI_API_KEY is set)
      2. Local openai-whisper package
      3. SpeechRecognition + Google STT
    Returns (transcription_text, engine_name).
    Raises ValueError if no engine succeeds.
    """
    openai_key = getattr(settings, 'OPENAI_API_KEY', None)

    # 1. OpenAI Whisper API
    if openai_key:
        try:
            import openai as openai_lib
            client = openai_lib.OpenAI(api_key=openai_key)
            with open(tmp_path, 'rb') as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="text",
                )
            text = str(transcript).strip()
            if text:
                return text, "whisper-api"
        except Exception as exc:
            logger.warning("OpenAI Whisper API failed: %s", exc)

    # 2. Local whisper library
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(tmp_path)
        text = result.get("text", "").strip()
        if text:
            return text, "whisper-local"
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("Local whisper failed: %s", exc)

    # 3. SpeechRecognition + Google STT (WAV only)
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
        if text:
            return text, "google-stt"
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("Google STT failed: %s", exc)

    raise ValueError(
        "No transcription engine is available. "
        "Set OPENAI_API_KEY for Whisper API, or install the 'openai-whisper' package."
    )


class VoiceContractView(APIView):
    """POST /api/multimodal/voice/"""
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return Response({"error": "audio file required"}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(audio_file.name or "audio.wav")[1].lower() or ".wav"
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            for chunk in audio_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            transcription, engine = _transcribe_audio(tmp_path)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        key_terms = _extract_key_terms(transcription)
        clause_types = _detect_clause_types(transcription)
        contract_type = _detect_contract_type(transcription)

        suggested_clauses = [
            {
                "clause_type": ct,
                "suggestion": f"Include a standard {ct} clause addressing key terms identified in the voice recording.",
                "priority": "high" if ct in ("Liability", "Termination", "Payment Terms") else "medium",
            }
            for ct in clause_types[:5]
        ]

        analysis = _run_downstream_analysis(transcription)

        return Response({
            "modality":               "voice",
            "transcription":          transcription,
            "extracted_text":         transcription,
            "key_terms":              key_terms,
            "suggested_clauses":      suggested_clauses,
            "contract_type":          contract_type,
            "detected_clause_types":  clause_types,
            "word_count":             len(transcription.split()),
            "confidence":             0.95,
            "transcription_engine":   engine,
            "analysis":               analysis,
        })


# ─────────────────────────────────────────────
# Document: PDF + OCR extraction
# ─────────────────────────────────────────────

def _extract_pdf_text(tmp_path: str) -> tuple:
    """
    Try pdfplumber → PyPDF2.
    Returns (text, method, confidence_score).
    Raises ValueError if all fail.
    """
    # pdfplumber (most reliable for text-layer PDFs)
    try:
        import pdfplumber
        with pdfplumber.open(tmp_path) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages[:20]]
        text = "\n\n".join(pages).strip()
        if text:
            return text, "pdfplumber", 0.95
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("pdfplumber failed: %s", exc)

    # PyPDF2 fallback
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(tmp_path)
        pages = [reader.pages[i].extract_text() or "" for i in range(min(20, len(reader.pages)))]
        text = "\n\n".join(pages).strip()
        if text:
            return text, "PyPDF2", 0.90
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("PyPDF2 failed: %s", exc)

    raise ValueError("PDF text extraction failed. Install pdfplumber or PyPDF2.")


def _extract_image_text(tmp_path: str) -> tuple:
    """
    Try pytesseract → PaddleOCR.
    Returns (text, method, confidence_score).
    Raises ValueError if all fail.
    """
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(tmp_path)
        text = pytesseract.image_to_string(img).strip()
        if text:
            return text, "pytesseract", 0.78
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("pytesseract failed: %s", exc)

    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, show_log=False)
        result = ocr.ocr(tmp_path, cls=True)
        lines = []
        for page_res in (result or []):
            for line in (page_res or []):
                if line and len(line) >= 2:
                    lines.append(line[1][0])
        text = " ".join(lines).strip()
        if text:
            return text, "PaddleOCR", 0.82
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("PaddleOCR failed: %s", exc)

    raise ValueError("OCR extraction failed. Install pytesseract (with Tesseract binary) or paddleocr.")


class DocumentScanView(APIView):
    """POST /api/multimodal/document/"""
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        doc_file = request.FILES.get('document')
        if not doc_file:
            return Response({"error": "document file required"}, status=status.HTTP_400_BAD_REQUEST)

        filename = (doc_file.name or "").lower()
        ext = os.path.splitext(filename)[1] or ".pdf"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            for chunk in doc_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            if filename.endswith('.pdf'):
                extracted_text, method, confidence_score = _extract_pdf_text(tmp_path)
                file_type = "pdf"
            elif filename.endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                extracted_text, method, confidence_score = _extract_image_text(tmp_path)
                file_type = "image"
            else:
                return Response(
                    {"error": "Unsupported file type. Upload a PDF or image (PNG/JPG/TIFF/BMP)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        clause_types = _detect_clause_types(extracted_text)
        clauses_detected = []
        for ct in clause_types:
            pattern = "|".join(CLAUSE_TYPE_KEYWORDS.get(ct, [ct.lower()]))
            match = re.search(pattern, extracted_text.lower())
            start_pos = match.start() if match else 0
            snippet = extracted_text[max(0, start_pos - 20): start_pos + 200].strip()
            clauses_detected.append({
                "clause_type": ct,
                "text_snippet": snippet[:300],
                "confidence": round(confidence_score * 0.9 + 0.05, 2),
            })

        key_terms = _extract_key_terms(extracted_text)
        analysis = _run_downstream_analysis(extracted_text)

        return Response({
            "modality":               "document",
            "extracted_text":         extracted_text[:3000],
            "key_terms":              key_terms,
            "contract_type":          _detect_contract_type(extracted_text),
            "detected_clause_types":  clause_types,
            "clauses_detected":       clauses_detected,
            "confidence_score":       round(confidence_score, 2),
            "total_characters":       len(extracted_text),
            "word_count":             len(extracted_text.split()),
            "file_type":              file_type,
            "extraction_method":      method,
            "analysis":               analysis,
        })


# ─────────────────────────────────────────────
# Email: parse + LLM extraction
# ─────────────────────────────────────────────

class EmailParserView(APIView):
    """POST /api/multimodal/email/"""
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        email_text = request.data.get("email_text", "").strip()
        if not email_text:
            return Response({"error": "email_text required"}, status=status.HTTP_400_BAD_REQUEST)

        # Extract parties via regex heuristics
        parties = []
        from_match = re.search(r'From:\s*(.+?)(?:\n|<)', email_text)
        to_match = re.search(r'To:\s*(.+?)(?:\n|<)', email_text)
        if from_match:
            parties.append({"role": "Sender", "name": from_match.group(1).strip(), "type": "individual"})
        if to_match:
            parties.append({"role": "Recipient", "name": to_match.group(1).strip(), "type": "individual"})

        # Extract dates
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
        ]
        dates_found = []
        for pat in date_patterns:
            dates_found.extend(re.findall(pat, email_text, re.IGNORECASE))

        # Extract payment amounts
        amounts = re.findall(
            r'(?:USD|INR|GBP|EUR|Rs\.?|₹|\$)\s*[\d,]+(?:\.\d{2})?',
            email_text, re.IGNORECASE,
        )

        # Extract obligations (sentences containing modal verbs)
        sentences = re.split(r'[.!?]', email_text)
        obligations = [
            sent.strip()[:200]
            for sent in sentences
            if any(w in sent.lower() for w in ["shall", "will", "must", "agree", "commit", "obligat"])
            and len(sent.strip()) > 20
        ]

        # LLM-based structured extraction
        prompt = f"""Extract contract-relevant information from this email. Return a JSON with these exact fields:
{{
  "suggested_contract_type": "<type>",
  "parties": [<list of party names as strings>],
  "key_obligations": [<list of obligation strings>],
  "payment_terms": "<payment terms if any>",
  "key_dates": [<list of date strings>],
  "draft_clauses": [
    {{"clause_type": "<type>", "draft_text": "<suggested clause text>"}}
  ]
}}

Email:
{email_text[:800]}

Respond with only the JSON."""

        llm_response = _call_ollama(prompt, temperature=0.3)

        fallback = {
            "suggested_contract_type": _detect_contract_type(email_text),
            "parties": [p["name"] for p in parties] or ["Party A", "Party B"],
            "key_obligations": obligations[:5] or ["Deliver agreed services", "Make payment within agreed timeline"],
            "payment_terms": amounts[0] if amounts else "To be negotiated",
            "key_dates": dates_found[:3] or [],
            "draft_clauses": [
                {
                    "clause_type": "Payment Terms",
                    "draft_text": f"Payment of {amounts[0] if amounts else '[AMOUNT]'} shall be made within 30 days of invoice.",
                },
                {
                    "clause_type": "Confidentiality",
                    "draft_text": "Each party shall maintain confidentiality of the other party's proprietary information.",
                },
                {
                    "clause_type": "Governing Law",
                    "draft_text": "This agreement shall be governed by the laws of India.",
                },
            ],
        }

        parsed = _parse_json_from_llm(llm_response, fallback)

        # Ensure array fields are valid
        if not isinstance(parsed.get("draft_clauses"), list):
            parsed["draft_clauses"] = fallback["draft_clauses"]
        if not isinstance(parsed.get("key_obligations"), list):
            parsed["key_obligations"] = fallback["key_obligations"]

        contract_value = _extract_contract_value(email_text)
        analysis = _run_downstream_analysis(email_text, contract_value)

        draft_clauses = parsed.get("draft_clauses", fallback["draft_clauses"])[:8]

        return Response({
            "modality":               "email",
            "extracted_text":         email_text,
            "contract_type":          parsed.get("suggested_contract_type", fallback["suggested_contract_type"]),
            "detected_clause_types":  [c.get("clause_type", "") for c in draft_clauses],
            "key_terms":              _extract_key_terms(email_text),
            "word_count":             len(email_text.split()),
            "confidence":             0.85,
            # Email-specific fields
            "parties":                parsed.get("parties", fallback["parties"]),
            "obligations":            parsed.get("key_obligations", obligations[:5]),
            "payment_terms":          parsed.get("payment_terms", fallback["payment_terms"]),
            "suggested_contract_type": parsed.get("suggested_contract_type", fallback["suggested_contract_type"]),
            "key_dates":              parsed.get("key_dates", dates_found[:3]),
            "amounts_detected":       amounts[:5],
            "draft_clauses":          draft_clauses,
            "analysis":               analysis,
        })
