"""
Network Health Scoring System.

Computes a weighted health score (0–100) based on detected issues.
Scoring is deterministic and explainable.

Category Weights:
- Routing:     30%
- Interface:   25%
- VLAN:        25%
- IP:          20%

Severity Deductions (per issue, from category's contribution):
- Critical: -15 points
- High:     -10 points
- Medium:    -5 points
- Low:       -2 points
"""

from typing import Any

# Category weights (must sum to 100)
CATEGORY_WEIGHTS = {
    "routing": 30,
    "interface": 25,
    "vlan": 25,
    "ip": 20,
}

# Which failure types map to which category
FAILURE_TYPE_CATEGORIES = {
    # Routing
    "missing_route": "routing",
    "no_default_gateway": "routing",

    # Interface
    "interface_admin_down": "interface",
    "interface_protocol_down": "interface",
    "interface_down": "interface",
    "physical_link_down": "interface",

    # VLAN
    "vlan_not_exists": "vlan",
    "native_vlan_not_exists": "vlan",
    "trunk_access_mismatch": "vlan",

    # IP
    "wrong_subnet_mask": "ip",
    "invalid_ip_config": "ip",
    "duplicate_ip": "ip",
}

# Per-issue severity deductions
SEVERITY_DEDUCTIONS = {
    "critical": 15,
    "high": 10,
    "medium": 5,
    "low": 2,
}


def calculate_health_score(issues: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate the network health score with full breakdown.

    Args:
        issues: List of issue dicts from the rule engine.

    Returns:
        Dict with total_score, category scores, and deduction log.
    """
    # Initialize each category at its max weight
    category_scores = {cat: weight for cat, weight in CATEGORY_WEIGHTS.items()}
    deductions = []

    for issue in issues:
        failure_type = issue.get("failure_type", "unknown")
        severity = issue.get("severity", "low")
        device = issue.get("device", "Unknown")
        interface = issue.get("interface", "N/A")

        # Map to category
        category = FAILURE_TYPE_CATEGORIES.get(failure_type, "ip")
        deduction = SEVERITY_DEDUCTIONS.get(severity, 2)

        # Apply deduction (don't go below 0 for any category)
        actual_deduction = min(deduction, category_scores[category])
        category_scores[category] -= actual_deduction

        deductions.append({
            "failure_type": failure_type,
            "severity": severity,
            "category": category,
            "deduction": actual_deduction,
            "device": device,
            "interface": interface,
            "reason": f"{severity.upper()} {failure_type.replace('_', ' ')} "
                      f"on {device} {interface}: -{actual_deduction} pts from {category}",
        })

    # Total score = sum of remaining category scores
    total_score = max(0, sum(category_scores.values()))

    # Calculate percentage scores for each category
    category_percentages = {}
    for cat, score in category_scores.items():
        max_score = CATEGORY_WEIGHTS[cat]
        pct = (score / max_score * 100) if max_score > 0 else 100
        category_percentages[cat] = round(pct, 1)

    return {
        "total_score": round(total_score, 1),
        "routing_score": category_percentages.get("routing", 100),
        "interface_score": category_percentages.get("interface", 100),
        "vlan_score": category_percentages.get("vlan", 100),
        "ip_score": category_percentages.get("ip", 100),
        "deductions": deductions,
        "category_raw": category_scores,
        "explanation": _generate_score_explanation(total_score, category_percentages, deductions),
    }


def _generate_score_explanation(
    total: float,
    categories: dict[str, float],
    deductions: list[dict[str, Any]],
) -> str:
    """Generate a human-readable explanation of the score."""
    if total >= 90:
        grade = "Excellent"
        summary = "The network is in great shape with minimal issues."
    elif total >= 70:
        grade = "Good"
        summary = "The network is functional but has some issues that should be addressed."
    elif total >= 50:
        grade = "Fair"
        summary = "The network has significant issues affecting connectivity."
    elif total >= 30:
        grade = "Poor"
        summary = "The network has critical problems that need immediate attention."
    else:
        grade = "Critical"
        summary = "The network is severely misconfigured and likely non-functional."

    explanation = f"Network Health: {grade} ({total}/100)\n\n{summary}\n\n"
    explanation += "Category Breakdown:\n"
    for cat, pct in categories.items():
        bar = "█" * int(pct // 10) + "░" * (10 - int(pct // 10))
        explanation += f"  {cat.capitalize():12s} {bar} {pct}%\n"

    if deductions:
        explanation += f"\n{len(deductions)} issue(s) detected:\n"
        for d in deductions[:10]:  # Show first 10
            explanation += f"  • {d['reason']}\n"
        if len(deductions) > 10:
            explanation += f"  ... and {len(deductions) - 10} more\n"

    return explanation
