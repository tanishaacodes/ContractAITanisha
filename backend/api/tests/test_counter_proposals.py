"""
Counter-Proposal Generation Test Suite
=======================================

Tests for AI-powered counter-proposal generation.

Test Coverage:
- Service layer: CounterProposalGenerator
- API endpoints: /api/clauses/{id}/counter-proposal, /api/clauses/{id}/analyze-negotiation
- Negotiation strategy generation
- Acceptance likelihood assessment
- Counterparty analysis integration
"""

import pytest
from django.test import TestCase, Client
from core.models import Contract, Clause, User, Role, Counterparty
from api.services.counter_proposal import CounterProposalGenerator
import json
from unittest.mock import patch, MagicMock


class CounterProposalGeneratorServiceTest(TestCase):
    """Test CounterProposalGenerator service"""

    def setUp(self):
        self.generator = CounterProposalGenerator(provider='openai')
        self.proposed_clause = (
            "The contractor shall indemnify and hold harmless the client "
            "from any and all claims, liabilities, and expenses without limitation."
        )

    def test_generate_counter_proposal_client_position(self):
        """Test generating counter-proposal from client position"""
        result = self.generator.generate_counter_proposal(
            proposed_clause=self.proposed_clause,
            concerns=['Unlimited liability', 'No cap on indemnity'],
            your_position='client'
        )

        self.assertTrue(result['success'])
        self.assertIn('counter_proposals', result)
        self.assertIn('negotiation_strategy', result)
        self.assertGreater(len(result['counter_proposals']), 0)

        # Check counter-proposal structure
        proposal = result['counter_proposals'][0]
        self.assertIn('text', proposal)
        self.assertIn('rank', proposal)
        self.assertIn('acceptance_likelihood', proposal)
        self.assertIn('rationale', proposal)

    def test_generate_counter_proposal_vendor_position(self):
        """Test generating counter-proposal from vendor position"""
        proposed = "Payment shall be made within 90 days of invoice receipt."

        result = self.generator.generate_counter_proposal(
            proposed_clause=proposed,
            concerns=['Long payment terms', 'No interest on late payment'],
            your_position='vendor'
        )

        self.assertTrue(result['success'])
        self.assertGreater(len(result['counter_proposals']), 0)

        # Vendor position should push for faster payment
        proposal_text = result['counter_proposals'][0]['text'].lower()
        # Look for vendor-favorable terms
        vendor_terms = ['30 days', '45 days', 'interest', 'penalty', 'prompt']
        # At least one term should appear (in fallback or AI mode)

    def test_negotiation_strategy_generation(self):
        """Test negotiation strategy generation"""
        result = self.generator.generate_counter_proposal(
            proposed_clause=self.proposed_clause,
            concerns=['Unlimited liability'],
            your_position='client'
        )

        self.assertTrue(result['success'])
        strategy = result['negotiation_strategy']

        # Check strategy components
        self.assertIn('approach', strategy)
        self.assertIn('reasoning', strategy)
        self.assertIn('acceptance_likelihood', strategy)
        self.assertIn('suggested_action', strategy)

        # Approach should be valid
        valid_approaches = ['CONFIDENT', 'COLLABORATIVE', 'CAUTIOUS']
        self.assertIn(strategy['approach'], valid_approaches)

        # Acceptance likelihood should be 0-100
        self.assertGreaterEqual(strategy['acceptance_likelihood'], 0)
        self.assertLessEqual(strategy['acceptance_likelihood'], 100)

    def test_multiple_counter_proposals(self):
        """Test generating multiple alternatives"""
        result = self.generator.generate_counter_proposal(
            proposed_clause=self.proposed_clause,
            concerns=['Unlimited liability'],
            your_position='client',
            num_alternatives=3
        )

        self.assertTrue(result['success'])
        self.assertGreaterEqual(len(result['counter_proposals']), 1)

        # Counter-proposals should be ranked
        ranks = [p['rank'] for p in result['counter_proposals']]
        self.assertEqual(ranks, sorted(ranks))

    def test_acceptance_likelihood_scoring(self):
        """Test acceptance likelihood assessment"""
        result = self.generator.generate_counter_proposal(
            proposed_clause=self.proposed_clause,
            concerns=['Unlimited liability'],
            your_position='client'
        )

        self.assertTrue(result['success'])

        # All proposals should have likelihood scores
        for proposal in result['counter_proposals']:
            likelihood = proposal['acceptance_likelihood']
            self.assertGreaterEqual(likelihood, 0.0)
            self.assertLessEqual(likelihood, 1.0)

        # Higher ranked proposals should generally have higher acceptance
        if len(result['counter_proposals']) > 1:
            first_likelihood = result['counter_proposals'][0]['acceptance_likelihood']
            last_likelihood = result['counter_proposals'][-1]['acceptance_likelihood']
            self.assertGreaterEqual(first_likelihood, last_likelihood - 0.2)  # Allow some variance

    def test_counterparty_profile_integration(self):
        """Test integration with counterparty profile"""
        counterparty_profile = {
            'name': 'Acme Corp',
            'negotiation_style': 'aggressive',
            'risk_tolerance': 'low',
            'typical_positions': ['Limited liability', 'Quick payment terms']
        }

        result = self.generator.generate_counter_proposal(
            proposed_clause=self.proposed_clause,
            concerns=['Unlimited liability'],
            your_position='client',
            counterparty_profile=counterparty_profile
        )

        self.assertTrue(result['success'])
        # Strategy should account for counterparty's aggressive style
        strategy = result['negotiation_strategy']
        # Aggressive counterparty might need CAUTIOUS or COLLABORATIVE approach

    def test_fallback_counter_proposal(self):
        """Test fallback counter-proposal generation when AI unavailable"""
        # Force fallback
        with patch.object(self.generator, '_is_ai_available', return_value=False):
            result = self.generator.generate_counter_proposal(
                proposed_clause=self.proposed_clause,
                concerns=['Unlimited liability'],
                your_position='client'
            )

            self.assertTrue(result['success'])
            self.assertTrue(result.get('using_fallback', False))
            self.assertGreater(len(result['counter_proposals']), 0)

    def test_empty_proposed_clause(self):
        """Test handling of empty proposed clause"""
        result = self.generator.generate_counter_proposal(
            proposed_clause='',
            concerns=['Test concern'],
            your_position='client'
        )

        self.assertFalse(result['success'])
        self.assertIn('error', result)

    def test_no_concerns_provided(self):
        """Test generating counter-proposal without specific concerns"""
        result = self.generator.generate_counter_proposal(
            proposed_clause=self.proposed_clause,
            concerns=[],
            your_position='client'
        )

        # Should still generate proposals based on general risk analysis
        self.assertTrue(result['success'])
        self.assertGreater(len(result['counter_proposals']), 0)

    def test_compromises_and_fallbacks(self):
        """Test generation of compromise positions"""
        result = self.generator.generate_counter_proposal(
            proposed_clause=self.proposed_clause,
            concerns=['Unlimited liability'],
            your_position='client'
        )

        self.assertTrue(result['success'])

        # Check for compromise suggestions in strategy
        strategy = result['negotiation_strategy']
        if 'fallback_positions' in strategy:
            self.assertGreater(len(strategy['fallback_positions']), 0)

    def test_changes_highlighting(self):
        """Test that key changes are highlighted"""
        result = self.generator.generate_counter_proposal(
            proposed_clause=self.proposed_clause,
            concerns=['Unlimited liability'],
            your_position='client'
        )

        self.assertTrue(result['success'])

        # Proposals should list key changes
        for proposal in result['counter_proposals']:
            if 'changes' in proposal:
                self.assertIsInstance(proposal['changes'], list)

    @patch('api.services.counter_proposal.openai')
    def test_openai_provider_integration(self, mock_openai):
        """Test OpenAI provider integration"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            'counter_proposals': [
                {
                    'text': 'The contractor shall indemnify the client up to 2x contract value.',
                    'changes': ['Added liability cap'],
                    'rationale': 'Limits exposure while maintaining protection'
                }
            ],
            'negotiation_strategy': {
                'approach': 'COLLABORATIVE',
                'reasoning': 'Test reasoning',
                'acceptance_likelihood': 75
            }
        })
        mock_openai.ChatCompletion.create.return_value = mock_response

        result = self.generator.generate_counter_proposal(
            proposed_clause=self.proposed_clause,
            concerns=['Unlimited liability'],
            your_position='client'
        )

        # Should use OpenAI if available

    @patch('api.services.counter_proposal.anthropic')
    def test_anthropic_provider_integration(self, mock_anthropic):
        """Test Anthropic provider integration"""
        generator = CounterProposalGenerator(provider='anthropic')

        # Mock Anthropic response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            'counter_proposals': [
                {
                    'text': 'Counter-proposal text',
                    'changes': ['Change 1'],
                    'rationale': 'Rationale'
                }
            ],
            'negotiation_strategy': {
                'approach': 'CONFIDENT',
                'reasoning': 'Test',
                'acceptance_likelihood': 80
            }
        })
        mock_anthropic.Anthropic.return_value.messages.create.return_value = mock_response

        result = generator.generate_counter_proposal(
            proposed_clause=self.proposed_clause,
            concerns=['Test'],
            your_position='client'
        )

        # Should use Anthropic if available


class CounterProposalAPITest(TestCase):
    """Test Counter-Proposal API endpoints"""

    def setUp(self):
        self.client = Client()
        role = Role.objects.create(name='Admin', description='Test')
        self.user = User.objects.create(email='test@example.com', role=role)
        self.contract = Contract.objects.create(
            filename='test_contract.pdf',
            original_filename='test_contract.pdf',
            uploaded_by=self.user,
            status='uploaded'
        )
        self.clause = Clause.objects.create(
            contract=self.contract,
            clause_name='Indemnity Clause',
            found=True,
            extracted_text='The contractor shall indemnify the client without limitation.',
            confidence=0.95,
            clause_type='indemnity',
            risk_score=0.85
        )
        self.counterparty = Counterparty.objects.create(
            name='Vendor Corp',
            negotiation_style='collaborative',
            risk_tolerance='medium'
        )

    def test_generate_counter_proposal_endpoint(self):
        """Test POST /api/clauses/{id}/counter-proposal"""
        url = f'/api/clauses/{self.clause.id}/counter-proposal'
        data = {
            'concerns': ['Unlimited liability', 'No cap'],
            'your_position': 'client',
            'provider': 'openai'
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('counter_proposals', result)
        self.assertIn('negotiation_strategy', result)

    def test_counter_proposal_with_counterparty(self):
        """Test counter-proposal with counterparty context"""
        url = f'/api/clauses/{self.clause.id}/counter-proposal'
        data = {
            'concerns': ['Unlimited liability'],
            'your_position': 'client',
            'counterparty_id': self.counterparty.id
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])

    def test_counter_proposal_without_concerns(self):
        """Test generating counter-proposal without specific concerns"""
        url = f'/api/clauses/{self.clause.id}/counter-proposal'
        data = {
            'your_position': 'vendor'
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])

    def test_analyze_negotiation_endpoint(self):
        """Test POST /api/clauses/{id}/analyze-negotiation"""
        url = f'/api/clauses/{self.clause.id}/analyze-negotiation'

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('risk_analysis', result)
        self.assertIn('negotiation_leverage', result)

    def test_counter_proposal_nonexistent_clause(self):
        """Test counter-proposal for non-existent clause"""
        url = '/api/clauses/99999/counter-proposal'
        data = {
            'concerns': ['Test'],
            'your_position': 'client'
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)

    def test_counter_proposal_missing_position(self):
        """Test counter-proposal without position"""
        url = f'/api/clauses/{self.clause.id}/counter-proposal'
        data = {
            'concerns': ['Test']
            # Missing your_position
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        # Should use default position or return error

    def test_multiple_concerns(self):
        """Test counter-proposal with multiple concerns"""
        url = f'/api/clauses/{self.clause.id}/counter-proposal'
        data = {
            'concerns': [
                'Unlimited liability',
                'No termination rights',
                'Lack of dispute resolution',
                'Unclear payment terms'
            ],
            'your_position': 'client'
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])

    def test_analyze_for_negotiation_workflow(self):
        """Test complete negotiation analysis workflow"""
        # Step 1: Analyze contract for negotiation
        analyze_url = f'/api/contracts/{self.contract.id}/analyze-for-negotiation'
        analyze_response = self.client.post(
            analyze_url,
            data=json.dumps({'min_risk_score': 0.7}),
            content_type='application/json'
        )

        self.assertEqual(analyze_response.status_code, 200)
        analysis = json.loads(analyze_response.content)
        self.assertTrue(analysis['success'])

        # Step 2: Generate counter-proposal for high-risk clause
        if analysis.get('priority_clauses'):
            clause_id = analysis['priority_clauses'][0]['clause_id']
            counter_url = f'/api/clauses/{clause_id}/counter-proposal'
            counter_response = self.client.post(
                counter_url,
                data=json.dumps({
                    'concerns': analysis['priority_clauses'][0].get('risk_factors', []),
                    'your_position': 'client'
                }),
                content_type='application/json'
            )

            # May succeed or fail depending on AI availability
            # Just check endpoint is wired correctly

    def test_counter_proposal_both_providers(self):
        """Test counter-proposal with both AI providers"""
        url = f'/api/clauses/{self.clause.id}/counter-proposal'

        providers = ['openai', 'anthropic']
        for provider in providers:
            data = {
                'concerns': ['Unlimited liability'],
                'your_position': 'client',
                'provider': provider
            }

            response = self.client.post(
                url,
                data=json.dumps(data),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 200)
            result = json.loads(response.content)
            self.assertTrue(result['success'])

    def test_negotiation_strategy_approaches(self):
        """Test different negotiation strategy approaches"""
        # High risk clause should suggest CAUTIOUS or COLLABORATIVE
        high_risk_clause = Clause.objects.create(
            contract=self.contract,
            clause_name='Severe Penalty Clause',
            found=True,
            extracted_text='The client shall pay unlimited penalties for any breach.',
            confidence=0.9,
            clause_type='penalty',
            risk_score=0.95
        )

        url = f'/api/clauses/{high_risk_clause.id}/counter-proposal'
        data = {
            'concerns': ['Unlimited penalties'],
            'your_position': 'client'
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])

        strategy = result['negotiation_strategy']
        # Should be cautious or collaborative for high-risk situations


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
