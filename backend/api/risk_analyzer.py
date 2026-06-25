"""
Risk Analysis Algorithm for Contract Deviation Detection
"""
from core.models import Contract, Clause, TemplateClause, ContractRiskAnalysis, ClauseDeviation
from rag import call_llm
from .risk_scoring_model import risk_scoring_algorithm, generate_risk_summary, get_top_risk_categories


def analyze_contract_risk(contract_id):
    """
    Perform comprehensive risk analysis on a contract

    Returns:
        ContractRiskAnalysis object with deviations
    """
    try:
        contract = Contract.objects.get(id=contract_id)

        # Delete any existing risk analysis
        ContractRiskAnalysis.objects.filter(contract=contract).delete()

        # Get template clauses for this contract type
        template_clauses = TemplateClause.objects.filter(
            contract_type=contract.contract_type
        )

        # Get extracted clauses for this contract
        extracted_clauses = Clause.objects.filter(contract=contract)

        # Create risk analysis record
        risk_analysis = ContractRiskAnalysis.objects.create(
            contract=contract,
            risk_level='LOW',  # Will be updated based on findings
            risk_score=0,
            total_deviations=0,
            critical_issues=0,
            medium_issues=0,
            low_issues=0,
            analysis_summary=''
        )

        deviations = []
        critical_count = 0
        medium_count = 0
        low_count = 0

        # Only check template-based deviations if templates exist
        has_templates = template_clauses.exists()

        # Check for missing clauses
        for template in template_clauses:
            clause_found = extracted_clauses.filter(
                clause_name=template.clause_name,
                found=True
            ).exists()

            if not clause_found:
                # Determine severity based on importance
                if template.importance == 'CRITICAL':
                    severity = 'HIGH'
                    critical_count += 1
                    recommendation = f'URGENT: Add {template.clause_name} clause to protect your interests. {template.description}'
                elif template.importance == 'IMPORTANT':
                    severity = 'MEDIUM'
                    medium_count += 1
                    recommendation = f'Consider adding {template.clause_name} clause. {template.description}'
                else:  # OPTIONAL
                    severity = 'LOW'
                    low_count += 1
                    recommendation = f'Optional: {template.clause_name} clause could be added for completeness.'

                deviation = ClauseDeviation.objects.create(
                    risk_analysis=risk_analysis,
                    clause_name=template.clause_name,
                    deviation_type='MISSING',
                    severity=severity,
                    description=f'Missing {template.clause_name} clause',
                    recommendation=recommendation
                )
                deviations.append(deviation)

        # Check for unfavorable terms in found clauses
        for template in template_clauses:
            if template.risk_keywords:
                # Find matching extracted clause
                matching_clause = extracted_clauses.filter(
                    clause_name=template.clause_name,
                    found=True
                ).first()

                if matching_clause and matching_clause.extracted_text:
                    text_lower = matching_clause.extracted_text.lower()

                    # Check for risk keywords
                    found_keywords = []
                    for keyword in template.risk_keywords:
                        if keyword.lower() in text_lower:
                            found_keywords.append(keyword)

                    if found_keywords:
                        # Unfavorable terms found
                        if template.importance == 'CRITICAL':
                            severity = 'HIGH'
                            critical_count += 1
                        elif template.importance == 'IMPORTANT':
                            severity = 'MEDIUM'
                            medium_count += 1
                        else:
                            severity = 'LOW'
                            low_count += 1

                        keywords_str = ', '.join(found_keywords)
                        deviation = ClauseDeviation.objects.create(
                            risk_analysis=risk_analysis,
                            clause_name=template.clause_name,
                            deviation_type='UNFAVORABLE',
                            severity=severity,
                            description=f'Potentially unfavorable terms detected in {template.clause_name}: {keywords_str}',
                            recommendation=f'Review {template.clause_name} carefully. Consider negotiating better terms.'
                        )
                        deviations.append(deviation)

        # ========== NEW RISK SCORING MODEL (20 Categories) ==========
        # Run keyword-based risk scoring on full contract text
        risk_scoring_result = risk_scoring_algorithm(contract.full_text)

        # Extract results from new model
        total_risk_score = risk_scoring_result['total_risk_score']
        risk_level = risk_scoring_result['risk_level'].upper()  # Convert to match DB choices
        category_breakdown = risk_scoring_result['category_breakdown']
        detailed_breakdown = risk_scoring_result['detailed_breakdown']

        # Categorize risks from category scores into critical/medium/low
        # Category score thresholds: 4-5 = Critical, 2-3.9 = Medium, 0.1-1.9 = Low
        model_critical_count = 0
        model_medium_count = 0
        model_low_count = 0

        for category, score in category_breakdown.items():
            if score >= 4.0:
                model_critical_count += 1
            elif score >= 2.0:
                model_medium_count += 1
            elif score >= 0.1:
                model_low_count += 1

        # Combine template-based and model-based counts
        total_critical = critical_count + model_critical_count
        total_medium = medium_count + model_medium_count
        total_low = low_count + model_low_count

        # Generate enhanced analysis summary
        # Total deviations = template deviations + risk categories with issues
        total_deviations = len(deviations) + total_critical + total_medium + total_low
        summary_parts = []

        # Include combined deviation counts
        if total_critical > 0:
            summary_parts.append(f'{total_critical} critical issue{"s" if total_critical > 1 else ""}')
        if total_medium > 0:
            summary_parts.append(f'{total_medium} medium issue{"s" if total_medium > 1 else ""}')
        if total_low > 0:
            summary_parts.append(f'{total_low} low issue{"s" if total_low > 1 else ""}')

        # Add top risk categories from new model
        top_risks = get_top_risk_categories(category_breakdown, top_n=3)
        if top_risks:
            risk_categories_text = ", ".join([f"{name} ({score}/5)" for name, score in top_risks])
            summary_parts.append(f'Top risk areas: {risk_categories_text}')

        if summary_parts:
            analysis_summary = f'Risk Score: {total_risk_score}/100. {" | ".join(summary_parts)}.'
        else:
            analysis_summary = f'Contract has low risk (Score: {total_risk_score}/100). No significant issues detected.'

        # Update risk analysis with both old and new model data
        risk_analysis.risk_level = risk_level
        risk_analysis.risk_score = int(total_risk_score)  # Store as integer
        risk_analysis.total_deviations = total_deviations
        risk_analysis.critical_issues = total_critical
        risk_analysis.medium_issues = total_medium
        risk_analysis.low_issues = total_low
        risk_analysis.analysis_summary = analysis_summary
        risk_analysis.category_breakdown = category_breakdown
        risk_analysis.detailed_breakdown = detailed_breakdown
        risk_analysis.save()

        return risk_analysis

    except Contract.DoesNotExist:
        raise Exception(f'Contract with ID {contract_id} not found')
    except Exception as e:
        raise Exception(f'Risk analysis failed: {str(e)}')


def get_risk_level_color(risk_level):
    """Get color code for risk level"""
    colors = {
        'LOW': 'green',
        'MEDIUM': 'yellow',
        'HIGH': 'red',
        'CRITICAL': 'darkred'
    }
    return colors.get(risk_level, 'gray')


def get_severity_color(severity):
    """Get color code for deviation severity"""
    colors = {
        'LOW': 'green',
        'MEDIUM': 'yellow',
        'HIGH': 'red'
    }
    return colors.get(severity, 'gray')


def explain_contract_risks(contract_id):
    """
    Generate LLM-based explanation of contract risks

    Returns:
        dict: {
            'risk_analysis': risk analysis data,
            'llm_explanation': AI-generated risk explanation,
            'contract_summary': brief contract summary
        }
    """
    try:
        contract = Contract.objects.get(id=contract_id)

        # Get risk analysis (run if not exists)
        risk_analysis = ContractRiskAnalysis.objects.filter(contract=contract).first()

        if not risk_analysis:
            # Run risk analysis first
            risk_analysis = analyze_contract_risk(contract_id)

        # Get all deviations
        deviations = ClauseDeviation.objects.filter(risk_analysis=risk_analysis)

        # Build context for LLM
        deviation_details = []
        for dev in deviations:
            deviation_details.append(
                f"- {dev.clause_name} ({dev.severity} severity, {dev.deviation_type}): "
                f"{dev.description}"
            )

        deviation_text = "\n".join(deviation_details) if deviation_details else "No deviations found."

        # Get extracted clauses for context
        extracted_clauses = Clause.objects.filter(contract=contract, found=True)
        clause_summaries = []
        for clause in extracted_clauses[:10]:  # Limit to top 10 clauses
            if clause.extracted_text:
                clause_summaries.append(
                    f"• {clause.clause_name}: {clause.extracted_text[:200]}..."
                )

        clauses_context = "\n".join(clause_summaries) if clause_summaries else "No clauses extracted."

        # Build comprehensive prompt for LLM
        prompt = f"""
You are a Legal Risk Analysis Expert specializing in contract review.

CONTRACT INFORMATION:
- Type: {contract.contract_type}
- Classification Confidence: {contract.confidence_score}%
- Overall Risk Level: {risk_analysis.risk_level}
- Risk Score: {risk_analysis.risk_score}/100
- Total Issues Found: {risk_analysis.total_deviations}
  • Critical Issues: {risk_analysis.critical_issues}
  • Medium Issues: {risk_analysis.medium_issues}
  • Low Issues: {risk_analysis.low_issues}

IDENTIFIED DEVIATIONS:
{deviation_text}

KEY EXTRACTED CLAUSES:
{clauses_context}

TASK:
Provide a comprehensive, professional risk explanation that answers:

1. EXECUTIVE SUMMARY (2-3 sentences)
   - What is the overall risk level and why?
   - What are the most critical concerns?

2. DETAILED RISK BREAKDOWN
   For each critical/medium risk identified:
   - What is the specific risk?
   - Why is it concerning from a legal/business perspective?
   - What are the potential consequences?

3. BUSINESS IMPACT
   - How might these risks affect business operations?
   - What are the financial/legal implications?

4. RECOMMENDED ACTIONS
   - What immediate steps should be taken?
   - What clauses need negotiation or addition?
   - Priority order of remediation

FORMATTING RULES:
- Use clear headings with "##" markdown syntax
- Use bullet points for lists
- Be specific and actionable
- Maintain professional legal tone
- Base analysis ONLY on the provided information
- If critical risks exist, emphasize urgency

Generate the risk explanation below:
"""

        # Generate structured explanation from DB data (fast, no Ollama timeout)
        explanation = _build_risk_explanation(
            contract, risk_analysis, deviations, extracted_clauses
        )

        # Build response
        result = {
            'contract_id': str(contract.id),
            'contract_filename': contract.original_filename,
            'contract_type': contract.contract_type,
            'risk_level': risk_analysis.risk_level,
            'risk_score': risk_analysis.risk_score,
            'total_deviations': risk_analysis.total_deviations,
            'critical_issues': risk_analysis.critical_issues,
            'medium_issues': risk_analysis.medium_issues,
            'low_issues': risk_analysis.low_issues,
            'analysis_summary': risk_analysis.analysis_summary,
            'executive_summary': risk_analysis.executive_summary,
            'llm_explanation': explanation,
            'category_breakdown': risk_analysis.category_breakdown,
            'detailed_breakdown': risk_analysis.detailed_breakdown,
            'deviations': [
                {
                    'clause_name': dev.clause_name,
                    'deviation_type': dev.deviation_type,
                    'severity': dev.severity,
                    'description': dev.description,
                    'recommendation': dev.recommendation
                }
                for dev in deviations
            ]
        }

        return result

    except Contract.DoesNotExist:
        raise Exception(f'Contract with ID {contract_id} not found')
    except Exception as e:
        raise Exception(f'Risk explanation failed: {str(e)}')


def _build_risk_explanation(contract, risk_analysis, deviations, clauses):
    """Instant template-based risk explanation from DB data — no Ollama call."""
    risk_level = risk_analysis.risk_level or 'Unknown'
    risk_score = risk_analysis.risk_score or 0
    total = risk_analysis.total_deviations or 0
    critical = risk_analysis.critical_issues or 0
    medium = risk_analysis.medium_issues or 0
    low = risk_analysis.low_issues or 0

    urgency = 'Immediate legal review recommended.' if critical > 0 else (
        'Negotiation recommended before signing.' if medium > 0 else
        'Contract is generally acceptable with minor refinements.'
    )

    lines = [
        '## Executive Summary',
        f'This **{contract.contract_type}** presents a **{risk_level} risk** profile '
        f'with an overall score of **{risk_score}/100**. Analysis identified **{total} issue(s)**: '
        f'{critical} critical, {medium} medium, and {low} low severity. {urgency}',
        '',
    ]

    if deviations:
        lines.append('## Detailed Risk Breakdown')
        for dev in deviations:
            sev_icon = {'critical': '🔴', 'medium': '🟡', 'low': '🟢'}.get(
                (dev.severity or '').lower(), '⚪')
            lines.append(
                f'- {sev_icon} **{dev.clause_name}** *({dev.severity}, {dev.deviation_type})*: '
                f'{dev.description}'
            )
            if dev.recommendation:
                lines.append(f'  - *Action*: {dev.recommendation}')
        lines.append('')

    lines.append('## Business Impact')
    if critical > 0:
        lines.append(
            f'- **High financial/legal exposure**: {critical} critical clause(s) may expose the '
            f'business to penalties, disputes, or unenforceable terms.'
        )
    if medium > 0:
        lines.append(
            f'- **Operational risk**: {medium} medium-severity issue(s) may affect contract '
            f'performance or create ambiguous obligations.'
        )
    if low > 0:
        lines.append(
            f'- **Minor refinements needed**: {low} low-severity item(s) that can be addressed '
            f'during standard review.'
        )
    if total == 0:
        lines.append('- Contract aligns well with standard templates; minimal business risk identified.')
    lines.append('')

    lines.append('## Recommended Actions')
    priority_devs = [d for d in deviations if (d.severity or '').lower() == 'critical'][:3]
    medium_devs = [d for d in deviations if (d.severity or '').lower() == 'medium'][:2]
    for dev in priority_devs:
        action = dev.recommendation or f'Review and negotiate {dev.clause_name} terms.'
        lines.append(f'1. **[CRITICAL]** {action}')
    for dev in medium_devs:
        action = dev.recommendation or f'Clarify {dev.clause_name} obligations.'
        lines.append(f'2. **[MEDIUM]** {action}')
    if not priority_devs and not medium_devs:
        lines.append('- Proceed with standard legal review before signing.')
    lines.append(f'- Obtain sign-off from legal counsel given the {risk_level} risk rating.')

    if clauses:
        lines.append('')
        lines.append('## Key Clauses Identified')
        for clause in list(clauses)[:5]:
            if clause.extracted_text:
                lines.append(f'- **{clause.clause_name}**: {clause.extracted_text[:150]}...')

    return '\n'.join(lines)


def _build_executive_summary(contract, risk_analysis, deviations):
    """Instant template-based executive summary from DB data — no Ollama call."""
    risk_level = risk_analysis.risk_level or 'Unknown'
    risk_score = risk_analysis.risk_score or 0
    total = risk_analysis.total_deviations or 0
    critical = risk_analysis.critical_issues or 0
    medium = risk_analysis.medium_issues or 0
    low = risk_analysis.low_issues or 0

    if critical > 0:
        verdict = 'requires immediate legal review before signing'
        action_urgency = 'Do NOT sign without addressing critical issues below.'
    elif medium > 0:
        verdict = 'requires negotiation on several medium-risk clauses'
        action_urgency = 'Negotiate flagged clauses before signing.'
    else:
        verdict = 'is generally acceptable with minor refinements'
        action_urgency = 'Proceed with standard legal review.'

    lines = [
        '## Executive Summary',
        f'This **{contract.contract_type}** {verdict}. The overall risk score is '
        f'**{risk_score}/100** ({risk_level} risk), with {total} issue(s) identified: '
        f'{critical} critical, {medium} medium, and {low} low. {action_urgency}',
        '',
    ]

    lines.append('## Key Risks')
    if deviations:
        for dev in deviations:
            sev_icon = {'critical': '🔴', 'medium': '🟡', 'low': '🟢'}.get(
                (dev.severity or '').lower(), '⚪')
            lines.append(
                f'- {sev_icon} **{dev.clause_name}**: {dev.description}'
            )
    else:
        lines.append('- No significant deviations from standard template identified.')
    lines.append('')

    lines.append('## Priority Actions')
    if critical > 0:
        critical_devs = [d for d in deviations if (d.severity or '').lower() == 'critical'][:3]
        for dev in critical_devs:
            lines.append(f'- {dev.recommendation or f"Negotiate {dev.clause_name} terms immediately."}')
    if medium > 0:
        medium_devs = [d for d in deviations if (d.severity or '').lower() == 'medium'][:2]
        for dev in medium_devs:
            lines.append(f'- {dev.recommendation or f"Clarify {dev.clause_name} obligations."}')
    if not critical and not medium:
        lines.append('- Complete standard legal review')
        lines.append('- Obtain authorized signatory approval')
    lines.append('- Ensure all parties have reviewed and agreed to final terms before execution')

    return '\n'.join(lines)


def generate_executive_summary(contract, risk_analysis):
    """
    Generate concise executive summary for contract analysis

    Args:
        contract: Contract model instance
        risk_analysis: ContractRiskAnalysis model instance

    Returns:
        str: Markdown formatted executive summary
    """
    try:
        # Get top 5 critical/medium deviations
        deviations = ClauseDeviation.objects.filter(
            risk_analysis=risk_analysis
        ).order_by('-severity', 'clause_name')[:5]

        # Build deviation summary for prompt
        deviation_summaries = []
        for dev in deviations:
            deviation_summaries.append(
                f"• {dev.clause_name} ({dev.severity}): {dev.description}"
            )

        top_concerns = "\n".join(deviation_summaries) if deviation_summaries else "No significant concerns identified."

        # Build focused prompt for executive summary
        prompt = f"""
You are a Contract Analysis Executive Summary Assistant.

TASK: Generate a concise executive summary (2-3 paragraphs) suitable for C-level executives who need to quickly understand the contract's risk profile and key decisions needed.

CONTRACT DETAILS:
- Type: {contract.contract_type}
- Classification Confidence: {contract.confidence_score}%
- Overall Risk Level: {risk_analysis.risk_level}
- Risk Score: {risk_analysis.risk_score}/100

KEY METRICS:
- Total Issues: {risk_analysis.total_deviations}
- Critical Issues: {risk_analysis.critical_issues}
- Medium Issues: {risk_analysis.medium_issues}
- Low Issues: {risk_analysis.low_issues}

TOP CONCERNS:
{top_concerns}

REQUIREMENTS:
1. Write in clear, business-focused language (avoid heavy legal jargon)
2. Focus on business impact and strategic implications
3. Be concise but actionable
4. Use the following structure:

## Executive Summary
[Write 2-3 paragraphs that provide:
- Overall assessment of the contract's risk level and why
- Most critical business concerns and their potential impact
- Whether this contract should proceed, needs negotiation, or requires legal review]

## Key Risks
[List 3-5 bullet points of the most important risks, focusing on business impact:
- Each bullet should explain WHAT the risk is and WHY it matters to the business
- Prioritize by severity and business impact]

## Priority Actions
[List 3-5 specific, actionable bullet points in priority order:
- What must be done before signing
- What clauses need negotiation or addition
- What approvals or reviews are needed]

FORMATTING:
- Use markdown headers (##) for sections
- Use bullet points (-) for lists
- Keep it scannable and professional
- Maximum 3-4 paragraphs in Executive Summary section
- Be specific and avoid vague statements

Generate the executive summary below:
"""

        # Generate structured summary from DB data (fast, no Ollama timeout)
        summary = _build_executive_summary(contract, risk_analysis, deviations)
        return summary

    except Exception as e:
        raise Exception(f'Executive summary generation failed: {str(e)}')
