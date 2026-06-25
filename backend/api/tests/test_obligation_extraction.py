"""
Test Suite for Obligation Extraction
=====================================
Comprehensive tests for obligation extraction service and API.
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from core.models import Contract, Clause, ContractObligation, User, Role
from api.services.obligation_extractor import ObligationExtractor
import json


class ObligationExtractorServiceTest(TestCase):
    """Test ObligationExtractor service"""

    def setUp(self):
        self.extractor = ObligationExtractor()

    def test_extract_payment_obligation(self):
        """Test extracting payment obligation"""
        clause_text = "The contractor shall pay the sum of $50,000 within 30 days of invoice receipt."

        obligations = self.extractor.extract_obligations(clause_text, 'payment')

        self.assertGreater(len(obligations), 0)
        self.assertEqual(obligations[0]['category'], 'PAYMENT')
        self.assertIn('30 days', obligations[0]['due_date_text'] or '')

    def test_extract_indemnity_obligation(self):
        """Test extracting indemnity obligation"""
        clause_text = "The contractor shall indemnify the client against all claims without limitation."

        obligations = self.extractor.extract_obligations(clause_text, 'indemnity')

        self.assertGreater(len(obligations), 0)
        self.assertIn('YOUR_COMPANY', [o['responsible_party'] for o in obligations])

    def test_extract_deadline(self):
        """Test deadline extraction"""
        clause_text = "The vendor must deliver the goods within 15 days."

        obligations = self.extractor.extract_obligations(clause_text)

        self.assertGreater(len(obligations), 0)
        self.assertIsNotNone(obligations[0]['due_date_text'])
        self.assertIn('15', obligations[0]['due_date_text'])

    def test_extract_penalty(self):
        """Test penalty extraction"""
        clause_text = "Failure to deliver will result in liquidated damages of $10,000."

        obligations = self.extractor.extract_obligations(clause_text)

        self.assertGreater(len(obligations), 0)

    def test_priority_assessment(self):
        """Test priority assessment"""
        high_priority = "The contractor shall immediately provide notice."
        low_priority = "The vendor should provide updates."

        high_obligations = self.extractor.extract_obligations(high_priority)
        low_obligations = self.extractor.extract_obligations(low_priority)

        if high_obligations:
            self.assertEqual(high_obligations[0]['priority'], 'HIGH')
        if low_obligations:
            self.assertIn(low_obligations[0]['priority'], ['MEDIUM', 'LOW'])

    def test_deduplication(self):
        """Test obligation deduplication"""
        clause_text = """
        The contractor shall pay fees.
        The contractor shall pay fees.
        The contractor shall pay fees.
        """

        obligations = self.extractor.extract_obligations(clause_text)

        # Should deduplicate identical obligations
        self.assertLess(len(obligations), 3)

    def test_empty_text(self):
        """Test with empty text"""
        obligations = self.extractor.extract_obligations("")
        self.assertEqual(len(obligations), 0)

    def test_no_obligations(self):
        """Test text with no obligations"""
        clause_text = "This is some random text without any obligations."
        obligations = self.extractor.extract_obligations(clause_text)
        self.assertEqual(len(obligations), 0)


class ObligationAPITest(TestCase):
    """Test Obligation API endpoints"""

    def setUp(self):
        self.client = Client()

        # Create test user and role
        role = Role.objects.create(name='Admin', description='Test Admin')
        self.user = User.objects.create(
            email='test@example.com',
            password='test123',
            role=role
        )

        # Create test contract
        self.contract = Contract.objects.create(
            original_filename='test_contract.pdf',
            filename='test_contract.pdf',
            status='uploaded',
            uploaded_by=self.user
        )

        # Create test clauses
        self.clause1 = Clause.objects.create(
            contract=self.contract,
            clause_name='Payment Terms',
            found=True,
            extracted_text='The contractor shall pay $100,000 within 30 days.',
            confidence=0.9
        )

        self.clause2 = Clause.objects.create(
            contract=self.contract,
            clause_name='Delivery Obligation',
            found=True,
            extracted_text='The vendor must deliver the goods immediately.',
            confidence=0.85
        )

    def test_extract_obligations_from_contract(self):
        """Test extracting obligations from contract"""
        url = f'/api/contracts/{self.contract.id}/obligations/extract'

        response = self.client.post(url)

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertGreater(data['obligations_extracted'], 0)

    def test_list_contract_obligations(self):
        """Test listing contract obligations"""
        # First extract
        extract_url = f'/api/contracts/{self.contract.id}/obligations/extract'
        self.client.post(extract_url)

        # Then list
        list_url = f'/api/contracts/{self.contract.id}/obligations/list'
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertGreater(data['total_obligations'], 0)

    def test_filter_obligations_by_category(self):
        """Test filtering obligations"""
        # Extract first
        self.client.post(f'/api/contracts/{self.contract.id}/obligations/extract')

        # Filter by category
        url = f'/api/contracts/{self.contract.id}/obligations/list?category=PAYMENT'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        if data['total_obligations'] > 0:
            for obl in data['obligations']:
                self.assertEqual(obl['category'], 'PAYMENT')

    def test_mark_obligation_complete(self):
        """Test marking obligation as complete"""
        # Extract first
        self.client.post(f'/api/contracts/{self.contract.id}/obligations/extract')

        # Get an obligation
        obligations = ContractObligation.objects.filter(contract=self.contract).first()

        if obligations:
            url = f'/api/obligations/{obligations.id}/complete'
            response = self.client.put(
                url,
                data=json.dumps({'completion_notes': 'Done'}),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])

    def test_reextract_obligations(self):
        """Test re-extracting obligations"""
        # Extract first time
        url = f'/api/contracts/{self.contract.id}/obligations/extract'
        response1 = self.client.post(url)
        count1 = json.loads(response1.content)['obligations_extracted']

        # Try re-extract without flag (should fail)
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, 400)

        # Re-extract with flag (should succeed)
        response3 = self.client.post(
            url,
            data=json.dumps({'reextract': True}),
            content_type='application/json'
        )
        self.assertEqual(response3.status_code, 201)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
