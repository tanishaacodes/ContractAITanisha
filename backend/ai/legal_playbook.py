"""
Legal Playbook & Action Engine
Converts clause risk into actionable legal strategies
"""
from typing import Dict, List, Any, Optional


def generate_playbook(
    clause_name: str,
    clause_text: str,
    risk_level: str,
    jurisdiction: str = "India",
    contract_type: str = None
) -> Dict[str, Any]:
    """
    Generate comprehensive legal playbook for a clause

    Args:
        clause_name: Name of the clause (e.g., "Limitation of Liability")
        clause_text: Full text of the clause
        risk_level: HIGH, MEDIUM, or LOW
        jurisdiction: Legal jurisdiction (India, UK, US, etc.)
        contract_type: Type of contract (optional)

    Returns:
        Dictionary with legal analysis and recommendations
    """

    # Clause-specific playbook templates
    playbooks = {
        "limitation of liability": {
            "risk_explanation": (
                "This clause creates unlimited exposure to third-party claims and indirect damages. "
                "Without explicit caps, the company could face liabilities exceeding the contract value, "
                "including consequential damages, lost profits, and regulatory penalties."
            ),
            "recommended_rewrite": (
                "Total aggregate liability under this Agreement shall not exceed one times (1x) "
                "the total fees paid or payable under this Agreement in the twelve (12) months "
                "preceding the claim. For willful misconduct or gross negligence, liability shall "
                "be capped at two times (2x) such amount."
            ),
            "fallbacks": [
                "Cap liability at 2x contract value for willful misconduct only",
                "Exclude indirect, consequential, and punitive damages from all claims",
                "Implement per-incident cap of 1x with annual aggregate of 3x",
                "Carve out data breach liability but cap at 5x contract value"
            ],
            "negotiation_strategy": (
                "Concede broader indemnity scope or extended warranty period in exchange "
                "for liability cap. Frame cap as 'industry standard' and provide comparable "
                "contracts as precedent. Emphasize mutual benefit of predictable risk allocation."
            )
        },

        "indemnity": {
            "risk_explanation": (
                "Broad indemnity clause requires defending and paying for claims arising from "
                "counterparty's actions, even without fault. This creates one-sided risk allocation "
                "and unlimited financial exposure for third-party claims."
            ),
            "recommended_rewrite": (
                "Each party shall indemnify the other only for third-party claims directly arising "
                "from its own negligence or willful misconduct. Indemnification obligations shall "
                "be subject to the liability limitations set forth in Article [X] and shall not "
                "extend to claims arising from the indemnified party's actions or omissions."
            ),
            "fallbacks": [
                "Limit indemnity to claims arising from indemnifying party's negligence only",
                "Exclude indemnity for counterparty's contributory negligence",
                "Cap indemnity at insurance coverage limits",
                "Require actual fault, not just contractual breach"
            ],
            "negotiation_strategy": (
                "Propose mutual indemnification with equal obligations. Limit scope to party's "
                "own negligence. Link indemnity caps to liability limits. Carve out IP indemnity "
                "as separate provision with different treatment."
            )
        },

        "termination": {
            "risk_explanation": (
                "One-sided termination rights allow counterparty to exit without cause while "
                "locking you into the agreement. Termination fees and payment obligations "
                "create financial penalties for exercising termination rights."
            ),
            "recommended_rewrite": (
                "Either party may terminate this Agreement for convenience upon ninety (90) days "
                "prior written notice. Upon termination, all outstanding payments for services "
                "rendered shall be due within thirty (30) days, with no additional termination fees "
                "or penalties. Both parties shall have mutual transition assistance obligations."
            ),
            "fallbacks": [
                "Reduce notice period to 60 days with mutual rights",
                "Eliminate termination fees or cap at actual costs incurred",
                "Add termination for material breach with 30-day cure period",
                "Include force majeure termination rights"
            ],
            "negotiation_strategy": (
                "Emphasize business relationship flexibility and changing needs. Propose mutual "
                "termination rights as 'fair and balanced'. Remove financial penalties by offering "
                "reasonable transition period instead."
            )
        },

        "intellectual property": {
            "risk_explanation": (
                "Broad IP assignment gives counterparty ownership of your work product, innovations, "
                "and improvements. This prevents reuse of methodologies and tools, limiting business "
                "operations and creating dependency on single client."
            ),
            "recommended_rewrite": (
                "Client shall own deliverables specifically created for Client under this Agreement. "
                "Service Provider retains all rights to pre-existing IP, tools, methodologies, and "
                "general know-how. Service Provider grants Client a perpetual, non-exclusive license "
                "to use background IP solely with the deliverables."
            ),
            "fallbacks": [
                "Limit assignment to specific deliverables, not general know-how",
                "Retain ownership but grant exclusive license to client",
                "Reserve right to reuse non-client-specific methodologies",
                "Carve out pre-existing IP and grant license only"
            ],
            "negotiation_strategy": (
                "Distinguish between foreground IP (deliverables) and background IP (tools/methods). "
                "Emphasize need to reuse general capabilities across clients. Offer exclusive field-of-use "
                "license as compromise."
            )
        },

        "payment terms": {
            "risk_explanation": (
                "Extended payment terms create cash flow issues and increase credit risk. Vague "
                "payment triggers and discretionary approval processes delay payment indefinitely. "
                "No interest on late payments removes incentive for timely payment."
            ),
            "recommended_rewrite": (
                "All invoices shall be paid within fifteen (15) days of receipt. Late payments shall "
                "accrue interest at 1.5% per month (18% annually). Payment shall not be withheld due "
                "to disputes unrelated to the specific invoice. Client may only dispute invoices within "
                "five (5) days of receipt."
            ),
            "fallbacks": [
                "Net 30 payment terms with 2% discount for payment within 10 days",
                "Progress payments tied to milestones, not client satisfaction",
                "Suspend services upon payment default exceeding 15 days",
                "Require advance payment for expenses exceeding defined threshold"
            ],
            "negotiation_strategy": (
                "Frame faster payment terms as cash flow necessity for smaller vendor. Offer early "
                "payment discount. Link payment terms to service continuity and quality maintenance."
            )
        },

        "warranty": {
            "risk_explanation": (
                "Broad warranties create ongoing liability for conditions beyond your control. "
                "Unlimited warranty period and strict liability regardless of fault creates "
                "unpredictable long-tail risk exposure."
            ),
            "recommended_rewrite": (
                "Service Provider warrants that services will be performed in a professional and "
                "workmanlike manner consistent with industry standards. This warranty is exclusive "
                "and in lieu of all other warranties, express or implied, including warranties of "
                "merchantability and fitness for particular purpose. Warranty period is ninety (90) "
                "days from delivery."
            ),
            "fallbacks": [
                "Limit warranty to conformance with specifications only",
                "Reduce warranty period to 30 days for software/services",
                "Exclude warranties for client-caused issues or modifications",
                "Cap warranty remedy at re-performance or refund, not damages"
            ],
            "negotiation_strategy": (
                "Separate product warranties from service warranties. Limit duration based on "
                "industry norms. Emphasize that broader warranties require higher pricing to cover risk."
            )
        },

        "confidentiality": {
            "risk_explanation": (
                "One-sided confidentiality obligations restrict your ability to use information while "
                "not protecting your own confidential information. Overly broad definitions of confidential "
                "information can include publicly available data or independently developed information."
            ),
            "recommended_rewrite": (
                "Each party agrees to maintain in confidence all Confidential Information of the other party. "
                "Confidential Information excludes information that: (i) is publicly available through no fault "
                "of receiving party; (ii) was rightfully known prior to disclosure; (iii) is independently developed; "
                "or (iv) is rightfully obtained from third parties. Confidentiality obligations survive for three (3) "
                "years after termination."
            ),
            "fallbacks": [
                "Propose mutual confidentiality obligations instead of one-sided",
                "Narrow definition to exclude public information and independently developed work",
                "Limit confidentiality period to 2-3 years post-termination",
                "Exclude residual knowledge and skills from confidentiality"
            ],
            "negotiation_strategy": (
                "Emphasize need for mutual protection and balanced obligations. Narrow the definition "
                "to exclude standard industry practices and public information. Limit duration to reasonable period."
            )
        },

        "dispute resolution": {
            "risk_explanation": (
                "One-sided dispute resolution provisions may require you to arbitrate in inconvenient forums "
                "or waive important legal rights. Mandatory arbitration can limit discovery and appeal rights. "
                "Venue selection in counterparty's jurisdiction creates logistical and cost disadvantages."
            ),
            "recommended_rewrite": (
                "Any disputes arising under this Agreement shall first be subject to good faith negotiation "
                "between senior executives for thirty (30) days. If unresolved, disputes shall be submitted to "
                "mediation, and if mediation fails, to binding arbitration under AAA Commercial Rules in a mutually "
                "agreed neutral location. Each party bears its own costs. Courts retain jurisdiction for injunctive relief."
            ),
            "fallbacks": [
                "Agree to mediation before arbitration as cost-saving measure",
                "Select neutral jurisdiction acceptable to both parties",
                "Preserve court jurisdiction for intellectual property disputes",
                "Allow each party to bear own costs regardless of outcome"
            ],
            "negotiation_strategy": (
                "Propose neutral forum and mutual cost-bearing. Emphasize desire to resolve disputes efficiently "
                "without excessive legal costs. Carve out injunctive relief for courts."
            )
        },

        "force majeure": {
            "risk_explanation": (
                "Narrow force majeure clauses may not excuse performance during unforeseen events, leaving "
                "you liable for non-performance beyond your control. One-sided provisions may allow counterparty "
                "to suspend without corresponding obligations."
            ),
            "recommended_rewrite": (
                "Neither party shall be liable for failure to perform due to causes beyond reasonable control, "
                "including acts of God, war, terrorism, pandemics, government restrictions, natural disasters, "
                "labor disputes, or supplier failures. Affected party must provide prompt notice and use reasonable "
                "efforts to resume performance. If force majeure continues for sixty (60) days, either party may "
                "terminate without penalty."
            ),
            "fallbacks": [
                "Include specific examples relevant to your business (e.g., pandemics, cyber attacks)",
                "Add termination right if force majeure exceeds 30-60 days",
                "Require affected party to mitigate and find alternatives",
                "Ensure mutual application to both parties equally"
            ],
            "negotiation_strategy": (
                "Emphasize need for broad definition to cover modern risks (cyber, pandemic). Propose mutual "
                "termination rights if prolonged. Frame as protection for both parties."
            )
        },

        "governing law": {
            "risk_explanation": (
                "Choice of unfamiliar or unfavorable governing law increases legal costs and uncertainty. "
                "Foreign law may have unfavorable interpretations of key provisions or lack established precedent "
                "for your industry."
            ),
            "recommended_rewrite": (
                "This Agreement shall be governed by the laws of [Neutral Jurisdiction] without regard to "
                "conflicts of law principles. Each party consents to personal jurisdiction in the courts of "
                "[Neutral Jurisdiction] for any disputes arising hereunder."
            ),
            "fallbacks": [
                "Propose law of jurisdiction where contract will be primarily performed",
                "Agree to law of party with larger financial stake in transaction",
                "Select internationally recognized jurisdiction with established commercial law",
                "Separate governing law from venue/jurisdiction provisions"
            ],
            "negotiation_strategy": (
                "Propose neutral jurisdiction with well-established commercial law (e.g., New York, Delaware, England). "
                "Emphasize predictability and enforceability of contract rights."
            )
        },

        "non-compete": {
            "risk_explanation": (
                "Broad non-compete restrictions limit your ability to pursue business opportunities and may prevent "
                "using general skills and knowledge. Overly long duration or wide geographic scope may be unenforceable "
                "but create litigation risk."
            ),
            "recommended_rewrite": (
                "During the term and for twelve (12) months thereafter, neither party shall directly solicit the other's "
                "clients specifically served under this Agreement for substantially similar services. This does not restrict "
                "general business activities, public marketing, or use of general skills and knowledge."
            ),
            "fallbacks": [
                "Limit restriction to direct solicitation of specific clients served",
                "Reduce duration to 6-12 months post-termination",
                "Narrow geographic scope to specific territories",
                "Exclude general business activities and public marketing"
            ],
            "negotiation_strategy": (
                "Narrow to customer non-solicitation rather than general non-compete. Emphasize need to use general "
                "skills and industry knowledge. Limit duration and scope to what's commercially reasonable."
            )
        }
    }

    # Normalize clause name and apply aliases
    clause_key = clause_name.lower().strip()

    # Clause name aliases for better matching
    aliases = {
        "indemnification": "indemnity",
        "indemnity clause": "indemnity",
        "liability limitation": "limitation of liability",
        "liability cap": "limitation of liability",
        "ip rights": "intellectual property",
        "ip": "intellectual property",
        "warranties": "warranty",
        "payment": "payment terms",
        "confidential information": "confidentiality",
        "non-disclosure": "confidentiality",
        "nda": "confidentiality",
        "dispute": "dispute resolution",
        "arbitration": "dispute resolution",
        "termination clause": "termination",
        "non compete": "non-compete",
        "noncompete": "non-compete",
    }

    # Apply alias if exists
    for alias, canonical in aliases.items():
        if alias in clause_key:
            clause_key = canonical
            break

    # Try to find best matching playbook
    matched_key = None
    for key in playbooks.keys():
        # Exact match or substring match (bidirectional)
        if clause_key == key or key in clause_key or clause_key in key:
            matched_key = key
            break

    # If matched, use that playbook; otherwise use default
    clause_key = matched_key if matched_key else clause_key

    playbook = playbooks.get(clause_key, {
        "risk_explanation": (
            f"This {clause_name} clause creates potential risk exposure that should be "
            "reviewed and negotiated to ensure balanced risk allocation between parties."
        ),
        "recommended_rewrite": (
            "Recommend consulting legal counsel to redraft this clause with appropriate "
            "protections, limitations, and mutual obligations."
        ),
        "fallbacks": [
            "Negotiate mutual obligations instead of one-sided terms",
            "Add explicit limitations and caps to reduce exposure",
            "Include carve-outs for circumstances beyond control"
        ],
        "negotiation_strategy": (
            "Request reciprocal terms and emphasize mutual benefit of balanced risk allocation. "
            "Use industry standards and comparable contracts as precedent."
        )
    })

    # Add jurisdiction-specific guidance
    jurisdiction_guidance = get_jurisdiction_guidance(clause_name, jurisdiction)

    return {
        **playbook,
        "jurisdiction_guidance": jurisdiction_guidance,
        "risk_level": risk_level,
        "clause_name": clause_name
    }


def get_jurisdiction_guidance(clause_name: str, jurisdiction: str) -> Dict[str, str]:
    """
    Provide jurisdiction-specific legal guidance

    Args:
        clause_name: Name of the clause
        jurisdiction: Legal jurisdiction

    Returns:
        Dictionary of jurisdiction-specific guidance
    """

    guidance_db = {
        "India": {
            "limitation of liability": (
                "Indian courts generally enforce liability caps if explicitly negotiated and "
                "clearly stated. Under Section 23 of Indian Contract Act, caps cannot exclude "
                "liability for fraud or gross negligence. Include specific monetary amounts, "
                "not just formulaic caps."
            ),
            "indemnity": (
                "Indian law recognizes indemnity under Section 124-125 of Contract Act. "
                "Indemnifier liable only for acts within scope of authority. Courts require "
                "clear language and mutual consideration. Joint and several liability must be explicit."
            ),
            "termination": (
                "Termination clauses governed by Contract Act Section 39-40. Advance notice "
                "requirements are enforceable. Penalty clauses (Section 74) are reduced to "
                "actual damages by courts. Ensure termination fees reflect genuine pre-estimate of loss."
            ),
            "default": (
                "Indian courts enforce clearly drafted contractual provisions but interpret "
                "ambiguities against the drafter. Include specific performance remedies as "
                "damages may be insufficient under Indian law."
            )
        },

        "UK": {
            "limitation of liability": (
                "Limitation clauses subject to Unfair Contract Terms Act 1977 (UCTA) reasonableness "
                "test. Must be brought to attention and not exclude liability for death/personal injury. "
                "Courts examine bargaining power and alternative options available."
            ),
            "indemnity": (
                "Indemnity clauses construed strictly under English law. Must use clear words to "
                "cover indirect/consequential losses. Subject to UCTA reasonableness test in B2C "
                "and some B2B contracts. Insurable interest required."
            ),
            "termination": (
                "Termination rights must be clear and unambiguous. Common law requires reasonable "
                "notice period if not specified. Post-termination restraints subject to restraint "
                "of trade doctrine if unreasonable."
            ),
            "default": (
                "English law favors freedom of contract but imposes reasonableness standards "
                "through UCTA and common law. Ensure clear drafting and evidence of negotiation "
                "for contentious terms."
            )
        },

        "US": {
            "limitation of liability": (
                "Generally enforceable except for gross negligence, willful misconduct, or fraud. "
                "State law varies - some states limit caps in consumer contracts. Must be "
                "conspicuous and bargained-for. Cannot violate public policy."
            ),
            "indemnity": (
                "Broad indemnity clauses enforceable but state laws vary significantly. Some states "
                "prohibit indemnity for indemnitee's own negligence. Third-party indemnity more "
                "readily enforced than first-party. Insurance requirements common."
            ),
            "termination": (
                "At-will termination generally permitted unless implied covenant of good faith. "
                "Termination fees enforceable if not penalties. Notice requirements are enforced. "
                "Employment-related terminations have additional statutory protections."
            ),
            "default": (
                "U.S. law generally enforces contracts as written under freedom of contract principles. "
                "Unconscionability and public policy provide limited exceptions. State law governs, "
                "creating significant variation across jurisdictions."
            )
        },

        "Singapore": {
            "limitation of liability": (
                "Limitation clauses generally enforceable under Unfair Contract Terms Act (UCTA) "
                "Singapore. Must satisfy reasonableness test. Cannot exclude liability for fraud, "
                "willful default, or death/personal injury. Clear and prominent drafting required."
            ),
            "indemnity": (
                "Indemnity provisions enforceable if clear and unambiguous. Singapore courts "
                "interpret strictly against indemnifier. Must comply with UCTA reasonableness "
                "in certain contexts. Insurance backing often required."
            ),
            "termination": (
                "Termination clauses enforced as written. Notice periods must be reasonable. "
                "Penalty clauses not enforceable - only genuine pre-estimates of loss. Singapore "
                "courts favor commercial certainty and enforce clear termination mechanisms."
            ),
            "default": (
                "Singapore law favors freedom of contract and commercial certainty. Courts enforce "
                "clearly drafted terms. UCTA provides limited reasonableness oversight. International "
                "commercial arbitration strongly supported."
            )
        }
    }

    jurisdiction_data = guidance_db.get(jurisdiction, guidance_db["US"])

    clause_key = None
    for key in ["limitation of liability", "indemnity", "termination", "intellectual property", "payment", "warranty",
                "confidentiality", "dispute resolution", "force majeure", "governing law", "non-compete"]:
        if key in clause_name.lower():
            clause_key = key
            break

    specific_guidance = jurisdiction_data.get(clause_key, jurisdiction_data["default"])

    return {
        jurisdiction: specific_guidance
    }


def generate_counter_proposal(
    clause_name: str,
    current_text: str,
    recommended_rewrite: str
) -> str:
    """
    Generate formal counter-proposal language

    Args:
        clause_name: Name of the clause
        current_text: Current clause text
        recommended_rewrite: Recommended replacement

    Returns:
        Formatted counter-proposal text
    """

    return f"""
COUNTER-PROPOSAL: {clause_name.upper()}

Current Language (Proposed by Counterparty):
{current_text}

Proposed Revision:
{recommended_rewrite}

Rationale:
This revision ensures balanced risk allocation between the parties and aligns with
industry-standard commercial terms. The proposed changes protect both parties' interests
while maintaining the core commercial intent of the provision.

We believe this revision is commercially reasonable and represents a fair allocation
of contractual risk. We are prepared to discuss this provision further during negotiations.
"""


def get_negotiation_precedents(clause_type: str, industry: str = None) -> List[Dict[str, str]]:
    """
    Retrieve negotiation precedents and comparable terms

    Args:
        clause_type: Type of clause
        industry: Industry sector (optional)

    Returns:
        List of precedent examples
    """

    precedents = [
        {
            "source": "Fortune 500 Standard MSA Template",
            "excerpt": "Total liability shall not exceed 1x annual fees...",
            "note": "Industry standard for professional services"
        },
        {
            "source": "Technology Vendor Agreement (SaaS)",
            "excerpt": "Aggregate liability capped at 12 months' fees paid...",
            "note": "Common in cloud services contracts"
        },
        {
            "source": "Gartner Model Contract Clauses",
            "excerpt": "Liability limited to direct damages only, excluding consequential...",
            "note": "Legal industry best practice"
        }
    ]

    return precedents[:3]
