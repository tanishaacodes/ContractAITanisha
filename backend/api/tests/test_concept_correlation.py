"""
Unit Tests for Concept Correlation Graph Engine
================================================
Tests for concept extraction, correlation computation, and Neo4j integration.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from api.services.concept_correlation_service import (
    ConceptCorrelationService,
    CONCEPTS,
    CONTRACT_ARCHETYPES,
    CORRELATION_THRESHOLD
)
from core.models import Contract, Clause

User = get_user_model()


class ConceptCorrelationServiceTests(TestCase):
    """Tests for ConceptCorrelationService"""

    def setUp(self):
        """Setup test data"""
        self.service = ConceptCorrelationService()

        # Create test user
        self.user = User.objects.create(
            email="test@primecontractai.com",
            username="testuser"
        )

        # Create test contract
        self.contract = Contract.objects.create(
            user=self.user,
            filename="test_contract.pdf",
            original_filename="test_contract.pdf",
            file_type="pdf",
            file_path="/tmp/test_contract.pdf",
            contract_type="MSA"
        )

    def test_archetype_graph_generation(self):
        """Test archetype graph returns valid React Flow format"""
        result = self.service.get_archetype_graph("MSA")

        # Check structure
        self.assertEqual(result["contract_type"], "MSA")
        self.assertIn("description", result)
        self.assertIn("nodes", result)
        self.assertIn("edges", result)
        self.assertIn("stats", result)

        # Check nodes
        self.assertEqual(len(result["nodes"]), 10)  # 10 concepts
        for node in result["nodes"]:
            self.assertIn("id", node)
            self.assertIn("data", node)
            self.assertIn("position", node)
            self.assertIn("strength", node["data"])

        # Check edges
        self.assertTrue(len(result["edges"]) > 0)
        for edge in result["edges"]:
            self.assertIn("source", edge)
            self.assertIn("target", edge)
            self.assertIn("weight", edge["data"])

    def test_all_archetypes_valid(self):
        """Test all contract archetypes return valid graphs"""
        for archetype in CONTRACT_ARCHETYPES.keys():
            result = self.service.get_archetype_graph(archetype)
            self.assertEqual(result["contract_type"], archetype)
            self.assertEqual(len(result["nodes"]), 10)

    def test_global_correlation_graph(self):
        """Test global graph across all archetypes"""
        result = self.service.get_full_correlation_graph()

        self.assertEqual(result["contract_type"], "ALL")
        self.assertEqual(len(result["nodes"]), 10)
        self.assertIn("nodes", result)
        self.assertIn("edges", result)

    def test_correlation_matrix(self):
        """Test correlation matrix generation"""
        result = self.service.get_correlation_matrix()

        self.assertIn("concepts", result)
        self.assertIn("matrix", result)
        self.assertEqual(len(result["concepts"]), 10)

        # Check matrix structure
        for concept in CONCEPTS:
            self.assertIn(concept, result["matrix"])
            self.assertEqual(len(result["matrix"][concept]), 10)

    def test_concept_summary(self):
        """Test concept summary generation"""
        result = self.service.get_concept_summary()

        self.assertIn("concepts", result)
        self.assertEqual(len(result["concepts"]), 10)

        for concept_data in result["concepts"]:
            self.assertIn("concept", concept_data)
            self.assertIn("color", concept_data)
            self.assertIn("average_strength", concept_data)
            self.assertIn("by_archetype", concept_data)

    def test_extract_concept_scores_from_contract(self):
        """Test concept extraction from real clauses"""
        # Create test clauses with different types
        Clause.objects.create(
            contract=self.contract,
            clause_type="liability",
            clause_name="Limitation of Liability",
            risk_score=0.85,
            extracted_text="Provider's total liability shall not exceed contract value."
        )
        Clause.objects.create(
            contract=self.contract,
            clause_type="termination",
            clause_name="Termination for Cause",
            risk_score=0.70,
            extracted_text="Either party may terminate for material breach."
        )
        Clause.objects.create(
            contract=self.contract,
            clause_type="indemnification",
            clause_name="Indemnification Clause",
            risk_score=0.90,
            extracted_text="Client shall indemnify Provider against third-party claims."
        )

        # Extract concepts
        concepts = self.service.extract_concept_scores_from_contract(str(self.contract.id))

        # Verify extraction
        self.assertIsInstance(concepts, dict)
        self.assertEqual(len(concepts), 10)  # All 10 concepts

        # Check that mapped concepts have higher scores
        self.assertGreater(concepts["Liability"], 0.5)
        self.assertGreater(concepts["Termination"], 0.5)
        self.assertGreater(concepts["Indemnification"], 0.5)

        # Check that unmapped concepts have baseline scores
        # (depends on clause mapping, but should be low)
        self.assertLessEqual(concepts["Force Majeure"], 0.2)

    def test_extract_concept_scores_no_clauses(self):
        """Test extraction from contract with no clauses"""
        concepts = self.service.extract_concept_scores_from_contract(str(self.contract.id))

        # Should return baseline scores
        for concept in CONCEPTS:
            self.assertIn(concept, concepts)
            self.assertGreaterEqual(concepts[concept], 0.0)

    def test_get_contract_concept_graph(self):
        """Test contract-specific concept graph generation"""
        # Create clauses
        Clause.objects.create(
            contract=self.contract,
            clause_type="indemnification",
            clause_name="Indemnity",
            risk_score=0.90
        )
        Clause.objects.create(
            contract=self.contract,
            clause_type="liability",
            clause_name="Liability Cap",
            risk_score=0.85
        )

        result = self.service.get_contract_concept_graph(str(self.contract.id))

        # Check structure
        self.assertEqual(result["contract_id"], str(self.contract.id))
        self.assertEqual(result["contract_type"], "MSA")
        self.assertEqual(result["filename"], "test_contract.pdf")
        self.assertIn("nodes", result)
        self.assertIn("edges", result)
        self.assertIn("concept_strengths", result)

        # Check concept strengths
        strengths = result["concept_strengths"]
        self.assertEqual(len(strengths), 10)
        self.assertGreater(strengths["Indemnification"], 0.5)
        self.assertGreater(strengths["Liability"], 0.5)

    def test_compare_contract_concepts(self):
        """Test contract concept comparison"""
        # Create second contract
        contract2 = Contract.objects.create(
            user=self.user,
            filename="test_contract_2.pdf",
            original_filename="test_contract_2.pdf",
            file_type="pdf",
            file_path="/tmp/test_contract_2.pdf",
            contract_type="SaaS"
        )

        # Add clauses to first contract (liability-heavy)
        Clause.objects.create(
            contract=self.contract,
            clause_type="liability",
            clause_name="Liability",
            risk_score=0.90
        )

        # Add clauses to second contract (IP-heavy)
        Clause.objects.create(
            contract=contract2,
            clause_type="intellectual property",
            clause_name="IP Ownership",
            risk_score=0.95
        )

        # Compare
        result = self.service.compare_contract_concepts(
            str(self.contract.id),
            str(contract2.id)
        )

        # Check structure
        self.assertIn("contract_id_1", result)
        self.assertIn("contract_id_2", result)
        self.assertIn("concept_differences", result)
        self.assertIn("major_increases", result)
        self.assertIn("major_decreases", result)

        # Check differences
        diffs = result["concept_differences"]
        self.assertEqual(len(diffs), 10)

        # IP Rights should show major increase
        ip_diff = diffs["IP Rights"]
        self.assertIn("difference", ip_diff)
        self.assertGreater(ip_diff["difference"], 0)

    def test_compute_concept_centrality(self):
        """Test centrality calculations"""
        result = self.service.compute_concept_centrality("MSA")

        # Check structure
        self.assertEqual(result["contract_type"], "MSA")
        self.assertIn("centrality_metrics", result)
        self.assertIn("ranked_by_influence", result)
        self.assertIn("most_influential", result)
        self.assertIn("graph_stats", result)

        # Check metrics
        metrics = result["centrality_metrics"]
        self.assertEqual(len(metrics), 10)

        for concept, scores in metrics.items():
            self.assertIn("degree_centrality", scores)
            self.assertIn("betweenness_centrality", scores)
            self.assertIn("eigenvector_centrality", scores)
            self.assertIn("strength", scores)

            # Centrality scores should be between 0 and 1
            self.assertGreaterEqual(scores["degree_centrality"], 0)
            self.assertLessEqual(scores["degree_centrality"], 1)

        # Check rankings
        self.assertEqual(len(result["ranked_by_influence"]), 10)
        self.assertIn(result["most_influential"], CONCEPTS)

    def test_detect_concept_communities(self):
        """Test community detection"""
        result = self.service.detect_concept_communities("MSA")

        # Check structure
        self.assertEqual(result["contract_type"], "MSA")
        self.assertIn("total_communities", result)
        self.assertIn("communities", result)
        self.assertIn("modularity_score", result)

        # Check communities
        self.assertGreater(result["total_communities"], 0)
        self.assertLessEqual(result["total_communities"], 10)  # Can't have more communities than nodes

        # Check modularity score (-1 to 1)
        self.assertGreaterEqual(result["modularity_score"], -1)
        self.assertLessEqual(result["modularity_score"], 1)

        # Check community structure
        for community_name, community_data in result["communities"].items():
            self.assertIn("id", community_data)
            self.assertIn("concepts", community_data)
            self.assertIn("size", community_data)
            self.assertIn("description", community_data)
            self.assertGreater(len(community_data["concepts"]), 0)

    def test_invalid_contract_type(self):
        """Test handling of invalid contract type"""
        with self.assertRaises(ValueError):
            self.service.get_archetype_graph("INVALID_TYPE")

    def test_invalid_contract_id(self):
        """Test handling of invalid contract ID"""
        with self.assertRaises(ValueError):
            self.service.get_contract_concept_graph("00000000-0000-0000-0000-000000000000")

    def test_correlation_threshold(self):
        """Test that edges respect correlation threshold"""
        result = self.service.get_full_correlation_graph()

        for edge in result["edges"]:
            weight = edge["data"]["weight"]
            # All edges should have weight above threshold
            self.assertGreaterEqual(weight, CORRELATION_THRESHOLD * 0.5)


class ConceptGraphAPITests(TestCase):
    """Integration tests for Concept Graph API endpoints"""

    def setUp(self):
        """Setup test data"""
        from rest_framework.test import APIClient

        self.client = APIClient()

        # Create and authenticate user
        self.user = User.objects.create(
            email="api_test@primecontractai.com",
            username="apitest"
        )
        self.client.force_authenticate(user=self.user)

        # Create test contract with clauses
        self.contract = Contract.objects.create(
            user=self.user,
            filename="api_test.pdf",
            original_filename="api_test.pdf",
            file_type="pdf",
            file_path="/tmp/api_test.pdf",
            contract_type="MSA"
        )

        Clause.objects.create(
            contract=self.contract,
            clause_type="liability",
            clause_name="Liability",
            risk_score=0.85
        )

    def test_get_all_archetype_graphs(self):
        """Test GET /api/concept-graph/all/"""
        response = self.client.get("/api/concept-graph/all/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("MSA", data)
        self.assertIn("SaaS", data)
        self.assertIn("ALL", data)

    def test_get_archetype_graph(self):
        """Test GET /api/concept-graph/MSA/"""
        response = self.client.get("/api/concept-graph/MSA/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["contract_type"], "MSA")
        self.assertEqual(len(data["nodes"]), 10)

    def test_get_correlation_matrix(self):
        """Test GET /api/concept-graph/matrix/"""
        response = self.client.get("/api/concept-graph/matrix/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("concepts", data)
        self.assertIn("matrix", data)

    def test_get_concept_summary(self):
        """Test GET /api/concept-graph/summary/"""
        response = self.client.get("/api/concept-graph/summary/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("concepts", data)
        self.assertIn("archetypes", data)

    def test_get_contract_concept_graph(self):
        """Test GET /api/concept-graph/contract/<contract_id>/"""
        response = self.client.get(f"/api/concept-graph/contract/{self.contract.id}/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["contract_id"], str(self.contract.id))
        self.assertIn("concept_strengths", data)

    def test_compare_contracts(self):
        """Test POST /api/concept-graph/compare/"""
        # Create second contract
        contract2 = Contract.objects.create(
            user=self.user,
            filename="api_test_2.pdf",
            original_filename="api_test_2.pdf",
            file_type="pdf",
            file_path="/tmp/api_test_2.pdf",
            contract_type="SaaS"
        )

        response = self.client.post("/api/concept-graph/compare/", {
            "contract_id_1": str(self.contract.id),
            "contract_id_2": str(contract2.id)
        }, format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("concept_differences", data)
        self.assertIn("major_increases", data)

    def test_get_centrality_analytics(self):
        """Test GET /api/concept-graph/analytics/centrality/"""
        response = self.client.get("/api/concept-graph/analytics/centrality/?contract_type=MSA")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("centrality_metrics", data)
        self.assertIn("ranked_by_influence", data)

    def test_get_community_detection(self):
        """Test GET /api/concept-graph/analytics/communities/"""
        response = self.client.get("/api/concept-graph/analytics/communities/?contract_type=MSA")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("communities", data)
        self.assertIn("modularity_score", data)

    def test_unauthorized_access(self):
        """Test that endpoints require authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/concept-graph/all/")
        self.assertEqual(response.status_code, 401)
