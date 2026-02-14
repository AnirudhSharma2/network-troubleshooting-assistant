"""
Mock AI Provider — Template-based explanations.

This provider generates explanations using pre-written templates
based on rule engine output. No API key required.

Perfect for demo, viva, and development.
"""

import random
from typing import Any
from services.ai.base import AIProvider


# ── Explanation Templates ─────────────────────────────────────

FAILURE_TYPE_EXPLANATIONS = {
    "interface_admin_down": {
        "simple": "This interface has been manually turned off by someone using the 'shutdown' command.",
        "concept": "Interface Shutdown",
        "why_fix": "The 'no shutdown' command re-enables the interface, allowing traffic to flow through it again. Think of it like flipping a light switch back on.",
        "analogy": "Imagine a road that has a gate across it. The 'shutdown' command closes the gate. 'No shutdown' opens it again so cars (data packets) can pass through.",
    },
    "interface_protocol_down": {
        "simple": "The interface is powered on but can't communicate with the device on the other end.",
        "concept": "Layer 2 Connectivity",
        "why_fix": "This usually means the cable is disconnected or the device on the other end has its port shut down. Check physical connections first.",
        "analogy": "It's like having your phone turned on but with no signal — the phone works, but it can't reach anyone.",
    },
    "interface_down": {
        "simple": "This interface is completely non-functional — both physically and logically.",
        "concept": "Physical Layer Failure",
        "why_fix": "Enable the interface and check the physical cable. Both ends need to be connected and active.",
        "analogy": "Like a phone that's turned off — nothing can get through until you power it on and connect it.",
    },
    "missing_route": {
        "simple": "The router doesn't know how to reach a certain network because there's no route for it.",
        "concept": "IP Routing",
        "why_fix": "Adding a route tells the router 'to reach network X, send packets through Y'. Without this instruction, the router drops the packet because it doesn't know where to send it.",
        "analogy": "Imagine giving a taxi driver an address that's not on their map. They can't take you there. Adding a route is like updating the map.",
    },
    "no_default_gateway": {
        "simple": "The device has no 'catch-all' route, so it can't reach any network it doesn't directly know about.",
        "concept": "Default Gateway / Default Route",
        "why_fix": "A default route (0.0.0.0/0) tells the device: 'If you don't know where to send something, send it here.' Without it, the device can only talk to directly connected networks.",
        "analogy": "It's like knowing your neighborhood but not having a phone book for anywhere else. The default gateway is your phone book for the rest of the world.",
    },
    "wrong_subnet_mask": {
        "simple": "The subnet mask on this interface is incorrect, which means the device miscalculates which addresses are 'local' vs 'remote'.",
        "concept": "Subnetting",
        "why_fix": "The correct subnet mask ensures the device accurately determines which IPs are on its local network. A /32 mask means 'only this one IP' — no other device can be on the same network.",
        "analogy": "Think of the subnet mask as the boundary of your neighborhood. If it's too small, you think your neighbors live far away. If it's too big, you think strangers are your neighbors.",
    },
    "invalid_ip_config": {
        "simple": "The IP address or subnet mask on this interface is not valid.",
        "concept": "IP Addressing",
        "why_fix": "A valid IP address and mask are essential for any network communication. Without them, the interface can't participate in the network.",
        "analogy": "It's like having an address that doesn't exist on any street — no mail can be delivered to or from this location.",
    },
    "vlan_not_exists": {
        "simple": "A port is assigned to a VLAN that hasn't been created on this switch.",
        "concept": "VLAN Configuration",
        "why_fix": "Creating the VLAN on the switch lets the port function. Until the VLAN exists, the port is essentially disabled because the switch doesn't know what traffic group it belongs to.",
        "analogy": "Imagine being assigned to Room 404 in a building, but Room 404 doesn't exist. You're left standing in the hallway.",
    },
    "native_vlan_not_exists": {
        "simple": "The trunk link's native VLAN doesn't exist on this switch.",
        "concept": "Native VLAN on Trunks",
        "why_fix": "The native VLAN carries untagged traffic across a trunk. If it doesn't exist, untagged frames are dropped.",
        "analogy": "The native VLAN is like the default lane on a highway. If that lane doesn't exist, traffic with no specific destination gets stuck.",
    },
    "trunk_access_mismatch": {
        "simple": "This port's mode doesn't match its configuration — it's set as access but has trunk settings, or vice versa.",
        "concept": "Switchport Modes (Access vs Trunk)",
        "why_fix": "Access ports connect to end devices (computers, printers). Trunk ports connect to other switches and carry multiple VLANs. Using the wrong mode means traffic won't flow correctly.",
        "analogy": "Imagine a two-lane road trying to merge into a one-lane tunnel, or a one-lane road forced onto a highway. The modes need to match the connection type.",
    },
    "duplicate_ip": {
        "simple": "Two or more interfaces have the same IP address, causing a conflict.",
        "concept": "IP Address Uniqueness",
        "why_fix": "Every interface must have a unique IP address. Duplicates cause ARP conflicts where devices fight over who owns the address, resulting in intermittent connectivity.",
        "analogy": "It's like two houses having the same street address — the mailman doesn't know which one to deliver to, so sometimes mail goes to the right place and sometimes it doesn't.",
    },
    "physical_link_down": {
        "simple": "The physical cable connection appears to be disconnected or faulty.",
        "concept": "Physical Layer (Layer 1)",
        "why_fix": "Network communication starts at the physical layer. No amount of configuration can fix a disconnected cable. In Packet Tracer, check that cables are properly connected between devices.",
        "analogy": "Like trying to make a phone call with no phone line connected — you can dial all you want, but nothing will happen.",
    },
}


class MockAIProvider(AIProvider):
    """Template-based AI provider that requires no external API."""

    def generate_explanation(self, issues: list[dict[str, Any]], score: float) -> str:
        if not issues:
            return (
                "✅ Great news! No network issues were detected.\n\n"
                f"Your network health score is {score}/100.\n"
                "All interfaces, routes, VLANs, and IP configurations appear correct."
            )

        lines = [
            f"🔍 Network Analysis Complete — Health Score: {score}/100\n",
            f"Found {len(issues)} issue(s) that need attention:\n",
        ]

        for i, issue in enumerate(issues, 1):
            ftype = issue.get("failure_type", "unknown")
            template = FAILURE_TYPE_EXPLANATIONS.get(ftype, {})
            simple = template.get("simple", issue.get("detail", "Unknown issue"))
            device = issue.get("device", "Unknown")
            interface = issue.get("interface", "N/A")
            severity = issue.get("severity", "medium").upper()

            lines.append(f"{'─' * 50}")
            lines.append(f"Issue #{i} [{severity}] — {device}, {interface}")
            lines.append(f"What's wrong: {simple}")
            lines.append(f"Technical detail: {issue.get('detail', '')}")

            fix = issue.get("fix_command")
            if fix:
                lines.append(f"Fix command:\n  {fix}")
            lines.append("")

        lines.append("─" * 50)
        if score >= 70:
            lines.append("Overall: The network has some issues but is mostly functional.")
        elif score >= 40:
            lines.append("Overall: Significant problems found. Fix the critical issues first.")
        else:
            lines.append("Overall: The network has severe issues and is likely non-functional.")

        return "\n".join(lines)

    def generate_learning_content(self, issue: dict[str, Any]) -> dict[str, str]:
        ftype = issue.get("failure_type", "unknown")
        template = FAILURE_TYPE_EXPLANATIONS.get(ftype, {})

        return {
            "concept": template.get("concept", ftype.replace("_", " ").title()),
            "explanation": template.get("simple", issue.get("detail", "No explanation available.")),
            "why_fix_works": template.get(
                "why_fix",
                "Applying the recommended fix addresses the root cause of the detected issue."
            ),
            "analogy": template.get(
                "analogy",
                "Think of network devices like roads and intersections — "
                "each needs to be properly connected and configured for traffic to flow."
            ),
            "fix_command": issue.get("fix_command", ""),
            "severity": issue.get("severity", "medium"),
            "device": issue.get("device", "Unknown"),
            "interface": issue.get("interface", "N/A"),
        }

    def generate_scenario(self, scenario_type: str, difficulty: str) -> dict[str, Any]:
        """Generate a practice scenario from pre-built templates."""
        scenarios = PRACTICE_SCENARIOS.get(scenario_type, PRACTICE_SCENARIOS["routing"])
        difficulty_scenarios = [s for s in scenarios if s["difficulty"] == difficulty]
        if not difficulty_scenarios:
            difficulty_scenarios = scenarios

        scenario = random.choice(difficulty_scenarios)
        return scenario


# ── Pre-built Practice Scenarios ──────────────────────────────

PRACTICE_SCENARIOS = {
    "routing": [
        {
            "title": "Missing Static Route Between Two Networks",
            "difficulty": "easy",
            "description": "Router R1 connects two networks (192.168.1.0/24 and 10.0.0.0/24) but PCs on one network cannot reach the other.",
            "network_config": """hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/1
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
! Note: No routing protocol or static routes configured between networks
! connected to a second router R2 with network 172.16.0.0/24""",
            "expected_issues": [
                {"type": "missing_route", "detail": "No route to 172.16.0.0/24 network"}
            ],
            "instructions": """Packet Tracer Lab Setup:
1. Place two routers (R1 and R2) connected via serial link
2. Connect a PC to R1's Gig0/0 (192.168.1.0/24 network)
3. Connect a PC to R2's Gig0/0 (172.16.0.0/24 network)
4. Configure IP addresses on all interfaces
5. DO NOT add any static routes or routing protocols
6. Try to ping from PC1 to PC2 — it should fail
7. Use the troubleshooting assistant to diagnose
8. Add the missing static routes to fix connectivity""",
        },
        {
            "title": "OSPF Network Statement Missing",
            "difficulty": "medium",
            "description": "Three routers running OSPF, but one router's network is not being advertised.",
            "network_config": """hostname R2
!
interface GigabitEthernet0/0
 ip address 10.0.1.1 255.255.255.0
 no shutdown
!
interface Serial0/0/0
 ip address 10.0.0.2 255.255.255.252
 no shutdown
!
router ospf 1
 network 10.0.0.0 0.0.0.3 area 0
! Missing: network 10.0.1.0 0.0.0.255 area 0""",
            "expected_issues": [
                {"type": "missing_route", "detail": "10.0.1.0/24 not advertised in OSPF"}
            ],
            "instructions": """Packet Tracer Lab Setup:
1. Create a 3-router OSPF topology (R1-R2-R3)
2. Configure OSPF on all routers
3. On R2, intentionally omit the network statement for one interface
4. Verify with 'show ip route' that the network is missing
5. Use the troubleshooting assistant to identify the issue
6. Add the missing OSPF network statement""",
        },
        {
            "title": "Default Route Loop with Wrong Next-Hop",
            "difficulty": "hard",
            "description": "Two routers each point their default route to the other, creating a routing loop.",
            "network_config": """hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface Serial0/0/0
 ip address 10.0.0.1 255.255.255.252
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 10.0.0.2
---
hostname R2
!
interface Serial0/0/0
 ip address 10.0.0.2 255.255.255.252
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 10.0.0.1""",
            "expected_issues": [
                {"type": "routing_loop", "detail": "Both routers point default routes at each other"}
            ],
            "instructions": """Packet Tracer Lab Setup:
1. Place two routers connected via serial link
2. Configure default routes on both pointing to each other
3. Connect a PC to R1 and try to ping an external IP (e.g., 8.8.8.8)
4. Watch the packet bounce back and forth (TTL expired)
5. Use the troubleshooting assistant to diagnose
6. Fix by setting the correct default route on one router""",
        },
    ],
    "vlan": [
        {
            "title": "PC on Wrong VLAN",
            "difficulty": "easy",
            "description": "A PC in the Sales department is assigned to the Engineering VLAN and cannot reach its file server.",
            "network_config": """hostname SW1
!
vlan 10
 name Sales
!
vlan 20
 name Engineering
!
interface FastEthernet0/1
 description Sales-PC1
 switchport mode access
 switchport access vlan 20
 ! Should be VLAN 10 for Sales
!
interface FastEthernet0/2
 description Sales-FileServer
 switchport mode access
 switchport access vlan 10""",
            "expected_issues": [
                {"type": "vlan_mismatch", "detail": "Sales PC on Engineering VLAN"}
            ],
            "instructions": """Packet Tracer Lab Setup:
1. Create a switch with VLAN 10 (Sales) and VLAN 20 (Engineering)
2. Connect Sales PC to Fa0/1, assign it to VLAN 20 (wrong!)
3. Connect Sales File Server to Fa0/2, assign to VLAN 10
4. Try to ping from PC to server — it should fail
5. Use the troubleshooting assistant to diagnose
6. Move Fa0/1 to VLAN 10""",
        },
        {
            "title": "Trunk Port Misconfigured as Access",
            "difficulty": "medium",
            "description": "Two switches connected by a link that should be a trunk but is set as access on one side.",
            "network_config": """hostname SW1
!
interface GigabitEthernet0/1
 description Link-to-SW2
 switchport mode access
 switchport access vlan 1
 ! Should be trunk mode
!
--- SW2 ---
hostname SW2
!
interface GigabitEthernet0/1
 description Link-to-SW1
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30""",
            "expected_issues": [
                {"type": "trunk_access_mismatch", "detail": "One side trunk, other side access"}
            ],
            "instructions": """Packet Tracer Lab Setup:
1. Place two switches and connect them
2. Set one side as trunk, the other as access
3. Create VLANs on both switches
4. Connect PCs on same VLAN to different switches
5. Ping should fail across switches for non-default VLANs
6. Use the troubleshooting assistant to diagnose
7. Set both sides to trunk mode""",
        },
    ],
    "interface": [
        {
            "title": "Interface Shutdown",
            "difficulty": "easy",
            "description": "A critical router interface is administratively shut down, blocking all traffic.",
            "network_config": """hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 shutdown
!
interface GigabitEthernet0/1
 ip address 10.0.0.1 255.255.255.0
 no shutdown""",
            "expected_issues": [
                {"type": "interface_admin_down", "detail": "GigabitEthernet0/0 is shutdown"}
            ],
            "instructions": """Packet Tracer Lab Setup:
1. Configure a router with two interfaces
2. Shut down one interface
3. Connect PCs to both interfaces
4. Try to ping — one network is unreachable
5. Use the troubleshooting assistant to find the shutdown interface
6. Apply 'no shutdown' to fix""",
        },
        {
            "title": "Serial Link Clock Rate Missing",
            "difficulty": "medium",
            "description": "A serial link between two routers won't come up because the DCE side is missing the clock rate.",
            "network_config": """hostname R1
!
interface Serial0/0/0
 ip address 10.0.0.1 255.255.255.252
 no shutdown
 ! Missing: clock rate 64000 (this is the DCE end)""",
            "expected_issues": [
                {"type": "physical_link_down", "detail": "Serial interface down, missing clock rate"}
            ],
            "instructions": """Packet Tracer Lab Setup:
1. Connect two routers via serial cable
2. Configure IP addresses on both serial interfaces
3. Don't set clock rate on the DCE end
4. Notice serial stays down/down
5. Use the troubleshooting assistant to diagnose
6. Add 'clock rate 64000' on the DCE end""",
        },
    ],
    "ip": [
        {
            "title": "Duplicate IP Address",
            "difficulty": "easy",
            "description": "Two interfaces on the same router have the same IP address.",
            "network_config": """hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown""",
            "expected_issues": [
                {"type": "duplicate_ip", "detail": "192.168.1.1 on two interfaces"}
            ],
            "instructions": """Packet Tracer Lab Setup:
1. Configure a router with two interfaces
2. Assign the same IP to both
3. Notice erratic behavior / ARP issues
4. Use the troubleshooting assistant to detect the duplicate
5. Change one interface to a unique IP""",
        },
        {
            "title": "Wrong Subnet Mask Prevents Communication",
            "difficulty": "medium",
            "description": "A router interface has a /32 mask, preventing all communication on that subnet.",
            "network_config": """hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.255
 no shutdown""",
            "expected_issues": [
                {"type": "wrong_subnet_mask", "detail": "/32 mask on LAN interface"}
            ],
            "instructions": """Packet Tracer Lab Setup:
1. Configure a router interface with a /32 (255.255.255.255) mask
2. Connect a PC to that network
3. Try to ping the router — it fails
4. Use the troubleshooting assistant to identify the mask issue
5. Change to the correct mask (e.g., 255.255.255.0)""",
        },
    ],
    "mixed": [
        {
            "title": "Multi-Layer Network Failure",
            "difficulty": "hard",
            "description": "A network with multiple simultaneous issues: shutdown interface, missing route, and VLAN mismatch.",
            "network_config": """hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 shutdown
!
interface GigabitEthernet0/1
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
! No routes to external networks
---
hostname SW1
!
vlan 10
 name Sales
vlan 20
 name Engineering
!
interface FastEthernet0/1
 switchport mode access
 switchport access vlan 20
 ! Should be VLAN 10
!
interface GigabitEthernet0/1
 switchport mode access
 ! Should be trunk to router""",
            "expected_issues": [
                {"type": "interface_admin_down", "detail": "GigabitEthernet0/0 shutdown"},
                {"type": "no_default_gateway", "detail": "No default route"},
                {"type": "vlan_mismatch", "detail": "Wrong VLAN assignment"},
                {"type": "trunk_access_mismatch", "detail": "Uplink should be trunk"}
            ],
            "instructions": """Packet Tracer Lab Setup:
1. Build a network with a router and switch
2. Introduce multiple errors: shutdown interface, missing routes, wrong VLANs
3. Use the troubleshooting assistant to find ALL issues
4. Fix them one by one, re-running analysis after each fix
5. Achieve a 100/100 health score""",
        },
    ],
}
