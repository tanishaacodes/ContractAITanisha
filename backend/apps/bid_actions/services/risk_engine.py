"""
Risk Propagation Engine
Models risk cascade across departments using DFS traversal
"""
from typing import Dict, Set
from apps.bid_actions.models import ActionItem, RiskPropagation


# Predefined department dependency chains for construction projects
# Civil → Mechanical → Electrical → MEP → Finance
DEPARTMENT_CASCADE_RULES = {
    'Civil': [
        {'to': 'Mechanical', 'weight': 0.7},
        {'to': 'Planning', 'weight': 0.5}
    ],
    'Mechanical': [
        {'to': 'Electrical', 'weight': 0.6},
        {'to': 'MEP', 'weight': 0.5}
    ],
    'Electrical': [
        {'to': 'MEP', 'weight': 0.5},
        {'to': 'Finance', 'weight': 0.4}
    ],
    'MEP': [
        {'to': 'QA/QC', 'weight': 0.4},
        {'to': 'HSE', 'weight': 0.3}
    ],
    'Legal': [
        {'to': 'Finance', 'weight': 0.7},
        {'to': 'Procurement', 'weight': 0.4}
    ],
    'Planning': [
        {'to': 'Procurement', 'weight': 0.5},
        {'to': 'Finance', 'weight': 0.4}
    ],
    'Procurement': [
        {'to': 'Finance', 'weight': 0.5}
    ],
    'HSE': [
        {'to': 'QA/QC', 'weight': 0.4}
    ],
}


def propagate_department_risks(tender_id: str) -> Dict[str, float]:
    """
    Calculate propagated risk scores for each department

    Args:
        tender_id: UUID of tender

    Returns:
        Dict mapping department name to propagated risk score
    """
    # Get all actions for this tender grouped by department
    actions = ActionItem.objects.filter(tender_id=tender_id).select_related('department')

    # Calculate average risk per department
    dept_risk_map: Dict[str, float] = {}
    dept_action_count: Dict[str, int] = {}

    for action in actions:
        dept_name = action.department.name
        if dept_name not in dept_risk_map:
            dept_risk_map[dept_name] = 0
            dept_action_count[dept_name] = 0

        dept_risk_map[dept_name] += action.risk_score
        dept_action_count[dept_name] += 1

    # Calculate averages
    for dept in dept_risk_map:
        if dept_action_count[dept] > 0:
            dept_risk_map[dept] /= dept_action_count[dept]

    # Propagate risks using DFS
    propagated_risk: Dict[str, float] = dept_risk_map.copy()
    visited: Set[str] = set()

    def dfs(dept_name: str, accumulated_risk: float):
        """DFS traversal for risk cascade"""
        if dept_name in visited:
            return
        visited.add(dept_name)

        edges = DEPARTMENT_CASCADE_RULES.get(dept_name, [])

        for edge in edges:
            target_dept = edge['to']
            weight = edge['weight']
            propagated = accumulated_risk * weight

            if target_dept in propagated_risk:
                # Add propagated risk (capped at 0.99)
                propagated_risk[target_dept] = min(
                    0.99,
                    propagated_risk[target_dept] + propagated
                )

            # Continue cascade
            dfs(target_dept, propagated)

    # Start DFS from high-risk departments
    sorted_depts = sorted(dept_risk_map.items(), key=lambda x: x[1], reverse=True)
    for dept_name, base_risk in sorted_depts:
        if dept_name not in visited:
            dfs(dept_name, base_risk)

    return propagated_risk


def create_risk_propagation_edges(tender_id: str) -> int:
    """
    Create RiskPropagation relationships based on department cascade rules

    Args:
        tender_id: UUID of tender

    Returns:
        Number of edges created
    """
    actions = ActionItem.objects.filter(tender_id=tender_id).select_related('department')

    # Group actions by department
    dept_actions: Dict[str, list] = {}
    for action in actions:
        dept_name = action.department.name
        if dept_name not in dept_actions:
            dept_actions[dept_name] = []
        dept_actions[dept_name].append(action)

    edges_created = 0

    # Create edges based on rules
    for source_dept, edges in DEPARTMENT_CASCADE_RULES.items():
        if source_dept not in dept_actions:
            continue

        for edge in edges:
            target_dept = edge['to']
            weight = edge['weight']

            if target_dept not in dept_actions:
                continue

            # Create edges from each source action to each target action
            for source_action in dept_actions[source_dept]:
                for target_action in dept_actions[target_dept]:
                    # Skip if edge already exists
                    if not RiskPropagation.objects.filter(
                        source_action=source_action,
                        target_action=target_action
                    ).exists():
                        RiskPropagation.objects.create(
                            source_action=source_action,
                            target_action=target_action,
                            propagation_weight=weight
                        )
                        edges_created += 1

    return edges_created


def calculate_action_delay_impact(action: ActionItem) -> int:
    """
    Predict delay impact in days based on risk, complexity, and dependencies

    Args:
        action: ActionItem instance

    Returns:
        Estimated delay in days
    """
    # Base delay by department (typical lead times)
    base_delays = {
        'Civil': 14,
        'Mechanical': 10,
        'Electrical': 8,
        'MEP': 7,
        'Legal': 5,
        'Finance': 3,
        'HSE': 4,
        'Planning': 6,
        'Procurement': 12,
        'QA/QC': 5,
        'Signaling': 10,
    }

    base = base_delays.get(action.department.name, 7)

    # Adjust for risk and complexity
    risk_multiplier = 1 + action.risk_score
    complexity_multiplier = 1 + action.complexity_score

    # Adjust for dependency count
    dependency_count = action.depends_on.count()
    dependency_factor = 1 + (dependency_count * 0.02)

    delay = base * risk_multiplier * complexity_multiplier * dependency_factor

    return round(delay)


def get_critical_path_actions(tender_id: str) -> list:
    """
    Identify actions on critical path (highest delay risk)

    Args:
        tender_id: UUID of tender

    Returns:
        List of ActionItem instances on critical path
    """
    actions = ActionItem.objects.filter(
        tender_id=tender_id
    ).prefetch_related('depends_on')

    # Calculate delay for each action
    action_delays = []
    for action in actions:
        delay = calculate_action_delay_impact(action)
        action_delays.append((action, delay))

    # Sort by delay (descending)
    action_delays.sort(key=lambda x: x[1], reverse=True)

    # Return top 20% as critical path
    critical_count = max(1, len(action_delays) // 5)
    critical_actions = [a[0] for a in action_delays[:critical_count]]

    return critical_actions
