"""
Clause Extraction Module
=========================
Extracts and segments clauses from contract text using pattern matching.

This module provides functionality to split contract documents into individual
clauses based on common legal document formatting patterns.
"""

import re
from typing import List, Dict


# Pattern definitions for identifying clause boundaries
CLAUSE_PATTERNS = [
    r"\n\d+\.\s+",                      # Numbered clauses: "1. ", "2. ", etc.
    r"\n\d+\.\d+\s+",                    # Sub-numbered: "1.1 ", "2.3 ", etc.
    r"\n[A-Z][A-Z\s]{3,}:",              # ALL CAPS HEADERS: "PAYMENT TERMS:"
    r"\nSection\s+\d+",                  # Section numbering: "Section 1"
    r"\nArticle\s+\d+",                  # Article numbering: "Article 1"
    r"\nClause\s+\d+",                   # Explicit clause: "Clause 1"
    r"\n\([a-z]\)\s+",                   # Lettered sub-clauses: "(a) ", "(b) "
    r"\n\([ivxlcdm]+\)\s+",              # Roman numeral sub-clauses: "(i) ", "(ii) "
]


def split_into_clauses(text: str, min_length: int = 50) -> List[str]:
    """
    Split contract text into individual clauses using pattern matching.

    Args:
        text (str): The full contract text to split
        min_length (int): Minimum character length for a valid clause (default: 50)

    Returns:
        List[str]: List of extracted clause texts

    Example:
        >>> text = "1. Payment Terms\\nPayment shall be made...\\n2. Liability\\nThe parties agree..."
        >>> clauses = split_into_clauses(text)
        >>> len(clauses)
        2
    """
    if not text or not isinstance(text, str):
        return []

    # Combine all patterns with OR (|)
    combined_pattern = "|".join(CLAUSE_PATTERNS)

    # Split text using the combined pattern
    splits = re.split(combined_pattern, text)

    # Filter and clean clauses
    clauses = []
    for clause in splits:
        # Strip whitespace
        cleaned = clause.strip()

        # Skip if too short or empty
        if len(cleaned) < min_length:
            continue

        # Normalize whitespace (collapse multiple spaces/newlines)
        cleaned = re.sub(r'\s+', ' ', cleaned)

        clauses.append(cleaned)

    return clauses


def extract_clause_with_metadata(text: str, min_length: int = 50) -> List[Dict[str, any]]:
    """
    Extract clauses with additional metadata about their structure.

    Args:
        text (str): The full contract text
        min_length (int): Minimum character length for a valid clause

    Returns:
        List[Dict]: List of clause objects with metadata

    Example:
        >>> clauses = extract_clause_with_metadata(contract_text)
        >>> clauses[0]
        {
            'text': 'Payment shall be made within 30 days...',
            'clause_number': '1',
            'start_position': 0,
            'end_position': 245,
            'word_count': 42
        }
    """
    if not text or not isinstance(text, str):
        return []

    clauses_metadata = []
    current_position = 0

    # Combined pattern for splitting
    combined_pattern = "|".join(CLAUSE_PATTERNS)

    # Find all matches (clause headers)
    matches = list(re.finditer(combined_pattern, text))

    # Extract text between matches
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        clause_text = text[start:end].strip()

        # Skip if too short
        if len(clause_text) < min_length:
            continue

        # Extract clause number/identifier from the header
        header = match.group(0).strip()
        clause_number = re.search(r'\d+', header)
        clause_number = clause_number.group(0) if clause_number else str(i + 1)

        # Normalize whitespace
        clause_text = re.sub(r'\s+', ' ', clause_text)

        clauses_metadata.append({
            'text': clause_text,
            'clause_number': clause_number,
            'header': header,
            'start_position': start,
            'end_position': end,
            'word_count': len(clause_text.split()),
            'char_count': len(clause_text)
        })

    return clauses_metadata


def identify_clause_type_by_keywords(clause_text: str) -> str:
    """
    Identify potential clause type based on keyword matching.

    This provides a basic heuristic classification before LLM processing.

    Args:
        clause_text (str): The clause text to analyze

    Returns:
        str: Identified clause type or 'General' if no match
    """
    clause_lower = clause_text.lower()

    # Keyword mapping for common clause types
    keyword_map = {
        'Payment': ['payment', 'invoice', 'fee', 'compensation', 'remuneration'],
        'Termination': ['terminate', 'termination', 'cancellation', 'cancel'],
        'Liability': ['liability', 'indemnity', 'indemnification', 'damages'],
        'Confidentiality': ['confidential', 'nda', 'non-disclosure', 'proprietary'],
        'Intellectual Property': ['intellectual property', 'ip', 'copyright', 'patent', 'trademark'],
        'Warranty': ['warranty', 'warranties', 'guarantee', 'representation'],
        'Dispute Resolution': ['dispute', 'arbitration', 'mediation', 'jurisdiction'],
        'Force Majeure': ['force majeure', 'act of god', 'unavoidable'],
        'Governing Law': ['governing law', 'jurisdiction', 'applicable law'],
        'Assignment': ['assignment', 'assign', 'transfer'],
        'Amendment': ['amendment', 'modify', 'modification', 'change'],
        'Severability': ['severability', 'severable', 'validity'],
        'Entire Agreement': ['entire agreement', 'whole agreement', 'complete agreement'],
    }

    # Count keyword matches for each type
    type_scores = {}
    for clause_type, keywords in keyword_map.items():
        score = sum(1 for keyword in keywords if keyword in clause_lower)
        if score > 0:
            type_scores[clause_type] = score

    # Return type with highest score, or 'General' if no matches
    if type_scores:
        return max(type_scores, key=type_scores.get)

    return 'General'


def merge_short_clauses(clauses: List[str], min_merge_length: int = 100) -> List[str]:
    """
    Merge very short clauses with their neighbors to avoid fragmentation.

    Args:
        clauses (List[str]): List of extracted clauses
        min_merge_length (int): Minimum length before merging with next clause

    Returns:
        List[str]: List of clauses with short ones merged
    """
    if not clauses:
        return []

    merged = []
    current = clauses[0]

    for clause in clauses[1:]:
        if len(current) < min_merge_length:
            # Merge with next clause
            current = f"{current} {clause}"
        else:
            # Add current to results and start new one
            merged.append(current)
            current = clause

    # Add the last clause
    if current:
        merged.append(current)

    return merged
