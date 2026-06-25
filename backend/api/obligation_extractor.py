"""
Obligation Extractor - Extract contractual obligations using LLM
"""

import json
from rag import call_llm


def generate_obligations(contract):
    """
    Extract contractual obligations from contract text using LLM

    Args:
        contract: Contract model instance

    Returns:
        list: Array of obligation dictionaries with structured metadata
    """
    try:
        # Check if contract has text
        if not contract.full_text or contract.full_text.strip() == '':
            raise Exception('Contract text is empty. Please ensure the contract has been processed.')

        # Build prompt for LLM
        prompt = f"""
You are a Contract Obligation Extraction AI Assistant.

TASK: Analyze the following contract and extract ALL contractual obligations for BOTH parties.
Look for DIVERSE obligation types - not just payments!

For each obligation, provide:
1. title: Brief obligation title (max 100 characters)
2. description: Detailed description of the obligation
3. category: One of [PAYMENT, DELIVERY, COMPLIANCE, REPORTING, NOTICE, TERMINATION, OTHER]
4. responsible_party: One of [YOUR_COMPANY, COUNTERPARTY, BOTH]
5. priority: One of [HIGH, MEDIUM, LOW] based on importance
6. due_date_text: Timeline/deadline if mentioned (e.g., "Within 30 days", "Quarterly", "Upon termination")
7. clause_reference: Clause name if identifiable

CATEGORY DEFINITIONS (USE VARIETY - NOT JUST PAYMENT!):
- PAYMENT: Money transfers, fees, invoices, charges
- DELIVERY: Goods delivery, service provision, shipment
- COMPLIANCE: Legal/regulatory requirements, standards, certifications
- REPORTING: Status reports, documentation, record-keeping
- NOTICE: Notifications, communications, information sharing
- TERMINATION: Contract ending, cancellation procedures
- OTHER: Insurance, warranties, indemnification, confidentiality

IMPORTANT GUIDELINES:
- Extract DIVERSE obligation types - look for delivery, compliance, reporting, notices, termination, not just payments!
- Extract obligations for BOTH parties (your company and counterparty)
- If obligation mentions "Buyer" or "Purchaser" -> responsible_party: YOUR_COMPANY
- If obligation mentions "Seller" or "Vendor" -> responsible_party: COUNTERPARTY
- If obligation applies to both -> responsible_party: BOTH
- Be specific and actionable

CONTRACT TEXT:
{contract.full_text[:3000]}

OUTPUT FORMAT (JSON array with DIVERSE categories):
[
  {{
    "title": "Pay invoice within 30 days",
    "description": "Buyer must pay all invoices within 30 days of receipt",
    "category": "PAYMENT",
    "responsible_party": "YOUR_COMPANY",
    "priority": "HIGH",
    "due_date_text": "Within 30 days of invoice",
    "clause_reference": "Payment Terms"
  }},
  {{
    "title": "Deliver goods to warehouse",
    "description": "Seller must deliver all goods to buyer's warehouse location",
    "category": "DELIVERY",
    "responsible_party": "COUNTERPARTY",
    "priority": "HIGH",
    "due_date_text": "As per delivery schedule",
    "clause_reference": "Delivery Terms"
  }},
  {{
    "title": "Submit monthly status reports",
    "description": "Contractor must provide monthly progress reports",
    "category": "REPORTING",
    "responsible_party": "COUNTERPARTY",
    "priority": "MEDIUM",
    "due_date_text": "Monthly by 5th",
    "clause_reference": "Reporting Requirements"
  }},
  {{
    "title": "Maintain ISO certification",
    "description": "Supplier must maintain valid ISO 9001 certification",
    "category": "COMPLIANCE",
    "responsible_party": "COUNTERPARTY",
    "priority": "HIGH",
    "due_date_text": "Throughout contract term",
    "clause_reference": "Quality Standards"
  }}
]

Extract all obligations with DIVERSE categories and return ONLY the JSON array, no additional text.
"""

        llm_response = call_llm(prompt, max_tokens=800, temperature=0.0, stream=False)
        response_text = llm_response.get('response', '[]')

        # Debug: Print raw LLM response
        print('[DEBUG] ===== RAW LLM RESPONSE =====')
        print(response_text[:1000])  # Print first 1000 chars
        print('[DEBUG] ===========================')

        # Parse JSON response
        # Try to extract JSON from response (in case LLM adds extra text or markdown)
        response_text = response_text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            # Find the first newline after opening ```
            first_newline = response_text.find('\n')
            if first_newline != -1:
                response_text = response_text[first_newline + 1:]
            # Remove closing ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

        # Find JSON array in response
        start_idx = response_text.find('[')

        if start_idx == -1:
            print('[ERROR] No JSON array found in response')
            raise Exception('No JSON array found in LLM response')

        # Try to parse the JSON, handling truncation
        json_str = response_text[start_idx:]

        try:
            # First, try to find and use the closing bracket if it exists
            end_idx = json_str.rfind(']')
            if end_idx > 0:
                json_str = json_str[:end_idx+1]
            obligations = json.loads(json_str)
            print(f'[SUCCESS] Parsed {len(obligations)} obligations from complete JSON')
        except json.JSONDecodeError as e:
            # JSON is truncated or malformed, try to repair it
            print(f'[WARNING] JSON parsing failed: {str(e)}')
            print(f'[WARNING] Attempting to repair truncated JSON...')

            # Find the last complete object by looking for },
            last_complete_obj = json_str.rfind('},')

            if last_complete_obj != -1:
                # Extract everything up to the last complete object and close the array
                repaired_json = json_str[:last_complete_obj+1] + '\n]'
                print(f'[INFO] Repaired JSON - truncated at position {last_complete_obj}')

                try:
                    obligations = json.loads(repaired_json)
                    print(f'[SUCCESS] Repaired JSON parsed! Recovered {len(obligations)} obligations')
                except json.JSONDecodeError as e2:
                    print(f'[ERROR] Repair attempt failed: {str(e2)}')
                    print(f'[DEBUG] Repaired JSON tail: ...{repaired_json[-300:]}')
                    raise Exception(f'Failed to parse even after repair: {str(e2)}')
            else:
                print('[ERROR] Could not find any complete obligation objects')
                raise Exception('JSON is too malformed to repair')

        # Validate and clean obligations
        cleaned_obligations = []
        seen_titles = set()  # Track seen titles for deduplication
        valid_categories = ['PAYMENT', 'DELIVERY', 'COMPLIANCE', 'REPORTING', 'NOTICE', 'TERMINATION', 'OTHER']
        valid_parties = ['YOUR_COMPANY', 'COUNTERPARTY', 'BOTH']
        valid_priorities = ['HIGH', 'MEDIUM', 'LOW']

        for obl in obligations:
            # Validate required fields
            if not obl.get('title') or not obl.get('description'):
                continue

            # Deduplicate by title (case-insensitive)
            title_lower = obl.get('title', '').lower().strip()
            if title_lower in seen_titles:
                print(f'[DEDUP] Skipping duplicate obligation: {obl.get("title")[:50]}...')
                continue
            seen_titles.add(title_lower)

            # Debug: Show what LLM returned
            raw_category = obl.get('category', 'OTHER')
            print(f'[DEBUG] Title: {obl.get("title")[:60]} | Raw Category: {raw_category}')

            # Validate and normalize category
            category = obl.get('category', 'OTHER').upper()
            if category not in valid_categories:
                print(f'[WARNING] Invalid category "{category}" - defaulting to OTHER')
                category = 'OTHER'

            # Validate and normalize party
            party = obl.get('responsible_party', 'BOTH').upper()
            if party not in valid_parties:
                party = 'BOTH'

            # Validate and normalize priority
            priority = obl.get('priority', 'MEDIUM').upper()
            if priority not in valid_priorities:
                priority = 'MEDIUM'

            cleaned_obligations.append({
                'title': obl.get('title', '')[:500],  # Limit title length
                'description': obl.get('description', ''),
                'full_text': obl.get('description', ''),  # Store full text for reference
                'category': category,
                'responsible_party': party,
                'priority': priority,
                'due_date_text': obl.get('due_date_text', '')[:200] if obl.get('due_date_text') else None,
                'clause_reference': obl.get('clause_reference', '')[:200] if obl.get('clause_reference') else None,
            })

        return cleaned_obligations

    except json.JSONDecodeError as e:
        print(f'JSON parsing error: {str(e)}')
        if 'response_text' in locals():
            print(f'Response text: {response_text[:500]}')
        raise Exception('Failed to parse LLM response as JSON')
    except Exception as e:
        print(f'Obligation extraction error: {str(e)}')
        import traceback
        traceback.print_exc()
        raise Exception(f'Obligation extraction failed: {str(e)}')
