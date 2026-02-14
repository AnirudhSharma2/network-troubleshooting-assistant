"""
Cisco IOS CLI Output Parser.

Parses common Cisco show commands and running-config blocks into
structured Python dictionaries for the rule engine to analyze.

Supported inputs:
- show ip interface brief
- show ip route
- show vlan brief
- show interfaces (status lines)
- running-config interface blocks
- running-config router blocks
"""

import re
from typing import Any


def parse_all(raw_text: str) -> dict[str, Any]:
    """
    Master parser: automatically detect and extract all parseable
    sections from a mixed CLI output / config paste.
    """
    result = {
        "interfaces": parse_ip_interface_brief(raw_text),
        "routes": parse_ip_route(raw_text),
        "vlans": parse_vlan_brief(raw_text),
        "interface_configs": parse_running_config_interfaces(raw_text),
        "router_config": parse_router_config(raw_text),
        "hostname": parse_hostname(raw_text),
        "raw_text": raw_text,
    }
    return result


# ── show ip interface brief ───────────────────────────────────

def parse_ip_interface_brief(text: str) -> list[dict[str, str]]:
    """
    Parse 'show ip interface brief' output.
    Returns list of {interface, ip, ok, method, status, protocol}.
    """
    interfaces = []
    pattern = re.compile(
        r"^(\S+)\s+"           # Interface name
        r"(\d+\.\d+\.\d+\.\d+|unassigned)\s+"  # IP address
        r"(YES|NO)\s+"         # OK?
        r"(\S+)\s+"            # Method
        r"([\w\s]+?)\s+"       # Status (may have spaces like "administratively down")
        r"(up|down)\s*$",      # Protocol
        re.MULTILINE | re.IGNORECASE,
    )

    for match in pattern.finditer(text):
        interfaces.append({
            "interface": match.group(1).strip(),
            "ip": match.group(2).strip(),
            "ok": match.group(3).strip(),
            "method": match.group(4).strip(),
            "status": match.group(5).strip().lower(),
            "protocol": match.group(6).strip().lower(),
        })

    # Fallback: simpler pattern for various Packet Tracer formats
    if not interfaces:
        simple_pattern = re.compile(
            r"^(\S+(?:Ethernet|Serial|Loopback|Vlan|Tunnel|Port-channel)\S*)\s+"
            r"(\d+\.\d+\.\d+\.\d+|unassigned)\s+"
            r"(YES|NO)\s+"
            r"(\S+)\s+"
            r"(.+)$",
            re.MULTILINE | re.IGNORECASE,
        )
        for match in simple_pattern.finditer(text):
            remaining = match.group(5).strip()
            parts = remaining.rsplit(None, 1)
            status_val = parts[0].strip().lower() if len(parts) >= 2 else remaining.strip().lower()
            protocol_val = parts[1].strip().lower() if len(parts) >= 2 else "down"
            interfaces.append({
                "interface": match.group(1).strip(),
                "ip": match.group(2).strip(),
                "ok": match.group(3).strip(),
                "method": match.group(4).strip(),
                "status": status_val,
                "protocol": protocol_val,
            })

    return interfaces


# ── show ip route ─────────────────────────────────────────────

def parse_ip_route(text: str) -> list[dict[str, str]]:
    """
    Parse 'show ip route' output.
    Returns list of {code, network, mask, next_hop, interface, ad_metric}.
    """
    routes = []

    # Connected and local routes
    connected_pattern = re.compile(
        r"^([CDSLROBNI*>i\s]{1,5})\s+"
        r"(\d+\.\d+\.\d+\.\d+)(?:/(\d+))?\s+"
        r"(?:\[(\d+/\d+)\])?\s*"
        r"(?:via\s+(\d+\.\d+\.\d+\.\d+))?,?\s*"
        r"(?:is directly connected,?\s*)?"
        r"(\S+)?",
        re.MULTILINE,
    )

    for match in connected_pattern.finditer(text):
        code = match.group(1).strip()
        network = match.group(2)
        mask = match.group(3) or ""
        ad_metric = match.group(4) or ""
        next_hop = match.group(5) or "directly connected"
        interface = match.group(6) or ""

        if network:
            routes.append({
                "code": code,
                "network": network,
                "mask": mask,
                "next_hop": next_hop,
                "interface": interface,
                "ad_metric": ad_metric,
            })

    return routes


# ── show vlan brief ───────────────────────────────────────────

def parse_vlan_brief(text: str) -> list[dict[str, Any]]:
    """
    Parse 'show vlan brief' output.
    Returns list of {vlan_id, name, status, ports[]}.
    """
    vlans = []
    pattern = re.compile(
        r"^(\d+)\s+"
        r"(\S+)\s+"
        r"(active|act/unsup|suspend)\s*"
        r"(.*)$",
        re.MULTILINE | re.IGNORECASE,
    )

    for match in pattern.finditer(text):
        ports_str = match.group(4).strip()
        ports = [p.strip() for p in ports_str.split(",") if p.strip()] if ports_str else []
        vlans.append({
            "vlan_id": int(match.group(1)),
            "name": match.group(2).strip(),
            "status": match.group(3).strip().lower(),
            "ports": ports,
        })

    return vlans


# ── running-config interface blocks ──────────────────────────

def parse_running_config_interfaces(text: str) -> list[dict[str, Any]]:
    """
    Parse interface blocks from running-config.
    Returns list of {interface, ip, mask, shutdown, switchport_mode,
                     access_vlan, trunk_allowed, description, commands[]}.
    """
    interfaces = []
    # Split on interface declarations
    blocks = re.split(r"(?=^interface\s+\S+)", text, flags=re.MULTILINE)

    for block in blocks:
        iface_match = re.match(r"^interface\s+(\S+)", block)
        if not iface_match:
            continue

        iface_name = iface_match.group(1)
        entry: dict[str, Any] = {
            "interface": iface_name,
            "ip": None,
            "mask": None,
            "shutdown": False,
            "switchport_mode": None,
            "access_vlan": None,
            "native_vlan": None,
            "trunk_allowed": None,
            "description": None,
            "commands": [],
        }

        for line in block.splitlines()[1:]:
            line = line.strip()
            if line.startswith("!") or not line:
                continue
            if line.startswith("interface "):
                break  # next interface block

            entry["commands"].append(line)

            # IP address
            ip_match = re.match(r"ip address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)", line)
            if ip_match:
                entry["ip"] = ip_match.group(1)
                entry["mask"] = ip_match.group(2)

            # Shutdown
            if line == "shutdown":
                entry["shutdown"] = True
            if line == "no shutdown":
                entry["shutdown"] = False

            # Switchport mode
            mode_match = re.match(r"switchport mode\s+(access|trunk)", line)
            if mode_match:
                entry["switchport_mode"] = mode_match.group(1)

            # Access VLAN
            access_match = re.match(r"switchport access vlan\s+(\d+)", line)
            if access_match:
                entry["access_vlan"] = int(access_match.group(1))

            # Trunk native VLAN
            native_match = re.match(r"switchport trunk native vlan\s+(\d+)", line)
            if native_match:
                entry["native_vlan"] = int(native_match.group(1))

            # Trunk allowed VLANs
            allowed_match = re.match(r"switchport trunk allowed vlan\s+(.+)", line)
            if allowed_match:
                entry["trunk_allowed"] = allowed_match.group(1).strip()

            # Description
            desc_match = re.match(r"description\s+(.+)", line)
            if desc_match:
                entry["description"] = desc_match.group(1).strip()

        interfaces.append(entry)

    return interfaces


# ── running-config router blocks ─────────────────────────────

def parse_router_config(text: str) -> list[dict[str, Any]]:
    """
    Parse router configuration blocks (OSPF, EIGRP, RIP, static).
    """
    routers = []

    # Dynamic routing protocols
    router_blocks = re.split(r"(?=^router\s+\S+)", text, flags=re.MULTILINE)
    for block in router_blocks:
        header = re.match(r"^router\s+(\S+)\s*(\d+)?", block)
        if not header:
            continue

        protocol = header.group(1).lower()
        process_id = header.group(2) or ""
        networks = []
        commands = []

        for line in block.splitlines()[1:]:
            line = line.strip()
            if line.startswith("!") or not line:
                continue
            if line.startswith("router "):
                break

            commands.append(line)
            net_match = re.match(r"network\s+(\S+)(?:\s+(\S+))?(?:\s+area\s+(\d+))?", line)
            if net_match:
                networks.append({
                    "network": net_match.group(1),
                    "wildcard": net_match.group(2) or "",
                    "area": net_match.group(3) or "",
                })

        routers.append({
            "protocol": protocol,
            "process_id": process_id,
            "networks": networks,
            "commands": commands,
        })

    # Static routes
    static_routes = re.findall(
        r"^ip route\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\S+)",
        text,
        re.MULTILINE,
    )
    for sr in static_routes:
        routers.append({
            "protocol": "static",
            "process_id": "",
            "networks": [{"network": sr[0], "mask": sr[1], "next_hop": sr[2]}],
            "commands": [f"ip route {sr[0]} {sr[1]} {sr[2]}"],
        })

    return routers


# ── Hostname ──────────────────────────────────────────────────

def parse_hostname(text: str) -> str:
    """Extract hostname from running-config."""
    match = re.search(r"^hostname\s+(\S+)", text, re.MULTILINE)
    return match.group(1) if match else "Unknown"
