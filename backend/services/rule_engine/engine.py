"""
Rule Engine Orchestrator.

Runs all diagnostic rules against parsed network data and
returns consolidated results.
"""

from typing import Any
from parsers.cisco_parser import parse_all
from services.rule_engine.rules import ALL_RULES


class RuleEngine:
    """
    Deterministic network diagnostic engine.
    
    This is the heart of the troubleshooting system.
    All diagnosis is rule-based — no AI involved in detection.
    """

    def __init__(self):
        self.rules = ALL_RULES

    def analyze(self, raw_input: str) -> dict[str, Any]:
        """
        Full analysis pipeline:
        1. Parse raw CLI / config text
        2. Run all rules
        3. Return structured results
        
        Args:
            raw_input: Raw CLI output or running-config text
            
        Returns:
            dict with 'parsed', 'issues', 'summary' keys
        """
        # Step 1: Parse
        parsed = parse_all(raw_input)

        # Step 2: Run all rules
        all_issues = []
        for rule_fn in self.rules:
            try:
                issues = rule_fn(parsed)
                all_issues.extend(issues)
            except Exception as e:
                all_issues.append({
                    "rule": rule_fn.__name__,
                    "failure_type": "rule_error",
                    "device": parsed.get("hostname", "Unknown"),
                    "interface": "N/A",
                    "severity": "low",
                    "detail": f"Rule {rule_fn.__name__} encountered an error: {str(e)}",
                    "fix_command": None,
                })

        # Step 3: Build summary
        summary = self._build_summary(all_issues)

        return {
            "parsed": {
                "hostname": parsed.get("hostname", "Unknown"),
                "interface_count": len(parsed.get("interfaces", [])),
                "route_count": len(parsed.get("routes", [])),
                "vlan_count": len(parsed.get("vlans", [])),
            },
            "issues": all_issues,
            "summary": summary,
        }

    def _build_summary(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """Build a summary of all detected issues."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        type_counts: dict[str, int] = {}

        for issue in issues:
            sev = issue.get("severity", "low")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

            ftype = issue.get("failure_type", "unknown")
            type_counts[ftype] = type_counts.get(ftype, 0) + 1

        return {
            "total_issues": len(issues),
            "by_severity": severity_counts,
            "by_type": type_counts,
        }


# Singleton instance
rule_engine = RuleEngine()
