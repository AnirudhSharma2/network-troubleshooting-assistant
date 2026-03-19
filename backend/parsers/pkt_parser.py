"""
Cisco Packet Tracer .pkt file parser.

Packet Tracer 5.x+ saves .pkt files as ZIP archives containing XML.
This parser extracts device configurations, interfaces, routing, and VLANs
from the XML and maps them to the same structure as cisco_parser.parse_all().

Fallback: Returns None if the file is old binary format (pre-5.x),
so the caller can display a clear error to the user.
"""

import zipfile
import io
import xml.etree.ElementTree as ET
from typing import Any, Optional


def parse_pkt_bytes(file_bytes: bytes) -> Optional[dict[str, Any]]:
    """
    Parse a .pkt file (raw bytes) into the standard parsed dict.

    Returns None if the file format is not supported (old binary .pkt).
    """
    # Try to open as ZIP archive
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            xml_data = _extract_xml(zf)
            if xml_data is None:
                return None
    except zipfile.BadZipFile:
        return None

    # Parse XML tree
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError:
        return None

    result: dict[str, Any] = {
        "interfaces": [],
        "routes": [],
        "vlans": [],
        "interface_configs": [],
        "router_config": [],
        "hostname": "PKT-Network",
        "raw_text": "",
        "source": "pkt_file",
        "_devices": [],  # internal: list of {name, type} for summary
    }

    _walk_devices(root, result)
    result["raw_text"] = _build_summary(result)
    return result


# ── ZIP extraction ────────────────────────────────────────────

def _extract_xml(zf: zipfile.ZipFile) -> Optional[bytes]:
    """Return the content of the main XML file inside the ZIP."""
    names = zf.namelist()
    # Prefer files with .xml extension or no extension (PT stores config as bare file)
    priority = [n for n in names if n.lower().endswith(".xml")]
    priority += [n for n in names if "." not in n.split("/")[-1]]
    priority += names  # fallback: try everything

    seen = set()
    for name in priority:
        if name in seen:
            continue
        seen.add(name)
        try:
            data = zf.read(name)
            # Quick sanity: must start with XML-like content
            stripped = data.lstrip()
            if stripped.startswith(b"<?xml") or stripped.startswith(b"<"):
                return data
        except Exception:
            continue
    return None


# ── Device walking ───────────────────────────────────────────

def _walk_devices(root: ET.Element, result: dict) -> None:
    """Find all device elements in the XML tree regardless of nesting."""
    DEVICE_TAGS = {"router", "switch", "device", "node", "host", "server", "pc"}

    found: list[ET.Element] = []
    for elem in root.iter():
        tag = _clean_tag(elem.tag)
        if tag in DEVICE_TAGS or ("device" in tag and tag != "devices"):
            found.append(elem)

    # If nothing found by tag, treat root children as devices
    if not found:
        found = list(root)

    for dev in found:
        _process_device(dev, result)


def _process_device(dev: ET.Element, result: dict) -> None:
    """Extract all config from a single device element."""
    name = (
        _child_text(dev, "name") or
        _child_text(dev, "hostname") or
        _child_text(dev, "label") or
        dev.get("name") or dev.get("label") or "Unknown"
    )
    dtype = (
        _child_text(dev, "type") or
        dev.get("type") or
        _clean_tag(dev.tag)
    )

    result["_devices"].append({"name": name, "type": dtype})
    if result["hostname"] == "PKT-Network" and name not in ("Unknown", ""):
        result["hostname"] = name

    _extract_interfaces(dev, name, result)
    _extract_routing(dev, result)
    _extract_vlans(dev, result)


# ── Interface extraction ──────────────────────────────────────

def _extract_interfaces(dev: ET.Element, device_name: str, result: dict) -> None:
    IFACE_TAGS = {"interface", "physicalinterface", "logicalinterface", "port"}

    for elem in dev.iter():
        if _clean_tag(elem.tag) not in IFACE_TAGS:
            continue
        if elem is dev:
            continue

        iface_name = (
            _child_text(elem, "name") or
            _child_text(elem, "label") or
            elem.get("name") or "Unknown"
        )

        ip = _child_text(elem, "ipaddress") or _child_text(elem, "ip") or "unassigned"
        mask = _child_text(elem, "subnetmask") or _child_text(elem, "mask") or ""

        # Admin status
        admin_raw = (
            _child_text(elem, "adminstatus") or
            _child_text(elem, "status") or
            _child_text(elem, "linestatus") or
            "up"
        ).lower()

        proto_raw = (
            _child_text(elem, "lineprotocol") or
            _child_text(elem, "protocolstatus") or
            _child_text(elem, "protocol") or
            "up"
        ).lower()

        is_shutdown = "down" in admin_raw or "shutdown" in admin_raw or "disable" in admin_raw
        status_str = "administratively down" if is_shutdown else "up"
        proto_str = "up" if "up" in proto_raw and not is_shutdown else "down"

        # Switchport info
        sw_mode = (_child_text(elem, "switchportmode") or "").lower() or None
        access_vlan_raw = _child_text(elem, "accessvlan") or _child_text(elem, "vlan")
        access_vlan = int(access_vlan_raw) if access_vlan_raw and access_vlan_raw.isdigit() else None
        native_vlan_raw = _child_text(elem, "nativevlan")
        native_vlan = int(native_vlan_raw) if native_vlan_raw and native_vlan_raw.isdigit() else None
        trunk_allowed = _child_text(elem, "trunkallowed") or _child_text(elem, "allowedvlans")

        # Append to interfaces list (show ip interface brief style)
        if ip != "unassigned":
            result["interfaces"].append({
                "interface": iface_name,
                "ip": ip,
                "ok": "YES",
                "method": "manual",
                "status": status_str,
                "protocol": proto_str,
            })

            # Add connected route
            if mask:
                net = _network_addr(ip, mask)
                prefix = _mask_to_cidr(mask)
                result["routes"].append({
                    "code": "C",
                    "network": net,
                    "mask": prefix,
                    "next_hop": "directly connected",
                    "interface": iface_name,
                    "ad_metric": "",
                })

        # Append to interface_configs (running-config style)
        result["interface_configs"].append({
            "interface": iface_name,
            "ip": ip if ip != "unassigned" else None,
            "mask": mask or None,
            "shutdown": is_shutdown,
            "switchport_mode": sw_mode,
            "access_vlan": access_vlan,
            "native_vlan": native_vlan,
            "trunk_allowed": trunk_allowed,
            "description": f"Device: {device_name}",
            "commands": [],
        })


# ── Routing extraction ────────────────────────────────────────

def _extract_routing(dev: ET.Element, result: dict) -> None:
    PROTO_TAGS = {"ospf", "rip", "eigrp", "bgp", "isis"}

    for elem in dev.iter():
        tag = _clean_tag(elem.tag)

        if tag in PROTO_TAGS:
            pid = elem.get("id") or elem.get("processid") or _child_text(elem, "processid") or ""
            networks = []
            for child in elem.iter():
                ctag = _clean_tag(child.tag)
                if ctag == "network":
                    addr = child.get("address") or _child_text(child, "address") or child.text or ""
                    if addr.strip():
                        networks.append({
                            "network": addr.strip(),
                            "wildcard": child.get("wildcard") or _child_text(child, "wildcard") or "",
                            "area": child.get("area") or _child_text(child, "area") or "",
                        })
            if networks or pid:
                result["router_config"].append({
                    "protocol": tag,
                    "process_id": pid,
                    "networks": networks,
                    "commands": [],
                })

        elif tag in ("staticroute", "iproute", "staticentry"):
            dest = _child_text(elem, "destination") or elem.get("destination") or ""
            mask = _child_text(elem, "mask") or elem.get("mask") or ""
            nexthop = _child_text(elem, "nexthop") or elem.get("nexthop") or ""
            if dest:
                result["router_config"].append({
                    "protocol": "static",
                    "process_id": "",
                    "networks": [{"network": dest, "mask": mask, "next_hop": nexthop}],
                    "commands": [f"ip route {dest} {mask} {nexthop}".strip()],
                })


# ── VLAN extraction ───────────────────────────────────────────

def _extract_vlans(dev: ET.Element, result: dict) -> None:
    existing_ids = {v["vlan_id"] for v in result["vlans"]}

    for elem in dev.iter():
        if _clean_tag(elem.tag) != "vlan":
            continue

        vid_raw = (
            _child_text(elem, "id") or
            _child_text(elem, "vlanid") or
            elem.get("id") or elem.get("vlanid") or ""
        )
        if not vid_raw or not vid_raw.isdigit():
            continue

        vid = int(vid_raw)
        if vid in existing_ids:
            continue
        existing_ids.add(vid)

        vname = _child_text(elem, "name") or elem.get("name") or f"VLAN{vid}"
        status = (_child_text(elem, "status") or "active").lower()

        result["vlans"].append({
            "vlan_id": vid,
            "name": vname,
            "status": status,
            "ports": [],
        })


# ── Helpers ───────────────────────────────────────────────────

def _clean_tag(tag: str) -> str:
    """Strip XML namespace and lowercase."""
    return tag.split("}")[-1].lower().strip()


def _child_text(elem: ET.Element, tag: str) -> Optional[str]:
    """Return text of first child matching tag (case-insensitive)."""
    for child in elem:
        if _clean_tag(child.tag) == tag.lower():
            text = (child.text or "").strip()
            return text if text else None
    return None


def _network_addr(ip: str, mask: str) -> str:
    """Compute network address via bitwise AND of IP and mask."""
    try:
        ip_parts = [int(x) for x in ip.split(".")]
        mask_parts = [int(x) for x in mask.split(".")]
        return ".".join(str(ip_parts[i] & mask_parts[i]) for i in range(4))
    except Exception:
        return ip


def _mask_to_cidr(mask: str) -> str:
    """Convert dotted-decimal mask to prefix length string."""
    try:
        return str(sum(bin(int(x)).count("1") for x in mask.split(".")))
    except Exception:
        return ""


def _build_summary(result: dict) -> str:
    """Build a human-readable text summary (stored as raw_text for reference)."""
    lines = ["! Reconstructed from Cisco Packet Tracer .pkt file", "!"]

    for dev in result["_devices"]:
        lines.append(f"! Device: {dev['name']}  Type: {dev['type']}")

    lines += [
        "!",
        "! show ip interface brief (reconstructed)",
        f"{'Interface':<30} {'IP-Address':<18} OK? {'Method':<8} {'Status':<25} Protocol",
    ]
    for iface in result["interfaces"]:
        lines.append(
            f"{iface['interface']:<30} {iface['ip']:<18} {iface['ok']:<4} "
            f"{iface['method']:<8} {iface['status']:<25} {iface['protocol']}"
        )

    return "\n".join(lines)
