"""
Tests for multi-device parsing and deterministic assistant artifacts.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.cisco_parser import parse_all
from services.analysis_assistant import build_evidence_report, build_fix_plan
from services.rule_engine.engine import RuleEngine


MULTI_DEVICE_CAPTURE = """
hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 shutdown
!
R1#show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     192.168.1.1     YES manual administratively down down
GigabitEthernet0/1     10.0.0.1        YES manual up                    up

---
hostname SW1
!
interface FastEthernet0/1
 switchport mode access
 switchport access vlan 99
!
SW1#show vlan brief
VLAN Name                             Status    Ports
1    default                          active    Fa0/1, Fa0/2
10   Sales                            active    Fa0/3
"""


CONFIG_ONLY_CAPTURE = """
hostname R9
!
interface GigabitEthernet0/0
 ip address 10.10.10.1 255.255.255.0
 no shutdown
!
router ospf 1
 network 10.10.10.0 0.0.0.255 area 0
"""


def test_parse_multi_device_capture():
    parsed = parse_all(MULTI_DEVICE_CAPTURE)

    assert len(parsed["devices"]) == 2
    assert parsed["devices"][0]["hostname"] == "R1"
    assert parsed["devices"][1]["hostname"] == "SW1"
    assert len(parsed["interface_configs"]) >= 2
    assert len(parsed["vlans"]) >= 2


def test_evidence_report_flags_missing_commands():
    parsed = parse_all(CONFIG_ONLY_CAPTURE)
    report = build_evidence_report(CONFIG_ONLY_CAPTURE, parsed, [])

    assert report["confidence"] == "low"
    missing = {item["command"] for item in report["missing_commands"]}
    assert "show ip interface brief" in missing
    assert "show ip route" in missing


def test_fix_plan_prioritizes_root_causes():
    engine = RuleEngine()
    result = engine.analyze(
        """
hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 shutdown
!
---
hostname R2
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
"""
    )

    plan = build_fix_plan(result["issues"])

    assert plan
    assert plan[0]["failure_type"] == "duplicate_ip"
    assert any(item["failure_type"] == "interface_admin_down" for item in plan)
