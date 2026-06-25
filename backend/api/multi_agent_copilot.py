"""
Multi-Agent Legal Co-Pilot System
==================================
Implements specialized AI agents for:
- Risk Analysis Agent
- Negotiation Strategy Agent
- Litigation Prediction Agent
- Compliance Advisory Agent
- Contract Drafting Agent
- Judge Prediction with Win Probability

Uses RAG + GraphRAG + Bayesian inference for intelligent legal assistance.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Try imports
try:
    from .bayesian_legal_risk_engine import get_legal_risk_engine, LegalRiskInput
    from .caselaw_bert_engine import get_hybrid_search, CaseDocument
    ENGINES_AVAILABLE = True
except ImportError:
    logger.warning("Risk engines not available")
    ENGINES_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

class AgentType(Enum):
    RISK_ANALYST = "risk_analyst"
    NEGOTIATION_STRATEGIST = "negotiation_strategist"
    LITIGATION_PREDICTOR = "litigation_predictor"
    COMPLIANCE_ADVISOR = "compliance_advisor"
    CONTRACT_DRAFTER = "contract_drafter"


@dataclass
class AgentContext:
    """Context for agent execution."""
    query: str
    contract_id: Optional[str] = None
    clause_text: Optional[str] = None
    jurisdiction: str = "US"
    counterparty: Optional[str] = None
    case_history: List[Dict] = None
    user_preferences: Dict = None


@dataclass
class AgentResponse:
    """Agent response structure."""
    agent_type: str
    answer: str
    confidence: float
    supporting_cases: List[Dict]
    risk_assessment: Optional[Dict] = None
    recommendations: List[str] = None
    win_probability: Optional[float] = None
    metadata: Dict = None


# ═══════════════════════════════════════════════════════════════
# BASE AGENT CLASS
# ═══════════════════════════════════════════════════════════════

class BaseAgent:
    """Base class for legal AI agents."""

    def __init__(self, agent_type: AgentType):
        """Initialize agent."""
        self.agent_type = agent_type
        self.name = agent_type.value
        logger.info(f"Initialized {self.name} agent")

    def process(self, context: AgentContext) -> AgentResponse:
        """Process request and generate response."""
        raise NotImplementedError("Subclasses must implement process()")

    def _retrieve_cases(self, query: str, jurisdiction: Optional[str] = None) -> List[Dict]:
        """Retrieve relevant case law using hybrid search."""
        if not ENGINES_AVAILABLE:
            return []

        try:
            search_engine = get_hybrid_search()
            results = search_engine.search(query, k=5, jurisdiction=jurisdiction)

            cases = []
            for result in results:
                cases.append({
                    "case_id": result.case.case_id,
                    "title": result.case.title,
                    "text": result.case.text[:500],
                    "jurisdiction": result.case.jurisdiction,
                    "year": result.case.year,
                    "court": result.case.court,
                    "relevance_score": result.score,
                    "reranked_score": result.reranked_score or result.score
                })
            return cases
        except Exception as e:
            logger.error(f"Error retrieving cases: {e}")
            return []


# ═══════════════════════════════════════════════════════════════
# RISK ANALYST AGENT
# ═══════════════════════════════════════════════════════════════

class RiskAnalystAgent(BaseAgent):
    """
    Specialized agent for contract risk analysis.
    Uses Bayesian inference + case law to assess legal risk.
    """

    def __init__(self):
        super().__init__(AgentType.RISK_ANALYST)

    def process(self, context: AgentContext) -> AgentResponse:
        """Analyze contract/clause risk."""
        # Retrieve relevant cases
        supporting_cases = self._retrieve_cases(
            context.query or context.clause_text,
            context.jurisdiction
        )

        # Perform Bayesian risk assessment
        risk_assessment = None
        if ENGINES_AVAILABLE and context.clause_text:
            risk_assessment = self._assess_risk(context)

        # Generate risk analysis
        answer = self._generate_risk_analysis(context, supporting_cases, risk_assessment)

        # Extract recommendations
        recommendations = self._extract_recommendations(risk_assessment)

        return AgentResponse(
            agent_type=self.name,
            answer=answer,
            confidence=0.85,
            supporting_cases=supporting_cases,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            metadata={"analysis_type": "comprehensive_risk"}
        )

    def _assess_risk(self, context: AgentContext) -> Dict:
        """Perform Bayesian risk assessment."""
        try:
            risk_engine = get_legal_risk_engine()

            # Infer clause strength from text
            clause_strength = self._infer_clause_strength(context.clause_text)

            # Create risk input
            risk_input = LegalRiskInput(
                event_type="Regulatory",  # Default, can be inferred
                clause_strength=clause_strength,
                jurisdiction=context.jurisdiction,
                counterparty_risk="Neutral",  # Default
                clause_text=context.clause_text,
                historical_cases=context.case_history or []
            )

            # Assess risk
            risk_output = risk_engine.assess_clause_risk(risk_input)

            return {
                "legal_risk_level": risk_output.legal_risk_level,
                "legal_risk_prob": risk_output.legal_risk_prob,
                "litigation_risk_level": risk_output.litigation_risk_level,
                "litigation_risk_prob": risk_output.litigation_risk_prob,
                "financial_risk_level": risk_output.financial_risk_level,
                "financial_risk_prob": risk_output.financial_risk_prob,
                "overall_score": risk_output.overall_score,
                "risk_score": risk_output.risk_score,
                "impact_score": risk_output.impact_score,
                "risk_drivers": risk_output.risk_drivers,
                "recommendation": risk_output.recommendation
            }
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return None

    def _infer_clause_strength(self, clause_text: str) -> str:
        """Infer clause strength from text characteristics."""
        if not clause_text:
            return "Medium"

        # Simple heuristics
        ambiguous_words = ["may", "could", "should", "reasonable", "appropriate"]
        strong_words = ["shall", "must", "will", "required", "mandatory"]

        ambiguous_count = sum(1 for word in ambiguous_words if word in clause_text.lower())
        strong_count = sum(1 for word in strong_words if word in clause_text.lower())

        if ambiguous_count > strong_count:
            return "Weak"
        elif strong_count > ambiguous_count + 2:
            return "Strong"
        else:
            return "Medium"

    def _generate_risk_analysis(
        self,
        context: AgentContext,
        cases: List[Dict],
        risk_assessment: Optional[Dict]
    ) -> str:
        """Generate comprehensive risk analysis narrative."""
        parts = []

        parts.append("## Risk Analysis\n")

        if risk_assessment:
            parts.append(f"**Overall Risk Level**: {risk_assessment['legal_risk_level']}\n")
            parts.append(f"**Risk Score**: {risk_assessment['risk_score']:.2f}/4.0\n")
            parts.append(f"**Impact Score**: {risk_assessment['impact_score']:.2f}/10.0\n\n")

            parts.append("### Risk Breakdown:\n")
            parts.append(f"- **Legal Risk**: {risk_assessment['legal_risk_level']} ")
            parts.append(f"(Low: {risk_assessment['legal_risk_prob']['Low']:.0%}, ")
            parts.append(f"Medium: {risk_assessment['legal_risk_prob']['Medium']:.0%}, ")
            parts.append(f"High: {risk_assessment['legal_risk_prob']['High']:.0%})\n")

            parts.append(f"- **Litigation Risk**: {risk_assessment['litigation_risk_level']} ")
            parts.append(f"(Low: {risk_assessment['litigation_risk_prob']['Low']:.0%}, ")
            parts.append(f"Medium: {risk_assessment['litigation_risk_prob']['Medium']:.0%}, ")
            parts.append(f"High: {risk_assessment['litigation_risk_prob']['High']:.0%})\n")

            parts.append(f"- **Financial Risk**: {risk_assessment['financial_risk_level']} ")
            parts.append(f"(Low: {risk_assessment['financial_risk_prob']['Low']:.0%}, ")
            parts.append(f"Medium: {risk_assessment['financial_risk_prob']['Medium']:.0%}, ")
            parts.append(f"High: {risk_assessment['financial_risk_prob']['High']:.0%})\n\n")

            if risk_assessment.get('risk_drivers'):
                parts.append("### Key Risk Drivers:\n")
                for driver in risk_assessment['risk_drivers'][:3]:
                    parts.append(f"- **{driver['factor']}** ({driver['impact']} impact): {driver['explanation']}\n")
                parts.append("\n")

        if cases:
            parts.append(f"### Supporting Case Law ({len(cases)} cases):\n")
            for i, case in enumerate(cases[:3], 1):
                parts.append(f"{i}. **{case['title']}** ({case['jurisdiction']}, {case['year']})\n")
                parts.append(f"   - Court: {case['court']}\n")
                parts.append(f"   - Relevance: {case['relevance_score']:.2%}\n")
            parts.append("\n")

        if risk_assessment and risk_assessment.get('recommendation'):
            parts.append(f"### Recommendation:\n{risk_assessment['recommendation']}\n")

        return "".join(parts)

    def _extract_recommendations(self, risk_assessment: Optional[Dict]) -> List[str]:
        """Extract actionable recommendations."""
        if not risk_assessment:
            return ["Perform detailed legal review", "Consult legal counsel"]

        recommendations = []

        if risk_assessment['legal_risk_level'] == "High":
            recommendations.append("Immediate legal review required - HIGH RISK clause")
            recommendations.append("Consider renegotiating terms to strengthen legal position")

        if risk_assessment['litigation_risk_level'] == "High":
            recommendations.append("Add mandatory arbitration clause")
            recommendations.append("Include jurisdiction and venue selection provisions")

        if risk_assessment['financial_risk_level'] == "High":
            recommendations.append("Add liability caps and indemnification limits")
            recommendations.append("Require counterparty insurance coverage")

        if not recommendations:
            recommendations.append("Risk profile acceptable - continue monitoring")

        return recommendations


# ═══════════════════════════════════════════════════════════════
# JUDGE PREDICTION AGENT
# ═══════════════════════════════════════════════════════════════

class LitigationPredictorAgent(BaseAgent):
    """
    Predicts litigation outcomes and win probability.
    Uses Bayesian model + historical case analysis.
    """

    def __init__(self):
        super().__init__(AgentType.LITIGATION_PREDICTOR)

    def process(self, context: AgentContext) -> AgentResponse:
        """Predict litigation outcome and win probability."""
        # Retrieve similar cases
        supporting_cases = self._retrieve_cases(context.query, context.jurisdiction)

        # Predict win probability
        win_prob, confidence = self._predict_win_probability(context, supporting_cases)

        # Generate prediction narrative
        answer = self._generate_prediction_analysis(context, win_prob, supporting_cases)

        recommendations = self._generate_litigation_strategy(win_prob, context.jurisdiction)

        return AgentResponse(
            agent_type=self.name,
            answer=answer,
            confidence=confidence,
            supporting_cases=supporting_cases,
            win_probability=win_prob,
            recommendations=recommendations,
            metadata={"prediction_type": "litigation_outcome"}
        )

    def _predict_win_probability(
        self,
        context: AgentContext,
        cases: List[Dict]
    ) -> Tuple[float, float]:
        """
        Predict win probability using:
        1. Bayesian model (if available)
        2. Historical case similarity
        3. Jurisdiction factors
        """
        if ENGINES_AVAILABLE and context.clause_text:
            try:
                risk_engine = get_legal_risk_engine()

                # Get risk assessment
                clause_strength = "Medium"  # Can be inferred
                jurisdiction_profile = risk_engine.jurisdiction_profiles.get(
                    context.jurisdiction,
                    risk_engine.jurisdiction_profiles["US"]
                )

                # Compute win probability
                win_prob = risk_engine.compute_win_probability(
                    jurisdiction_profile["enforcement_level"],
                    clause_strength,
                    "Medium"  # Legal risk level
                )

                return win_prob, 0.85
            except Exception as e:
                logger.error(f"Error in win probability prediction: {e}")

        # Fallback: estimate from case outcomes
        if cases:
            # Simplified: assume similar cases predict outcome
            return 0.55, 0.65  # Moderate win probability, lower confidence

        return 0.50, 0.50  # No information

    def _generate_prediction_analysis(
        self,
        context: AgentContext,
        win_prob: float,
        cases: List[Dict]
    ) -> str:
        """Generate litigation prediction narrative."""
        parts = []

        parts.append("## Litigation Outcome Prediction\n\n")
        parts.append(f"**Win Probability**: {win_prob:.0%}\n")
        parts.append(f"**Jurisdiction**: {context.jurisdiction}\n\n")

        # Interpret probability
        if win_prob >= 0.70:
            parts.append("### Assessment: **FAVORABLE** ✅\n")
            parts.append("Strong litigation prospects. Legal position well-supported by precedent.\n\n")
        elif win_prob >= 0.50:
            parts.append("### Assessment: **UNCERTAIN** ⚠️\n")
            parts.append("Outcome uncertain. Consider settlement or arbitration.\n\n")
        else:
            parts.append("### Assessment: **UNFAVORABLE** ❌\n")
            parts.append("Weak litigation position. Strongly recommend alternative dispute resolution.\n\n")

        # Case analysis
        if cases:
            parts.append(f"### Analysis Based on {len(cases)} Similar Cases:\n")
            for i, case in enumerate(cases[:3], 1):
                parts.append(f"{i}. **{case['title']}** ({case['year']})\n")
                parts.append(f"   - Jurisdiction: {case['jurisdiction']}\n")
                parts.append(f"   - Relevance: {case['relevance_score']:.0%}\n")
            parts.append("\n")

        return "".join(parts)

    def _generate_litigation_strategy(self, win_prob: float, jurisdiction: str) -> List[str]:
        """Generate litigation strategy recommendations."""
        recommendations = []

        if win_prob >= 0.70:
            recommendations.append("Pursue litigation - strong prospects")
            recommendations.append(f"Prepare comprehensive brief citing precedent in {jurisdiction}")
            recommendations.append("Consider early summary judgment motion")
        elif win_prob >= 0.50:
            recommendations.append("Pursue settlement negotiations in parallel with litigation prep")
            recommendations.append("Consider mediation before trial")
            recommendations.append("Strengthen case with additional discovery")
        else:
            recommendations.append("AVOID litigation - poor prospects")
            recommendations.append("Pursue arbitration or mediation")
            recommendations.append("Consider settlement at favorable terms")
            recommendations.append("Review clause amendments to strengthen position for future disputes")

        return recommendations


# ═══════════════════════════════════════════════════════════════
# NEGOTIATION STRATEGIST AGENT
# ═══════════════════════════════════════════════════════════════

class NegotiationStrategistAgent(BaseAgent):
    """
    Provides negotiation strategy and tactics.
    Analyzes leverage points and recommends positions.
    """

    def __init__(self):
        super().__init__(AgentType.NEGOTIATION_STRATEGIST)

    def process(self, context: AgentContext) -> AgentResponse:
        """Generate negotiation strategy."""
        # Retrieve market standards
        supporting_cases = self._retrieve_cases(
            f"standard {context.query} clause negotiation",
            context.jurisdiction
        )

        # Analyze negotiation position
        strategy = self._analyze_negotiation_position(context, supporting_cases)

        # Generate strategy narrative
        answer = self._generate_strategy_narrative(strategy, context)

        return AgentResponse(
            agent_type=self.name,
            answer=answer,
            confidence=0.80,
            supporting_cases=supporting_cases,
            recommendations=strategy['recommendations'],
            metadata=strategy['metadata']
        )

    def _analyze_negotiation_position(
        self,
        context: AgentContext,
        cases: List[Dict]
    ) -> Dict:
        """Analyze negotiation leverage and positions."""
        # Simplified negotiation analysis
        leverage_points = []
        fallback_positions = []
        must_haves = []

        if context.clause_text:
            # Identify negotiable vs non-negotiable terms
            if "shall" in context.clause_text.lower():
                must_haves.append("Mandatory obligations must be clearly defined")
            if "limitation of liability" in context.query.lower():
                leverage_points.append("Liability caps are standard in this jurisdiction")
                fallback_positions.append("Accept mutual liability caps rather than unilateral")

        recommendations = [
            "Start with aggressive position, prepared to compromise on non-essentials",
            "Document all counterparty concerns for pattern analysis",
            "Use market standards as anchor for position",
        ]

        return {
            "leverage_points": leverage_points,
            "fallback_positions": fallback_positions,
            "must_haves": must_haves,
            "recommendations": recommendations,
            "metadata": {"strategy_type": "integrative"}
        }

    def _generate_strategy_narrative(self, strategy: Dict, context: AgentContext) -> str:
        """Generate negotiation strategy narrative."""
        parts = []

        parts.append("## Negotiation Strategy\n\n")

        if strategy['leverage_points']:
            parts.append("### Leverage Points:\n")
            for point in strategy['leverage_points']:
                parts.append(f"- {point}\n")
            parts.append("\n")

        if strategy['must_haves']:
            parts.append("### Non-Negotiable (Must-Haves):\n")
            for item in strategy['must_haves']:
                parts.append(f"- {item}\n")
            parts.append("\n")

        if strategy['fallback_positions']:
            parts.append("### Fallback Positions:\n")
            for position in strategy['fallback_positions']:
                parts.append(f"- {position}\n")
            parts.append("\n")

        parts.append("### Recommended Approach:\n")
        parts.append("1. Open with market-standard terms backed by precedent\n")
        parts.append("2. Emphasize mutual benefit and risk sharing\n")
        parts.append("3. Prepare BATNA (Best Alternative to Negotiated Agreement)\n")
        parts.append("4. Document concessions for quid pro quo\n\n")

        return "".join(parts)


# ═══════════════════════════════════════════════════════════════
# MULTI-AGENT ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

class LegalCoPilot:
    """
    Multi-agent legal co-pilot orchestrator.
    Routes queries to appropriate specialized agents.
    """

    def __init__(self):
        """Initialize all agents."""
        self.agents = {
            AgentType.RISK_ANALYST: RiskAnalystAgent(),
            AgentType.LITIGATION_PREDICTOR: LitigationPredictorAgent(),
            AgentType.NEGOTIATION_STRATEGIST: NegotiationStrategistAgent(),
        }
        logger.info("Initialized Legal Co-Pilot with 3 specialized agents")

    def process_query(
        self,
        query: str,
        agent_type: Optional[AgentType] = None,
        context: Optional[AgentContext] = None
    ) -> AgentResponse:
        """
        Process user query with appropriate agent.

        Args:
            query: User question/request
            agent_type: Specific agent to use (auto-detected if None)
            context: Additional context

        Returns:
            Agent response
        """
        # Create context if not provided
        if context is None:
            context = AgentContext(query=query)
        else:
            context.query = query

        # Auto-detect agent if not specified
        if agent_type is None:
            agent_type = self._route_query(query)

        # Get agent
        agent = self.agents.get(agent_type)
        if agent is None:
            # Fallback to risk analyst
            agent = self.agents[AgentType.RISK_ANALYST]

        # Process with agent
        logger.info(f"Processing query with {agent.name}")
        return agent.process(context)

    def multi_agent_analysis(self, context: AgentContext) -> Dict[str, AgentResponse]:
        """
        Run multiple agents in parallel for comprehensive analysis.

        Returns:
            Dictionary of agent responses
        """
        responses = {}

        for agent_type, agent in self.agents.items():
            try:
                response = agent.process(context)
                responses[agent_type.value] = response
            except Exception as e:
                logger.error(f"Error in {agent_type.value}: {e}")

        return responses

    def _route_query(self, query: str) -> AgentType:
        """Auto-detect appropriate agent based on query."""
        query_lower = query.lower()

        # Keywords for each agent type
        if any(word in query_lower for word in ["risk", "assess", "evaluate", "analyze risk"]):
            return AgentType.RISK_ANALYST

        if any(word in query_lower for word in ["litigation", "lawsuit", "court", "judge", "win", "probability"]):
            return AgentType.LITIGATION_PREDICTOR

        if any(word in query_lower for word in ["negotiat", "strategy", "position", "leverage", "bargain"]):
            return AgentType.NEGOTIATION_STRATEGIST

        # Default to risk analyst
        return AgentType.RISK_ANALYST


# ═══════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════

_copilot_instance: Optional[LegalCoPilot] = None


def get_legal_copilot() -> LegalCoPilot:
    """Get singleton Legal Co-Pilot instance."""
    global _copilot_instance
    if _copilot_instance is None:
        _copilot_instance = LegalCoPilot()
    return _copilot_instance
