"""
Tests for the rule engine, scoring system, and CLI parser.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.cisco_parser import parse_all
from services.rule_engine.engine import RuleEngine
from services.scoring import calculate_health_score


# ── Sample CLI Outputs ────────────────────────────────────────

SAMPLE_CONFIG_WITH_ISSUES = """
hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 shutdown
!
interface GigabitEthernet0/1
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
interface Serial0/0/0
 ip address 172.16.0.1 255.255.255.252
 no shutdown
"""

SAMPLE_SHOW_IP_INTERFACE_BRIEF = """
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     192.168.1.1     YES manual administratively down down
GigabitEthernet0/1     10.0.0.1        YES manual up                    up
Serial0/0/0            172.16.0.1      YES manual down                  down
Loopback0              1.1.1.1         YES manual up                    up
"""

SAMPLE_DUPLICATE_IP = """
hostname R2
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
"""

SAMPLE_VLAN_CONFIG = """
hostname SW1
!
10   Sales                            active    Fa0/2, Fa0/3
20   Engineering                      active    Fa0/4
!
interface FastEthernet0/1
 switchport mode access
 switchport access vlan 99
!
"""

SAMPLE_WRONG_SUBNET = """
hostname R3
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.255
 no shutdown
"""

SAMPLE_HEALTHY_CONFIG = """
hostname R4
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/1
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 10.0.0.254
"""


# ── Parser Tests ──────────────────────────────────────────────

def test_parse_hostname():
    parsed = parse_all(SAMPLE_CONFIG_WITH_ISSUES)
    assert parsed["hostname"] == "R1", f"Expected R1, got {parsed['hostname']}"
    print("✅ test_parse_hostname passed")


def test_parse_interfaces():
    parsed = parse_all(SAMPLE_SHOW_IP_INTERFACE_BRIEF)
    interfaces = parsed["interfaces"]
    assert len(interfaces) >= 3, f"Expected ≥3 interfaces, got {len(interfaces)}"
    
    gig0 = next((i for i in interfaces if "0/0" in i["interface"] and "Gig" in i["interface"]), None)
    assert gig0 is not None, "GigabitEthernet0/0 not found"
    assert "administratively" in gig0["status"], f"Expected admin down, got {gig0['status']}"
    print("✅ test_parse_interfaces passed")


def test_parse_interface_configs():
    parsed = parse_all(SAMPLE_CONFIG_WITH_ISSUES)
    iface_configs = parsed["interface_configs"]
    assert len(iface_configs) >= 3, f"Expected ≥3 interface configs, got {len(iface_configs)}"
    
    gig0 = next((i for i in iface_configs if "0/0" in i["interface"]), None)
    assert gig0 is not None
    assert gig0["ip"] == "192.168.1.1"
    assert gig0["shutdown"] == True
    print("✅ test_parse_interface_configs passed")


def test_parse_vlans():
    vlan_text = """
1    default                          active    Fa0/1, Fa0/2
10   Sales                            active    Fa0/3
20   Engineering                      active    Fa0/4
"""
    parsed = parse_all(vlan_text)
    vlans = parsed["vlans"]
    assert len(vlans) >= 2, f"Expected ≥2 VLANs, got {len(vlans)}"
    print("✅ test_parse_vlans passed")


# ── Rule Engine Tests ─────────────────────────────────────────

def test_detect_interface_shutdown():
    engine = RuleEngine()
    result = engine.analyze(SAMPLE_CONFIG_WITH_ISSUES)
    issues = result["issues"]
    
    shutdown_issues = [i for i in issues if i["failure_type"] == "interface_admin_down"]
    assert len(shutdown_issues) >= 1, f"Expected ≥1 shutdown issues, got {len(shutdown_issues)}"
    assert any("0/0" in i["interface"] for i in shutdown_issues)
    print("✅ test_detect_interface_shutdown passed")


def test_detect_interface_down():
    engine = RuleEngine()
    result = engine.analyze(SAMPLE_SHOW_IP_INTERFACE_BRIEF)
    issues = result["issues"]
    
    down_issues = [i for i in issues if "interface" in i["failure_type"]]
    assert len(down_issues) >= 1, f"Expected ≥1 interface issues, got {len(down_issues)}"
    print("✅ test_detect_interface_down passed")


def test_detect_duplicate_ip():
    engine = RuleEngine()
    result = engine.analyze(SAMPLE_DUPLICATE_IP)
    issues = result["issues"]
    
    dup_issues = [i for i in issues if i["failure_type"] == "duplicate_ip"]
    assert len(dup_issues) >= 1, f"Expected ≥1 duplicate IP issues, got {len(dup_issues)}"
    assert "192.168.1.1" in dup_issues[0]["detail"]
    print("✅ test_detect_duplicate_ip passed")


def test_detect_vlan_not_exists():
    engine = RuleEngine()
    result = engine.analyze(SAMPLE_VLAN_CONFIG)
    issues = result["issues"]
    
    vlan_issues = [i for i in issues if i["failure_type"] == "vlan_not_exists"]
    assert len(vlan_issues) >= 1, f"Expected ≥1 VLAN issues, got {len(vlan_issues)}"
    assert "99" in vlan_issues[0]["detail"]
    print("✅ test_detect_vlan_not_exists passed")


def test_detect_wrong_subnet():
    engine = RuleEngine()
    result = engine.analyze(SAMPLE_WRONG_SUBNET)
    issues = result["issues"]
    
    subnet_issues = [i for i in issues if i["failure_type"] == "wrong_subnet_mask"]
    assert len(subnet_issues) >= 1, f"Expected ≥1 subnet issues, got {len(subnet_issues)}"
    print("✅ test_detect_wrong_subnet passed")


def test_healthy_config():
    engine = RuleEngine()
    result = engine.analyze(SAMPLE_HEALTHY_CONFIG)
    issues = result["issues"]
    
    # Healthy config should have minimal issues
    critical = [i for i in issues if i["severity"] == "critical"]
    assert len(critical) == 0, f"Expected 0 critical issues for healthy config, got {len(critical)}"
    print("✅ test_healthy_config passed")


# ── Scoring Tests ─────────────────────────────────────────────

def test_perfect_score():
    score = calculate_health_score([])
    assert score["total_score"] == 100, f"Expected 100, got {score['total_score']}"
    print("✅ test_perfect_score passed")


def test_score_deduction():
    issues = [
        {"failure_type": "interface_admin_down", "severity": "high", "device": "R1", "interface": "Gig0/0"},
        {"failure_type": "missing_route", "severity": "high", "device": "R1", "interface": "N/A"},
    ]
    score = calculate_health_score(issues)
    assert score["total_score"] < 100, f"Expected <100, got {score['total_score']}"
    assert score["total_score"] > 0, f"Expected >0, got {score['total_score']}"
    assert len(score["deductions"]) == 2
    print("✅ test_score_deduction passed")


def test_critical_severity():
    issues = [
        {"failure_type": "duplicate_ip", "severity": "critical", "device": "R1", "interface": "Gig0/0"},
    ]
    score = calculate_health_score(issues)
    # Critical deduction is 15 from IP category (max 20)
    assert score["total_score"] == 85, f"Expected 85, got {score['total_score']}"
    print("✅ test_critical_severity passed")


def test_full_pipeline():
    """End-to-end test: raw input → rule engine → scoring."""
    engine = RuleEngine()
    result = engine.analyze(SAMPLE_CONFIG_WITH_ISSUES)
    score = calculate_health_score(result["issues"])
    
    assert score["total_score"] <= 100
    assert score["total_score"] >= 0
    assert "routing_score" in score
    assert "interface_score" in score
    assert "vlan_score" in score
    assert "ip_score" in score
    print(f"✅ test_full_pipeline passed (score: {score['total_score']}/100)")


# ── Run All Tests ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Running Network Troubleshooting Assistant Tests")
    print("=" * 50 + "\n")
    
    print("── Parser Tests ──")
    test_parse_hostname()
    test_parse_interfaces()
    test_parse_interface_configs()
    test_parse_vlans()
    
    print("\n── Rule Engine Tests ──")
    test_detect_interface_shutdown()
    test_detect_interface_down()
    test_detect_duplicate_ip()
    test_detect_vlan_not_exists()
    test_detect_wrong_subnet()
    test_healthy_config()
    
    print("\n── Scoring Tests ──")
    test_perfect_score()
    test_score_deduction()
    test_critical_severity()
    test_full_pipeline()
    
    print("\n" + "=" * 50)
    print("All tests passed! ✅")
    print("=" * 50)
