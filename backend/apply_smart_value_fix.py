"""
Apply the smart contract value fix to views.py
This adds automatic fallback from contract_value to total_liability
"""

import re

# Read the file
with open('api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find the exposure analysis section
old_pattern = r'''        # Add exposure analysis if requested
        if include_exposure:
            exposure_engine = ExposureEngine\(\)
            # Use default value of 10 Crore if contract_value is not set
            default_value = "10 Crore"
            contract_value_str = contract\.contract_value or default_value
            contract_value = exposure_engine\.parse_contract_value\(contract_value_str\)

            logger\.info\(f"\[WHAT-IF\] Contract value string: '\{contract_value_str\}'"\)
            logger\.info\(f"\[WHAT-IF\] Parsed contract value: \{contract_value\}"\)

            if contract_value > 0:'''

new_code = '''        # Add exposure analysis if requested
        if include_exposure:
            logger.info(f"[WHAT-IF-EXPOSURE] ===== STARTING EXPOSURE CALCULATION =====")
            exposure_engine = ExposureEngine()

            # Smart contract value extraction: Try multiple sources
            contract_value = 0
            value_source = "none"

            # 1. Try contract_value field first
            if contract.contract_value and contract.contract_value not in ["Not set", "not set", ""]:
                contract_value = exposure_engine.parse_contract_value(contract.contract_value)
                value_source = f"contract_value: '{contract.contract_value}'"
                logger.info(f"[WHAT-IF-EXPOSURE] Using contract_value field: {contract_value}")

            # 2. Fallback to total_liability
            if contract_value == 0 and contract.total_liability and float(contract.total_liability) > 0:
                contract_value = float(contract.total_liability)
                value_source = f"total_liability: {contract.total_liability}"
                logger.info(f"[WHAT-IF-EXPOSURE] Using total_liability: {contract_value}")

            logger.info(f"[WHAT-IF-EXPOSURE] Final contract value: {contract_value} (from {value_source})")

            if contract_value > 0:'''

# Apply the replacement
content_new = re.sub(old_pattern, new_code, content, flags=re.DOTALL)

if content_new != content:
    print("✓ Pattern found and replaced")
    with open('api/views.py', 'w', encoding='utf-8') as f:
        f.write(content_new)
    print("✓ File updated successfully")
else:
    print("✗ Pattern not found - manual fix needed")
