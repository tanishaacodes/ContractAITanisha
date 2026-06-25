"""
Contract Redline Engine
=======================
Core AI logic for contract redlining:
- Clause risk classification
- Risk scoring (0-100)
- Redline diff generation
- AI-powered clause suggestions
"""

import json
import re
from difflib import unified_diff
from typing import Dict, List, Optional, Any
import requests
from django.conf import settings


# Risk type definitions with keywords for classification
RISK_CATEGORIES = {
    'FINANCIAL': {
        'keywords': ['payment', 'fee', 'cost', 'price', 'compensation', 'damages', 'penalty', 'interest', 'refund'],
        'weight': 1.2
    },
    'LIABILITY': {
        'keywords': ['liable', 'liability', 'responsible', 'responsibility', 'damages', 'loss', 'harm', 'negligence'],
        'weight': 1.5
    },
    'TERMINATION': {
        'keywords': ['terminate', 'termination', 'cancel', 'cancellation', 'end', 'expiry', 'expire', 'notice period'],
        'weight': 1.3
    },
    'IP': {
        'keywords': ['intellectual property', 'patent', 'copyright', 'trademark', 'trade secret', 'license', 'ownership'],
        'weight': 1.4
    },
    'CONFIDENTIALITY': {
        'keywords': ['confidential', 'confidentiality', 'non-disclosure', 'nda', 'proprietary', 'secret', 'private'],
        'weight': 1.2
    },
    'GOVERNING_LAW': {
        'keywords': ['governing law', 'jurisdiction', 'applicable law', 'venue', 'arbitration', 'dispute resolution'],
        'weight': 1.1
    },
    'INDEMNITY': {
        'keywords': ['indemnify', 'indemnification', 'hold harmless', 'defend', 'indemnitor', 'indemnitee'],
        'weight': 1.5
    },
    'FORCE_MAJEURE': {
        'keywords': ['force majeure', 'act of god', 'unforeseeable', 'beyond control', 'natural disaster', 'pandemic'],
        'weight': 1.0
    },
    'DATA_PRIVACY': {
        'keywords': ['data protection', 'privacy', 'personal data', 'gdpr', 'ccpa', 'data processing', 'data breach'],
        'weight': 1.3
    },
    'COMPLIANCE': {
        'keywords': ['compliance', 'regulatory', 'legal requirement', 'law', 'regulation', 'statute', 'audit'],
        'weight': 1.2
    }
}

# Risk indicators that increase score (high severity)
HIGH_RISK_INDICATORS = [
    'unlimited liability', 'any and all damages', 'sole discretion', 'without limitation',
    'irrevocable', 'perpetual', 'exclusive', 'waive', 'forfeit', 'automatically renew',
    'unilateral', 'at will', 'immediate termination', 'without cause', 'without notice',
    'indemnify', 'hold harmless', 'consequential damages', 'punitive damages'
]

# Medium risk indicators (moderate severity)
MEDIUM_RISK_INDICATORS = [
    'shall', 'must', 'obligated', 'required', 'warranty', 'represent', 'covenant',
    'terminate', 'breach', 'default', 'penalty', 'liquidated damages', 'liable',
    'responsible', 'obligation', 'binding', 'enforceable', 'jurisdiction',
    'confidential', 'proprietary', 'intellectual property', 'non-compete',
    'non-solicitation', 'assignment', 'subcontract', 'audit', 'inspection'
]

# Protective language that decreases risk
PROTECTIVE_INDICATORS = [
    'capped at', 'limited to', 'maximum of', 'not exceed', 'reasonable', 'mutual',
    'prior written consent', 'good faith', 'commercially reasonable', 'proportionate',
    'best efforts', 'reasonable efforts'
]


def get_ollama_response(prompt: str, temperature: float = 0.2) -> str:
    """
    Call Ollama API for LLM responses.
    """
    ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434/api/generate')
    model = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:0.5b')

    try:
        response = requests.post(
            ollama_url,
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': 1024
                }
            },
            timeout=60
        )

        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            print(f"[REDLINE_ENGINE] Ollama error: {response.status_code}")
            return ''
    except Exception as e:
        print(f"[REDLINE_ENGINE] Ollama connection error: {e}")
        return ''


def classify_risk_type(clause_text: str) -> str:
    """
    Classify the risk type of a clause based on keywords.
    Returns the most relevant risk category.
    """
    clause_lower = clause_text.lower()
    scores = {}

    for risk_type, config in RISK_CATEGORIES.items():
        score = 0
        for keyword in config['keywords']:
            if keyword in clause_lower:
                score += 1
        scores[risk_type] = score * config['weight']

    if max(scores.values()) == 0:
        return 'OTHER'

    return max(scores, key=scores.get)


def calculate_risk_score(clause_text: str) -> int:
    """
    Calculate risk score (0-100) for a clause.
    Higher score = higher risk.

    Score ranges:
    - 0-29: Low risk (green)
    - 30-59: Medium risk (yellow)
    - 60-100: High risk (red)
    """
    clause_lower = clause_text.lower()
    base_score = 25  # Start with baseline that can go either way

    high_risk_count = 0
    medium_risk_count = 0
    protective_count = 0

    # Add points for HIGH-risk indicators (+15 each, significant impact)
    for indicator in HIGH_RISK_INDICATORS:
        if indicator in clause_lower:
            high_risk_count += 1
            base_score += 15

    # Add points for MEDIUM-risk indicators (+5 each)
    for indicator in MEDIUM_RISK_INDICATORS:
        if indicator in clause_lower:
            medium_risk_count += 1
            base_score += 5

    # Cap medium risk contribution to avoid over-counting common terms
    if medium_risk_count > 4:
        base_score -= (medium_risk_count - 4) * 3  # Reduce excess

    # Subtract points for protective language (-8 each)
    for indicator in PROTECTIVE_INDICATORS:
        if indicator in clause_lower:
            protective_count += 1
            base_score -= 8

    # Adjust for clause length
    word_count = len(clause_text.split())
    if word_count < 15:
        base_score -= 5  # Short clauses are usually simpler
    elif word_count > 200:
        base_score += 10  # Long clauses may hide unfavorable terms

    # Boost risk based on category weights
    risk_type = classify_risk_type(clause_text)
    if risk_type in RISK_CATEGORIES:
        weight = RISK_CATEGORIES[risk_type]['weight']
        if weight > 1.2:
            base_score = int(base_score * 1.1)  # Boost high-weight categories slightly

    # Ensure minimum score based on risk indicators found
    if high_risk_count >= 2:
        base_score = max(base_score, 60)  # At least high risk
    elif high_risk_count == 1:
        base_score = max(base_score, 45)  # At least medium risk
    elif medium_risk_count >= 3:
        base_score = max(base_score, 35)  # At least medium risk

    # Cap score between 0-100
    return max(0, min(100, base_score))


def generate_redline_diff(original: str, revised: str) -> str:
    """
    Generate unified diff format redline.
    """
    diff = unified_diff(
        original.splitlines(),
        revised.splitlines(),
        lineterm='',
        fromfile='Original',
        tofile='Suggested'
    )
    return '\n'.join(diff)


def generate_risk_explanation(clause_text: str, risk_type: str, risk_score: int) -> str:
    """Generate a rule-based risk explanation (fast, no LLM)."""
    clause_lower = clause_text.lower()
    explanations = []

    if 'unlimited liability' in clause_lower or 'any and all damages' in clause_lower:
        explanations.append("Contains unlimited liability exposure.")
    if 'sole discretion' in clause_lower or 'unilateral' in clause_lower:
        explanations.append("One-sided terms giving excessive control to one party.")
    if 'waive' in clause_lower or 'forfeit' in clause_lower:
        explanations.append("Contains waiver provisions limiting legal recourse.")
    if 'automatically renew' in clause_lower:
        explanations.append("Auto-renewal may lock into extended commitments.")
    if 'without notice' in clause_lower or 'immediate termination' in clause_lower:
        explanations.append("Allows termination without adequate notice.")
    if 'indemnify' in clause_lower or 'hold harmless' in clause_lower:
        explanations.append("Indemnification creates liability exposure.")

    if not explanations:
        risk_name = risk_type.lower().replace('_', ' ')
        if risk_score >= 60:
            return f"This {risk_name} clause contains elevated risk terms requiring review."
        elif risk_score >= 30:
            return f"This {risk_name} clause has moderate risk factors."
        else:
            return f"Standard {risk_name} clause with minimal risk."

    return " ".join(explanations)


def generate_suggested_clause(clause_text: str, risk_score: int, risk_type: str = "OTHER", jurisdiction: str = "Common Law") -> str:
    """
    Generate improved clause using LLM with rule-based fallback.
    According to ContractAI spec: Use GPT-4/Ollama to generate intelligent suggestions for ALL clauses.
    """
    print(f"[REDLINE_ENGINE] Analyzing clause (risk_score={risk_score}, risk_type={risk_type})")
    print(f"[REDLINE_ENGINE] Clause text (first 100 chars): {clause_text[:100]}...")

    # For low-risk clauses, try LLM first, then return original if LLM unavailable
    if risk_score < 30:
        # Low risk - try gentle improvements via LLM
        llm_suggestion = _llm_suggest_clause(clause_text, risk_type, jurisdiction, "balanced", risk_score)
        if llm_suggestion and llm_suggestion != clause_text:
            print(f"[REDLINE_ENGINE] LLM suggestion differs from original (low risk)")
            return llm_suggestion
        print(f"[REDLINE_ENGINE] Returning original for low-risk clause (llm_suggestion empty or same)")
        return clause_text  # No changes needed

    # For medium/high risk clauses, always try LLM first
    llm_suggestion = _llm_suggest_clause(clause_text, risk_type, jurisdiction, "balanced", risk_score)
    if llm_suggestion and llm_suggestion != clause_text:
        print(f"[REDLINE_ENGINE] LLM suggestion differs from original (medium/high risk)")
        return llm_suggestion

    # Fallback to rule-based replacements if LLM fails
    print(f"[REDLINE_ENGINE] LLM unavailable or returned same text, using rule-based fallback for risk_score={risk_score}")
    print(f"[REDLINE_ENGINE] Applying {jurisdiction}-specific rules")

    suggested = clause_text

    # Base replacements (Common Law default)
    replacements = [
        ('unlimited liability', 'liability limited to direct damages not exceeding the contract value'),
        ('any and all damages', 'direct damages'),
        ('sole discretion', 'reasonable discretion'),
        ('without limitation', 'subject to reasonable limitations'),
        ('irrevocable', 'revocable with 30 days written notice'),
        ('perpetual', 'for the term of this agreement'),
        ('at will', 'with 30 days prior written notice'),
        ('immediate termination', 'termination with 14 days notice'),
        ('without cause', 'for material breach'),
        ('without notice', 'with reasonable notice'),
        ('automatically renew', 'renew upon mutual written agreement'),
    ]

    # Jurisdiction-specific overrides and additions
    if jurisdiction == "UAE":
        # UAE requires longer notice periods and Sharia compliance
        replacements.extend([
            ('30 days prior written notice', '60 days prior written notice in accordance with UAE Labour Law'),
            ('14 days notice', '30 days notice per UAE Commercial Transactions Law'),
            ('payment due immediately', 'payment due within 30 days per UAE Federal Law No. 18 of 1993'),
            ('interest', 'late payment fees (interest not applicable under UAE law)'),
        ])

    elif jurisdiction == "EU":
        # EU requires GDPR considerations and employee protections
        replacements.extend([
            ('damages', 'damages (excluding GDPR violations, personal injury, or gross negligence)'),
            ('termination', 'termination (subject to EU employment protection directives where applicable)'),
            ('payment due immediately', 'payment due within 60 days per EU Late Payment Directive'),
            ('data', 'data (subject to GDPR compliance requirements)'),
        ])

    elif jurisdiction == "US":
        # US-specific terms
        replacements.extend([
            ('governing law', 'governed by the laws of [State], excluding conflicts of law principles'),
            ('arbitration', 'binding arbitration in accordance with AAA Commercial Arbitration Rules'),
        ])

    elif jurisdiction == "UK":
        # UK-specific terms
        replacements.extend([
            ('governing law', 'governed by English law'),
            ('courts', 'courts of England and Wales'),
            ('payment due immediately', 'payment due within 30 days per Late Payment of Commercial Debts Act'),
        ])

    # Apply all replacements
    for old, new in replacements:
        pattern = re.compile(re.escape(old), re.IGNORECASE)
        suggested = pattern.sub(new, suggested)

    return suggested


def _llm_suggest_clause(clause_text: str, risk_type: str, jurisdiction: str, perspective: str = "balanced", risk_score: int = 50) -> str:
    """
    Use LLM (Ollama) to generate improved clause suggestion.
    Follows the ContractAI spec prompt design from the PDF.
    """
    perspective_instructions = {
        'balanced': 'Create a balanced clause that protects both parties fairly.',
        'buyer_favorable': 'Rewrite to favor the buyer/customer with stronger protections.',
        'seller_favorable': 'Rewrite to favor the seller/provider while remaining reasonable.'
    }

    instruction = perspective_instructions.get(perspective, perspective_instructions['balanced'])

    # Jurisdiction-specific context for LLM
    jurisdiction_context = {
        'UAE': 'Consider UAE Labour Law, UAE Commercial Transactions Law (Federal Law No. 18 of 1993), and Sharia principles. Use 60-day notice periods, avoid interest terms (use late fees instead), reference UAE-specific statutes.',
        'EU': 'Consider GDPR compliance, EU Late Payment Directive (60-day payment terms), EU employment protection directives, and consumer protection laws. Always exclude GDPR violations from liability caps.',
        'US': 'Consider state law variations, AAA arbitration rules, UCC for commercial transactions, and specify jurisdiction excluding conflicts of law. Use 30-day notice periods as standard.',
        'UK': 'Consider English law, Late Payment of Commercial Debts Act, UK employment law, and specify courts of England and Wales. Use reasonable notice periods.',
        'Common Law': 'Consider common law principles applicable in UK, US, Australia, Canada, and India. Use balanced terms with 30-day notice periods.'
    }

    context = jurisdiction_context.get(jurisdiction, jurisdiction_context['Common Law'])

    prompt = f"""You are a contract risk analyst and expert legal drafter specializing in {jurisdiction} law.

Analyze this contract clause and rewrite it to reduce legal risk:

Original Clause:
"{clause_text}"

Risk Type: {risk_type}
Risk Score: {risk_score}/100
Jurisdiction: {jurisdiction}
Jurisdiction Context: {context}
Instruction: {instruction}

IMPORTANT: You MUST rewrite the clause to make it safer, clearer, and more balanced. Do NOT return the original text unchanged.

Your tasks:
1. Identify specific risks in the clause under {jurisdiction} law (unlimited liability, one-sided terms, vague language, non-compliance, etc.)
2. Rewrite the clause with safer alternative wording that:
   - Complies with {jurisdiction} legal requirements and regulations
   - Adds reasonable limitations to liability (consider jurisdiction-specific caps)
   - Includes appropriate notice periods for {jurisdiction}
   - Balances rights between parties
   - Makes terms more specific and clear
   - Reduces litigation risk under {jurisdiction} courts
3. Reference specific laws or standards from {jurisdiction} where applicable
4. Explain what you changed and why it's safer under {jurisdiction} law

Respond in JSON format:
{{
    "suggested_clause": "<your rewritten clause compliant with {jurisdiction} law - MUST be different from original>",
    "explanation": "<what you changed and why it's safer under {jurisdiction} law>"
}}

Respond ONLY with valid JSON. The suggested_clause MUST be a rewritten version, not the original."""

    response = get_ollama_response(prompt, temperature=0.2)

    if not response:
        return ""

    # Log the raw response for debugging
    print(f"[REDLINE_ENGINE] LLM Response (first 200 chars): {response[:200]}")

    # Try to extract JSON from response - use multiple strategies
    try:
        # Strategy 1: Try direct JSON parsing first (fastest)
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                result = json.loads(json_match.group())
                suggested = result.get('suggested_clause', '').strip()
                if suggested and len(suggested) > 10:
                    if suggested == clause_text:
                        print(f"[REDLINE_ENGINE] Strategy 1 - LLM returned original unchanged (clause is already well-written)")
                    else:
                        print(f"[REDLINE_ENGINE] Strategy 1 success - extracted {len(suggested)} chars, differs from original")
                    return suggested
            except json.JSONDecodeError as e:
                print(f"[REDLINE_ENGINE] Strategy 1 JSON parse error: {e}")
                pass  # Try next strategy

        # Strategy 2: Clean up the JSON string and try again
        if json_match:
            json_str = json_match.group()

            # More aggressive cleaning for multiline strings
            # First, extract the suggested_clause value manually
            clause_pattern = r'"suggested_clause"\s*:\s*"((?:[^"\\]|\\.)*)"\s*[,}]'
            clause_match = re.search(clause_pattern, json_str, re.DOTALL)

            if clause_match:
                suggested = clause_match.group(1)
                # Unescape common escape sequences
                suggested = suggested.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                suggested = suggested.strip()

                if suggested and len(suggested) > 10:
                    if suggested == clause_text:
                        print(f"[REDLINE_ENGINE] Strategy 2 - LLM returned original unchanged (clause is already well-written)")
                    else:
                        print(f"[REDLINE_ENGINE] Strategy 2 success - extracted {len(suggested)} chars, differs from original")
                    return suggested

        # Strategy 3: Try to find any substantial text that looks like a clause
        # Look for sentences that are different from the original
        sentences = re.findall(r'[A-Z][^.!?]*[.!?]', response)
        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence) > 50 and
                sentence != clause_text and
                not sentence.startswith('You are') and
                not sentence.startswith('Tasks') and
                'JSON' not in sentence):
                print(f"[REDLINE_ENGINE] Strategy 3 success - found alternative sentence")
                return sentence

    except Exception as e:
        print(f"[REDLINE_ENGINE] LLM extraction error: {e}")

    print(f"[REDLINE_ENGINE] All strategies failed, returning empty")
    return ""


def analyze_clause(clause_text: str, jurisdiction: str = "Common Law") -> Dict[str, Any]:
    """
    Clause analysis using LLM-powered suggestions with rule-based scoring.
    According to ContractAI spec: combines risk scoring + LLM suggestions.
    Returns risk classification, score, explanation, and suggested revision.
    """
    risk_type = classify_risk_type(clause_text)
    risk_score = calculate_risk_score(clause_text)
    risk_explanation = generate_risk_explanation(clause_text, risk_type, risk_score)

    # Pass risk_type and jurisdiction to LLM for better suggestions
    suggested_clause = generate_suggested_clause(clause_text, risk_score, risk_type, jurisdiction)

    if suggested_clause != clause_text:
        improvement_summary = "Replaced high-risk terms with balanced alternatives."
    else:
        improvement_summary = "No changes needed - clause appears balanced."

    return {
        'risk_type': risk_type,
        'risk_score': risk_score,
        'risk_explanation': risk_explanation,
        'suggested_clause': suggested_clause,
        'improvement_summary': improvement_summary
    }


def split_contract_into_clauses(contract_text: str) -> List[Dict[str, Any]]:
    """
    Split contract text into individual clauses.
    Improved version that handles various contract formats better.
    """
    clauses = []

    # Remove page markers and excessive whitespace
    text = re.sub(r'---\s*Page\s+\d+\s*---', '', contract_text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Try multiple splitting strategies in order of specificity

    # Strategy 1: Split by numbered sections with all-caps headers
    # Pattern: "4\nLETTER OF INTENT" or "1.\nDEFINITIONS"
    numbered_sections = re.split(r'\n(\d+\.?\s*\n[A-Z][A-Z\s]{2,})', text)

    if len(numbered_sections) > 3:  # Found structured sections
        current_section = ""
        section_number = 0
        section_title = "Introduction"  # Initialize with default

        for part in numbered_sections:
            part = part.strip()
            if not part:
                continue

            # Check if this is a section header (number + title)
            header_match = re.match(r'^(\d+)\.?\s*\n?([A-Z][A-Z\s]{2,})', part)

            if header_match:
                # Save previous section if exists
                if current_section and len(current_section) > 30:
                    clauses.append({
                        'index': section_number,
                        'name': section_title,
                        'text': current_section.strip()
                    })

                # Start new section
                section_number = int(header_match.group(1))
                section_title = header_match.group(2).strip().title()
                current_section = part
            else:
                # Continue current section
                current_section += "\n" + part

        # Add last section
        if current_section and len(current_section) > 30:
            clauses.append({
                'index': section_number,
                'name': section_title,
                'text': current_section.strip()
            })

    # Strategy 2: If Strategy 1 didn't work, try sentence-based splitting
    if len(clauses) == 0:
        # Split by periods followed by newline and capital letter
        sentences = re.split(r'\.\s*\n+(?=[A-Z])', text)

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 30:  # Skip very short fragments
                continue

            # Try to identify clause type from content
            clause_name = _identify_clause_type(sentence)

            clauses.append({
                'index': i,
                'name': clause_name,
                'text': sentence if not sentence.endswith('.') else sentence + '.'
            })

    # Strategy 3: If still no clauses, split by double newlines (fallback)
    if len(clauses) == 0:
        sections = re.split(r'\n\n+', text)

        for i, section in enumerate(sections):
            section = section.strip()
            if len(section) < 30:
                continue

            clause_name = _identify_clause_type(section)

            clauses.append({
                'index': i,
                'name': clause_name,
                'text': section
            })

    # Limit clause length to avoid huge sections
    final_clauses = []
    for clause in clauses:
        # If a clause is too long (> 1500 chars), try to split it further
        if len(clause['text']) > 1500:
            # Split long clauses into sub-clauses by sentences
            sub_clauses = _split_long_clause(clause)
            final_clauses.extend(sub_clauses)
        else:
            final_clauses.append(clause)

    return final_clauses if final_clauses else clauses


def _identify_clause_type(text: str) -> str:
    """Identify clause type from content."""
    text_lower = text.lower()[:200]  # Check first 200 chars

    # Check for common clause indicators
    clause_types = {
        'payment': ['payment', 'fee', 'price', 'invoice', 'cost'],
        'delivery': ['delivery', 'deliver', 'shipment', 'transport'],
        'liability': ['liable', 'liability', 'responsible', 'damages'],
        'termination': ['terminate', 'termination', 'cancel', 'end'],
        'warranty': ['warrant', 'guarantee', 'represent'],
        'confidentiality': ['confidential', 'non-disclosure', 'nda'],
        'indemnification': ['indemnify', 'hold harmless'],
        'governing law': ['governing law', 'jurisdiction', 'applicable law'],
        'definitions': ['definition', 'means', 'shall mean'],
        'scope': ['scope', 'services', 'work'],
        'term': ['term', 'duration', 'period'],
    }

    for clause_type, keywords in clause_types.items():
        for keyword in keywords:
            if keyword in text_lower:
                return clause_type.title()

    # Default based on content length
    if len(text) < 100:
        return "Short Clause"
    elif len(text) < 300:
        return "Standard Clause"
    else:
        return "Detailed Clause"


def _split_long_clause(clause: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Split a long clause into smaller sub-clauses."""
    text = clause['text']
    base_name = clause['name']
    base_index = clause['index']

    # Split by sentences (periods followed by space/newline)
    sentences = re.split(r'\.\s+', text)

    sub_clauses = []
    current_text = ""
    sub_index = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Add sentence to current chunk
        current_text += sentence + ". "

        # If chunk is big enough, create a sub-clause
        if len(current_text) > 500:
            sub_clauses.append({
                'index': base_index + sub_index,
                'name': f"{base_name} (Part {sub_index + 1})",
                'text': current_text.strip()
            })
            current_text = ""
            sub_index += 1

    # Add remaining text
    if current_text.strip():
        sub_clauses.append({
            'index': base_index + sub_index,
            'name': f"{base_name} (Part {sub_index + 1})" if sub_index > 0 else base_name,
            'text': current_text.strip()
        })

    return sub_clauses if sub_clauses else [clause]


def process_contract_for_redlining(contract_text: str, jurisdiction: str = "Common Law") -> Dict[str, Any]:
    """
    Main entry point: Process entire contract for redlining.
    Returns analyzed clauses with risk scores and suggestions.
    """
    # Split into clauses
    clauses = split_contract_into_clauses(contract_text)

    analyzed_clauses = []
    total_risk_score = 0
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0

    for clause_data in clauses:
        # Analyze each clause
        analysis = analyze_clause(clause_data['text'], jurisdiction)

        # Generate redline diff
        redline_diff = generate_redline_diff(
            clause_data['text'],
            analysis['suggested_clause']
        )

        # Categorize by risk level
        risk_score = analysis['risk_score']
        if risk_score >= 60:
            risk_level = 'HIGH'
            high_risk_count += 1
        elif risk_score >= 30:
            risk_level = 'MEDIUM'
            medium_risk_count += 1
        else:
            risk_level = 'LOW'
            low_risk_count += 1

        total_risk_score += risk_score

        analyzed_clauses.append({
            'index': clause_data['index'],
            'clause_name': clause_data['name'],
            'original_text': clause_data['text'],
            'suggested_text': analysis['suggested_clause'],
            'redline_diff': redline_diff,
            'risk_type': analysis['risk_type'],
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_explanation': analysis['risk_explanation'],
            'improvement_summary': analysis.get('improvement_summary', '')
        })

    # Calculate overall risk
    avg_risk = total_risk_score / len(clauses) if clauses else 0

    if avg_risk >= 60 or high_risk_count >= 3:
        overall_risk_level = 'HIGH'
    elif avg_risk >= 40 or high_risk_count >= 1:
        overall_risk_level = 'MEDIUM'
    else:
        overall_risk_level = 'LOW'

    return {
        'total_clauses': len(clauses),
        'high_risk_count': high_risk_count,
        'medium_risk_count': medium_risk_count,
        'low_risk_count': low_risk_count,
        'overall_risk_level': overall_risk_level,
        'average_risk_score': round(avg_risk, 1),
        'clauses': analyzed_clauses
    }


def regenerate_clause_suggestion(
    clause_text: str,
    perspective: str = "balanced",
    jurisdiction: str = "Common Law"
) -> Dict[str, Any]:
    """
    Regenerate a suggestion for a specific clause with different perspectives.
    perspective: 'balanced', 'buyer_favorable', 'seller_favorable'
    Uses the ContractAI spec LLM approach.
    """
    # Get risk analysis first
    risk_type = classify_risk_type(clause_text)
    risk_score = calculate_risk_score(clause_text)

    # Use the LLM suggestion helper
    suggested_clause = _llm_suggest_clause(clause_text, risk_type, jurisdiction, perspective, risk_score)

    if suggested_clause and suggested_clause != clause_text:
        # Generate additional metadata about the changes
        changes_made = _describe_changes(clause_text, suggested_clause)
        risk_reduction = f"Reduces {risk_type.lower()} risk by addressing problematic terms."

        return {
            'suggested_clause': suggested_clause,
            'changes_made': changes_made,
            'risk_reduction': risk_reduction
        }

    # Fallback if LLM unavailable
    return {
        'suggested_clause': clause_text,
        'changes_made': 'LLM service unavailable. Unable to generate perspective-specific suggestion.',
        'risk_reduction': 'Manual review recommended.'
    }


def _describe_changes(original: str, revised: str) -> str:
    """Generate a brief description of changes between original and revised clauses."""
    if original == revised:
        return "No changes made."

    # Simple heuristic to describe changes
    orig_words = set(original.lower().split())
    rev_words = set(revised.lower().split())

    removed = orig_words - rev_words
    added = rev_words - orig_words

    changes = []
    if removed:
        changes.append(f"Removed risky terms: {', '.join(list(removed)[:5])}")
    if added:
        changes.append(f"Added protective language: {', '.join(list(added)[:5])}")

    return "; ".join(changes) if changes else "Clause reworded for clarity and risk reduction."
