import os
import tempfile
import shutil
from pathlib import Path
import json
import io
import unicodedata
import re

from django.conf import settings

# Import these at module level (safe imports)
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image

# PaddleOCR will be imported lazily to avoid Django reloader issues
ocr_engine = None

# OCR text cleaner for fixing common misreading errors
try:
    from .ocr_text_cleaner import clean_ocr_text
except ImportError:
    # Fallback if cleaner not available
    def clean_ocr_text(text):
        return text


# =========================================================
# TEXT NORMALIZATION & LIGATURE FIXING
# =========================================================

def normalize_extracted_text(text):
    """
    Fix Unicode ligatures and special characters that PDFs often encode incorrectly.

    Common issues in PDF extraction:
    - Ligatures: fi, fl, ffi, ffl, ft, tt, ti → Ɵ, Ʃ, Ō, ﬀ, ﬃ, etc.
    - Special characters: smart quotes, em dashes, etc.
    """
    if not text:
        return text

    # Step 1: Unicode normalization (NFKC = compatibility decomposition + composition)
    # This handles many special characters and ligatures
    text = unicodedata.normalize('NFKC', text)

    # Step 2: Remove spaces before problematic characters FIRST (before ligature replacement)
    # Example: "Construc Ɵon" → "ConstructƟon" (then ligature map will make it "Construction")
    text = re.sub(r'([a-z])\s+\u019f', '\\1\u019f', text, flags=re.IGNORECASE)  # Ɵ
    text = re.sub(r'([a-z])\s+\u01a9', '\\1\u01a9', text, flags=re.IGNORECASE)  # Ʃ
    text = re.sub(r'([a-z])\s+\u014c', '\\1\u014c', text, flags=re.IGNORECASE)  # Ō
    text = re.sub(r'([a-z])\s+\u019e', '\\1\u019e', text, flags=re.IGNORECASE)  # ƞ

    # Step 3: Fix common PDF ligatures that NFKC doesn't catch
    ligature_map = {
        # Common ligatures
        '\ufb00': 'ff',  # ﬀ
        '\ufb01': 'fi',  # ﬁ
        '\ufb02': 'fl',  # ﬂ
        '\ufb03': 'ffi', # ﬃ
        '\ufb04': 'ffl', # ﬄ
        '\ufb05': 'ft',  # ﬅ
        '\ufb06': 'st',  # ﬆ

        # Problem characters seen in the extraction
        '\u019f': 'ti',  # Ɵ - Latin Capital Letter O with Middle Tilde (common in "tion", "tial", etc.)
        'Ɵ': 'ti',      # Additional fallback
        '\u01a9': 'tt',  # Ʃ - Latin Capital Letter Esh
        'Ʃ': 'tt',      # Double-t ligature (fallback)
        '\u014c': 'ft',  # Ō - Latin Capital Letter O with Macron
        'Ō': 'ft',      # ft ligature (e.g., "after") (fallback)
        '\u019e': 'tf',  # ƞ - Latin Small Letter N with Long Right Leg
        'ƞ': 'tf',      # tf combination (fallback)
        'ﬃ': 'ffi',    # ffi ligature
        'ﬀ': 'ff',     # ff ligature
        'ﬁ': 'fi',     # fi ligature
        'ﬂ': 'fl',     # fl ligature

        # Additional special characters
        '\u2018': "'",   # Left single quote
        '\u2019': "'",   # Right single quote
        '\u201c': '"',   # Left double quote
        '\u201d': '"',   # Right double quote
        '\u2013': '-',   # En dash
        '\u2014': '-',   # Em dash
        '\u2026': '...', # Ellipsis
    }

    for old_char, new_char in ligature_map.items():
        text = text.replace(old_char, new_char)

    # Step 4: Final normalization
    text = unicodedata.normalize('NFKC', text)

    return text


def get_ocr_engine():
    """Lazy initialization of PaddleOCR engine (import only when needed)"""
    global ocr_engine
    if ocr_engine is None:
        try:
            # Import PaddleOCR only when first needed to avoid Django reloader conflicts
            from paddleocr import PaddleOCR

            ocr_engine = PaddleOCR(
                use_angle_cls=True,  # Enable angle classification for rotated text
                lang='en'            # English language
            )
            print("[OCR] PaddleOCR initialized successfully")
        except Exception as e:
            print(f"[OCR ERROR] Failed to initialize PaddleOCR: {e}")
            raise
    return ocr_engine


# =========================================================
# PDF TEXT EXTRACTION (NON-OCR)
# =========================================================

def extract_text_from_pdf_js(file_path):
    """
    Extract text from PDF using PyPDF2 (non-OCR).
    Applies Unicode normalization and ligature fixing.
    """
    try:
        reader = PdfReader(file_path)
        text = []
        total_pages = len(reader.pages)

        for i, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                # Apply normalization to fix ligatures and special characters
                page_text = normalize_extracted_text(page_text)
                text.append(f"\n--- Page {i} ---\n{page_text}")

        final_text = "\n".join(text).strip()
        # Apply final normalization
        final_text = normalize_extracted_text(final_text)

        return {
            "text": final_text,
            "pages": total_pages,
            "ocr_performed": False
        }

    except Exception as e:
        print("[PDF TEXT ERROR]", e)
        return {
            "text": "",
            "pages": None,
            "error": str(e),
            "ocr_performed": False
        }


# =========================================================
# PDF OCR FALLBACK
# =========================================================

def perform_ocr_on_pdf(file_path, max_pages=None):
    """
    Perform OCR on PDF using PaddleOCR + PyMuPDF (fitz)
    PyMuPDF converts PDF pages to images without needing Poppler
    PaddleOCR provides superior accuracy compared to Tesseract
    """
    max_pages = max_pages or getattr(settings, "MAX_OCR_PAGES", 10)
    temp_dir = tempfile.mkdtemp()

    try:
        # Get PaddleOCR engine
        ocr = get_ocr_engine()

        # Open PDF with PyMuPDF
        pdf_document = fitz.open(file_path)
        total_pages = len(pdf_document)
        pages_to_process = min(total_pages, max_pages)

        print(f"[OCR] Processing {pages_to_process} pages out of {total_pages} using PaddleOCR")

        aggregated_text = []

        for page_num in range(pages_to_process):
            try:
                # Get the page
                page = pdf_document[page_num]

                # Convert page to image (pixmap)
                # zoom=2 gives ~200 DPI, zoom=3 gives ~300 DPI
                # Increased to 3x for better OCR accuracy (fixes issues like "T10ns" → "obligations")
                mat = fitz.Matrix(3, 3)  # 3x zoom for higher quality OCR
                pix = page.get_pixmap(matrix=mat)

                # Save pixmap to temporary image file (PaddleOCR works with file paths)
                temp_image_path = os.path.join(temp_dir, f'page_{page_num}.png')
                pix.save(temp_image_path)

                # Perform OCR on the image using PaddleOCR
                # Try new API first (predict), fall back to old API (ocr)
                result = None
                try:
                    result = ocr.predict(temp_image_path)
                except (TypeError, AttributeError):
                    # Fall back to old API
                    result = ocr.ocr(temp_image_path, cls=True)

                # Extract text from PaddleOCR result
                # Handle both new format (list of dicts with 'rec_texts') and old format
                page_text = []
                if result:
                    for page_result in result:
                        if isinstance(page_result, dict):
                            # New PaddleOCR format: {'rec_texts': [...], ...}
                            texts = page_result.get('rec_texts', [])
                            page_text.extend([str(t) for t in texts])
                        elif isinstance(page_result, list):
                            # Old format: [[box, (text, confidence)], ...]
                            for line in page_result:
                                if line and len(line) >= 2:
                                    text_info = line[1]
                                    if isinstance(text_info, tuple) and len(text_info) >= 1:
                                        page_text.append(str(text_info[0]))
                                    elif isinstance(text_info, str):
                                        page_text.append(text_info)

                text = '\n'.join(page_text)

                if text.strip():
                    # Apply normalization to OCR text as well
                    text = normalize_extracted_text(text)
                    aggregated_text.append(f"\n--- Page {page_num + 1} ---\n{text}")
                    print(f"[OCR] Page {page_num + 1}: Extracted {len(text)} chars")
                else:
                    print(f"[OCR] Page {page_num + 1}: No text extracted")

            except Exception as e:
                print(f"[OCR PAGE ERROR] Page {page_num + 1}:", e)

        pdf_document.close()

        return {
            "text": "\n".join(aggregated_text).strip(),
            "pages": pages_to_process,
            "ocr_performed": True
        }

    except Exception as e:
        print("[PDF OCR ERROR]", e)
        import traceback
        traceback.print_exc()
        return {
            "text": "",
            "pages": None,
            "error": str(e),
            "ocr_performed": False
        }

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# =========================================================
# IMAGE OCR
# =========================================================

def perform_ocr_on_image(file_path):
    """
    OCR for images using PaddleOCR
    """
    try:
        # Get PaddleOCR engine
        ocr = get_ocr_engine()

        # Perform OCR on the image - try new API first, fall back to old
        result = None
        try:
            result = ocr.predict(file_path)
        except (TypeError, AttributeError):
            result = ocr.ocr(file_path, cls=True)

        # Extract text from PaddleOCR result
        # Handle both new format (list of dicts) and old format
        extracted_text = []
        if result:
            for page_result in result:
                if isinstance(page_result, dict):
                    # New format: {'rec_texts': [...], ...}
                    texts = page_result.get('rec_texts', [])
                    extracted_text.extend([str(t) for t in texts])
                elif isinstance(page_result, list):
                    # Old format: [[box, (text, confidence)], ...]
                    for line in page_result:
                        if line and len(line) >= 2:
                            text_info = line[1]
                            if isinstance(text_info, tuple) and len(text_info) >= 1:
                                extracted_text.append(str(text_info[0]))
                            elif isinstance(text_info, str):
                                extracted_text.append(text_info)

        result_text = '\n'.join(extracted_text).strip()
        # Apply normalization to OCR text
        return normalize_extracted_text(result_text)

    except Exception as e:
        print("[IMAGE OCR ERROR]", e)
        import traceback
        traceback.print_exc()
        return ""


# =========================================================
# MAIN FILE EXTRACTION ENTRY POINT
# =========================================================

def extract_text_from_file(file_path, ext):
    """
    Unified extractor for PDF, DOCX, Images.
    """

    ext = ext.lower()
    extracted_text = ""
    pages = None
    ocr_performed = False

    try:
        # ---------------- DOCX ----------------
        if ext == ".docx":
            doc = Document(file_path)
            extracted_text = "\n".join(p.text for p in doc.paragraphs if p.text)

        # ---------------- PDF ----------------
        elif ext == ".pdf":
            print("[PDF] Trying text extraction...")
            result = extract_text_from_pdf_js(file_path)
            extracted_text = result.get("text", "")
            pages = result.get("pages")

            # Calculate minimum expected characters based on pages
            # A typical page should have at least 200 characters
            min_chars_expected = (pages or 1) * 200
            actual_chars = len(extracted_text.strip())

            print(f"[PDF] Extracted {actual_chars} chars from {pages} pages (expected min: {min_chars_expected})")

            if not extracted_text or actual_chars < min_chars_expected:
                print("[PDF] Insufficient text extraction, running OCR...")
                ocr_result = perform_ocr_on_pdf(file_path)
                extracted_text = ocr_result.get("text", "")
                pages = ocr_result.get("pages", pages)
                ocr_performed = True

        # ---------------- IMAGE ----------------
        elif ext in [".png", ".jpg", ".jpeg"]:
            print("[IMAGE] Running OCR...")
            extracted_text = perform_ocr_on_image(file_path)
            pages = 1
            ocr_performed = True

        else:
            return {
                "text": "",
                "pages": None,
                "error": "Unsupported file type",
                "ocr_performed": False
            }

        # Apply text normalization to fix ligatures and special characters
        extracted_text = normalize_extracted_text(extracted_text)

        # Apply OCR error correction if OCR was used
        if ocr_performed and extracted_text:
            print("[OCR] Applying OCR error correction...")
            extracted_text = clean_ocr_text(extracted_text)
            print(f"[OCR] Text cleaned: {len(extracted_text)} chars")

        return {
            "text": extracted_text,
            "pages": pages,
            "ocr_performed": ocr_performed
        }

    except Exception as e:
        print("[EXTRACTION ERROR]", e)
        return {
            "text": "",
            "pages": None,
            "error": str(e),
            "ocr_performed": ocr_performed
        }


# =========================================================
# CONTRACT CLASSIFICATION
# =========================================================

def classify_contract(text, filename=""):
    """
    Rule-based contract classifier.
    Priority order: most specific → least specific.
    Uses keyword density so incidental mentions don't trigger wrong type.
    NDA only when the entire agreement is about non-disclosure, not just a clause.
    """
    try:
        t = text.lower()
        fn = (filename or "").lower()

        # Helper: require minimum keyword count for ambiguous terms
        def count(kw): return t.count(kw)

        # ── Tier 1: Title-level signals (very high confidence) ──
        if ("master service agreement" in t or "master services agreement" in t or
                "master services and technology" in t or "master technology agreement" in t or
                count("msa") >= 3 or "master service" in fn):
            return {"contractType": "Master Service Agreement", "confidenceScore": 92}

        if "construction agreement" in t or "construction agreement" in fn or (
            "construction" in fn or (
                count("construction") >= 2 and ("contractor" in t or "subcontractor" in t)
            )
        ):
            return {"contractType": "Construction Agreement", "confidenceScore": 88}

        if "software development agreement" in t or "software license agreement" in t or "saas agreement" in t or (
            ("software" in fn or "saas" in fn) and ("agreement" in fn or "contract" in fn)
        ):
            return {"contractType": "Software Agreement", "confidenceScore": 88}

        # ── Tier 2: Strong body signals (need multiple keywords) ──
        if count("employment") >= 2 and ("employee" in t or "salary" in t or "employer" in t):
            return {"contractType": "Employment Agreement", "confidenceScore": 85}

        if count("construction") >= 2 and ("contractor" in t or "subcontractor" in t or "project" in t):
            return {"contractType": "Construction Agreement", "confidenceScore": 85}

        if (count("software development") >= 2 or count("software services") >= 2 or
                "saas" in t or count("software license") >= 1):
            return {"contractType": "Software Agreement", "confidenceScore": 85}

        if ("service agreement" in t or count("professional services") >= 2 or
                count("consulting") >= 3):
            return {"contractType": "Service Agreement", "confidenceScore": 80}

        if count("supply") >= 2 and ("supplier" in t or "purchase order" in t):
            return {"contractType": "Supply Agreement", "confidenceScore": 80}

        if count("purchase") >= 2 or (count("vendor") >= 2 and "procurement" in t):
            return {"contractType": "Purchase Agreement", "confidenceScore": 75}

        if ("lease agreement" in t or count("tenancy") >= 2 or
                (count("lease") >= 3 and ("landlord" in t or "tenant" in t))):
            return {"contractType": "Lease Agreement", "confidenceScore": 80}

        if count("partnership") >= 2 and count("partner") >= 3:
            return {"contractType": "Partnership Agreement", "confidenceScore": 78}

        if ("loan agreement" in t or count("credit facility") >= 1 or
                (count("loan") >= 2 and "borrower" in t)):
            return {"contractType": "Loan Agreement", "confidenceScore": 80}

        if count("distribution") >= 2 and "distributor" in t:
            return {"contractType": "Distribution Agreement", "confidenceScore": 78}

        # ── Tier 3: NDA — only when the whole agreement IS a non-disclosure ──
        # Use word-boundary safe counts (avoid "standard", "agenda" matching "nda")
        import re as _re
        nda_word_count = len(_re.findall(r'\bnda\b', t))
        nda_count = count("non-disclosure") + nda_word_count
        if ("non-disclosure agreement" in t or "nda" in fn.split('.')[0].split('-') or
                (nda_count >= 4 and count("confidential") >= 5 and count("service") < 3)):
            return {"contractType": "NDA", "confidenceScore": 88}

        # ── Tier 4: Weak signals — filename fallback ──
        if "software" in fn:
            return {"contractType": "Software Agreement", "confidenceScore": 65}
        if "construction" in fn:
            return {"contractType": "Construction Agreement", "confidenceScore": 65}
        if "employment" in fn or "employee" in fn:
            return {"contractType": "Employment Agreement", "confidenceScore": 65}
        if "lease" in fn or "rental" in fn:
            return {"contractType": "Lease Agreement", "confidenceScore": 65}
        if "nda" in fn or "non-disclosure" in fn:
            return {"contractType": "NDA", "confidenceScore": 65}
        if "service" in fn:
            return {"contractType": "Service Agreement", "confidenceScore": 60}

        return {"contractType": "General Contract", "confidenceScore": 50}

    except Exception as e:
        print("[CLASSIFY ERROR]", e)
        return {"contractType": "unknown", "confidenceScore": 0}


# =========================================================
# CLAUSE EXTRACTION (RULE BASED)
# =========================================================

def extract_clauses(text):
    clause_names = [
        "Confidentiality",
        "Termination",
        "Payment Terms",
        "Limitation of Liability",
        "Indemnification",
        "Governing Law",
        "Dispute Resolution",
        "Intellectual Property",
        "Force Majeure",
        "Arbitration",
    ]

    return [find_clause_in_text(text, name) for name in clause_names]


def find_clause_in_text(text, clause_name):
    """
    Improved clause extraction with better section boundary detection.
    Prioritizes finding clause name as a heading, then falls back to keyword search.
    """
    import re

    text_lower = text.lower()
    clause_lower = clause_name.lower()

    matches = []
    context_sentences = []
    match_count = 0
    first_match_pos = -1
    clause_text = ''

    print(f"[EXTRACT] Searching for clause: {clause_name}")

    # STRATEGY 1: Find clause name as a HEADING (most reliable)
    # Patterns to detect section headings:
    # - "Confidentiality" or "CONFIDENTIALITY" on its own line
    # - "1. Confidentiality" or "1.1 Confidentiality"
    # - "Article 1: Confidentiality" or "ARTICLE 7 — CONFIDENTIALITY"
    heading_patterns = [
        rf'(?:^|\n\n)({re.escape(clause_name)})\s*[\n:]',  # Clause name on its own line
        rf'(?:^|\n\n)({re.escape(clause_name.upper())})\s*[\n:]',  # ALL CAPS
        rf'(?:^|\n)\d+\.?\d*\.?\s*({re.escape(clause_name)})',  # "1. Confidentiality"
        rf'(?:^|\n)(?:ARTICLE|Article|SECTION|Section|CLAUSE|Clause)\s+\d+\s*[:.;—–-]+\s*({re.escape(clause_name.upper())})',  # "ARTICLE 7 — CONFIDENTIALITY"
        rf'(?:^|\n)(?:Article|Section|Clause)\s+\d+\s*[:.;—–-]+\s*({re.escape(clause_name)})',  # "Article 7 — Confidentiality"
    ]

    heading_match = None
    for pattern in heading_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            heading_match = match
            first_match_pos = match.start()
            break

    if heading_match:
        print(f"[EXTRACT] ✓ Found '{clause_name}' as HEADING at position {heading_match.start()}")

        # Extract from this heading to the next section heading
        section_start = heading_match.start()

        # Find the NEXT section heading after the current one.
        # Matches: "ARTICLE 8", "Article 8", "Section 8", "8.", "8.1" at line start,
        # or ALL-CAPS standalone headings like "TERMINATION\n"
        # Uses \n (single) so it also catches sections separated by page-break markers.
        search_text = text[section_start + len(heading_match.group(0)):]
        next_section_pattern = re.compile(
            r'(?:^|\n)'
            r'(?:'
            r'(?:ARTICLE|Article|SECTION|Section|CLAUSE|Clause)\s+\d+'  # Article 8 / Section 3
            r'|(?:---\s*Page\s*\d+\s*---)'                              # --- Page 5 ---
            r'|\d+\.\s+[A-Z][A-Za-z]'                                  # 8. Termination
            r'|[A-Z][A-Z\s\-]{6,}\n'                                   # ALL CAPS HEADING\n
            r')',
            re.MULTILINE,
        )
        next_match = next_section_pattern.search(search_text)

        if next_match:
            section_end = section_start + len(heading_match.group(0)) + next_match.start()
        else:
            # No next section found — cap at 2000 chars to avoid runaway
            section_end = min(section_start + 2000, len(text))

        clause_text = text[section_start:section_end].strip()
        print(f"[EXTRACT] Extracted section from {section_start} to {section_end} ({len(clause_text)} chars)")
        print(f"[EXTRACT] First 150 chars: {clause_text[:150]}")
        match_count = 1

        # Build context sentence from the heading line
        heading_line_end = text.find("\n", section_start + 1)
        if heading_line_end == -1:
            heading_line_end = min(section_start + 150, len(text))

        heading_sentence = text[section_start:heading_line_end].strip()

        context_sentences.append({
            "text": heading_sentence,
            "keyword": clause_name,
            "keywordStart": heading_match.start(1) - section_start,
            "keywordEnd": heading_match.end(1) - section_start,
            "start": section_start,
            "end": heading_line_end
        })

        # textSpans stores only the SHORT heading line (for keyword highlighting in the UI)
        # Full clause body is in clauseText / extracted_text
        matches.append({
            "text": heading_sentence,
            "start": section_start,
            "end": heading_line_end
        })

    else:
        print(f"[EXTRACT] ✗ '{clause_name}' NOT found as heading - using keyword fallback")

        # STRATEGY 2: Keyword search (fallback when not found as heading)
        start = 0
        while True:
            pos = text_lower.find(clause_lower, start)
            if pos == -1:
                break

            if first_match_pos == -1:
                first_match_pos = pos
                print(f"[EXTRACT] Found keyword '{clause_name}' at position {pos}")

            # Extract sentence containing the keyword
            sentence_start = text.rfind(".", 0, pos)
            sentence_start = sentence_start + 1 if sentence_start != -1 else 0

            sentence_end = text.find(".", pos + len(clause_name))
            sentence_end = sentence_end + 1 if sentence_end != -1 else len(text)

            sentence = text[sentence_start:sentence_end].strip()

            keyword_start_in_sentence = pos - sentence_start
            keyword_end_in_sentence = keyword_start_in_sentence + len(clause_name)

            matches.append({
                "text": sentence,
                "start": sentence_start,
                "end": sentence_end
            })

            context_sentences.append({
                "text": sentence,
                "keyword": clause_name,
                "keywordStart": keyword_start_in_sentence,
                "keywordEnd": keyword_end_in_sentence,
                "start": sentence_start,
                "end": sentence_end
            })

            match_count += 1
            start = pos + 1

        # Try to extract the surrounding section for the first match
        if first_match_pos != -1 and not clause_text:
            # Find section boundaries using comprehensive patterns
            section_pattern = r'(?:^|\n\n)(?:\d+\.(?:\d+)?\.?\s+[A-Z]|(?:Article|Section|Clause)\s+\d+|[A-Z][A-Z\s]{8,}\n)'
            section_matches = list(re.finditer(section_pattern, text, re.MULTILINE))

            para_start = 0
            para_end = len(text)

            # Find which section contains our keyword
            for i, sec_match in enumerate(section_matches):
                next_section_start = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(text)

                if sec_match.start() <= first_match_pos < next_section_start:
                    para_start = sec_match.start()
                    para_end = next_section_start
                    break

            # If section not found or too large, use paragraph breaks
            if para_end - para_start > 2000 or para_start == 0:
                # Look for double newlines (paragraph breaks)
                para_start = text.rfind("\n\n", max(0, first_match_pos - 600), first_match_pos)
                para_start = para_start + 2 if para_start != -1 else max(0, first_match_pos - 400)

                para_end = text.find("\n\n", first_match_pos + len(clause_name))
                para_end = para_end if para_end != -1 else min(first_match_pos + 1200, len(text))

            # Limit to reasonable length
            if para_end - para_start > 2500:
                para_end = min(para_start + 2500, len(text))

            clause_text = text[para_start:para_end].strip()

    # Calculate confidence based on match quality
    confidence = 0
    if match_count > 0:
        # Base score: 50 for keyword-only, 65 for heading match
        base = 65 if heading_match else 50

        # Text quality bonus: longer extracted text = more complete clause
        text_len = len(clause_text)
        if text_len > 1500:
            text_bonus = 20
        elif text_len > 800:
            text_bonus = 14
        elif text_len > 300:
            text_bonus = 8
        elif text_len > 100:
            text_bonus = 4
        else:
            text_bonus = 0

        # Keyword density bonus: multiple mentions = more relevant
        density_bonus = min(10, match_count * 3)

        # Clause-specific keywords that indicate rich content
        rich_keywords = ['shall', 'party', 'agreement', 'obligation', 'liability', 'damages',
                         'terminate', 'govern', 'arbitration', 'confidential', 'payment', 'force majeure']
        text_lower_check = clause_text.lower()
        richness_bonus = min(5, sum(1 for kw in rich_keywords if kw in text_lower_check))

        confidence = min(98, base + text_bonus + density_bonus + richness_bonus)

    print(f"[EXTRACT] Final result for '{clause_name}': found={match_count > 0}, confidence={confidence}, text_length={len(clause_text)}")

    return {
        "clauseName": clause_name,
        "found": match_count > 0,
        "confidence": confidence,
        "matchCount": match_count,
        "textSpans": matches,
        "contextSentences": context_sentences,
        "clauseText": clause_text,
    }


def auto_correct_clause(clause_text):
    """
    Use LLM to generate a safer alternative for a risky clause

    Args:
        clause_text (str): The original risky clause text

    Returns:
        dict: {
            'suggested_text': str,
            'explanation': str
        }
    """
    import requests
    import os
    from django.conf import settings

    OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_API = os.environ.get("OLLAMA_API", f"{OLLAMA_BASE_URL}/api/chat")
    OLLAMA_MODEL = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:0.5b')

    prompt = f"""You are a legal contract expert. Rewrite the following clause to reduce legal risk while maintaining the original intent.

Original Clause:
{clause_text}

Instructions:
- Make the language more balanced and fair
- Reduce one-sided obligations
- Add reasonable safeguards
- Keep it concise and professional
- Maintain the core business purpose

Provide ONLY the rewritten clause, nothing else."""

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0.3, "num_predict": 500},
            "stream": False
        }

        response = requests.post(OLLAMA_API, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        suggested_text = result.get('message', {}).get('content', '').strip()

        return {
            'suggested_text': suggested_text,
            'explanation': 'Rewritten to reduce legal risk and improve fairness'
        }

    except Exception as e:
        print(f'Auto-correction error: {str(e)}')
        return {
            'suggested_text': clause_text,
            'explanation': f'Error generating suggestion: {str(e)}'
        }


# =========================================================
# PDF MODIFICATION WITH ACCEPTED CLAUSE CHANGES
# =========================================================

def create_modified_pdf(original_pdf_path, clause_changes, contract_name):
    """
    Create a modified PDF by copying the original and adding modification annotations.
    This preserves the exact original PDF format and structure.

    Args:
        original_pdf_path: Path to the original PDF file
        clause_changes: List of dicts with {clause_name, original_text, accepted_text}
        contract_name: Name of the contract for the output filename

    Returns:
        str: Path to the newly created modified PDF
    """
    import fitz  # PyMuPDF for text search and highlighting
    from datetime import datetime
    import re

    try:
        # Create output directory
        output_dir = os.path.join(settings.MEDIA_ROOT, 'modified_contracts')
        os.makedirs(output_dir, exist_ok=True)

        # Generate unique filename
        timestamp = int(datetime.now().timestamp() * 1000)
        safe_contract_name = re.sub(r'[^\w\-_.]', '_', contract_name)
        if safe_contract_name.lower().endswith('.pdf'):
            safe_contract_name = safe_contract_name[:-4]
        output_filename = f'{timestamp}-Modified_{safe_contract_name}.pdf'
        output_path = os.path.join(output_dir, output_filename)

        # Check if original PDF exists
        if not os.path.exists(original_pdf_path):
            filename = os.path.basename(original_pdf_path)
            alternative_path = os.path.join(settings.MEDIA_ROOT, filename)
            if os.path.exists(alternative_path):
                original_pdf_path = alternative_path
            else:
                raise FileNotFoundError(f'Original PDF not found: {original_pdf_path}')

        # Open PDF with PyMuPDF
        doc = fitz.open(original_pdf_path)

        print(f'[PDF_MODIFY] Processing PDF ({len(doc)} pages)')
        print(f'[PDF_MODIFY] Searching and highlighting {len(clause_changes)} clauses')

        total_highlights = 0
        annotation_count = 0

        # Process each clause change
        for idx, change in enumerate(clause_changes, 1):
            clause_name = change.get('clause_name', 'Unknown')
            original_text = change.get('original_text', '').strip()
            accepted_text = change.get('accepted_text', '').strip()

            # Check if this is a MISSING clause (description starts with "Missing")
            is_missing_clause = original_text.lower().startswith('missing')

            if is_missing_clause:
                # For missing clauses, add a prominent annotation on the last page
                print(f'[PDF_MODIFY] Adding note for MISSING clause: "{clause_name}"')

                last_page = doc[-1]
                # Add annotation at top right of last page
                y_position = 100 + (idx * 60)  # Stack annotations vertically

                annot = last_page.add_text_annot(
                    point=(last_page.rect.width - 100, y_position),
                    text=f"⚠ MISSING CLAUSE #{idx}: {clause_name}\n\n"
                         f"Issue:\n{original_text}\n\n"
                         f"Suggested Addition:\n{accepted_text[:300]}{'...' if len(accepted_text) > 300 else ''}",
                    icon="Note"
                )
                annot.set_colors(stroke=[1, 0, 0])  # Red icon
                annot.set_opacity(0.9)
                annot.update()

                annotation_count += 1
                total_highlights += 1

            else:
                # For existing clauses, search and highlight the text
                search_text = original_text[:100] if len(original_text) > 100 else original_text
                search_text = search_text.strip()

                found_instances = 0

                # Search through each page
                for page_num in range(len(doc)):
                    page = doc[page_num]

                    # Search for text instances on this page
                    text_instances = page.search_for(search_text)

                    if text_instances:
                        print(f'[PDF_MODIFY] Found "{clause_name}" on page {page_num + 1}')

                        for inst in text_instances:
                            # Highlight the original text in orange
                            highlight = page.add_highlight_annot(inst)
                            highlight.set_colors(stroke=[1, 0.6, 0])  # Orange highlight
                            highlight.set_opacity(0.5)
                            highlight.update()

                            # Add a text annotation (sticky note) with the replacement
                            annot = page.add_text_annot(
                                point=(inst.x1 + 5, inst.y0 - 5),
                                text=f"CHANGE #{idx}: {clause_name}\n\n"
                                     f"Current Text (Risky):\n{original_text[:200]}{'...' if len(original_text) > 200 else ''}\n\n"
                                     f"Suggested Replacement:\n{accepted_text[:200]}{'...' if len(accepted_text) > 200 else ''}",
                                icon="Comment"
                            )
                            annot.set_colors(stroke=[1, 0, 0])  # Red icon
                            annot.set_opacity(0.9)
                            annot.update()

                            annotation_count += 1
                            found_instances += 1

                        total_highlights += len(text_instances)

                if found_instances == 0:
                    print(f'[PDF_MODIFY] Could not locate "{clause_name}" text - adding general note')
                    # If we can't find it, add a note to the last page
                    last_page = doc[-1]
                    y_position = 100 + (idx * 60)

                    annot = last_page.add_text_annot(
                        point=(last_page.rect.width - 100, y_position),
                        text=f"CHANGE #{idx}: {clause_name}\n\n"
                             f"Original:\n{original_text[:150]}...\n\n"
                             f"Replace with:\n{accepted_text[:150]}...",
                        icon="Help"
                    )
                    annot.set_colors(stroke=[1, 0.5, 0])
                    annot.update()
                    annotation_count += 1

        # Add a header banner to the first page
        first_page = doc[0]
        header_rect = fitz.Rect(0, 0, first_page.rect.width, 40)

        # Draw yellow warning banner
        shape = first_page.new_shape()
        shape.draw_rect(header_rect)
        shape.finish(fill=[1, 0.95, 0.8], color=[0.9, 0.6, 0])  # Light yellow fill, orange border
        shape.commit()

        # Add text to banner
        text_point = fitz.Point(40, 25)
        first_page.insert_text(
            text_point,
            f"MODIFIED CONTRACT - {len(clause_changes)} Clause(s) Highlighted for Change",
            fontsize=10,
            color=[0.5, 0.3, 0],
            fontname="helv"
        )

        text_point2 = fitz.Point(40, 38)
        first_page.insert_text(
            text_point2,
            f"Click on orange highlights to see suggested changes | {total_highlights} location(s) marked",
            fontsize=8,
            color=[0.5, 0.3, 0],
            fontname="helv"
        )

        # Add metadata
        doc.set_metadata({
            'title': f'Modified - {contract_name}',
            'author': 'ContractAI - Risky Clause Redlining',
            'subject': f'{len(clause_changes)} clause(s) marked for modification',
            'creator': 'ContractAI',
            'producer': 'PyMuPDF'
        })

        # Save the modified PDF
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()

        print(f'[PDF_MODIFY] Successfully created modified PDF: {output_path}')
        return output_path

    except Exception as e:
        print(f'[PDF_MODIFY] Error creating modified PDF: {str(e)}')
        import traceback
        traceback.print_exc()
        raise Exception(f'Failed to create modified PDF: {str(e)}')


# =========================================================
# SEMANTIC QUERY PARSING FOR AI CHAT
# =========================================================

def parse_semantic_query(query):
    """
    Parse user query to extract semantic intent and metadata filters

    Args:
        query (str): User's natural language query

    Returns:
        dict: {
            'filters': dict with metadata filters,
            'search_terms': list of extracted keywords,
            'semantic_query': cleaned query for RAG
        }
    """
    query_lower = query.lower().strip()
    filters = {}
    search_terms = []

    # Risk level detection - expanded patterns
    if any(term in query_lower for term in ['low risk', 'low-risk', 'minimal risk', 'safe contract', 'with low risk']):
        filters['risk_level'] = 'LOW'
        search_terms.extend(['low risk', 'safe', 'minimal risk'])
    elif any(term in query_lower for term in ['medium risk', 'moderate risk', 'with medium risk']):
        filters['risk_level'] = 'MEDIUM'
        search_terms.extend(['medium risk', 'moderate risk'])
    elif any(term in query_lower for term in ['high risk', 'risky', 'dangerous', 'with high risk', 'that are high risk', 'that have high risk']):
        filters['risk_level'] = 'HIGH'
        search_terms.extend(['high risk', 'risky'])
    elif any(term in query_lower for term in ['critical risk', 'very risky', 'critical', 'with critical risk']):
        filters['risk_level'] = 'CRITICAL'
        search_terms.extend(['critical', 'critical risk'])

    # Contract type detection
    contract_types = {
        'employment': ['employment', 'job', 'employee', 'hiring', 'employment contract'],
        'nda': ['nda', 'non-disclosure', 'confidentiality agreement', 'non disclosure'],
        'service': ['service agreement', 'msa', 'master service', 'service contract'],
        'lease': ['lease', 'rental', 'rent', 'lease agreement'],
        'purchase': ['purchase', 'vendor', 'procurement', 'purchase agreement'],
        'consulting': ['consulting', 'consultant', 'consulting agreement'],
        'license': ['license', 'licensing', 'license agreement'],
        'partnership': ['partnership', 'joint venture', 'partnership agreement'],
    }

    for contract_type, keywords in contract_types.items():
        if any(kw in query_lower for kw in keywords):
            filters['contract_type_contains'] = contract_type
            search_terms.append(contract_type)
            break

    # Liability level detection
    if any(term in query_lower for term in ['low liability', 'minimal liability']):
        filters['liability_level'] = 'LOW'
    elif any(term in query_lower for term in ['medium liability', 'moderate liability']):
        filters['liability_level'] = 'MEDIUM'
    elif any(term in query_lower for term in ['high liability', 'significant liability']):
        filters['liability_level'] = 'HIGH'

    # Arbitration detection
    if any(term in query_lower for term in ['arbitration', 'arbitration clause', 'with arbitration']):
        filters['has_arbitration'] = True
    elif any(term in query_lower for term in ['no arbitration', 'without arbitration']):
        filters['has_arbitration'] = False

    # Jurisdiction detection
    jurisdictions = ['dubai', 'uae', 'usa', 'uk', 'india', 'singapore', 'hong kong', 'california', 'new york', 'delaware']
    for jurisdiction in jurisdictions:
        if jurisdiction in query_lower:
            filters['jurisdiction_contains'] = jurisdiction
            search_terms.append(jurisdiction)
            break

    # Status detection
    if any(term in query_lower for term in ['approved', 'approved contract']):
        filters['status'] = 'APPROVED'
    elif any(term in query_lower for term in ['draft', 'draft contract']):
        filters['status'] = 'DRAFT'
    elif any(term in query_lower for term in ['rejected', 'rejected contract']):
        filters['status'] = 'REJECTED'

    # Value-based queries
    if any(term in query_lower for term in ['high value', 'expensive', 'large contract']):
        search_terms.extend(['high value', 'expensive'])

    # List/show contracts detection
    list_triggers = ['show me', 'list', 'show all', 'display', 'get all', 'what', 'which', 'my']
    contract_terms = ['uploaded', 'my contract', 'all contract', 'contracts', 'contract']

    # Also detect very simple queries like "contracts?" or "my contracts?"
    simple_list_patterns = ['contracts?', 'my contracts?', 'contracts', 'my contracts', 'all contracts']
    is_simple_list = any(query_lower.strip() == pattern for pattern in simple_list_patterns)

    if any(term in query_lower for term in list_triggers):
        if any(term in query_lower for term in contract_terms):
            # Check if this is a simple listing request (not a clause search)
            clause_search = any(clause in query_lower for clause in ['termination', 'payment', 'liability', 'clause', 'terms', 'termination'])
            if not clause_search and not filters:  # Only show all if no specific filters
                filters['show_all'] = True

    # Handle simple list patterns
    if is_simple_list and not filters:
        filters['show_all'] = True

    # Extract key clause-related terms
    clause_keywords = [
        'termination', 'payment', 'liability', 'indemnification',
        'confidentiality', 'intellectual property', 'force majeure',
        'dispute resolution', 'governing law', 'warranty', 'damages'
    ]

    for keyword in clause_keywords:
        if keyword in query_lower:
            search_terms.append(keyword)

    # Clean the query for RAG (remove filter words, keep semantic meaning)
    semantic_query = query
    # Only remove common action words, but keep "contracts" as it has semantic value
    for term in ['show me', 'find all', 'find', 'get', 'list all', 'list']:
        semantic_query = semantic_query.replace(term, ' ')
    semantic_query = ' '.join(semantic_query.split())  # Clean extra spaces

    return {
        'filters': filters,
        'search_terms': search_terms,
        'semantic_query': semantic_query if semantic_query.strip() else query
    }
