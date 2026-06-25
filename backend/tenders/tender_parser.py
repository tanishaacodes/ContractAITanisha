"""
Tender PDF Parsing Engine
Layout-aware hierarchical parsing for EPC tenders
"""
import re
import pdfplumber
from typing import List, Dict, Any


class TenderParser:
    """Parse tender PDFs with layout-aware section detection"""

    def __init__(self):
        self.section_patterns = [
            r'^(\d+(\.\d+)*)\s+(.+)$',  # 1.2.3 Section Title
            r'^([A-Z]+(\.[A-Z]+)*)\s+(.+)$',  # A.B Section Title
            r'^(SECTION|PART|CHAPTER)\s+(\d+|[A-Z]+)[:\s]+(.+)$',  # SECTION 1: Title
        ]

    def _clean_text(self, text: str) -> str:
        """Clean text from PDF encoding issues"""
        if not text:
            return ""

        # Remove (cid:XXX) patterns from corrupted PDFs
        text = re.sub(r'\(cid:\d+\)', '', text)

        # Remove other common PDF artifacts
        text = re.sub(r'\(col:\d+\)', '', text)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)  # Control characters

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

        self.boq_keywords = [
            'bill of quantities', 'boq', 'schedule of quantities',
            'price schedule', 'work items', 'quantity schedule'
        ]

        self.eligibility_keywords = [
            'eligibility', 'qualification', 'turnover', 'net worth',
            'experience', 'similar work', 'financial capacity'
        ]

        self.commercial_keywords = [
            'payment terms', 'liquidated damages', 'performance guarantee',
            'earnest money', 'emd', 'bid security', 'retention money',
            'warranty', 'defects liability'
        ]

    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main parsing method - extracts structured information from tender PDF

        Returns:
            {
                'full_text': str,
                'sections': List[Dict],
                'tables': List[Dict],
                'metadata': Dict
            }
        """
        sections = []
        tables = []
        full_text = ""
        metadata = {}

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text with layout preservation for better BOQ extraction
                text = page.extract_text(layout=True, x_tolerance=3, y_tolerance=3)
                if text:
                    # Clean text from PDF encoding issues
                    text = self._clean_text(text)
                    full_text += text + "\n"
                    page_sections = self._parse_sections(text, page_num)
                    sections.extend(page_sections)

                # Extract tables
                page_tables = page.extract_tables()
                for table_idx, table in enumerate(page_tables):
                    tables.append({
                        'page': page_num,
                        'table_index': table_idx,
                        'data': table,
                        'type': self._classify_table(table)
                    })

        # Build hierarchical structure
        hierarchical_sections = self._build_hierarchy(sections)

        # Extract metadata
        metadata = self._extract_metadata(full_text, sections, tables)

        return {
            'full_text': full_text,
            'sections': hierarchical_sections,
            'tables': tables,
            'metadata': metadata
        }

    def _parse_sections(self, text: str, page_num: int) -> List[Dict]:
        """Parse sections from text"""
        sections = []
        lines = text.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to match section patterns
            section_match = None
            for pattern in self.section_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    section_match = match
                    break

            if section_match:
                # Save previous section
                if current_section:
                    sections.append(current_section)

                # Start new section
                if len(section_match.groups()) >= 3:
                    section_number = section_match.group(1)
                    section_title = section_match.group(3)
                else:
                    section_number = section_match.group(1)
                    section_title = section_match.group(2) if len(section_match.groups()) > 1 else ""

                current_section = {
                    'number': section_number,
                    'title': section_title.strip(),
                    'content': '',
                    'page': page_num,
                    'level': self._calculate_level(section_number)
                }
            elif current_section:
                # Add to current section content
                current_section['content'] += line + '\n'

        # Don't forget the last section
        if current_section:
            sections.append(current_section)

        return sections

    def _calculate_level(self, section_number: str) -> int:
        """Calculate hierarchical level from section number"""
        # Count dots for numbered sections (1.2.3 -> level 3)
        if '.' in section_number:
            return len(section_number.split('.'))
        # Single number or letter -> level 1
        return 1

    def _build_hierarchy(self, sections: List[Dict]) -> List[Dict]:
        """Build parent-child relationships between sections"""
        for i, section in enumerate(sections):
            section['parent_number'] = None

            # Find parent by looking backwards for lower level
            for j in range(i - 1, -1, -1):
                if sections[j]['level'] < section['level']:
                    # Check if this is actually the parent
                    if section['number'].startswith(sections[j]['number']):
                        section['parent_number'] = sections[j]['number']
                        break

        return sections

    def _extract_from_tables(self, tables: List[Dict]) -> Dict:
        """Extract financial metadata from tables"""
        metadata = {}

        # Keywords to look for in table cells
        value_keywords = {
            'estimated_value': ['estimated cost', 'estimated value', 'contract value', 'tender value', 'project cost'],
            'emd_amount': ['emd', 'earnest money', 'bid security', 'security deposit'],
            'submission_deadline': ['last date', 'submission date', 'closing date', 'bid submission'],
            'technical_opening': ['technical opening', 'technical bid opening'],
            'financial_opening': ['financial opening', 'financial bid opening', 'price bid opening'],
            'completion_period': ['completion period', 'contract period', 'duration', 'time for completion'],
        }

        for table_data in tables:
            table = table_data.get('data', [])
            if not table or len(table) < 2:
                continue

            # Search for key-value pairs in table rows
            for row in table:
                if not row or len(row) < 2:
                    continue

                # Clean and join all cells in the row
                row_text = ' '.join([str(cell).strip() if cell else '' for cell in row])
                row_lower = row_text.lower()

                # Check each metadata type
                for meta_key, keywords in value_keywords.items():
                    if meta_key in metadata:  # Already found
                        continue

                    # Check if any keyword is in this row
                    for keyword in keywords:
                        if keyword in row_lower:
                            # Try to find the value in subsequent cells
                            for i, cell in enumerate(row):
                                if not cell:
                                    continue

                                cell_str = str(cell).strip()

                                # Extract numeric values
                                if meta_key in ['estimated_value', 'emd_amount']:
                                    # Look for numbers with optional Lakh/Crore/Million
                                    import re
                                    # Pattern: Rs. 50.00 Lakh or 5,00,000 or 50.50 Crore
                                    amount_match = re.search(r'(?:Rs\.?|INR|₹)?\s*([\d,\.]+)\s*(Lakh|Crore|Million)?', cell_str, re.IGNORECASE)
                                    if amount_match:
                                        try:
                                            value = float(amount_match.group(1).replace(',', ''))
                                            multiplier_text = amount_match.group(2)

                                            # Apply multipliers
                                            if multiplier_text:
                                                mult_lower = multiplier_text.lower()
                                                if mult_lower == 'crore':
                                                    value *= 10000000  # 1 Crore = 10 Million
                                                elif mult_lower == 'lakh':
                                                    value *= 100000  # 1 Lakh = 100,000
                                                elif mult_lower == 'million':
                                                    value *= 1000000

                                            # Only accept reasonable amounts (> 1000)
                                            if value >= 1000:
                                                metadata[meta_key] = value
                                                break
                                        except:
                                            pass

                                # Extract dates
                                elif meta_key in ['submission_deadline', 'technical_opening', 'financial_opening']:
                                    date_match = re.search(r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', cell_str)
                                    if date_match:
                                        metadata[meta_key] = date_match.group(0)
                                        break

                                # Extract period (days/months)
                                elif meta_key == 'completion_period':
                                    period_match = re.search(r'(\d+)\s*(?:days|months|weeks)', cell_str.lower())
                                    if period_match:
                                        metadata[meta_key] = period_match.group(1)
                                        break

        return metadata

    def _classify_table(self, table: List[List]) -> str:
        """Classify table type based on headers"""
        if not table or len(table) < 2:
            return 'UNKNOWN'

        header_text = ' '.join([str(cell).lower() for cell in table[0] if cell])

        # Check for BOQ table
        boq_indicators = ['item', 'description', 'quantity', 'unit', 'rate', 'amount']
        if sum(1 for indicator in boq_indicators if indicator in header_text) >= 3:
            return 'BOQ'

        # Check for eligibility table
        if any(keyword in header_text for keyword in ['eligibility', 'qualification', 'criteria']):
            return 'ELIGIBILITY'

        # Check for commercial table
        if any(keyword in header_text for keyword in ['payment', 'milestone', 'schedule']):
            return 'COMMERCIAL'

        return 'GENERAL'

    def _extract_metadata(self, full_text: str, sections: List[Dict], tables: List[Dict]) -> Dict:
        """Extract key metadata from tender document — broad real-world patterns."""
        metadata = {}

        # 1. Table-based extraction first (most reliable)
        table_metadata = self._extract_from_tables(tables)
        metadata.update(table_metadata)

        # Helper: parse Indian amounts
        def parse_amount(val_str, unit_str=''):
            try:
                val = float(val_str.replace(',', ''))
                unit = (unit_str or '').lower()
                if 'crore' in unit or unit == 'cr':
                    val *= 10_000_000
                elif 'lakh' in unit or 'lac' in unit:
                    val *= 100_000
                elif 'million' in unit:
                    val *= 1_000_000
                return val
            except Exception:
                return None

        # 2. Reference number
        if not metadata.get('reference_number'):
            for pat in [
                r'(?:Tender|NIT|RFP|RFQ|EOI)\s*(?:No\.?|Number|Ref)[.:\s]+([A-Z0-9][A-Z0-9\-_/\.]{3,40})',
                r'(?:Notice\s+Inviting\s+Tender|NIT)\s*(?:No\.?|Number)[.:\s]+([A-Z0-9][A-Z0-9\-_/\.]{3,40})',
                r'(?:Advt\.?\s*No\.?|Advertisement\s*No\.?)[.:\s]+([A-Z0-9][A-Z0-9\-_/\.]{3,40})',
            ]:
                m = re.search(pat, full_text, re.IGNORECASE)
                if m:
                    metadata['reference_number'] = m.group(1).strip()
                    break

        # 3. Estimated value (many real-world phrasings)
        if not metadata.get('estimated_value'):
            for pat in [
                r'(?:estimated|approximate|total|contract|tender|project)\s*(?:cost|value|amount)[^\n]{0,60}'
                r'(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|cr\b|lakh|lac\b|million)?',
                r'(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh)\s*(?:only|approximately|rupees)',
                r'(?:NIT|work)\s*(?:value|amount|cost)[^\n]{0,30}(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh)?',
                r'(?:put\s+to\s+tender|tender\s+for)[^\n]{0,60}(?:Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh)?',
            ]:
                m = re.search(pat, full_text, re.IGNORECASE)
                if m:
                    v = parse_amount(m.group(1), m.group(2) if len(m.groups()) > 1 else '')
                    if v and v >= 1000:
                        metadata['estimated_value'] = v
                        break

        # 4. EMD / Earnest Money / Bid Security
        if not metadata.get('emd_amount'):
            emd_amounts = []
            for pat in [
                r'(?:EMD|earnest\s+money\s+deposit|earnest\s+money|bid\s+security|tender\s+security)'
                r'[^\n]{0,80}(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:/--?|/--)?\s*(crore|lakh|million)?',
                r'(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:/--?|/--)?\s*(crore|lakh|million)?'
                r'[^\n]{0,80}(?:EMD|earnest\s+money|bid\s+security)',
            ]:
                # Find all matches, not just first
                for m in re.finditer(pat, full_text, re.IGNORECASE):
                    v = parse_amount(m.group(1), m.group(2) if len(m.groups()) > 1 else '')
                    if v and v >= 100:
                        emd_amounts.append(v)
            # Use the largest EMD amount found (avoid placeholders)
            if emd_amounts:
                metadata['emd_amount'] = max(emd_amounts)

        # 5. Submission deadline (many date formats)
        if not metadata.get('submission_deadline'):
            date_pat = r'(\d{1,2}[./-]\d{1,2}[./-](?:\d{4}|\d{2}))'
            deadline_kw = [
                'last date', 'due date', 'closing date', 'submission date',
                'submission deadline', 'bid submission', 'receipt of bids',
                'last date of submission', 'tender closing date',
            ]
            for kw in deadline_kw:
                idx = full_text.lower().find(kw)
                if idx != -1:
                    window = full_text[idx: idx + 300]
                    dm = re.search(date_pat, window)
                    if dm:
                        metadata['submission_deadline'] = dm.group(1)
                        break

        # 6. Completion period
        if not metadata.get('completion_period'):
            # First try text numbers like "one year", "two months"
            text_period_patterns = [
                r'(?:time\s+for\s+completion|completion\s+period|contract\s+duration|'
                r'project\s+duration|period\s+of\s+completion|contract\s+period)'
                r'[^\n]{0,80}(one|two|three|four|five|six|seven|eight|nine|ten|twelve)\s*(year|years|month|months)',
            ]
            text_to_num = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'twelve': 12
            }
            for pat in text_period_patterns:
                m = re.search(pat, full_text, re.IGNORECASE)
                if m:
                    text_num = m.group(1).lower()
                    unit = m.group(2).lower()
                    val = text_to_num.get(text_num, 0)
                    if val > 0:
                        if 'month' in unit:
                            val *= 30
                        elif 'year' in unit:
                            val *= 365
                        metadata['completion_period'] = str(val)
                        break

            # Fall back to numeric patterns if text pattern didn't match
            if not metadata.get('completion_period'):
                for pat in [
                    r'(?:time\s+for\s+completion|completion\s+period|contract\s+duration|'
                    r'project\s+duration|period\s+of\s+completion|contract\s+period)'
                    r'[^\n]{0,60}(\d+)\s*(days?|months?|weeks?|years?)',
                    r'(\d+)\s*(months?|days?)\s+(?:from\s+date\s+of|from\s+award|from\s+commencement)',
                ]:
                    m = re.search(pat, full_text, re.IGNORECASE)
                    if m:
                        val = int(m.group(1 if 'months' in pat or 'days' not in m.group(0)[:20] else 1))
                        # Standardise: store as days
                        unit = m.group(2).lower() if len(m.groups()) > 1 else 'days'
                        if 'month' in unit:
                            val *= 30
                        elif 'year' in unit:
                            val *= 365
                        elif 'week' in unit:
                            val *= 7
                        metadata['completion_period'] = str(val)
                        break

        # 7. Technical & financial opening dates
        # Only store if the keyword appears in its own dedicated context AND
        # the date found is different from submission_deadline (to avoid false copies)
        date_pat = r'(\d{1,2}[./-]\d{1,2}[./-](?:\d{4}|\d{2}))'
        submission_date_str = metadata.get('submission_deadline', '')
        for field, kws in [
            ('technical_opening', ['technical bid opening', 'technical opening', 'opening of technical bid']),
            ('financial_opening', ['financial bid opening', 'financial opening', 'price bid opening', 'commercial bid opening']),
        ]:
            if not metadata.get(field):
                for kw in kws:
                    idx = full_text.lower().find(kw)
                    if idx != -1:
                        window = full_text[idx: idx + 300]
                        dm = re.search(date_pat, window)
                        if dm:
                            found_date = dm.group(1)
                            # Don't store if it's the same as submission_deadline
                            if found_date != submission_date_str:
                                metadata[field] = found_date
                            break

        return metadata

    def extract_boq_items(self, tables: List[Dict]) -> List[Dict]:
        """Extract BOQ items from tables (BOQ-classified or any table with description-like columns)"""
        boq_items = []

        # Accept BOQ tables first, then fall back to any GENERAL table that looks like work items
        accepted_types = {'BOQ', 'GENERAL', 'ELIGIBILITY', 'COMMERCIAL', 'UNKNOWN'}

        for table_info in tables:
            if table_info['type'] not in accepted_types:
                continue

            table = table_info['data']
            if not table or len(table) < 2:
                continue

            headers = [str(h).lower() if h else '' for h in table[0]]
            header_text = ' '.join(headers)

            # Find column indices with flexible matching
            item_col = self._find_column(headers, ['item', 'sr', 's.no', 'sl no', 'sno', 'no.', '#', 's/n', 'sl.', 'serial'])
            desc_col = self._find_column(headers, ['description', 'particulars', 'work', 'criteria', 'requirement', 'detail', 'item description', 'scope'])
            qty_col = self._find_column(headers, ['quantity', 'qty', 'qtty', 'qnty', 'quan'])
            unit_col = self._find_column(headers, ['unit', 'uom', 'measure'])
            rate_col = self._find_column(headers, ['rate', 'unit rate', 'unit price', 'price'])
            amount_col = self._find_column(headers, ['amount', 'total', 'value', 'cost', 'estimated cost', 'price'])

            # Skip tables with no usable description column
            if desc_col is None and item_col is None:
                continue

            # Extract items
            for row in table[1:]:
                if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                    continue

                item = {}

                if item_col is not None and item_col < len(row) and row[item_col]:
                    item['item_code'] = self._clean_text(str(row[item_col]))[:500]  # Limit to 500 chars

                if desc_col is not None and desc_col < len(row) and row[desc_col]:
                    desc = self._clean_text(str(row[desc_col]))
                    if desc and len(desc) > 3:
                        item['description'] = desc
                elif item_col is not None and item_col < len(row) and row[item_col]:
                    # Use item column as description if no desc column
                    item['description'] = self._clean_text(str(row[item_col]))

                # Extract quantity with better number parsing
                if qty_col is not None and qty_col < len(row) and row[qty_col]:
                    qty_str = str(row[qty_col]).strip()
                    if qty_str and qty_str.lower() not in ['', 'nil', 'n/a', '-', 'na']:
                        try:
                            # Remove commas and any non-numeric chars except decimal point
                            clean_qty = re.sub(r'[^\d.]', '', qty_str)
                            if clean_qty:
                                item['quantity'] = float(clean_qty)
                        except Exception:
                            pass

                # Extract unit
                if unit_col is not None and unit_col < len(row) and row[unit_col]:
                    unit_str = self._clean_text(str(row[unit_col]))
                    if unit_str and unit_str.lower() not in ['', 'nil', 'n/a', '-', 'na']:
                        item['unit'] = unit_str[:50]  # Limit unit length

                # Extract rate with better number parsing
                if rate_col is not None and rate_col < len(row) and row[rate_col]:
                    rate_str = str(row[rate_col]).strip()
                    if rate_str and rate_str.lower() not in ['', 'nil', 'n/a', '-', 'na']:
                        try:
                            # Remove currency symbols, commas, and extract number
                            clean_rate = re.sub(r'[^\d.]', '', rate_str)
                            if clean_rate:
                                item['rate'] = float(clean_rate)
                        except Exception:
                            pass

                # Extract amount with currency handling
                if amount_col is not None and amount_col < len(row) and row[amount_col]:
                    amount_str = str(row[amount_col]).strip()
                    if amount_str and amount_str.lower() not in ['', 'nil', 'n/a', '-', 'na']:
                        try:
                            # Handle Indian currency formats (Rs., Lakh, Crore)
                            amount_val = self._parse_currency_value(amount_str)
                            if amount_val is not None:
                                item['amount'] = amount_val
                        except Exception:
                            pass

                # Fallback: if we have description but missing qty/amount, try to extract from row data
                if 'description' in item and item['description']:
                    # If quantity is missing, look for numeric values in the row
                    if 'quantity' not in item and len(row) > 2:
                        for cell in row:
                            if cell and str(cell).strip():
                                cell_str = str(cell).strip()
                                # Skip if it's the item code or description
                                if cell_str == item.get('item_code') or cell_str == item.get('description'):
                                    continue
                                # Try to parse as quantity (small numbers, might have decimals)
                                clean_val = re.sub(r'[^\d.]', '', cell_str)
                                if clean_val and '.' in clean_val:
                                    try:
                                        val = float(clean_val)
                                        if val < 100000 and 'quantity' not in item:  # Likely a quantity
                                            item['quantity'] = val
                                            break
                                    except:
                                        pass

                    # If amount is missing, look for larger numeric values
                    if 'amount' not in item and len(row) > 2:
                        for cell in row:
                            if cell and str(cell).strip():
                                cell_str = str(cell).strip()
                                # Try to parse as currency
                                amount_val = self._parse_currency_value(cell_str)
                                if amount_val and amount_val >= 100:  # Likely an amount
                                    item['amount'] = amount_val
                                    break

                    boq_items.append(item)

        return boq_items

    def extract_scope_from_text(self, full_text: str) -> List[Dict]:
        """
        Fallback: extract work scope / eligibility criteria items from plain text
        when no BOQ tables are found.
        """
        items = []
        lines = full_text.split('\n')

        # Bullet / numbered item pattern
        bullet_pat = re.compile(
            r'^\s*(?:\d+[\.\)]\s+|\([a-zA-Z]\)\s+|[a-z]\.\s+|[-\u2022*]\s+|[ivxlc]+\.\s+)'
            r'(.{15,300})$',
            re.IGNORECASE,
        )
        scope_keywords = [
            'shall', 'must', 'should', 'required', 'minimum', 'experience',
            'turnover', 'certificate', 'similar work', 'completed', 'provide',
            'supply', 'install', 'construct', 'fabricate', 'design', 'commission',
        ]
        section_triggers = [
            'scope of work', 'scope of supply', 'eligibility', 'qualification',
            'technical criteria', 'financial criteria', 'experience criteria',
            'bill of quantities', 'schedule of work', 'work description',
        ]

        in_scope_section = False
        item_counter = 1
        seen = set()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            lower = stripped.lower()

            if any(trigger in lower for trigger in section_triggers):
                in_scope_section = True
                continue

            if not in_scope_section:
                continue

            m = bullet_pat.match(line)
            if m:
                desc = m.group(1).strip().rstrip('.')
                if len(desc) < 15 or desc.lower() in seen:
                    continue
                if not any(kw in desc.lower() for kw in scope_keywords):
                    continue
                seen.add(desc.lower())
                items.append({'item_code': str(item_counter), 'description': desc})
                item_counter += 1
                if item_counter > 30:
                    break

        return items

    def extract_pipe_table_boq(self, full_text: str) -> List[Dict]:
        """
        Parse BOQ from pipe-delimited text tables (e.g. Word/plain-text PDFs).
        Handles lines like: 1 | Earthwork excavation... | 4500 | CUM | 280 | 12,60,000
        Active inside any BOQ/Bill of Quantities section.
        """
        # Normalise CID artifacts: (cid:NNN) → strip them out
        clean_text = re.sub(r'\(cid:\d+\)', '', full_text)

        items = []
        lines = clean_text.split('\n')

        boq_triggers = [
            'bill of quantities', 'boq', 'schedule of quantities',
            'price schedule', 'work items', 'quantity schedule',
        ]
        end_triggers = [
            'section 5', 'section 6', 'section 7', 'commercial conditions',
            'special conditions', 'instructions to bidders',
        ]

        in_boq = False
        header_found = False
        col_item = col_desc = col_qty = col_unit = col_rate = col_amount = None

        for line in lines:
            stripped = line.strip()
            lower = stripped.lower()

            # Detect BOQ section start
            if not in_boq:
                if any(t in lower for t in boq_triggers):
                    in_boq = True
                continue

            # Detect section end
            if any(t in lower for t in end_triggers):
                break

            # Skip lines without pipe separator
            if '|' not in stripped:
                continue

            # Skip separator lines: only dashes, unicode box-drawing, spaces, pipes
            stripped_of_separators = re.sub(r'[\-\=\u2500-\u257F\s|]', '', stripped)
            if not stripped_of_separators:
                continue

            cols = [c.strip() for c in stripped.split('|')]
            # Drop empty leading/trailing cells
            if cols and cols[0] == '':
                cols = cols[1:]
            if cols and cols[-1] == '':
                cols = cols[:-1]
            if len(cols) < 3:
                continue

            joined = ' '.join(cols).lower()

            # Detect header row
            if not header_found and ('description' in joined or 'qty' in joined or 'descrip' in joined):
                header_found = True
                headers = [c.lower() for c in cols]
                col_item   = self._find_column(headers, ['item', 'sr', 'no', 's.no', '#'])
                col_desc   = self._find_column(headers, ['description', 'descrip', 'particulars', 'work'])
                col_qty    = self._find_column(headers, ['qty', 'quantity'])
                col_unit   = self._find_column(headers, ['unit', 'uom'])
                col_rate   = self._find_column(headers, ['rate', 'unit rate', 'unit price'])
                col_amount = self._find_column(headers, ['amount', 'total', 'value', 'cost'])
                continue

            if not header_found:
                # No header yet — try auto-detect by shape: first col numeric, last col looks like amount
                if re.match(r'^\d+$', cols[0]) and len(cols) >= 4:
                    # Assume: item | desc | qty | unit | rate | amount
                    col_item, col_desc, col_qty, col_unit = 0, 1, 2, 3
                    col_rate   = 4 if len(cols) > 4 else None
                    col_amount = 5 if len(cols) > 5 else (4 if len(cols) > 4 else None)
                    header_found = True
                else:
                    continue

            def _get(idx):
                return cols[idx].strip() if idx is not None and idx < len(cols) else ''

            item_code = _get(col_item)
            desc      = _get(col_desc)

            # Skip continuation rows (no item code and no meaningful desc)
            if not item_code and (not desc or len(desc) < 5):
                continue

            # Skip rows where item_code is not a number (total/subtotal rows like "TOTAL")
            if item_code and not re.match(r'^\d+', item_code):
                continue

            item = {}
            if item_code:
                item['item_code'] = item_code
            if desc and len(desc) > 3:
                item['description'] = desc

            if 'description' not in item:
                continue

            qty_str = _get(col_qty)
            if qty_str:
                clean = re.sub(r'[^\d.]', '', qty_str)
                if clean:
                    try:
                        item['quantity'] = float(clean)
                    except ValueError:
                        pass

            unit_str = _get(col_unit)
            if unit_str and unit_str.upper() not in ('', '-', 'NA', 'N/A'):
                item['unit'] = unit_str

            rate_str = _get(col_rate)
            if rate_str:
                rate_val = self._parse_currency_value(rate_str)
                if rate_val and rate_val > 0:
                    item['rate'] = rate_val

            amount_str = _get(col_amount)
            if amount_str:
                amount_val = self._parse_currency_value(amount_str)
                if amount_val and amount_val > 0:
                    item['amount'] = amount_val

            items.append(item)

        return items

    def _parse_currency_value(self, value_str: str) -> float:
        """Parse currency value handling Rs., Lakh, Crore, etc."""
        if not value_str:
            return None

        value_str = str(value_str).strip().lower()

        # Remove currency symbols
        value_str = value_str.replace('rs.', '').replace('rs', '').replace('₹', '').replace('inr', '')
        value_str = value_str.strip()

        # Check for multipliers
        multiplier = 1
        if 'crore' in value_str or 'cr' in value_str:
            multiplier = 10000000
            value_str = value_str.replace('crore', '').replace('cr', '')
        elif 'lakh' in value_str or 'lac' in value_str:
            multiplier = 100000
            value_str = value_str.replace('lakh', '').replace('lac', '')
        elif 'million' in value_str:
            multiplier = 1000000
            value_str = value_str.replace('million', '')
        elif 'thousand' in value_str or 'k' in value_str:
            multiplier = 1000
            value_str = value_str.replace('thousand', '').replace('k', '')

        # Extract numeric value (remove commas and non-numeric except decimal)
        clean_value = re.sub(r'[^\d.]', '', value_str.strip())

        if clean_value:
            try:
                return float(clean_value) * multiplier
            except:
                pass

        return None

    def extract_fixed_width_boq(self, full_text: str) -> List[Dict]:
        """
        Extract BOQ from fixed-width text tables (space-separated columns).
        Handles both properly formatted lines AND concatenated BOQ items on single lines.
        """
        items = []

        # Find BOQ section
        boq_triggers = ['bill of quantities', 'boq', 'schedule a']
        boq_start = -1
        for trigger in boq_triggers:
            if trigger in full_text.lower():
                boq_start = full_text.lower().index(trigger)
                break

        if boq_start == -1:
            return items

        # Extract BOQ text (up to section 6 or 10000 chars)
        end_triggers = ['section 6', 'section 7', 'terms and conditions']
        boq_end = boq_start + 10000
        for trigger in end_triggers:
            idx = full_text.lower().find(trigger, boq_start)
            if idx != -1:
                boq_end = idx
                break

        boq_text = full_text[boq_start:boq_end]

        # Split on item code patterns: A.1, A.2, B.1, C.1, D.1, E.1, etc.
        # Pattern: Letter.Number at word boundary
        item_pattern = r'([A-E]\.(?:\d+))\s+'
        segments = re.split(item_pattern, boq_text)

        # Process segments in pairs (item_code, content)
        for i in range(1, len(segments), 2):
            if i + 1 >= len(segments):
                break

            item_code = segments[i].strip()
            content = segments[i + 1].strip()

            # Extract description and numbers
            # Numbers at the end: usually Qty, Rate, Amount
            numbers = re.findall(r'\d+(?:\.\d+)?', content)

            if len(numbers) < 2:
                continue

            # Extract unit (2-10 letter word before numbers)
            unit_match = re.search(r'\b([A-Za-z]{1,10}\.?)\s+\d', content)
            unit = unit_match.group(1) if unit_match else ''

            # Description is everything before the unit/numbers
            if unit:
                desc_end = content.find(unit)
                description = content[:desc_end].strip()
            else:
                # Find where numbers start
                first_num_pos = re.search(r'\s+\d+\s+\d', content)
                if first_num_pos:
                    description = content[:first_num_pos.start()].strip()
                else:
                    description = content[:max(0, len(content) - 50)].strip()

            # Clean description
            description = self._clean_text(description)

            if len(description) < 3:
                continue

            item = {
                'item_code': item_code,
                'description': description
            }

            # Extract numbers: last 3 are typically Qty, Rate, Amount
            if len(numbers) >= 3:
                try:
                    item['quantity'] = float(numbers[-3])
                    item['rate'] = float(numbers[-2])
                    item['amount'] = float(numbers[-1])
                except:
                    pass
            elif len(numbers) >= 2:
                try:
                    item['quantity'] = float(numbers[-2])
                    item['amount'] = float(numbers[-1])
                except:
                    pass

            if unit:
                item['unit'] = unit

            items.append(item)

        return items

    def _find_column(self, headers: List[str], keywords: List[str]) -> int:
        """Find column index by matching keywords - flexible matching"""
        for i, header in enumerate(headers):
            # Clean header: remove extra spaces, newlines, special chars
            clean_header = re.sub(r'\s+', ' ', header.lower().strip())
            clean_header = re.sub(r'[^\w\s]', '', clean_header)  # Remove punctuation

            for keyword in keywords:
                clean_keyword = keyword.lower().strip()
                # Match if keyword is in header or header is in keyword
                if clean_keyword in clean_header or clean_header in clean_keyword:
                    return i
                # Also try exact match without spaces
                if clean_header.replace(' ', '') == clean_keyword.replace(' ', ''):
                    return i
        return None


class BOQClassifier:
    """Classify BOQ items into Civil/Mechanical/MEP categories"""

    def __init__(self):
        self.category_keywords = {
            'CIVIL': [
                'earthwork', 'excavation', 'concrete', 'rcc', 'pcc',
                'foundation', 'masonry', 'brickwork', 'plastering',
                'flooring', 'roofing', 'steel', 'reinforcement',
                'formwork', 'shuttering', 'backfilling', 'compaction'
            ],
            'MECHANICAL': [
                'fabrication', 'piping', 'machinery', 'equipment',
                'pump', 'valve', 'fitting', 'welding', 'structural steel',
                'crane', 'hoist', 'conveyor', 'tank', 'vessel'
            ],
            'ELECTRICAL': [
                'electrical', 'cable', 'wiring', 'panel', 'switchgear',
                'transformer', 'lighting', 'conduit', 'mcb', 'mccb',
                'earthing', 'motor', 'generator', 'ups', 'battery'
            ],
            'PLUMBING': [
                'plumbing', 'drainage', 'sewerage', 'water supply',
                'sanitary', 'fixture', 'pipe', 'faucet', 'tap',
                'wc', 'washbasin', 'gutter', 'downpipe'
            ],
            'HVAC': [
                'hvac', 'air conditioning', 'ventilation', 'ahu',
                'fcu', 'duct', 'grille', 'diffuser', 'chiller',
                'cooling', 'heating', 'vrf', 'vav'
            ],
        }

    def classify(self, description: str) -> str:
        """Classify BOQ item based on description"""
        description_lower = description.lower()

        # Score each category
        scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            scores[category] = score

        # Get best match
        if max(scores.values()) > 0:
            best_category = max(scores, key=scores.get)

            # Combine ELECTRICAL, PLUMBING, HVAC into MEP
            if best_category in ['ELECTRICAL', 'PLUMBING', 'HVAC']:
                return 'MEP'
            return best_category

        return 'OTHER'
