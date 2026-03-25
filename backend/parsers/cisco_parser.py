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
- combined multi-device captures separated by hostnames, prompts, or --- blocks
"""

import re
from typing import Any


PROMPT_RE = re.compile(r"^(?P<host>[A-Za-z0-9_.()-]+)(?:\([^)]+\))?[#>]")
SEPARATOR_RE = re.compile(r"(?m)^\s*(?:-{3,}|={3,})\s*$")


def parse_all(raw_text: str) -> dict[str, Any]:
    """
    Master parser: automatically detect and extract all parseable
    sections from a mixed CLI output / config paste.
    """
    normalized = raw_text.replace("\r\n", "\n")
    devices = _parse_device_captures(normalized)

    if len(devices) == 1:
        device = devices[0]
        device["devices"] = []
        return device

    return {
        "interfaces": [iface for device in devices for iface in device["interfaces"]],
        "routes": [route for device in devices for route in device["routes"]],
        "vlans": [vlan for device in devices for vlan in device["vlans"]],
        "interface_configs": [
            iface for device in devices for iface in device["interface_configs"]
        ],
        "router_config": [
            router for device in devices for router in device["router_config"]
        ],
        "hostname": "Combined Capture",
        "raw_text": normalized,
        "devices": devices,
    }


def _parse_device_captures(raw_text: str) -> list[dict[str, Any]]:
    blocks = (
        _split_by_hostname_blocks(raw_text)
        or _split_by_prompt_blocks(raw_text)
        or _split_by_separator_blocks(raw_text)
        or [raw_text]
    )

    parsed_devices = []
    for block in blocks:
        parsed = _parse_single_device(block)
        if _has_meaningful_data(parsed):
            parsed_devices.append(parsed)

    if not parsed_devices:
        parsed_devices.append(_parse_single_device(raw_text))

    return _merge_duplicate_devices(parsed_devices)


def _parse_single_device(raw_text: str) -> dict[str, Any]:
    cleaned = _strip_prompt_commands(raw_text)
    hostname = parse_hostname(cleaned)
    if hostname == "Unknown":
        hostname = _extract_prompt_hostname(raw_text)

    parsed = {
        "interfaces": parse_ip_interface_brief(cleaned),
        "routes": parse_ip_route(cleaned),
        "vlans": parse_vlan_brief(cleaned),
        "interface_configs": parse_running_config_interfaces(cleaned),
        "router_config": parse_router_config(cleaned),
        "hostname": hostname,
        "raw_text": raw_text.strip(),
    }

    for collection_name in ("interfaces", "interface_configs"):
        for entry in parsed[collection_name]:
            entry.setdefault("device", hostname)

    return parsed


def _split_by_hostname_blocks(raw_text: str) -> list[str]:
    matches = list(re.finditer(r"^hostname\s+\S+", raw_text, re.MULTILINE))
    if len(matches) < 2:
        return []

    blocks = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_text)
        block = raw_text[start:end].strip()
        if block:
            blocks.append(block)

    return blocks


def _split_by_separator_blocks(raw_text: str) -> list[str]:
    blocks = [block.strip() for block in SEPARATOR_RE.split(raw_text) if block.strip()]
    return blocks if len(blocks) > 1 else []


def _split_by_prompt_blocks(raw_text: str) -> list[str]:
    lines = raw_text.splitlines()
    if not lines:
        return []

    groups: list[tuple[str, list[str]]] = []
    current_host = ""
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        prompt_match = PROMPT_RE.match(stripped)
        if prompt_match:
            host = prompt_match.group("host")
            if current_lines and current_host and host != current_host:
                groups.append((current_host, current_lines))
                current_lines = []
            current_host = host
        current_lines.append(line)

    if current_lines:
        groups.append((current_host, current_lines))

    unique_hosts = {host for host, _ in groups if host}
    if len(unique_hosts) < 2:
        return []

    return ["\n".join(group_lines).strip() for _, group_lines in groups if any(l.strip() for l in group_lines)]


def _merge_duplicate_devices(devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen_index: dict[str, int] = {}

    for device in devices:
        hostname = device.get("hostname", "Unknown")
        if hostname == "Unknown" or hostname not in seen_index:
            seen_index[hostname] = len(merged)
            merged.append(device)
            continue

        existing = merged[seen_index[hostname]]
        existing["raw_text"] = "\n".join(
            part for part in (existing.get("raw_text", ""), device.get("raw_text", "")) if part
        ).strip()
        for key in ("interfaces", "routes", "vlans", "interface_configs", "router_config"):
            existing[key].extend(device.get(key, []))

    return merged


def _strip_prompt_commands(raw_text: str) -> str:
    cleaned_lines = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        prompt_match = PROMPT_RE.match(stripped)
        if not prompt_match:
            cleaned_lines.append(line)
            continue

        command = PROMPT_RE.sub("", stripped, count=1).strip()
        if not command:
            continue

        lower = command.lower()
        if lower.startswith((
            "show ",
            "terminal length",
            "enable",
            "conf t",
            "configure terminal",
            "end",
            "exit",
            "write ",
            "copy ",
        )):
            continue

        cleaned_lines.append(command)

    return "\n".join(cleaned_lines)


def _extract_prompt_hostname(raw_text: str) -> str:
    for line in raw_text.splitlines():
        match = PROMPT_RE.match(line.strip())
        if match:
            return match.group("host")
    return "Unknown"


def _has_meaningful_data(parsed: dict[str, Any]) -> bool:
    return any(
        parsed.get(key)
        for key in ("interfaces", "routes", "vlans", "interface_configs", "router_config")
    ) or parsed.get("hostname") != "Unknown"


# ── show ip interface brief ───────────────────────────────────

def parse_ip_interface_brief(text: str) -> list[dict[str, str]]:
    """
    Parse 'show ip interface brief' output.
    Returns list of {interface, ip, ok, method, status, protocol}.
    """
    interfaces = []
    pattern = re.compile(
        r"^(\S+)\s+"
        r"(\d+\.\d+\.\d+\.\d+|unassigned)\s+"
        r"(YES|NO)\s+"
        r"(\S+)\s+"
        r"([\w\s]+?)\s+"
        r"(up|down)\s*$",
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
                break

            entry["commands"].append(line)

            ip_match = re.match(r"ip address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)", line)
            if ip_match:
                entry["ip"] = ip_match.group(1)
                entry["mask"] = ip_match.group(2)

            if line == "shutdown":
                entry["shutdown"] = True
            if line == "no shutdown":
                entry["shutdown"] = False

            mode_match = re.match(r"switchport mode\s+(access|trunk)", line)
            if mode_match:
                entry["switchport_mode"] = mode_match.group(1)

            access_match = re.match(r"switchport access vlan\s+(\d+)", line)
            if access_match:
                entry["access_vlan"] = int(access_match.group(1))

            native_match = re.match(r"switchport trunk native vlan\s+(\d+)", line)
            if native_match:
                entry["native_vlan"] = int(native_match.group(1))

            allowed_match = re.match(r"switchport trunk allowed vlan\s+(.+)", line)
            if allowed_match:
                entry["trunk_allowed"] = allowed_match.group(1).strip()

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
    """Extract hostname from running-config or prompt output."""
    match = re.search(r"^hostname\s+(\S+)", text, re.MULTILINE)
    if match:
        return match.group(1)

    prompt_match = re.search(r"^([A-Za-z0-9_.()-]+)(?:\([^)]+\))?[#>]", text, re.MULTILINE)
    return prompt_match.group(1) if prompt_match else "Unknown"
