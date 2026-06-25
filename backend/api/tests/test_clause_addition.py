"""
Test Suite for Clause Addition
================================
Tests for clause addition service and API.
"""

import pytest
from django.test import TestCase, Client
from core.models import Contract, Clause, User, Role
from api.services.clause_addition import ClauseAdditionService
import json


class ClauseAdditionServiceTest(TestCase):
    """Test ClauseAdditionService"""

    def setUp(self):
        self.service = ClauseAdditionService()

    def test_add_clause_risk_assessment(self):
        """Test risk assessment for new clause"""
        clause_text = "The contractor shall indemnify without limitation for all damages."
        result = self.service.add_clause_to_contract(
            clause_text=clause_text,
            clause_name='Indemnity',
            clause_type='indemnity',
            contract_model=None
        )

        self.assertTrue(result['success'])
        self.assertGreater(result['risk_score'], 0.7)  # High risk
        self.assertEqual(result['risk_level'], 'HIGH')

    def test_low_risk_clause(self):
        """Test low risk clause"""
        clause_text = "The parties agree to maintain confidentiality."
        result = self.service.add_clause_to_contract(
            clause_text=clause_text,
            clause_name='Confidentiality',
            clause_type='confidentiality',
            contract_model=None
        )

        self.assertTrue(result['success'])
        self.assertLess(result['risk_score'], 0.6)

    def test_risk_keyword_detection(self):
        """Test risk keyword detection"""
        high_risk_keywords = ['unlimited', 'without limitation', 'consequential damages']

        for keyword in high_risk_keywords:
            clause_text = f"The contractor shall be liable {keyword}."
            result = self.service.add_clause_to_contract(
                clause_text=clause_text,
                clause_name='Test',
                clause_type='liability',
                contract_model=None
            )

            self.assertTrue(result['success'])
            self.assertGreater(result['risk_score'], 0.5)


class ClauseAdditionAPITest(TestCase):
    """Test Clause Addition API"""

    def setUp(self):
        self.client = Client()
        role = Role.objects.create(name='Admin')
        self.user = User.objects.create(email='test@example.com', role=role)
        self.contract = Contract.objects.create(
            filename='test.pdf',
            uploaded_by=self.user,
            contract_value='10 Crore'
        )

    def test_add_clause_api(self):
        """Test adding clause via API"""
        url = f'/api/contracts/{self.contract.id}/clauses/add'
        data = {
            'clause_name': 'Force Majeure',
            'clause_type': 'force_majeure',
            'clause_text': 'Neither party shall be liable for delays caused by force majeure events.',
            'run_simulation': False
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('clause_id', result)

    def test_simulate_clause_addition(self):
        """Test simulating clause addition"""
        url = f'/api/contracts/{self.contract.id}/clauses/simulate-addition'
        data = {
            'clause_name': 'Test Clause',
            'clause_type': 'general',
            'clause_text': 'This is a test clause with sufficient text.'
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('risk_assessment', result)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
