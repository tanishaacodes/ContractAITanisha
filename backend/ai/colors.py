"""
Business Unit Color Mapping
Gartner-style color coding for contract visualization
"""

# Business Unit to Color mapping (Material UI colors)
BU_COLORS = {
    "EPC": "#1976d2",           # Blue
    "Oil & Gas": "#d32f2f",     # Red
    "Defense": "#388e3c",        # Green
    "IT Services": "#f57c00",   # Orange
    "Manufacturing": "#7b1fa2",  # Purple
    "Construction": "#00796b",   # Teal
    "Healthcare": "#c2185b",     # Pink
    "Finance": "#455a64",        # Blue Grey
    "Consulting": "#5e35b1",     # Deep Purple
    "Energy": "#e64a19",         # Deep Orange
    "Telecom": "#0288d1",        # Light Blue
    "Automotive": "#303f9f",     # Indigo
    "Others": "#757575"          # Grey
}

def get_bu_color(business_unit: str):
    """
    Get color for a business unit

    Args:
        business_unit: Business unit name

    Returns:
        Hex color code
    """
    return BU_COLORS.get(business_unit, BU_COLORS["Others"])

def get_all_bu_colors():
    """
    Get all business unit colors for legend

    Returns:
        Dictionary of BU -> color mappings
    """
    return BU_COLORS.copy()

def get_bu_list():
    """
    Get list of all business units

    Returns:
        List of business unit names
    """
    return list(BU_COLORS.keys())
