"""
Deterministic troubleshooting assistant helpers.

Builds evidence coverage, confidence, and an ordered fix plan from
parsed CLI captures and rule-engine issues.
"""

from collections import defaultdict
from typing import Any
import re


COMMAND_CATALOG = [
    {
        "key": "running_config",
        "label": "show running-config",
        "weight": 35,
        "why": "Needed for shutdown, switchport, VLAN, and routing protocol checks.",
        "recommendation": "Capture the full running configuration from each relevant device.",
    },
    {
        "key": "ip_interface_brief",
        "label": "show ip interface brief",
        "weight": 25,
        "why": "Confirms interface IPs, admin state, and protocol state.",
        "recommendation": "Run this on routers and Layer 3 switches to validate live interface status.",
    },
    {
        "key": "ip_route",
        "label": "show ip route",
        "weight": 20,
        "why": "Required for default-route and reachability checks.",
        "recommendation": "Run this on every router involved in the path you are troubleshooting.",
    },
    {
        "key": "vlan_brief",
        "label": "show vlan brief",
        "weight": 20,
        "why": "Validates VLAN existence and access-port assignments on switches.",
        "recommendation": "Run this on switches when VLAN or trunking issues are suspected.",
    },
]


FAILURE_TYPE_PRIORITY = {
    "duplicate_ip": {
        "weight": 100,
        "title": "Resolve duplicate IP conflicts first",
        "summary": "Duplicate IPs create inconsistent reachability and ARP instability.",
    },
    "invalid_ip_config": {
        "weight": 95,
        "title": "Correct invalid IP addressing",
        "summary": "Broken addressing prevents the interface from participating in the network at all.",
    },
    "physical_link_down": {
        "weight": 92,
        "title": "Restore physical links",
        "summary": "Layer 1 failures block every higher-level check and make routing symptoms misleading.",
    },
    "interface_down": {
        "weight": 90,
        "title": "Bring down interfaces back online",
        "summary": "A fully down interface blocks traffic before any routing or VLAN logic matters.",
    },
    "interface_protocol_down": {
        "weight": 88,
        "title": "Fix protocol-down interfaces",
        "summary": "Layer 2 adjacency problems often create downstream routing and gateway symptoms.",
    },
    "interface_admin_down": {
        "weight": 86,
        "title": "Re-enable shutdown interfaces",
        "summary": "Administratively disabled ports are often the root cause of several secondary alarms.",
    },
    "wrong_subnet_mask": {
        "weight": 80,
        "title": "Correct subnet mask mismatches",
        "summary": "Bad masks distort local-vs-remote decisions and can mimic routing failures.",
    },
    "vlan_not_exists": {
        "weight": 72,
        "title": "Create missing VLANs",
        "summary": "Access ports on undefined VLANs drop traffic immediately.",
    },
    "trunk_access_mismatch": {
        "weight": 68,
        "title": "Align trunk and access settings",
        "summary": "Switchport mode mismatches frequently break inter-switch communication.",
    },
    "native_vlan_not_exists": {
        "weight": 60,
        "title": "Repair native VLAN configuration",
        "summary": "Native VLAN mismatches can silently drop untagged traffic.",
    },
    "missing_route": {
        "weight": 54,
        "title": "Add missing routes",
        "summary": "Once interfaces and addressing are stable, routing gaps become meaningful.",
    },
    "no_default_gateway": {
        "weight": 50,
        "title": "Add a default route",
        "summary": "A missing default route blocks unknown destinations after local connectivity is fixed.",
    },
}


SEVERITY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


ISSUE_TO_COMMAND_KEYS = {
    "duplicate_ip": {"running_config", "ip_interface_brief"},
    "invalid_ip_config": {"running_config", "ip_interface_brief"},
    "wrong_subnet_mask": {"running_config", "ip_interface_brief"},
    "physical_link_down": {"ip_interface_brief"},
    "interface_down": {"ip_interface_brief", "running_config"},
    "interface_protocol_down": {"ip_interface_brief"},
    "interface_admin_down": {"ip_interface_brief", "running_config"},
    "missing_route": {"ip_route", "running_config"},
    "no_default_gateway": {"ip_route", "running_config"},
    "vlan_not_exists": {"vlan_brief", "running_config"},
    "native_vlan_not_exists": {"vlan_brief", "running_config"},
    "trunk_access_mismatch": {"running_config"},
}


def build_analysis_artifacts(
    raw_text: str,
    parsed: dict[str, Any],
    issues: list[dict[str, Any]],
    score_result: dict[str, Any],
) -> dict[str, Any]:
    evidence = build_evidence_report(raw_text, parsed, issues)
    fix_plan = build_fix_plan(issues)
    insights = build_insights(parsed, issues, evidence, fix_plan)
    analysis_summary = build_analysis_summary(
        parsed=parsed,
        issues=issues,
        evidence=evidence,
        fix_plan=fix_plan,
        score_result=score_result,
    )

    return {
        "engine_mode": "deterministic_copilot",
        "evidence": evidence,
        "fix_plan": fix_plan,
        "insights": insights,
        "analysis_summary": analysis_summary,
    }


def build_evidence_report(
    raw_text: str,
    parsed: dict[str, Any],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    checks = []
    detected_keys = set()
    total_weight = sum(command["weight"] for command in COMMAND_CATALOG)
    detected_weight = 0

    for command in COMMAND_CATALOG:
        detected = _command_detected(command["key"], raw_text, parsed)
        if detected:
            detected_keys.add(command["key"])
            detected_weight += command["weight"]

        checks.append({
            "key": command["key"],
            "label": command["label"],
            "detected": detected,
            "weight": command["weight"],
            "why": command["why"],
            "recommendation": command["recommendation"],
        })

    coverage_score = round((detected_weight / total_weight) * 100, 1) if total_weight else 100.0
    confidence = "high" if coverage_score >= 80 else "medium" if coverage_score >= 55 else "low"

    missing_commands = [
        {
            "command": check["label"],
            "reason": check["recommendation"],
        }
        for check in checks
        if not check["detected"]
    ]

    for issue in issues:
        needed_keys = ISSUE_TO_COMMAND_KEYS.get(issue.get("failure_type", ""), set())
        missing_for_issue = [key for key in needed_keys if key not in detected_keys]
        for missing_key in missing_for_issue:
            command = next(item for item in COMMAND_CATALOG if item["key"] == missing_key)
            extra = {
                "command": command["label"],
                "reason": f"Helps confirm {issue.get('failure_type', '').replace('_', ' ')} on {issue.get('device', 'Unknown')}.",
            }
            if extra not in missing_commands:
                missing_commands.append(extra)

    device_count = len(parsed.get("devices") or [parsed]) if _parsed_has_scope(parsed) else 0
    notes = []
    if device_count > 1:
        notes.append(f"Combined capture detected across {device_count} devices.")
    if coverage_score < 60:
        notes.append("Evidence is thin. Missing command output can hide secondary issues.")
    if not issues and coverage_score < 70:
        notes.append("No issues were found, but confidence is limited because not all key commands were present.")
    if not parsed.get("routes") and not _command_detected("ip_route", raw_text, parsed):
        notes.append("Routing conclusions are based on incomplete routing-table evidence.")

    summary = (
        f"Capture coverage {coverage_score:.0f}% ({confidence} confidence). "
        f"{len(missing_commands)} recommended capture command(s) remain."
    )

    return {
        "summary": summary,
        "overall_score": coverage_score,
        "confidence": confidence,
        "device_count": device_count,
        "command_checks": checks,
        "missing_commands": missing_commands,
        "notes": notes,
    }


def build_fix_plan(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for issue in issues:
        grouped[issue.get("failure_type", "unknown")].append(issue)

    plan = []
    for failure_type, grouped_issues in grouped.items():
        priority_meta = FAILURE_TYPE_PRIORITY.get(
            failure_type,
            {
                "weight": 40,
                "title": failure_type.replace("_", " ").title(),
                "summary": "Address this issue after higher-impact failures are resolved.",
            },
        )

        severity = max(
            (issue.get("severity", "low") for issue in grouped_issues),
            key=lambda value: SEVERITY_RANK.get(value, 0),
        )
        devices = sorted({issue.get("device", "Unknown") for issue in grouped_issues})
        issue_refs = [
            f"{issue.get('device', 'Unknown')} — {issue.get('interface', 'N/A')}"
            for issue in grouped_issues
        ]
        commands = []
        for issue in grouped_issues:
            command = issue.get("fix_command")
            if command and command not in commands:
                commands.append(command)

        plan.append({
            "priority_score": priority_meta["weight"] * 10 + SEVERITY_RANK.get(severity, 0),
            "title": priority_meta["title"],
            "summary": priority_meta["summary"],
            "failure_type": failure_type,
            "severity": severity,
            "issue_count": len(grouped_issues),
            "devices": devices,
            "issue_refs": issue_refs,
            "commands": commands,
        })

    ordered = sorted(
        plan,
        key=lambda item: (-item["priority_score"], -item["issue_count"], item["title"]),
    )

    for index, item in enumerate(ordered, start=1):
        item["priority"] = index
        item.pop("priority_score", None)

    return ordered


def build_insights(
    parsed: dict[str, Any],
    issues: list[dict[str, Any]],
    evidence: dict[str, Any],
    fix_plan: list[dict[str, Any]],
) -> list[str]:
    insights = []
    devices = parsed.get("devices") or [parsed]
    named_devices = [device.get("hostname", "Unknown") for device in devices if device.get("hostname")]

    if named_devices:
        insights.append(
            f"Analysis scope: {len(devices)} device(s) captured ({', '.join(named_devices[:4])})."
        )
    if fix_plan:
        top_step = fix_plan[0]
        insights.append(
            f"Fix order matters: start with '{top_step['title']}' before lower-priority routing or VLAN symptoms."
        )
    if evidence.get("missing_commands"):
        next_commands = ", ".join(
            command["command"] for command in evidence["missing_commands"][:3]
        )
        insights.append(f"Next best evidence to collect: {next_commands}.")
    if not issues:
        insights.append("No rule violations were detected in the captured data set.")

    return insights


def build_analysis_summary(
    parsed: dict[str, Any],
    issues: list[dict[str, Any]],
    evidence: dict[str, Any],
    fix_plan: list[dict[str, Any]],
    score_result: dict[str, Any],
) -> str:
    device_count = evidence.get("device_count", 0)
    issue_count = len(issues)
    score = score_result.get("total_score", 0)

    lines = [
        f"Deterministic analysis completed across {device_count or 1} device(s).",
        f"Network health score: {score}/100 with {issue_count} issue(s) detected.",
        f"Evidence confidence: {evidence.get('confidence', 'low')} ({evidence.get('overall_score', 0)}% capture coverage).",
    ]

    if fix_plan:
        top_step = fix_plan[0]
        lines.append(
            f"Start with priority {top_step['priority']}: {top_step['title']}."
        )
    else:
        lines.append("No repair actions are currently prioritized because no issues were found.")

    if evidence.get("missing_commands"):
        lines.append(
            "Recommended next captures: "
            + ", ".join(item["command"] for item in evidence["missing_commands"][:3])
            + "."
        )

    if parsed.get("devices"):
        lines.append("Combined multi-device capture was processed successfully.")

    return "\n".join(lines)


def _command_detected(command_key: str, raw_text: str, parsed: dict[str, Any]) -> bool:
    raw = raw_text.lower()

    if command_key == "running_config":
        return bool(
            parsed.get("interface_configs")
            or parsed.get("router_config")
            or re.search(r"^hostname\s+\S+", raw_text, re.MULTILINE)
        )

    if command_key == "ip_interface_brief":
        return bool(
            parsed.get("interfaces")
            or "show ip interface brief" in raw
            or re.search(r"^interface\s+ip-address\s+ok\?\s+method\s+status\s+protocol", raw, re.MULTILINE)
        )

    if command_key == "ip_route":
        return bool(
            parsed.get("routes")
            or "show ip route" in raw
            or "gateway of last resort" in raw
            or "codes: c - connected" in raw
        )

    if command_key == "vlan_brief":
        return bool(
            parsed.get("vlans")
            or "show vlan brief" in raw
            or re.search(r"^vlan\s+name\s+status\s+ports", raw, re.MULTILINE)
        )

    return False


def _parsed_has_scope(parsed: dict[str, Any]) -> bool:
    return any(
        parsed.get(key)
        for key in ("interfaces", "routes", "vlans", "interface_configs", "router_config", "devices")
    )
