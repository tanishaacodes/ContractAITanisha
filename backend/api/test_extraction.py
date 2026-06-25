"""
Test suite for clause extraction accuracy (FR-11)
Target: >= 85% extraction accuracy on curated sample set
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import extract_clauses
import json

# Sample contracts with known clauses (ground truth)
TEST_CONTRACTS = [
    {
        'name': 'Sample NDA Agreement',
        'text': '''
            CONFIDENTIALITY AND NON-DISCLOSURE AGREEMENT

            This Non-Disclosure Agreement ("NDA") is entered into as of January 1, 2024.

            1. CONFIDENTIALITY OBLIGATIONS
            The Receiving Party agrees to maintain all confidential information in strict confidence.
            All proprietary information and trade secrets shall be protected under this agreement.

            2. LIMITATION OF LIABILITY
            In no event shall either party be liable for indirect, incidental, or consequential damages.
            The total liability shall not exceed the fees paid under this agreement.

            3. TERMINATION CLAUSE
            This agreement shall terminate upon 30 days written notice from either party.
            Upon termination, all confidential materials shall be returned.

            4. INTELLECTUAL PROPERTY RIGHTS
            All intellectual property, including patents and copyrights, remain the property of their owner.
            No IP rights are transferred under this agreement.

            5. ARBITRATION
            Any dispute shall be resolved through binding arbitration rather than litigation.

            6. GOVERNING LAW
            This agreement shall be governed by and construed under the laws of New York.

            7. ENTIRE AGREEMENT
            This agreement constitutes the entire agreement between the parties and supersedes all previous agreements.
        ''',
        'expected_clauses': {
            'Confidentiality': True,
            'Non-Disclosure': True,
            'Limitation of Liability': True,
            'Termination': True,
            'Intellectual Property': True,
            'Arbitration': True,
            'Governing Law': True,
            'Entire Agreement': True,
            'Indemnification': False,
            'Renewal': False,
            'Payment Terms': False,
            'Warranty': False,
            'Dispute Resolution': False,
            'Force Majeure': False,
            'Severability': False,
            'Amendment': False,
        }
    },
    {
        'name': 'Service Agreement',
        'text': '''
            SERVICE AGREEMENT

            This Service Agreement ("Agreement") is between Company A and Company B.

            PAYMENT AND COMPENSATION
            Client shall pay Service Provider a monthly fee of $10,000 for services rendered.
            Invoices shall be issued monthly, due within 30 days of receipt.

            RENEWAL AND CONTINUATION
            This agreement shall automatically renew on an annual basis unless either party provides
            written notice of non-renewal at least 60 days before the expiration date.
            The term may be extended by mutual written agreement.

            WARRANTIES AND REPRESENTATIONS
            Service Provider warrants that all services will be performed in a professional manner.
            As-is services are provided without additional warranty or guarantee.

            DISPUTE RESOLUTION AND ARBITRATION
            Any disputes arising from this agreement shall first be attempted to be resolved through
            negotiation. If negotiation fails, disputes shall proceed to binding arbitration.

            AMENDMENT TO AGREEMENT
            Any modifications or amendments to this agreement must be made in writing and signed by both parties.

            FORCE MAJEURE
            Neither party shall be held liable for failure to perform due to unforeseen circumstances or acts of God.

            INDEMNIFICATION
            Each party shall indemnify and hold harmless the other party from any third-party claims arising
            from its breach of this agreement.
        ''',
        'expected_clauses': {
            'Payment Terms': True,
            'Renewal': True,
            'Warranty': True,
            'Dispute Resolution': True,
            'Arbitration': True,
            'Amendment': True,
            'Force Majeure': True,
            'Indemnification': True,
            'Confidentiality': False,
            'Non-Disclosure': False,
            'Limitation of Liability': False,
            'Termination': False,
            'Intellectual Property': False,
            'Governing Law': False,
            'Entire Agreement': False,
            'Severability': False,
        }
    },
    {
        'name': 'Mixed Contract',
        'text': '''
            COMPREHENSIVE COMMERCIAL AGREEMENT

            CONFIDENTIALITY PROVISIONS
            All confidential and proprietary information shall be kept strictly confidential.

            PAYMENT TERMS AND CONDITIONS
            Payment shall be made within 30 days of invoice. Fees are non-refundable.

            LIMITATION OF LIABILITY
            Neither party shall be liable for any indirect damages or loss of profits.

            INTELLECTUAL PROPERTY AND OWNERSHIP
            All copyrights, patents, and trademarks remain with their respective owners.

            SEVERABILITY CLAUSE
            If any provision is found to be unenforceable, the remaining provisions shall continue in effect.

            GOVERNING LAW JURISDICTION
            This agreement shall be governed by applicable state law and jurisdiction.
        ''',
        'expected_clauses': {
            'Confidentiality': True,
            'Payment Terms': True,
            'Limitation of Liability': True,
            'Intellectual Property': True,
            'Severability': True,
            'Governing Law': True,
            'Non-Disclosure': False,
            'Indemnification': False,
            'Termination': False,
            'Renewal': False,
            'Warranty': False,
            'Dispute Resolution': False,
            'Arbitration': False,
            'Force Majeure': False,
            'Entire Agreement': False,
            'Amendment': False,
        }
    }
]


def test_extraction_accuracy():
    """Test extraction accuracy against known contracts"""
    total_tests = 0
    correct_predictions = 0
    clause_accuracies = {}

    print("\n" + "="*80)
    print("CLAUSE EXTRACTION ACCURACY TEST (FR-11)")
    print("="*80 + "\n")

    for contract in TEST_CONTRACTS:
        print(f"Testing: {contract['name']}")
        print("-" * 80)

        # Extract clauses using the improved algorithm
        extracted = extract_clauses(contract['text'])

        # Create a map of clause names to extraction results
        extracted_map = {clause['clauseName']: clause for clause in extracted}

        # Compare with expected results
        for clause_name, expected_found in contract['expected_clauses'].items():
            total_tests += 1

            if clause_name not in clause_accuracies:
                clause_accuracies[clause_name] = {'correct': 0, 'total': 0}

            extraction = extracted_map.get(clause_name, {})
            actual_found = extraction.get('found', False)
            confidence = extraction.get('confidence', 0)
            match_count = extraction.get('matchCount', 0)

            is_correct = actual_found == expected_found
            if is_correct:
                correct_predictions += 1
                clause_accuracies[clause_name]['correct'] += 1
            clause_accuracies[clause_name]['total'] += 1

            status = "[PASS]" if is_correct else "[FAIL]"
            print(f"  {status} | {clause_name:30s} | Found: {str(actual_found):5} | "
                  f"Expected: {str(expected_found):5} | Confidence: {confidence:5.1f}% | Matches: {match_count}")

        print()

    # Calculate overall accuracy
    overall_accuracy = (correct_predictions / total_tests * 100) if total_tests > 0 else 0

    print("="*80)
    print("ACCURACY SUMMARY")
    print("="*80)
    print(f"\nOverall Accuracy: {overall_accuracy:.1f}% ({correct_predictions}/{total_tests})")
    print(f"Target: >= 85%")
    print(f"Status: {'[PASSED]' if overall_accuracy >= 85 else '[FAILED]'}\n")

    # Per-clause accuracy
    print("Per-Clause Accuracy:")
    print("-" * 80)
    for clause_name in sorted(clause_accuracies.keys()):
        stats = clause_accuracies[clause_name]
        accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {clause_name:30s}: {accuracy:5.1f}% ({stats['correct']}/{stats['total']})")

    print("\n" + "="*80 + "\n")

    return {
        'overall_accuracy': overall_accuracy,
        'total_tests': total_tests,
        'correct_predictions': correct_predictions,
        'clause_accuracies': clause_accuracies,
        'passed': overall_accuracy >= 85
    }


if __name__ == '__main__':
    result = test_extraction_accuracy()
    exit(0 if result['passed'] else 1)
