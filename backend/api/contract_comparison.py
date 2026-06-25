"""
Contract Comparison Module

Provides utilities for comparing contracts using semantic similarity analysis
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


def preprocess_text(text):
    """
    Preprocess text for comparison by cleaning and normalizing
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:!?-]', '', text)

    return text.strip()


def compute_clause_similarity(text1, text2):
    """
    Compute semantic similarity between two text clauses using TF-IDF and cosine similarity

    Args:
        text1: First clause text
        text2: Second clause text

    Returns:
        float: Similarity score between 0 and 1 (1 being identical)
    """
    if not text1 or not text2:
        return 0.0

    # Preprocess texts
    text1_clean = preprocess_text(text1)
    text2_clean = preprocess_text(text2)

    if not text1_clean or not text2_clean:
        return 0.0

    try:
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),  # Use unigrams and bigrams
            max_features=1000
        )

        # Fit and transform both texts
        tfidf_matrix = vectorizer.fit_transform([text1_clean, text2_clean])

        # Compute cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

        return float(similarity)

    except Exception as e:
        print(f"Error computing similarity: {e}")
        # Fallback to simple Jaccard similarity
        return compute_jaccard_similarity(text1_clean, text2_clean)


def compute_jaccard_similarity(text1, text2):
    """
    Compute Jaccard similarity as a fallback method

    Args:
        text1: First text
        text2: Second text

    Returns:
        float: Jaccard similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0

    # Convert to sets of words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    # Compute Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)

    if not union:
        return 0.0

    return len(intersection) / len(union)


def compare_contracts(reference_contract_id, compare_contract_ids, keywords=None):
    """
    Compare multiple contracts against a reference contract

    Args:
        reference_contract_id: ID of the reference contract
        compare_contract_ids: List of contract IDs to compare
        keywords: Optional list of keywords to search for

    Returns:
        dict: Comparison results including risk analysis, clause alignment, and keyword matches
    """
    from core.models import Contract, Clause

    try:
        # Get reference contract
        reference_contract = Contract.objects.get(id=reference_contract_id)
        ref_clauses = Clause.objects.filter(contract=reference_contract, found=True)

        # Get comparison contracts
        compare_contracts = Contract.objects.filter(id__in=compare_contract_ids)

        result = {
            'reference_contract': {
                'id': str(reference_contract.id),
                'name': reference_contract.original_filename,
                'type': reference_contract.contract_type
            },
            'compared_contracts': [],
            'clause_comparison': {
                'aligned_clauses': [],
                'total_aligned': 0
            },
            'missing_clauses': [],
            'keyword_matches': {}
        }

        # Compare each contract
        for comp_contract in compare_contracts:
            comp_clauses = Clause.objects.filter(contract=comp_contract, found=True)

            result['compared_contracts'].append({
                'id': str(comp_contract.id),
                'name': comp_contract.original_filename,
                'type': comp_contract.contract_type
            })

            # Compare clauses
            for ref_clause in ref_clauses:
                best_match = None
                best_similarity = 0

                for comp_clause in comp_clauses:
                    similarity = compute_clause_similarity(
                        ref_clause.extracted_text,
                        comp_clause.extracted_text
                    )

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = comp_clause

                if best_match and best_similarity > 0.5:
                    result['clause_comparison']['aligned_clauses'].append({
                        'clause_type': ref_clause.clause_name,
                        'similarity_score': best_similarity,
                        'reference_clause': ref_clause.extracted_text[:300],
                        'matched_clause': best_match.extracted_text[:300]
                    })

        result['clause_comparison']['total_aligned'] = len(result['clause_comparison']['aligned_clauses'])

        # Keyword matching if provided
        if keywords:
            for keyword in keywords:
                result['keyword_matches'][keyword] = []

                # Search in reference
                ref_count = reference_contract.full_text.lower().count(keyword.lower())
                result['keyword_matches'][keyword].append({
                    'contract_name': reference_contract.original_filename,
                    'is_reference': True,
                    'count': ref_count
                })

                # Search in comparison contracts
                for comp_contract in compare_contracts:
                    comp_count = comp_contract.full_text.lower().count(keyword.lower())
                    result['keyword_matches'][keyword].append({
                        'contract_name': comp_contract.original_filename,
                        'is_reference': False,
                        'count': comp_count
                    })

        return result

    except Exception as e:
        print(f"Contract comparison error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
