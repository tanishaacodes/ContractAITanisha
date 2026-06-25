"""
Document Reader
===============
Extracts plain text from TXT, DOCX, and PDF files.

PDF fallback chain (tries each library in order):
  1. pdfplumber  — best for digital PDFs
  2. pypdf        — lightweight pure-python fallback
  3. PyMuPDF (fitz) — handles encrypted / complex PDFs
  4. pdfminer.six — last resort character-level extraction

All four libraries are already in requirements.txt.
"""

import logging
import unicodedata
import re

logger = logging.getLogger(__name__)


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


def extract_text(file_path: str) -> str:
    """
    Extract text from a contract file.

    Supports: .txt, .docx, .pdf

    Returns:
        Extracted plain text (may be empty for image-only scans).

    Raises:
        ValueError: Unsupported format or all PDF extractors failed.
    """
    ext = file_path.lower().rsplit(".", 1)[-1]

    if ext == "txt":
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
            return normalize_extracted_text(text)

    elif ext == "docx":
        text = _extract_docx(file_path)
        return normalize_extracted_text(text)

    elif ext == "pdf":
        text = _extract_pdf(file_path)
        return normalize_extracted_text(text)

    else:
        raise ValueError(f"Unsupported file format: .{ext}. Supported: txt, docx, pdf")


# ─────────────────────────────────────────────────────────────────────────────
# DOCX
# ─────────────────────────────────────────────────────────────────────────────

def _extract_docx(file_path: str) -> str:
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        raise ValueError(f"Could not read DOCX file: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# PDF — fallback chain
# ─────────────────────────────────────────────────────────────────────────────

def _extract_pdf(file_path: str) -> str:
    errors = []

    # 1. pdfplumber
    try:
        text = _pdf_pdfplumber(file_path)
        if text.strip():
            logger.info(f"[PDF] Extracted via pdfplumber: {len(text)} chars")
            return text
        logger.warning("[PDF] pdfplumber returned empty text, trying next extractor.")
    except Exception as e:
        errors.append(f"pdfplumber: {e}")
        logger.warning(f"[PDF] pdfplumber failed: {e}")

    # 2. pypdf
    try:
        text = _pdf_pypdf(file_path)
        if text.strip():
            logger.info(f"[PDF] Extracted via pypdf: {len(text)} chars")
            return text
        logger.warning("[PDF] pypdf returned empty text, trying next extractor.")
    except Exception as e:
        errors.append(f"pypdf: {e}")
        logger.warning(f"[PDF] pypdf failed: {e}")

    # 3. PyMuPDF (fitz)
    try:
        text = _pdf_pymupdf(file_path)
        if text.strip():
            logger.info(f"[PDF] Extracted via PyMuPDF: {len(text)} chars")
            return text
        logger.warning("[PDF] PyMuPDF returned empty text, trying next extractor.")
    except Exception as e:
        errors.append(f"PyMuPDF: {e}")
        logger.warning(f"[PDF] PyMuPDF failed: {e}")

    # 4. pdfminer.six
    try:
        text = _pdf_pdfminer(file_path)
        if text.strip():
            logger.info(f"[PDF] Extracted via pdfminer: {len(text)} chars")
            return text
        logger.warning("[PDF] pdfminer returned empty text.")
    except Exception as e:
        errors.append(f"pdfminer: {e}")
        logger.warning(f"[PDF] pdfminer failed: {e}")

    # All extractors either failed or returned nothing
    if errors:
        raise ValueError(
            f"All PDF extractors failed. Errors: {' | '.join(errors)}. "
            "The PDF may be scanned/image-based (no selectable text)."
        )

    # Extractors ran but returned empty — likely a scanned PDF
    raise ValueError(
        "PDF appears to be image-based (scanned). No selectable text found. "
        "Please paste the contract text manually instead."
    )


def _pdf_pdfplumber(file_path: str) -> str:
    import pdfplumber
    parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                # Normalize each page's text
                t = normalize_extracted_text(t)
                parts.append(t)
    return "\n".join(parts)


def _pdf_pypdf(file_path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader  # older name
    reader = PdfReader(file_path)
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            # Normalize each page's text
            t = normalize_extracted_text(t)
            parts.append(t)
    return "\n".join(parts)


def _pdf_pymupdf(file_path: str) -> str:
    import fitz  # PyMuPDF
    doc = fitz.open(file_path)
    parts = []
    for page in doc:
        t = page.get_text()
        if t:
            # Normalize each page's text
            t = normalize_extracted_text(t)
            parts.append(t)
    doc.close()
    return "\n".join(parts)


def _pdf_pdfminer(file_path: str) -> str:
    from pdfminer.high_level import extract_text as pdfminer_extract
    text = pdfminer_extract(file_path) or ""
    # Normalize the extracted text
    return normalize_extracted_text(text)


# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_string(raw_text: str) -> str:
    """Pass-through for plain text already in memory."""
    return raw_text.strip()
