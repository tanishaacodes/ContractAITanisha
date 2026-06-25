"""
OCR Text Cleaner
================
Fixes common OCR misreading errors in extracted text.

Common OCR Errors:
- '1' (one) misread as 'i' or 'l'
- '0' (zero) misread as 'O'
- 'rn' misread as 'm'
- Special characters corrupted

Usage:
    from api.ocr_text_cleaner import clean_ocr_text

    dirty_text = "c0ntract obl1gat10ns"
    clean_text = clean_ocr_text(dirty_text)
    # Returns: "contract obligations"
"""

import re
import logging

logger = logging.getLogger(__name__)


class OCRTextCleaner:
    """
    Cleans and corrects common OCR errors in extracted text.
    """

    # Common OCR misreading patterns
    OCR_ERROR_PATTERNS = {
        # Number-letter confusion in common legal words
        r'\bobl1gat10ns?\b': 'obligations',
        r'\bT10ns?\b': 'tions',
        r'\bc0ntract\b': 'contract',
        r'\bc0nfidential\b': 'confidential',
        r'\bliab1lity\b': 'liability',
        r'\bpenalt1es?\b': 'penalties',
        r'\bterminat10n\b': 'termination',
        r'\bindemn1ty\b': 'indemnity',
        r'\barb1trat10n\b': 'arbitration',
        r'\bpaym3nt\b': 'payment',
        r'\bagre3ment\b': 'agreement',

        # Common 0/O confusion
        r'\bc0mpany\b': 'company',
        r'\bc0mpliance\b': 'compliance',
        r'\bc0mpensation\b': 'compensation',

        # l/1 confusion
        r'\bc1ause\b': 'clause',
        r'\blega1\b': 'legal',

        # Double character misreading
        r'\brn\b': 'm',  # 'rn' often misread as 'm'
    }

    # Legal terminology spell check (common words)
    LEGAL_TERMS = {
        'agrcement': 'agreement',
        'agreeement': 'agreement',
        'contarct': 'contract',
        'contraact': 'contract',
        'obligaton': 'obligation',
        'obligaion': 'obligation',
        'liablity': 'liability',
        'liabilty': 'liability',
        'terminaton': 'termination',
        'termintion': 'termination',
        'arbitraton': 'arbitration',
        'arbitration': 'arbitration',
        'confidetial': 'confidential',
        'confidental': 'confidential',
        'indemnty': 'indemnity',
        'indemity': 'indemnity',
    }

    def __init__(self):
        """Initialize the OCR text cleaner."""
        logger.info("OCRTextCleaner initialized")

    def clean(self, text: str) -> str:
        """
        Clean OCR errors from text.

        Args:
            text (str): Dirty text from OCR

        Returns:
            str: Cleaned text
        """
        if not text:
            return text

        original_length = len(text)
        cleaned_text = text

        # Fix OCR error patterns (regex-based)
        for pattern, replacement in self.OCR_ERROR_PATTERNS.items():
            cleaned_text = re.sub(pattern, replacement, cleaned_text, flags=re.IGNORECASE)

        # Fix common misspellings (whole word replacement)
        words = cleaned_text.split()
        corrected_words = []

        for word in words:
            # Remove punctuation for matching
            clean_word = re.sub(r'[^\w]', '', word.lower())

            if clean_word in self.LEGAL_TERMS:
                # Replace with correct term, preserving case
                if word[0].isupper():
                    correction = self.LEGAL_TERMS[clean_word].capitalize()
                else:
                    correction = self.LEGAL_TERMS[clean_word]

                # Restore punctuation
                corrected_word = re.sub(re.escape(clean_word), correction, word, flags=re.IGNORECASE)
                corrected_words.append(corrected_word)
            else:
                corrected_words.append(word)

        cleaned_text = ' '.join(corrected_words)

        # Fix common spacing issues
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Multiple spaces → single space
        cleaned_text = re.sub(r'\s+([.,;:])', r'\1', cleaned_text)  # Space before punctuation
        cleaned_text = cleaned_text.strip()

        # Log if significant changes were made
        changes = original_length - len(cleaned_text)
        if abs(changes) > 10:
            logger.info(f"OCR cleaning: {original_length} → {len(cleaned_text)} chars ({changes:+d})")

        return cleaned_text

    def clean_clause(self, clause_text: str) -> str:
        """
        Clean a single clause text.

        Args:
            clause_text (str): Clause text from OCR

        Returns:
            str: Cleaned clause text
        """
        return self.clean(clause_text)


# Singleton instance
_cleaner_instance = None


def get_ocr_cleaner() -> OCRTextCleaner:
    """
    Get singleton instance of OCR text cleaner.

    Returns:
        OCRTextCleaner: The cleaner instance
    """
    global _cleaner_instance
    if _cleaner_instance is None:
        _cleaner_instance = OCRTextCleaner()
    return _cleaner_instance


# Convenience function
def clean_ocr_text(text: str) -> str:
    """
    Quick cleaning for OCR text.

    Args:
        text (str): Dirty OCR text

    Returns:
        str: Cleaned text

    Example:
        >>> clean_ocr_text("c0ntract obl1gat10ns")
        'contract obligations'
    """
    cleaner = get_ocr_cleaner()
    return cleaner.clean(text)
