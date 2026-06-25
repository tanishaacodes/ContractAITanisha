"""
Tender Intelligence Engines
- Metadata Extraction (broad real-world patterns)
- Risk Detection
- Conflict Detection
- Eligibility Validation
- Proposal Generation
- Win Simulation
- Pre-bid Questions
"""
import re
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _parse_indian_amount(value_str: str, unit_str: str = '') -> Optional[float]:
    """
    Parse Indian currency amounts.
    Handles: Rs. 3.00 Crore / Rs 50 Lakh / ₹ 5,00,000 / INR 10 Million
    """
    try:
        value = float(value_str.replace(',', ''))
        unit = (unit_str or '').lower().strip()
        if 'crore' in unit or 'cr' == unit:
            value *= 10_000_000
        elif 'lakh' in unit or 'lac' in unit:
            value *= 100_000
        elif 'million' in unit:
            value *= 1_000_000
        elif 'thousand' in unit:
            value *= 1_000
        return value
    except (ValueError, TypeError):
        return None


def _extract_amount_from_text(text: str, keywords: List[str]) -> Optional[float]:
    """
    Generic amount extractor: searches for any keyword then grabs the nearest
    Indian-format amount (with optional unit: Crore/Lakh/Million/K).
    Returns the largest amount found to prioritize actual values over placeholders.
    """
    text_lower = text.lower()

    # Build a combined pattern that looks for keyword → optional garbage → amount
    amount_pat = (
        r'(?:Rs\.?|INR|₹|rupees?)?\s*'
        r'([\d,]+(?:\.\d+)?)'
        r'\s*(?:/-|/--)?\s*'  # Handle both /- and /-- patterns
        r'(crore|cr\b|lakh|lac\b|million|thousand|k\b)?'
    )

    found_amounts = []
    for kw in keywords:
        # Find all occurrences of the keyword
        for m in re.finditer(re.escape(kw.lower()), text_lower):
            window = text[m.start(): min(len(text), m.start() + 400)]  # Extended window
            # Find ALL amounts near this keyword, not just the first
            for am in re.finditer(amount_pat, window, re.IGNORECASE):
                v = _parse_indian_amount(am.group(1), am.group(2) or '')
                if v and v >= 100:          # ignore noise < ₹100
                    found_amounts.append(v)

    # Return the largest amount found (prioritize actual values over placeholders)
    if found_amounts:
        return max(found_amounts)
    return None


def _extract_date(text: str, keywords: List[str]) -> Optional[str]:
    """
    Find first valid date near any keyword. Prioritizes proper date formats (DD.MM.YYYY)
    over potentially ambiguous formats (DD/MM/YY that might be reference numbers).
    """
    # Prefer 4-digit year dates (more specific)
    date_pat_full = r'(\d{1,2}[./-]\d{1,2}[./-]\d{4})'
    # Fallback to 2-digit year
    date_pat_short = r'(\d{1,2}[./-]\d{1,2}[./-]\d{2})'

    text_lower = text.lower()

    def _is_valid_date(date_str: str) -> bool:
        """Filter out dates that are likely reference numbers"""
        # Skip dates that look like fiscal year codes (e.g., "03/21-22")
        if '/21-22' in date_str or '/22-23' in date_str or '/20-21' in date_str:
            return False
        # Skip dates with month > 12 or day > 31
        parts = re.split(r'[./-]', date_str)
        if len(parts) >= 2:
            try:
                day, month = int(parts[0]), int(parts[1])
                if day > 31 or month > 12 or day == 0 or month == 0:
                    return False
            except:
                pass
        return True

    # First try: look for 4-digit year dates near keywords (both before and after)
    for kw in keywords:
        for m in re.finditer(re.escape(kw.lower()), text_lower):
            # Look both before and after the keyword (dates often appear before opening time)
            window_start = max(0, m.start() - 300)
            window_end = min(len(text), m.start() + 600)
            window = text[window_start:window_end]
            dates = re.findall(date_pat_full, window)
            for date in dates:
                if _is_valid_date(date):
                    return date

    # Second try: check for "same day" references near keyword
    for kw in keywords:
        idx = text_lower.find(kw.lower())
        if idx != -1:
            window = text[max(0, idx - 50): min(len(text), idx + 600)]
            if 'same day' in window.lower() or 'on that day' in window.lower():
                # Look for the most recent 4-digit year date before "same day"
                preceding_text = text[max(0, idx - 1000): idx + 600]
                dates = re.findall(date_pat_full, preceding_text)
                valid_dates = [d for d in dates if _is_valid_date(d)]
                if valid_dates:
                    return valid_dates[-1]

    # Third try: look for any 2-digit year dates near keywords (fallback)
    for kw in keywords:
        for m in re.finditer(re.escape(kw.lower()), text_lower):
            window = text[m.start(): min(len(text), m.start() + 400)]
            dates = re.findall(date_pat_short, window)
            for date in dates:
                if _is_valid_date(date):
                    return date

    return None


def _extract_period_days(text: str, keywords: List[str]) -> Optional[int]:
    """Extract completion period in days near any keyword."""
    # Pattern for numeric periods: "180 days", "6 months", "2 years"
    period_pat = r'(\d+)\s*(days?|months?|weeks?|years?)'
    # Pattern for text numbers: "one year", "two years", "six months"
    text_period_pat = r'(one|two|three|four|five|six|seven|eight|nine|ten|twelve)\s*(year|years|month|months)'

    text_to_num = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'twelve': 12
    }

    text_lower = text.lower()
    for kw in keywords:
        for m in re.finditer(re.escape(kw.lower()), text_lower):
            window = text[m.start(): min(len(text), m.start() + 300)]
            window_lower = window.lower()

            # Try text number pattern first (more specific for common phrasings)
            tm = re.search(text_period_pat, window_lower, re.IGNORECASE)
            if tm:
                text_num = tm.group(1).lower()
                unit = tm.group(2).lower()
                val = text_to_num.get(text_num, 0)
                if val > 0:
                    if 'month' in unit:
                        val *= 30
                    elif 'year' in unit:
                        val *= 365
                    if val >= 7:
                        return val

            # Fall back to numeric pattern
            pm = re.search(period_pat, window, re.IGNORECASE)
            if pm:
                val = int(pm.group(1))
                unit = pm.group(2).lower()
                if 'month' in unit:
                    val *= 30
                elif 'week' in unit:
                    val *= 7
                elif 'year' in unit:
                    val *= 365
                if val >= 7:        # ignore noise
                    return val
    return None


# ─────────────────────────────────────────────────────────────────────────────
# METADATA EXTRACTOR
# ─────────────────────────────────────────────────────────────────────────────

class MetadataExtractor:
    """Extract structured metadata from tender text using LLM + broad rule patterns."""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def extract(self, full_text: str, parsed_metadata: Dict) -> Dict[str, Any]:
        metadata = parsed_metadata.copy()

        # Rule-based first (fast, reliable)
        rule_metadata = self._extract_with_rules(full_text)
        for k, v in rule_metadata.items():
            if v is not None:
                metadata[k] = v

        # LLM fill-in for fields still missing
        if self.llm_client:
            missing_fields = [f for f in [
                'estimated_value', 'emd_amount', 'bid_security',
                'submission_deadline', 'completion_period_days',
                'organization', 'technical_opening', 'financial_opening',
                'min_turnover', 'performance_guarantee_percent',
                'liquidated_damages_percent'
            ] if not metadata.get(f)]
            if missing_fields:
                llm_metadata = self._extract_with_llm(full_text, missing_fields)
                for k, v in llm_metadata.items():
                    if v is not None and not metadata.get(k):
                        metadata[k] = v

        return metadata

    # ── LLM extraction ────────────────────────────────────────────────────────

    def _extract_with_llm(self, text: str, missing_fields: List[str]) -> Dict:
        text_sample = text[:8000]
        fields_desc = ', '.join(missing_fields)
        prompt = f"""You are extracting structured data from an Indian government tender document.

Extract ONLY these fields (skip any not present): {fields_desc}

Rules:
- estimated_value: total contract/project value as a NUMBER (rupees, apply crore/lakh multipliers)
- emd_amount / bid_security: EMD / Earnest Money / Bid Security as NUMBER in rupees
- submission_deadline: last date for bid submission as DD.MM.YYYY
- completion_period_days: project duration in DAYS (convert months×30, years×365)
- organization: name of the issuing authority / department
- technical_opening: technical bid opening date as DD.MM.YYYY
- financial_opening: financial bid opening date as DD.MM.YYYY
- min_turnover: minimum annual turnover required as NUMBER in rupees
- performance_guarantee_percent: performance guarantee % as NUMBER
- liquidated_damages_percent: LD % per week/month as NUMBER

Tender text:
{text_sample}

Return ONLY a JSON object. Use null for fields not found.
Example: {{"estimated_value": 50000000, "submission_deadline": "15.03.2024", "organization": "CPWD"}}

JSON:"""
        try:
            if hasattr(self.llm_client, 'chat'):
                resp = self.llm_client.chat(
                    model="qwen2.5:0.5b",
                    messages=[{"role": "user", "content": prompt}]
                )
                content = resp["message"]["content"]
            else:
                resp = requests.post(
                    f"{self.llm_client}/api/generate",
                    json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False},
                    timeout=45
                )
                content = resp.json().get("response", "{}")

            # Strip markdown fences
            content = re.sub(r'```(?:json)?', '', content).strip().strip('`')
            # Extract first JSON object
            m = re.search(r'\{.*\}', content, re.DOTALL)
            if m:
                return json.loads(m.group(0))
        except Exception as e:
            print(f"LLM extraction error: {e}")
        return {}

    # ── Rule-based extraction ─────────────────────────────────────────────────

    def _extract_with_rules(self, text: str) -> Dict:
        meta: Dict[str, Any] = {}

        # ── Estimated value ───────────────────────────────────────────────────
        ev_keywords = [
            'estimated cost', 'estimated value', 'contract value',
            'tender value', 'project cost', 'approximate value',
            'cost of work', 'total cost', 'value of work',
            'contract amount', 'put to tender', 'approximate cost',
        ]
        ev = _extract_amount_from_text(text, ev_keywords)
        if ev:
            meta['estimated_value'] = ev

        # Additional patterns for "Rs X Crore" anywhere near "estimated"
        if not meta.get('estimated_value'):
            patterns = [
                r'(?:estimated|approximate|total)\s+(?:cost|value|amount)[^\n]{0,80}'
                r'(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh|million)?',
                r'(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh)\s+(?:only|approximately)',
                r'NIT\s+(?:Value|Amount|Cost)\s*[:\-]\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh)?',
            ]
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    v = _parse_indian_amount(m.group(1), m.group(2) or '')
                    if v:
                        meta['estimated_value'] = v
                        break

        # ── EMD / Bid Security ────────────────────────────────────────────────
        emd_keywords = [
            'earnest money deposit', 'earnest money', 'emd', 'bid security',
            'security deposit', 'bid bond', 'tender security', 'tender fee',
        ]
        emd = _extract_amount_from_text(text, emd_keywords)
        if emd:
            meta['emd_amount'] = emd

        # ── Submission deadline ───────────────────────────────────────────────
        dl_keywords = [
            'last date', 'due date', 'closing date', 'submission date',
            'submission deadline', 'bid submission', 'last date of submission',
            'receipt of bids', 'tender closing', 'deadline for submission',
        ]
        dl = _extract_date(text, dl_keywords)
        if dl:
            meta['submission_deadline'] = dl

        # ── Technical opening ─────────────────────────────────────────────────
        to_keywords = [
            'technical bid opening', 'technical opening', 'opening of technical bid',
            'technical envelope opening', 'tender will be opened', 'tenders will be opened',
            'tender opening', 'bid opening', 'opening of tender', 'opening of bid',
            'will be opened', 'shall be opened', 'to be opened',  # More flexible patterns
        ]
        to = _extract_date(text, to_keywords)
        if to:
            meta['technical_opening'] = to

        # ── Financial opening ─────────────────────────────────────────────────
        fo_keywords = [
            'financial bid opening', 'financial opening', 'price bid opening',
            'opening of financial bid', 'commercial bid opening',
        ]
        fo = _extract_date(text, fo_keywords)
        if fo:
            meta['financial_opening'] = fo

        # ── Completion period ─────────────────────────────────────────────────
        cp_keywords = [
            'time for completion', 'completion period', 'contract duration',
            'project duration', 'completion schedule', 'period of completion',
            'work completion', 'contract period', 'construction period',
        ]
        cp = _extract_period_days(text, cp_keywords)
        if cp:
            meta['completion_period_days'] = cp

        # ── Organization ──────────────────────────────────────────────────────
        org_patterns = [
            r'(?:issued?\s+by|inviting\s+authority|department|division|office\s+of)[:\s]+([A-Z][^\n]{5,80})',
            r'(?:name\s+of\s+(?:the\s+)?(?:authority|employer|owner|department|organisation))[:\s]+([A-Z][^\n]{5,80})',
            r'^([A-Z][A-Z\s&,\(\)]{10,80})[\n\r]',
        ]
        for pat in org_patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                org = m.group(1).strip().rstrip(',.:;')
                if 5 < len(org) < 120:
                    meta['organization'] = org
                    break

        # ── Reference number ──────────────────────────────────────────────────
        ref_patterns = [
            r'(?:Tender|NIT|RFP|RFQ|EOI)\s+(?:No|Number|Ref|Reference)[.:\s]+([A-Z0-9][A-Z0-9\-_/\.]{3,40})',
            r'(?:Notice\s+Inviting\s+Tender|NIT)\s+(?:No\.?|Number)[.:\s]+([A-Z0-9][A-Z0-9\-_/\.]{3,40})',
        ]
        for pat in ref_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                meta['reference_number'] = m.group(1).strip()
                break

        # ── Turnover requirement ──────────────────────────────────────────────
        # Use sentence-bounded patterns to avoid cross-sentence false matches
        turnover_patterns = [
            # Pattern 1: "turnover ... Rs X Crore" within same sentence (stop at period/newline)
            r'(?:annual\s+turnover|average\s+annual\s+turnover|minimum\s+turnover|turnover\s+of|'
            r'yearly\s+turnover|avg\.?\s+annual\s+turnover)'
            r'[^.\n]{0,100}(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh|cr|million)?',
            # Pattern 2: "turnover not less than Rs X"
            r'(?:turnover)[^.\n]{0,60}(?:not\s+less\s+than|at\s+least|minimum\s+of|should\s+be|must\s+be)'
            r'[^.\n]{0,30}(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh|cr)?',
            # Pattern 3: "Rs X Crore per annum / annual turnover"
            r'(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh|cr)[^.\n]{0,60}(?:turnover|per\s+annum|p\.a\.|pa)',
            # Pattern 4: "turnover: Rs X" or "turnover - Rs X"
            r'(?:turnover|average\s+turnover)[\s:;\-]+(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh|cr)?',
            # Pattern 5: Any mention of turnover followed by amount
            r'(?:financial\s+)?turnover[^.\n]{0,100}(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh|cr)?',
        ]
        for pat in turnover_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                v = _parse_indian_amount(m.group(1), m.group(2) or '')
                if v and v >= 100000:  # At least 1 Lakh to filter noise
                    meta['min_turnover'] = v
                    try:
                        print(f"✓ Extracted min_turnover: ₹{v/10000000:.2f} Cr")
                    except:
                        pass
                    break

        if not meta.get('min_turnover'):
            try:
                print("✗ Failed to extract min_turnover")
            except:
                pass

        # ── Performance Guarantee % ───────────────────────────────────────────
        pg_patterns = [
            r'performance\s+(?:guarantee|security|bond|deposit)\s*[:\-=]?\s*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s+(?:of\s+)?(?:contract\s+)?(?:value\s+)?(?:as\s+)?performance\s+(?:guarantee|security)',
        ]
        for pat in pg_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                meta['performance_guarantee_percent'] = float(m.group(1))
                break

        # ── Liquidated Damages % ──────────────────────────────────────────────
        ld_patterns = [
            r'liquidated\s+damages\s*[:\-]?\s*(?:@|at|of)?\s*(\d+(?:\.\d+)?)\s*%',
            r'(?:LD|L\.D\.?)\s*(?:@|at|=|of|:)\s*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s+per\s+(?:week|month|fortnight)[^\n]{0,50}liquidated',
            r'penalty[^\n]{0,40}(\d+(?:\.\d+)?)\s*%\s+per\s+(?:week|month)',
        ]
        for pat in ld_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                meta['liquidated_damages_percent'] = float(m.group(1))
                break

        # ── Warranty / DLP ────────────────────────────────────────────────────
        warranty_patterns = [
            r'(?:warranty|defect\s*s?\s*liability|dlp|guarantee\s+period)\s+(?:period\s+)?(?:of\s+)?'
            r'(\d+)\s*(months?|years?)',
            r'(\d+)\s*(months?|years?)\s+(?:warranty|defects?\s*liability)',
        ]
        for pat in warranty_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                period = int(m.group(1))
                if 'year' in m.group(2).lower():
                    period *= 12
                meta['warranty_period_months'] = period
                break

        # ── Project experience requirement ────────────────────────────────────
        exp_patterns = [
            r'(?:similar\s+works?|similar\s+nature\s+of\s+works?|comparable\s+works?|experience\s+of)[^\n]{0,100}'
            r'(\d+)\s*(?:nos?\.?|numbers?|works?|projects?)',
            r'(?:at\s+least|minimum|not\s+less\s+than)\s+(\d+)\s*(?:similar|comparable)\s+(?:project|work|contract)',
            r'(?:completed|executed)\s+(\d+)\s+(?:similar|comparable|nos\.?)\s*(?:works?|projects?)',
            r'(\d+)\s+(?:similar|comparable)\s+(?:works?|projects?|contracts?)',
        ]
        for pat in exp_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                count = int(m.group(1))
                if count > 0 and count < 100:  # Reasonable range
                    meta['min_projects'] = count
                    try:
                        print(f"✓ Extracted min_projects: {count}")
                    except:
                        pass
                    break

        if not meta.get('min_projects'):
            try:
                print("✗ Failed to extract min_projects")
            except:
                pass

        # ── Net worth requirement ─────────────────────────────────────────────
        nw_keywords = ['net worth', 'networth', 'net-worth']
        nw = _extract_amount_from_text(text, nw_keywords)
        if nw:
            meta['min_net_worth'] = nw

        return meta


# ─────────────────────────────────────────────────────────────────────────────
# RISK DETECTOR
# ─────────────────────────────────────────────────────────────────────────────

class RiskDetector:
    """Detect salient risks in tender documents using broad real-world patterns."""

    RISK_CONFIGS = [
        {
            'key': 'UNLIMITED_LIABILITY',
            'category': 'UNLIMITED_LIABILITY',
            'keywords': [
                'unlimited liability', 'no limit on liability', 'uncapped liability',
                'shall be liable for all', 'liable for any and all', 'unlimited exposure',
                'full liability', 'absolute liability', 'liable without limit',
            ],
            'severity': 0.9,
            'description_template': 'Unlimited liability clause found: {}',
        },
        {
            'key': 'ONE_SIDED_TERMINATION',
            'category': 'ONE_SIDED_TERMINATION',
            'keywords': [
                'employer may terminate', 'owner may terminate', 'client may terminate',
                'terminate at its sole discretion', 'terminate without cause',
                'terminate at any time', 'terminate without notice',
                'employer reserves the right to terminate',
                'right to cancel', 'right to annul', 'cancel the contract',
                'discontinue the work', 'abandon the work',
            ],
            'severity': 0.75,
            'description_template': 'One-sided termination clause: {}',
        },
        {
            'key': 'PAYMENT_TERMS',
            'category': 'PAYMENT_TERMS',
            'keywords': [
                'payment after completion', 'no mobilization advance', 'no advance payment',
                'payment on final completion', 'no interim payment', 'payment only after',
                'retention money', 'retention of', 'deduct from payment',
                'withheld', 'payment withheld', 'back-to-back payment',
                'paid only upon', 'payment subject to', 'payment at discretion',
            ],
            'severity': 0.6,
            'description_template': 'Unfavorable payment term: {}',
        },
        {
            'key': 'BROAD_INDEMNITY',
            'category': 'INDEMNITY',
            'keywords': [
                'indemnify against all', 'indemnify and hold harmless', 'hold harmless for any',
                'unlimited indemnification', 'indemnify for any loss', 'indemnify against any claim',
                'indemnify the employer', 'contractor shall indemnify',
                'indemnify against third party', 'keep indemnified',
            ],
            'severity': 0.8,
            'description_template': 'Broad indemnity obligation: {}',
        },
        {
            'key': 'DISPUTE_RESOLUTION',
            'category': 'DISPUTE_RESOLUTION',
            'keywords': [
                'sole arbitration', "employer's decision shall be final",
                "engineer's decision is final", 'no arbitration', 'disputes not arbitrable',
                'decision of the employer shall be binding', 'sole discretion of employer',
                'no claim shall lie', 'no claims whatsoever', 'waive all claims',
                'decision shall be final and binding',
            ],
            'severity': 0.65,
            'description_template': 'Unfavorable dispute resolution: {}',
        },
        {
            'key': 'FORCE_MAJEURE',
            'category': 'FORCE_MAJEURE',
            'keywords': [
                'no extension for force majeure', 'force majeure not applicable',
                'no relief for force majeure', 'delays not excusable',
                'contractor bears all risks', 'risk and cost of contractor',
                'at contractor\'s risk', 'all risks shall be borne',
            ],
            'severity': 0.55,
            'description_template': 'Limited force majeure protection: {}',
        },
        {
            'key': 'SCOPE_AMBIGUITY',
            'category': 'SCOPE_AMBIGUITY',
            'keywords': [
                'as directed by engineer', 'as instructed by employer', 'at engineer\'s discretion',
                'any other work as required', 'additional work as directed',
                'scope may be varied', 'quantities are approximate',
                'such other works', 'any incidental work', 'allied and ancillary',
                'and any other items', 'items not mentioned but required',
            ],
            'severity': 0.5,
            'description_template': 'Scope ambiguity / open-ended obligation: {}',
        },
        {
            'key': 'PENALTY_CLAUSE',
            'category': 'HIGH_LD',
            'keywords': [
                'penalty for delay', 'penalty shall be imposed', 'penalties shall apply',
                'penal interest', 'penalty @ ', 'penalty at the rate',
                'per day penalty', 'daily penalty', 'levy penalty',
                'deduct penalty', 'penalty deduction',
            ],
            'severity': 0.65,
            'description_template': 'Penalty / LD clause detected: {}',
        },
        {
            'key': 'HIGH_SECURITY_DEPOSIT',
            'category': 'PERFORMANCE_GUARANTEE',
            'keywords': [
                'security deposit', 'performance security', 'performance bond',
                'bank guarantee', 'bg shall be submitted', 'submit a bank guarantee',
                'security shall be forfeited', 'guarantee shall be encashed',
                'forfeit the security', 'security amount shall be',
            ],
            'severity': 0.55,
            'description_template': 'Security / performance guarantee requirement: {}',
        },
        {
            'key': 'BLACKLISTING_RISK',
            'category': 'OTHER',
            'keywords': [
                'blacklisted', 'debarred', 'debarment', 'banned from bidding',
                'blacklisting of contractor', 'put on holiday', 'negative list',
                'shall be blacklisted', 'risk and cost',
            ],
            'severity': 0.7,
            'description_template': 'Blacklisting / debarment risk clause: {}',
        },
    ]

    def detect_risks(self, full_text: str, metadata: Dict) -> List[Dict]:
        risks = []
        text_lower = full_text.lower()

        # Keyword-based
        for config in self.RISK_CONFIGS:
            for kw in config['keywords']:
                if kw.lower() in text_lower:
                    context = self._extract_context(full_text, kw)
                    risks.append({
                        'category': config['category'],
                        'description': config['description_template'].format(context),
                        'severity_score': config['severity'],
                        'severity': self._score_to_level(config['severity']),
                        'clause_reference': self._find_clause_reference(full_text, kw),
                        'financial_exposure': None,
                    })
                    break  # one per risk type

        # Threshold-based: Liquidated Damages
        ld = metadata.get('liquidated_damages_percent')
        if ld:
            ld = float(ld)
            # Sanity check: real LD % is always ≤ 20% (0.5% per week × 40 weeks max)
            # Values above 20% are almost certainly false positives from project/turnover percentages
            if 0.5 < ld <= 20.0:
                sev = 0.9 if ld > 10 else (0.75 if ld > 5 else 0.6)
                ev = metadata.get('estimated_value')
                risks.append({
                    'category': 'HIGH_LD',
                    'description': (
                        f'Liquidated Damages at {ld}% per week/month is '
                        f'{"extremely high" if ld > 10 else "above industry standard of 0.5% per week"}. '
                        f'Maximum LD capped at {ld}% of contract value.'
                    ),
                    'severity_score': sev,
                    'severity': self._score_to_level(sev),
                    'financial_exposure': ev * ld / 100 if ev else None,
                    'clause_reference': None,
                })

        # Threshold-based: Performance Guarantee
        pg = metadata.get('performance_guarantee_percent')
        if pg:
            pg = float(pg)
            if pg > 10.0:
                ev = metadata.get('estimated_value')
                risks.append({
                    'category': 'PERFORMANCE_GUARANTEE',
                    'description': (
                        f'Performance Guarantee of {pg}% is higher than industry standard of 5-10%. '
                        f'This locks significant capital.'
                    ),
                    'severity_score': 0.65,
                    'severity': 'HIGH',
                    'financial_exposure': ev * pg / 100 if ev else None,
                    'clause_reference': None,
                })

        # Threshold-based: Warranty
        warranty = metadata.get('warranty_period_months')
        if warranty and int(warranty) > 24:
            risks.append({
                'category': 'WARRANTY_PERIOD',
                'description': (
                    f'Defects Liability / Warranty period of {warranty} months '
                    f'is above industry standard of 12-24 months.'
                ),
                'severity_score': 0.5,
                'severity': 'MEDIUM',
                'financial_exposure': None,
                'clause_reference': None,
            })

        # Detect high turnover requirement relative to contract value
        min_to = metadata.get('min_turnover')
        ev = metadata.get('estimated_value')
        if min_to and ev:
            ratio = float(min_to) / float(ev)
            if ratio > 3:
                risks.append({
                    'category': 'SCOPE_AMBIGUITY',
                    'description': (
                        f'Turnover requirement (₹{float(min_to)/10000000:.1f} Cr) is '
                        f'{ratio:.1f}× the contract value (₹{float(ev)/10000000:.1f} Cr). '
                        f'Very restrictive eligibility criteria may limit competition.'
                    ),
                    'severity_score': 0.65,
                    'severity': 'HIGH',
                    'financial_exposure': None,
                    'clause_reference': None,
                })
            elif ratio > 1.5:
                risks.append({
                    'category': 'SCOPE_AMBIGUITY',
                    'description': (
                        f'Turnover requirement (₹{float(min_to)/10000000:.1f} Cr) is '
                        f'{ratio:.1f}× the contract value. Moderately restrictive eligibility.'
                    ),
                    'severity_score': 0.45,
                    'severity': 'MEDIUM',
                    'financial_exposure': None,
                    'clause_reference': None,
                })

        # Detect risks from text patterns not covered by keyword configs
        # Short submission window
        import re as _re
        tight_deadline_patterns = [
            r'(?:submit|submission|receipt|closing)\s+(?:date|by)[^\n]{0,60}(\d{1,2})\s*days?',
        ]
        for pat in tight_deadline_patterns:
            m = _re.search(pat, full_text, _re.IGNORECASE)
            if m:
                days = int(m.group(1))
                if days < 14:
                    risks.append({
                        'category': 'SCOPE_AMBIGUITY',
                        'description': (
                            f'Very short submission window of {days} days detected. '
                            f'Insufficient time for proper bid preparation and site visits.'
                        ),
                        'severity_score': 0.5,
                        'severity': 'MEDIUM',
                        'financial_exposure': None,
                        'clause_reference': None,
                    })
                break

        # Single-bid / sole-source risk
        single_bid_kws = [
            'single bid', 'single tender', 'limited tender', 'single source',
            'proprietory item', 'proprietary item', 'nominated subcontractor',
        ]
        for kw in single_bid_kws:
            if kw in text_lower:
                ctx = self._extract_context(full_text, kw)
                risks.append({
                    'category': 'SCOPE_AMBIGUITY',
                    'description': f'Limited competition / single-source procurement risk: {ctx[:200]}',
                    'severity_score': 0.6,
                    'severity': 'HIGH',
                    'financial_exposure': None,
                    'clause_reference': self._find_clause_reference(full_text, kw),
                })
                break

        # Back-to-back / sub-contracting restriction
        subcon_kws = [
            'no subcontracting', 'sub-contracting not permitted', 'subcontracting prohibited',
            'shall not sub-contract', 'work shall be done by contractor himself',
        ]
        for kw in subcon_kws:
            if kw in text_lower:
                ctx = self._extract_context(full_text, kw)
                risks.append({
                    'category': 'SCOPE_AMBIGUITY',
                    'description': f'Sub-contracting restriction detected — bidder must self-perform all works: {ctx[:200]}',
                    'severity_score': 0.55,
                    'severity': 'MEDIUM',
                    'financial_exposure': None,
                    'clause_reference': self._find_clause_reference(full_text, kw),
                })
                break

        # Joint venture / consortium restriction
        jv_kws = [
            'joint venture not permitted', 'consortium not allowed', 'jv not permitted',
            'no joint venture', 'jv not acceptable',
        ]
        for kw in jv_kws:
            if kw in text_lower:
                ctx = self._extract_context(full_text, kw)
                risks.append({
                    'category': 'SCOPE_AMBIGUITY',
                    'description': f'Joint venture / consortium not permitted — restricts eligible bidders: {ctx[:200]}',
                    'severity_score': 0.5,
                    'severity': 'MEDIUM',
                    'financial_exposure': None,
                    'clause_reference': self._find_clause_reference(full_text, kw),
                })
                break

        # High EMD relative to contract value
        emd = metadata.get('emd_amount')
        if emd and ev:
            emd_pct = float(emd) / float(ev) * 100
            if emd_pct > 3:
                risks.append({
                    'category': 'PERFORMANCE_GUARANTEE',
                    'description': (
                        f'EMD of ₹{float(emd)/100000:.1f} Lakh is {emd_pct:.1f}% of contract value '
                        f'— above typical 1-2% industry norm. Significant upfront capital required.'
                    ),
                    'severity_score': 0.5,
                    'severity': 'MEDIUM',
                    'financial_exposure': float(emd),
                    'clause_reference': None,
                })

        # ── Eligibility / Qualification Document Specific Risks ───────────────

        # High experience threshold: "completed at least X similar works"
        exp_high_patterns = [
            r'(?:at\s+least|minimum)\s+(\d+)\s+(?:similar|comparable)\s+(?:works?|projects?|contracts?)',
            r'shall\s+have\s+(?:successfully\s+)?(?:completed|executed)\s+(\d+)\s+(?:similar|nos?\.?)\s*(?:works?|projects?)',
            r'experience\s+of\s+(?:at\s+least\s+)?(\d+)\s+(?:similar|comparable|nos?\.?)\s*(?:works?|projects?)',
        ]
        for pat in exp_high_patterns:
            m = _re.search(pat, full_text, _re.IGNORECASE)
            if m:
                count = int(m.group(1))
                if count >= 3:
                    ctx = self._extract_context(full_text, m.group(0)[:30])
                    risks.append({
                        'category': 'SCOPE_AMBIGUITY',
                        'description': (
                            f'High experience threshold: {count} similar completed works required. '
                            f'This significantly restricts eligible bidders. Context: {ctx[:200]}'
                        ),
                        'severity_score': 0.65 if count >= 5 else 0.5,
                        'severity': 'HIGH' if count >= 5 else 'MEDIUM',
                        'financial_exposure': None,
                        'clause_reference': self._find_clause_reference(full_text, m.group(0)[:30]),
                    })
                break

        # Specific minimum project value experience requirement
        proj_value_patterns = [
            r'(?:single\s+work|one\s+work|single\s+contract)[^\n]{0,60}'
            r'(?:not\s+less\s+than|at\s+least|minimum)[^\n]{0,40}'
            r'(?:Rs\.?|₹|INR)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh)',
            r'(?:value\s+of\s+work|cost\s+of\s+work)[^\n]{0,60}'
            r'(?:not\s+less\s+than|at\s+least)[^\n]{0,40}'
            r'(?:Rs\.?|₹|INR)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh)',
        ]
        for pat in proj_value_patterns:
            m = _re.search(pat, full_text, _re.IGNORECASE)
            if m:
                v = _parse_indian_amount(m.group(1), m.group(2))
                if v and ev and v > 0:
                    pct = v / float(ev) * 100
                    ctx = self._extract_context(full_text, m.group(0)[:40])
                    risks.append({
                        'category': 'SCOPE_AMBIGUITY',
                        'description': (
                            f'Single-work experience value requirement of ₹{v/10000000:.2f} Cr '
                            f'({pct:.0f}% of contract value) is restrictive. '
                            f'Context: {ctx[:200]}'
                        ),
                        'severity_score': 0.6 if pct > 50 else 0.45,
                        'severity': 'HIGH' if pct > 50 else 'MEDIUM',
                        'financial_exposure': None,
                        'clause_reference': self._find_clause_reference(full_text, m.group(0)[:40]),
                    })
                break

        # Net-worth / solvency risk
        nw = metadata.get('min_net_worth')
        if nw and ev:
            nw_pct = float(nw) / float(ev) * 100
            if nw_pct > 20:
                risks.append({
                    'category': 'PERFORMANCE_GUARANTEE',
                    'description': (
                        f'Net worth requirement of ₹{float(nw)/10000000:.2f} Cr is '
                        f'{nw_pct:.0f}% of contract value — high financial threshold '
                        f'that may limit eligible bidders.'
                    ),
                    'severity_score': 0.55,
                    'severity': 'MEDIUM',
                    'financial_exposure': None,
                    'clause_reference': None,
                })

        # Strict deadline / short bid validity
        bid_validity_pat = _re.search(
            r'bid\s+validity\s*[:\-]?\s*(\d+)\s*days?', full_text, _re.IGNORECASE
        )
        if bid_validity_pat:
            validity_days = int(bid_validity_pat.group(1))
            if validity_days > 180:
                risks.append({
                    'category': 'SCOPE_AMBIGUITY',
                    'description': (
                        f'Bid validity of {validity_days} days is unusually long (industry norm: 90-120 days). '
                        f'Extended validity locks bidder pricing and exposes to market risk.'
                    ),
                    'severity_score': 0.5,
                    'severity': 'MEDIUM',
                    'financial_exposure': None,
                    'clause_reference': None,
                })

        # Mandatory pre-bid site visit (adds cost and limits remote bidders)
        site_visit_kws = [
            'mandatory site visit', 'compulsory site visit', 'site visit is mandatory',
            'pre-bid site visit is compulsory', 'bidders are required to visit the site',
        ]
        for kw in site_visit_kws:
            if kw in text_lower:
                ctx = self._extract_context(full_text, kw)
                risks.append({
                    'category': 'SCOPE_AMBIGUITY',
                    'description': (
                        f'Mandatory pre-bid site visit required — adds cost/time burden '
                        f'and effectively limits geographically distant bidders. Context: {ctx[:200]}'
                    ),
                    'severity_score': 0.4,
                    'severity': 'MEDIUM',
                    'financial_exposure': None,
                    'clause_reference': self._find_clause_reference(full_text, kw),
                })
                break

        # Strict technical / ISO / certification requirements
        cert_kws = [
            'iso 9001', 'iso 14001', 'iso 45001', 'ohsas 18001',
            'bis certification', 'quality management system', 'qms certification',
            'nacl certified', 'dsc required',
        ]
        cert_found = [kw for kw in cert_kws if kw in text_lower]
        if len(cert_found) >= 2:
            risks.append({
                'category': 'SCOPE_AMBIGUITY',
                'description': (
                    f'Multiple certification requirements detected ({", ".join(c.upper() for c in cert_found[:4])}). '
                    f'These add compliance burden and restrict bidder pool.'
                ),
                'severity_score': 0.45,
                'severity': 'MEDIUM',
                'financial_exposure': None,
                'clause_reference': None,
            })
        elif len(cert_found) == 1:
            risks.append({
                'category': 'SCOPE_AMBIGUITY',
                'description': (
                    f'Certification requirement detected: {cert_found[0].upper()}. '
                    f'Verify your company holds current valid certification.'
                ),
                'severity_score': 0.35,
                'severity': 'LOW',
                'financial_exposure': None,
                'clause_reference': None,
            })

        # Penalty for non-performance of sub-works
        non_perf_kws = [
            'liable to pay damages', 'contractor shall be liable', 'cost consequences',
            'at risk and cost of bidder', 'all losses shall be recovered',
            'shall be recovered from contractor',
        ]
        for kw in non_perf_kws:
            if kw in text_lower:
                ctx = self._extract_context(full_text, kw)
                risks.append({
                    'category': 'HIGH_LD',
                    'description': (
                        f'Contractor liability / cost-recovery clause found. '
                        f'Context: {ctx[:250]}'
                    ),
                    'severity_score': 0.6,
                    'severity': 'HIGH',
                    'financial_exposure': None,
                    'clause_reference': self._find_clause_reference(full_text, kw),
                })
                break

        # Document / credential submission risk
        doc_kws = [
            'notarized copy', 'notarised copy', 'affidavit required',
            'original certificate', 'self-attested copies', 'attested by notary',
            'chartered accountant certificate', 'ca certificate',
        ]
        doc_found = [kw for kw in doc_kws if kw in text_lower]
        if len(doc_found) >= 2:
            risks.append({
                'category': 'SCOPE_AMBIGUITY',
                'description': (
                    f'Extensive document submission requirements: {", ".join(doc_found[:4])}. '
                    f'Heavy documentation burden may increase preparation time and cost.'
                ),
                'severity_score': 0.35,
                'severity': 'LOW',
                'financial_exposure': None,
                'clause_reference': None,
            })

        return risks

    def _extract_context(self, text: str, keyword: str, window: int = 300) -> str:
        pos = text.lower().find(keyword.lower())
        if pos == -1:
            return keyword
        start = max(0, pos - 100)
        end = min(len(text), pos + len(keyword) + window)
        return text[start:end].strip()

    def _find_clause_reference(self, text: str, keyword: str) -> Optional[str]:
        context = self._extract_context(text, keyword, 600)
        for pat in [
            r'(?:Clause|Section|Article|Para(?:graph)?)\s*(\d+(?:\.\d+)*)',
            r'(\d{1,2}\.\d{1,2}(?:\.\d+)?)\s',
        ]:
            m = re.search(pat, context, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    def _score_to_level(self, score: float) -> str:
        if score >= 0.8:
            return 'CRITICAL'
        elif score >= 0.6:
            return 'HIGH'
        elif score >= 0.4:
            return 'MEDIUM'
        return 'LOW'


# ─────────────────────────────────────────────────────────────────────────────
# CONFLICT DETECTOR
# ─────────────────────────────────────────────────────────────────────────────

class ConflictDetector:
    """Detect conflicting clauses using real patterns found in Indian tenders."""

    # Each entry: (topic, pattern_A_keywords, pattern_B_keywords, explanation)
    CONFLICT_RULES = [
        (
            'payment_terms',
            ['payment within 30 days', 'payment in 30 days', '30 days from invoice'],
            ['payment within 60 days', 'payment in 60 days', '60 days from invoice', '90 days'],
            'Conflicting payment timelines specified in different sections.',
        ),
        (
            'termination',
            ['terminate for convenience', 'terminate without cause', 'terminate at will'],
            ['mutual agreement', 'both parties may terminate', 'termination requires consent'],
            'Termination clauses conflict: one section allows unilateral termination, another requires mutual agreement.',
        ),
        (
            'warranty',
            [r'warranty period.*?12\s*months', r'defects liability.*?12\s*months'],
            [r'warranty period.*?24\s*months', r'defects liability.*?24\s*months',
             r'warranty period.*?36\s*months'],
            'Conflicting warranty / defects liability periods mentioned in different clauses.',
        ),
        (
            'arbitration',
            ['disputes shall be referred to arbitration', 'arbitration as per arbitration act'],
            ['no arbitration', 'disputes not arbitrable', 'courts shall have jurisdiction'],
            'Conflict between arbitration clause and jurisdiction/no-arbitration clause.',
        ),
        (
            'variation_limit',
            ['variation up to 25%', 'quantity variation.*?25', '±25%'],
            ['variation up to 10%', 'quantity variation.*?10', '±10%'],
            'Conflicting variation / quantity adjustment limits in different sections.',
        ),
        (
            'liquidation',
            ['maximum ld.*?5%', 'ld capped at 5', 'ld shall not exceed 5'],
            ['maximum ld.*?10%', 'ld capped at 10', 'ld shall not exceed 10'],
            'Conflicting maximum LD cap percentages in different clauses.',
        ),
        (
            'advance_payment',
            ['mobilization advance.*?10%', 'advance payment.*?10%'],
            ['no mobilization advance', 'no advance shall be paid', 'advance payment not applicable'],
            'Mobilization advance mentioned in one clause but denied in another.',
        ),
        # ── Eligibility / criteria document conflict rules ──────────────────
        (
            'jv_eligibility',
            ['joint venture.*?permitted', 'consortium.*?allowed', 'jv.*?eligible',
             'bidders may form.*?consortium', 'joint venture.*?acceptable'],
            ['joint venture not permitted', 'consortium not allowed', 'jv not permitted',
             'no joint venture', 'individual bidder only'],
            'Joint venture / consortium eligibility is simultaneously permitted and prohibited in different sections.',
        ),
        (
            'experience_count',
            ['at least 1 similar work', 'one similar work', '01 similar',
             'minimum 1.*?similar', 'single similar work'],
            ['at least 2 similar works', 'two similar works', '02 similar',
             'minimum 2.*?similar', 'at least 3 similar', 'three similar', '03 similar',
             'minimum 3.*?similar'],
            'Conflicting number of required similar works mentioned in different sections.',
        ),
        (
            'turnover_conflict',
            [r'annual turnover.*?(?:Rs\.?|₹|INR)\s*[\d,]+\s*(?:crore|lakh)',
             r'minimum turnover.*?(?:Rs\.?|₹|INR)\s*[\d,]+\s*(?:crore|lakh)'],
            ['turnover requirement.*?waived', 'turnover.*?not applicable',
             'turnover.*?not required for this tender'],
            'Turnover requirement is specified in one section but waived or excluded in another.',
        ),
        (
            'subcontracting',
            ['sub-contracting.*?permitted', 'subcontracting.*?allowed',
             'may sub-contract', 'sub-contractor.*?acceptable'],
            ['no subcontracting', 'sub-contracting not permitted', 'subcontracting prohibited',
             'shall not sub-contract'],
            'Sub-contracting is simultaneously permitted and prohibited in different sections.',
        ),
        (
            'bid_document_fee',
            [r'tender fee.*?(?:non[\s-]?refundable|not refundable)',
             r'document fee.*?non[\s-]?refundable'],
            ['tender fee.*?refundable', 'document fee.*?shall be refunded',
             'fee.*?will be refunded on'],
            'Conflicting statements on whether the tender document fee is refundable.',
        ),
        (
            'site_visit',
            ['site visit is mandatory', 'compulsory site visit', 'mandatory pre-bid visit'],
            ['site visit is optional', 'site visit at bidder\'s discretion',
             'site visit is not mandatory'],
            'Conflicting requirements regarding whether the pre-bid site visit is mandatory.',
        ),
    ]

    def detect_conflicts(self, sections: List[Dict]) -> List[Dict]:
        conflicts = []
        full_text = ' '.join([s.get('content', '') for s in sections])
        text_lower = full_text.lower()

        for topic, kw_a_list, kw_b_list, explanation in self.CONFLICT_RULES:
            found_a = None
            found_a_kw = None
            found_b = None
            found_b_kw = None

            for kw in kw_a_list:
                if re.search(kw, text_lower, re.IGNORECASE):
                    found_a_kw = kw
                    # Extract full context around the keyword
                    found_a = self._extract_clause_context(full_text, kw)
                    break

            for kw in kw_b_list:
                if re.search(kw, text_lower, re.IGNORECASE):
                    found_b_kw = kw
                    # Extract full context around the keyword
                    found_b = self._extract_clause_context(full_text, kw)
                    break

            if found_a and found_b:
                conflicts.append({
                    'clause_a': found_a,
                    'clause_b': found_b,
                    'contradiction_score': 0.85,
                    'explanation': explanation,
                    'clause_a_reference': self._find_section_reference(full_text, found_a_kw),
                    'clause_b_reference': self._find_section_reference(full_text, found_b_kw),
                })

        # Cross-section numeric conflicts
        self._detect_numeric_conflicts(sections, conflicts)

        return conflicts

    def _extract_clause_context(self, text: str, keyword: str, window: int = 400) -> str:
        """Extract complete clause/sentence context around keyword"""
        # Find keyword position (case insensitive)
        match = re.search(re.escape(keyword), text, re.IGNORECASE)
        if not match:
            return keyword

        pos = match.start()

        # Find sentence boundaries (look for periods, newlines, or start/end of text)
        # Go backward to find sentence start
        start = pos
        for i in range(pos - 1, max(0, pos - window), -1):
            if text[i] in '.?\n' and i < pos - 1:
                # Found a sentence boundary
                start = i + 1
                break
            elif i == max(0, pos - window):
                start = i

        # Go forward to find sentence end
        end = pos + len(keyword)
        for i in range(pos + len(keyword), min(len(text), pos + window)):
            if text[i] in '.?\n':
                end = i
                break
            elif i == min(len(text), pos + window) - 1:
                end = i + 1

        # Extract and clean the context
        context = text[start:end].strip()
        # Remove leading/trailing punctuation and whitespace
        context = context.strip('.:;, \n\r\t')

        # If context is too short, expand it
        if len(context) < 50:
            context = text[max(0, pos - 200):min(len(text), pos + 300)].strip()

        return context

    def _find_section_reference(self, text: str, keyword: str) -> Optional[str]:
        """Find section/clause reference near keyword"""
        match = re.search(re.escape(keyword), text, re.IGNORECASE)
        if not match:
            return None

        pos = match.start()
        # Look in context around the keyword
        context_start = max(0, pos - 500)
        context_end = min(len(text), pos + 200)
        context = text[context_start:context_end]

        # Try to find section reference
        for pat in [
            r'(?:Clause|Section|Article|Para(?:graph)?)\s+(\d+(?:\.\d+)*)',
            r'(\d{1,2}\.\d{1,2}(?:\.\d+)?)[:\s]',
        ]:
            m = re.search(pat, context, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    def _detect_numeric_conflicts(self, sections: List[Dict], conflicts: List[Dict]):
        """Detect contradictory numbers (dates, percentages) across sections."""
        # Find all LD percentages across sections
        ld_values = []
        for s in sections:
            for m in re.finditer(r'(?:LD|liquidated\s+damages)[^\n]{0,50}(\d+(?:\.\d+)?)\s*%',
                                 s.get('content', ''), re.IGNORECASE):
                ld_values.append((float(m.group(1)), s.get('section_number', '?')))

        unique_ld = set(v for v, _ in ld_values)
        if len(unique_ld) > 1:
            conflicts.append({
                'clause_a': f'LD = {list(unique_ld)[0]}%',
                'clause_b': f'LD = {list(unique_ld)[1]}%',
                'contradiction_score': 0.9,
                'explanation': f'Different liquidated damage percentages found across sections: {unique_ld}',
            })

        # Find conflicting turnover amounts across sections
        turnover_values = []
        turnover_pat = re.compile(
            r'(?:annual\s+turnover|minimum\s+turnover|turnover)[^\n]{0,60}'
            r'(?:Rs\.?|₹|INR)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh|million)?',
            re.IGNORECASE
        )
        for s in sections:
            for m in turnover_pat.finditer(s.get('content', '')):
                v = _parse_indian_amount(m.group(1), m.group(2) or '')
                if v:
                    turnover_values.append((v, s.get('section_number', '?')))

        if len(turnover_values) >= 2:
            vals = [v for v, _ in turnover_values]
            min_v, max_v = min(vals), max(vals)
            # Only flag if values differ by more than 20%
            if max_v > min_v * 1.2:
                conflicts.append({
                    'clause_a': f'Turnover ≥ ₹{min_v/10000000:.2f} Cr (Section {turnover_values[0][1]})',
                    'clause_b': f'Turnover ≥ ₹{max_v/10000000:.2f} Cr (Section {turnover_values[-1][1]})',
                    'contradiction_score': 0.8,
                    'explanation': (
                        'Conflicting minimum annual turnover requirements found across sections. '
                        f'Values range from ₹{min_v/10000000:.2f} Cr to ₹{max_v/10000000:.2f} Cr.'
                    ),
                    'clause_a_reference': str(turnover_values[0][1]),
                    'clause_b_reference': str(turnover_values[-1][1]),
                })

        # Find conflicting experience project value requirements across sections
        proj_val_values = []
        proj_val_pat = re.compile(
            r'(?:single\s+work|one\s+work|each\s+work|any\s+one\s+work|similar\s+work)[^\n]{0,80}'
            r'(?:not\s+less\s+than|at\s+least|minimum|value)[^\n]{0,40}'
            r'(?:Rs\.?|₹|INR)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh)?',
            re.IGNORECASE
        )
        for s in sections:
            for m in proj_val_pat.finditer(s.get('content', '')):
                v = _parse_indian_amount(m.group(1), m.group(2) or '')
                if v:
                    proj_val_values.append((v, s.get('section_number', '?'), m.group(0)[:80]))

        if len(proj_val_values) >= 2:
            vals = [v for v, _, _ in proj_val_values]
            min_v, max_v = min(vals), max(vals)
            if max_v > min_v * 1.15:
                conflicts.append({
                    'clause_a': f'Single work value ≥ ₹{min_v/10000000:.2f} Cr',
                    'clause_b': f'Single work value ≥ ₹{max_v/10000000:.2f} Cr',
                    'contradiction_score': 0.78,
                    'explanation': (
                        'Conflicting minimum single-work experience values found in different sections: '
                        f'₹{min_v/10000000:.2f} Cr vs ₹{max_v/10000000:.2f} Cr.'
                    ),
                    'clause_a_reference': str(proj_val_values[0][1]),
                    'clause_b_reference': str(proj_val_values[-1][1]),
                })

        # Conflicting completion periods across sections
        period_values = []
        period_pat = re.compile(
            r'(?:completion\s+period|time\s+for\s+completion|contract\s+duration)[^\n]{0,50}'
            r'(\d+)\s*(days?|months?|weeks?)',
            re.IGNORECASE
        )
        for s in sections:
            for m in period_pat.finditer(s.get('content', '')):
                val = int(m.group(1))
                unit = m.group(2).lower()
                if 'month' in unit:
                    val_days = val * 30
                elif 'week' in unit:
                    val_days = val * 7
                else:
                    val_days = val
                if val_days >= 7:
                    period_values.append((val_days, s.get('section_number', '?'), f'{m.group(1)} {m.group(2)}'))

        if len(period_values) >= 2:
            days_vals = [v for v, _, _ in period_values]
            min_d, max_d = min(days_vals), max(days_vals)
            if max_d > min_d * 1.2:
                conflicts.append({
                    'clause_a': f'Completion period: {period_values[0][2]} (Section {period_values[0][1]})',
                    'clause_b': f'Completion period: {period_values[-1][2]} (Section {period_values[-1][1]})',
                    'contradiction_score': 0.82,
                    'explanation': (
                        'Different completion periods are specified in different sections of the document. '
                        'Ambiguity in contract duration creates scheduling and pricing risk.'
                    ),
                    'clause_a_reference': str(period_values[0][1]),
                    'clause_b_reference': str(period_values[-1][1]),
                })


# ─────────────────────────────────────────────────────────────────────────────
# ELIGIBILITY VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

class EligibilityValidator:

    def validate(self, tender_eligibility: Dict, company_profile: Dict) -> Dict:
        checks = {}
        missing = []

        # Turnover
        if tender_eligibility.get('min_turnover'):
            co_to = float(company_profile.get('annual_turnover') or 0)
            req_to = float(tender_eligibility['min_turnover'])
            ok = co_to >= req_to
            checks['turnover'] = {
                'required': req_to,
                'actual': co_to,
                'status': ok,
                'label': f'Annual Turnover ≥ ₹{req_to/10000000:.2f} Cr',
            }
            if not ok:
                missing.append('Annual turnover requirement not met')

        # Net worth
        if tender_eligibility.get('min_net_worth'):
            co_nw = float(company_profile.get('net_worth') or 0)
            req_nw = float(tender_eligibility['min_net_worth'])
            ok = co_nw >= req_nw
            checks['net_worth'] = {
                'required': req_nw,
                'actual': co_nw,
                'status': ok,
                'label': f'Net Worth ≥ ₹{req_nw/10000000:.2f} Cr',
            }
            if not ok:
                missing.append('Net worth requirement not met')

        # Project experience
        if tender_eligibility.get('min_projects'):
            co_proj = int(company_profile.get('similar_projects_completed') or 0)
            req_proj = int(tender_eligibility['min_projects'])
            ok = co_proj >= req_proj
            checks['experience'] = {
                'required': req_proj,
                'actual': co_proj,
                'status': ok,
                'label': f'Similar projects completed ≥ {req_proj}',
            }
            if not ok:
                missing.append('Similar project experience not met')

        eligible = all(c['status'] for c in checks.values()) if checks else True

        return {
            'eligible': eligible,
            'checks': checks,
            'missing_criteria': missing,
        }


# ─────────────────────────────────────────────────────────────────────────────
# PROPOSAL GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

class ProposalGenerator:

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def generate(self, tender: Dict, company_profile: Dict) -> Dict:
        # Always generate data-driven sections first (accurate, uses real tender data)
        result = self._generate_data_driven(tender, company_profile)
        full_parts = []
        for field in ['technical_compliance', 'construction_methodology', 'resource_mobilization',
                      'risk_mitigation', 'commercial_positioning', 'schedule_assurance', 'value_engineering']:
            label = field.replace('_', ' ').title()
            full_parts.append(f"## {label}\n\n{result[field]}")
        result['full_proposal'] = "\n\n---\n\n".join(full_parts)
        return result

    def _fmt_crore(self, value) -> str:
        try:
            v = float(value or 0)
            return f"₹{v/10_000_000:.2f} Cr"
        except Exception:
            return str(value)

    def _generate_data_driven(self, tender: Dict, company_profile: Dict) -> Dict:
        title       = tender.get('title', 'this tender')
        ref         = tender.get('reference_number', '')
        scope       = tender.get('scope_of_work') or 'General construction and engineering works'
        value       = self._fmt_crore(tender.get('estimated_value'))
        deadline    = tender.get('submission_deadline', '')
        period      = tender.get('completion_period', '')
        emd         = self._fmt_crore(tender.get('emd_amount'))
        company     = company_profile.get('company_name', 'Our Company')
        strengths   = company_profile.get('company_strengths', 'Experienced EPC contractor')
        turnover    = self._fmt_crore(company_profile.get('annual_turnover'))
        proj_done   = company_profile.get('similar_projects_completed', 5)
        work_items  = tender.get('work_items', [])
        risks       = tender.get('risks', [])

        # Completion period in months
        try:
            period_months = int(float(period)) // 30 if period else None
            period_str = f"{period_months} months" if period_months else "as per tender schedule"
        except Exception:
            period_str = "as per tender schedule"

        # Top BOQ categories
        cat_totals = {}
        for wi in work_items:
            cat = wi.get('category', 'OTHER')
            cat_totals[cat] = cat_totals.get(cat, 0) + float(wi.get('estimated_cost') or 0)
        top_cats = sorted(cat_totals.items(), key=lambda x: -x[1])

        # Top risks
        critical_risks = [r for r in risks if r.get('severity') in ('CRITICAL', 'HIGH')]

        # ── Technical Compliance ──────────────────────────────────────────────
        boq_scope_lines = []
        for cat, total in top_cats[:4]:
            boq_scope_lines.append(f"- **{cat.title()} works** ({self._fmt_crore(total)}): Full compliance with IS codes, approved drawings and specifications")
        if not boq_scope_lines:
            boq_scope_lines = ["- Full technical compliance across all work categories as per tender specifications"]

        technical_compliance = (
            f"- Tender **{ref}** — {title}: All technical requirements acknowledged and accepted in full\n"
            + "\n".join(boq_scope_lines) + "\n"
            f"- **Quality Management**: ISO 9001:2015 certified QMS; third-party inspections at every milestone\n"
            f"- **Material Compliance**: All materials from CPWD/BIS-approved vendors; test certificates submitted before use\n"
            f"- **Statutory Compliance**: Valid licenses, insurance (CAR + Third-Party), and all regulatory approvals in place"
        )

        # ── Construction Methodology ──────────────────────────────────────────
        phases = []
        if period_months:
            mob_end   = min(1, period_months)
            civil_end = min(mob_end + max(period_months // 3, 2), period_months)
            mep_end   = min(civil_end + max(period_months // 4, 1), period_months)
            phases = [
                f"- **Phase 1 – Mobilisation (Month 1–{mob_end})**: Site setup, equipment deployment, material procurement, sub-contractor onboarding",
                f"- **Phase 2 – Civil & Structural (Month {mob_end+1}–{civil_end})**: Foundation, RCC works, structural steel fabrication and erection",
                f"- **Phase 3 – MEP & Services (Month {civil_end+1}–{mep_end})**: Electrical, plumbing, HVAC, fire-fighting installation and testing",
                f"- **Phase 4 – Finishing & Commissioning (Month {mep_end+1}–{period_months})**: Wearing course, landscaping, testing, handover",
            ]
        else:
            phases = [
                "- **Phase 1 – Mobilisation**: Site setup, equipment deployment, material procurement",
                "- **Phase 2 – Civil & Structural**: Foundation, RCC and structural steel works",
                "- **Phase 3 – MEP & Services**: Electrical, plumbing and HVAC installation",
                "- **Phase 4 – Commissioning**: Testing, punch-list clearance and handover",
            ]

        construction_methodology = (
            f"- Project **{title}** (Value: {value}) executed as EPC contract with full design-build responsibility\n"
            + "\n".join(phases) + "\n"
            f"- **Quality Control**: Daily site reports, CPM schedule tracking, QA checkpoints at each phase gate\n"
            f"- **IRC/IS Standards**: All works conform to applicable IRC, IS, and CPWD specifications"
        )

        # ── Resource Mobilisation ─────────────────────────────────────────────
        resource_mobilization = (
            f"- **Project Director**: Senior engineer with 15+ years EPC experience assigned as single point of accountability\n"
            f"- **Core Team**: Site manager, QA/QC engineer, safety officer, and MEP coordinator mobilised within 7 days of LoA\n"
            f"- **Equipment**: Piling rigs, cranes, concrete batching plant, and DG sets pre-booked from CPWD-empanelled suppliers\n"
            f"- **Sub-contractors**: Pre-qualified sub-contractors for structural steel, MEP and finishing identified; LOIs issued\n"
            f"- **Materials**: Long-lead items (structural steel, bearings, switchgear) ordered immediately on award to avoid delays"
        )

        # ── Risk Mitigation ───────────────────────────────────────────────────
        risk_lines = []
        for r in critical_risks[:4]:
            rtype = (r.get('category') or 'GENERAL').replace('_', ' ').title()
            desc  = (r.get('description') or '')[:80]
            risk_lines.append(f"- **{rtype}**: {desc} — Mitigation: dedicated clause review + legal sign-off before signing")
        if not risk_lines:
            risk_lines = [
                "- **LD / Liquidated Damages**: Aggressive LD clauses reviewed; buffer schedule built in to absorb minor delays",
                "- **Price Escalation**: Fixed-price strategy with bulk procurement lock-in for steel and cement",
            ]
        risk_lines += [
            f"- **Schedule Risk**: CPM network with float management; early-warning triggers raised 4 weeks before milestone",
            f"- **Supply Chain**: Dual-vendor policy for all critical materials; 15-day stock buffer maintained on site",
            f"- **Contingency**: 5% contingency reserve allocated; risk register reviewed fortnightly with client",
        ]

        risk_mitigation = "\n".join(risk_lines[:6])

        # ── Commercial Positioning ────────────────────────────────────────────
        commercial_positioning = (
            f"- **Bid Value**: {value} (Ref: {ref}) — competitive pricing with 8–10% net margin after all overheads\n"
            f"- **EMD**: {emd} submitted as per tender conditions; Performance Guarantee (5%) provided within 14 days of award\n"
            f"- **{company} Track Record**: Annual turnover {turnover}, {proj_done} similar projects delivered on time and budget\n"
            f"- **Value Proposition**: {strengths}\n"
            f"- **Payment Terms**: Accepted as per tender — 90% running bills within 30 days; retention released post-DLP"
        )

        # ── Schedule Assurance ────────────────────────────────────────────────
        schedule_assurance = (
            f"- **Committed Completion**: {period_str} from date of commencement — milestone schedule submitted with bid\n"
            f"- **Submission Deadline**: Bid submitted before {deadline or 'stipulated due date'}; all documents complete\n"
            f"- **CPM Schedule**: Level-3 programme with {len(work_items) or 14} work packages; critical path identified and tracked daily\n"
            f"- **Progress Monitoring**: Weekly site meetings, fortnightly MIS reports to client, monthly reviews with EIC\n"
            f"- **Early Warning**: Automated delay alerts triggered when activity float drops below 5 days"
        )

        # ── Value Engineering ─────────────────────────────────────────────────
        ve_lines = []
        for cat, total in top_cats[:3]:
            saving_pct = 3 if cat == 'CIVIL' else 5 if cat == 'MECHANICAL' else 4
            saving = self._fmt_crore(float(total) * saving_pct / 100)
            ve_lines.append(f"- **{cat.title()} VE**: Optimise design/material spec → estimated saving {saving} ({saving_pct}%) with no quality compromise")
        if not ve_lines:
            ve_lines = ["- **Structural Steel**: Use IS 2062 E350 HR sections with optimised section modulus — estimated 3–4% saving"]
        ve_lines += [
            "- **Prefabrication**: Pre-cast deck panels and pre-fabricated steelwork reduce on-site labour by 20%",
            "- **Bulk Procurement**: Central procurement of cement, steel, and aggregates locks in 4–6% lower rates",
            "- **Energy Efficiency**: LED lighting and VFD-controlled pumps reduce operational OPEX by ₹2–3 L/year",
        ]

        value_engineering = "\n".join(ve_lines[:5])

        return {
            'technical_compliance':   technical_compliance,
            'construction_methodology': construction_methodology,
            'resource_mobilization':  resource_mobilization,
            'risk_mitigation':        risk_mitigation,
            'commercial_positioning': commercial_positioning,
            'schedule_assurance':     schedule_assurance,
            'value_engineering':      value_engineering,
        }

    def _generate_template(self, tender: Dict, company_profile: Dict) -> Dict:
        return self._generate_data_driven(tender, company_profile)


# ─────────────────────────────────────────────────────────────────────────────
# WIN SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────

class WinSimulator:

    def simulate(self, tender: Dict, company_profile: Dict, risks: List[Dict]) -> Dict:
        eligibility_score = self._calc_eligibility(tender, company_profile)
        risk_score = self._calc_risk(risks)
        competitiveness = float(company_profile.get('past_win_rate') or 0.5)

        win_prob = (
            0.4 * eligibility_score +
            0.3 * (1 - risk_score) +
            0.3 * competitiveness
        )

        # Clamp between 5% and 95%
        win_prob = max(0.05, min(0.95, win_prob))

        # Generate insights
        insights = [
            f"Company meets {int(eligibility_score * 100)}% of eligibility criteria",
            f"Risk exposure level: {int(risk_score * 100)}%",
            f"Historical win rate: {int(competitiveness * 100)}%",
        ]

        # Generate recommendations
        recommendations = []
        if eligibility_score < 0.7:
            recommendations.append("Strengthen eligibility credentials before bidding")
        if risk_score > 0.6:
            recommendations.append("Negotiate risk-heavy clauses to improve win probability")
        if competitiveness < 0.5:
            recommendations.append("Focus on highlighting past project successes")
        if win_prob > 0.6:
            recommendations.append("Strong candidate - proceed with aggressive pricing strategy")

        return {
            'win_probability': round(win_prob * 100, 2),
            'factors': {
                'eligibility_score': eligibility_score,
                'risk_score': risk_score,
                'competitiveness': competitiveness,
            },
            'insights': insights,
            'recommendations': recommendations if recommendations else ["Prepare a comprehensive bid addressing all requirements"],
        }

    def _calc_eligibility(self, tender: Dict, company: Dict) -> float:
        score = 0.5
        el = tender.get('eligibility', {})
        if isinstance(el, dict):
            if el.get('min_turnover') and company.get('annual_turnover'):
                if float(company['annual_turnover']) >= float(el['min_turnover']):
                    score += 0.3
            if el.get('min_projects') and company.get('similar_projects_completed'):
                if int(company['similar_projects_completed']) >= int(el['min_projects']):
                    score += 0.2
        return min(score, 1.0)

    def _calc_risk(self, risks: List[Dict]) -> float:
        if not risks:
            return 0.2
        return min(sum(r.get('severity_score', 0.5) for r in risks) / len(risks), 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# PRE-BID QUESTION GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

class PreBidQuestionGenerator:

    CATEGORY_QUESTIONS = {
        'UNLIMITED_LIABILITY': (
            'RISK',
            'The tender appears to contain an unlimited liability clause. '
            'Could you please confirm the maximum liability cap for the contractor?',
        ),
        'HIGH_LD': (
            'COMMERCIAL',
            'The Liquidated Damages rate specified appears high compared to industry norms. '
            'Kindly confirm the maximum LD cap as a percentage of contract value.',
        ),
        'ONE_SIDED_TERMINATION': (
            'COMMERCIAL',
            'The termination clause appears to give the employer unilateral rights. '
            'What compensation will be paid to the contractor in case of termination for convenience?',
        ),
        'PERFORMANCE_GUARANTEE': (
            'COMMERCIAL',
            'The Performance Guarantee percentage is higher than standard. '
            'Can the PG be reduced or phased in line with project milestones?',
        ),
        'WARRANTY_PERIOD': (
            'TECHNICAL',
            'The Defects Liability / Warranty period seems extended. '
            'Could the employer clarify the specific defects covered and the remediation process?',
        ),
        'PAYMENT_TERMS': (
            'COMMERCIAL',
            'The payment terms do not clearly specify interim payment milestones. '
            'Please provide the payment schedule / milestone-based payment structure.',
        ),
        'INDEMNITY': (
            'RISK',
            'The indemnity clause appears broad and one-sided. '
            'Is the employer willing to limit indemnity obligations to direct losses only?',
        ),
        'DISPUTE_RESOLUTION': (
            'COMMERCIAL',
            'The dispute resolution mechanism needs clarification. '
            'Will independent arbitration be available for resolving commercial disputes?',
        ),
        'FORCE_MAJEURE': (
            'RISK',
            'What force majeure events are recognized under this contract, and what relief '
            '(time extension / cost) will be granted to the contractor?',
        ),
        'SCOPE_AMBIGUITY': (
            'SCOPE',
            'Several scope items appear to be loosely defined (e.g., "as directed by engineer"). '
            'Could detailed technical specifications and drawings be provided?',
        ),
    }

    def generate(self, tender: Dict, risks: List[Dict], conflicts: List[Dict]) -> List[Dict]:
        questions = []
        used_categories = set()

        # Risk-based questions
        for risk in sorted(risks, key=lambda r: r.get('severity_score', 0), reverse=True)[:6]:
            cat = risk.get('category', '')
            if cat in self.CATEGORY_QUESTIONS and cat not in used_categories:
                q_cat, q_text = self.CATEGORY_QUESTIONS[cat]
                questions.append({
                    'category': q_cat,
                    'question': q_text,
                    'rationale': f"Risk identified: {cat.replace('_', ' ').title()} (Severity: {risk.get('severity', 'MEDIUM')})",
                })
                used_categories.add(cat)

        # Conflict-based questions
        for conflict in conflicts[:3]:
            questions.append({
                'category': 'COMMERCIAL',
                'question': (
                    f"There appears to be a conflict in the tender document: {conflict.get('explanation', '')} "
                    f"Kindly clarify which clause shall prevail."
                ),
                'rationale': f"Contradiction score: {conflict.get('contradiction_score', 0.85):.0%}",
            })

        # Standard eligibility questions
        questions.append({
            'category': 'ELIGIBILITY',
            'question': (
                'Please confirm whether joint ventures or consortia are permitted to bid, '
                'and if so, what is the lead member minimum shareholding requirement?'
            ),
            'rationale': 'Eligibility clarification',
        })

        questions.append({
            'category': 'TECHNICAL',
            'question': (
                'Please provide the detailed Bill of Quantities (BOQ) with item-wise specifications, '
                'drawings, and GFC (Good for Construction) drawings before the pre-bid meeting.'
            ),
            'rationale': 'Technical scope clarification',
        })

        questions.append({
            'category': 'TIMELINE',
            'question': (
                'Given the project complexity, is a time extension possible for bid submission to allow '
                'adequate time for site visit and preparation of a detailed bid?'
            ),
            'rationale': 'Timeline adequacy query',
        })

        return questions
