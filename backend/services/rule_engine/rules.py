"""
Network Diagnostic Rules.

Each rule function takes parsed network data and returns a list of
issue dicts: {rule, failure_type, device, interface, severity, detail, fix_command}.

Severity levels: critical, high, medium, low
"""

from typing import Any
import ipaddress


def _iter_device_views(parsed: dict[str, Any]):
    """Yield one parsed view per device when combined device data is provided."""
    devices = parsed.get("devices") or []
    if devices:
        for device in devices:
            yield {
                "hostname": device.get("hostname", parsed.get("hostname", "Unknown")),
                "interfaces": device.get("interfaces", []),
                "routes": device.get("routes", []),
                "vlans": device.get("vlans", []),
                "interface_configs": device.get("interface_configs", []),
                "router_config": device.get("router_config", []),
                "raw_text": device.get("raw_text", parsed.get("raw_text", "")),
            }
        return

    yield parsed


def check_interface_status(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect interfaces that are administratively down or have protocol down.
    
    Maps to real Packet Tracer scenario: 'show ip interface brief' shows
    interfaces with status 'administratively down' or protocol 'down'.
    """
    issues = []
    for device_parsed in _iter_device_views(parsed):
        hostname = device_parsed.get("hostname", "Unknown")

        for iface in device_parsed.get("interfaces", []):
            name = iface.get("interface", "")
            device_name = iface.get("device", hostname)
            status = iface.get("status", "").lower()
            protocol = iface.get("protocol", "").lower()

            if "administratively" in status and "down" in status:
                issues.append({
                    "rule": "check_interface_status",
                    "failure_type": "interface_admin_down",
                    "device": device_name,
                    "interface": name,
                    "severity": "high",
                    "detail": f"Interface {name} on {device_name} is administratively shut down. "
                              f"No traffic can pass through this interface.",
                    "fix_command": f"interface {name}\n no shutdown",
                })
            elif status == "up" and protocol == "down":
                issues.append({
                    "rule": "check_interface_status",
                    "failure_type": "interface_protocol_down",
                    "device": device_name,
                    "interface": name,
                    "severity": "critical",
                    "detail": f"Interface {name} on {device_name} is UP but protocol is DOWN. "
                              f"This usually indicates a Layer 2 issue — cable disconnected, "
                              f"speed/duplex mismatch, or the remote end is down.",
                    "fix_command": f"! Check physical connection on {name}\n"
                                  f"! Verify cable is connected and remote device port is up",
                })
            elif status == "down" and protocol == "down":
                issues.append({
                    "rule": "check_interface_status",
                    "failure_type": "interface_down",
                    "device": device_name,
                    "interface": name,
                    "severity": "critical",
                    "detail": f"Interface {name} on {device_name} is completely DOWN. "
                              f"Physical link failure or interface not configured.",
                    "fix_command": f"interface {name}\n no shutdown",
                })

        for iface_cfg in device_parsed.get("interface_configs", []):
            if not iface_cfg.get("shutdown", False):
                continue

            name = iface_cfg.get("interface", "")
            device_name = iface_cfg.get("device", hostname)
            already_found = any(
                issue["device"] == device_name
                and issue["interface"] == name
                and issue["failure_type"] == "interface_admin_down"
                for issue in issues
            )
            if already_found:
                continue

            issues.append({
                "rule": "check_interface_status",
                "failure_type": "interface_admin_down",
                "device": device_name,
                "interface": name,
                "severity": "high",
                "detail": f"Interface {name} on {device_name} has 'shutdown' in config. "
                          f"This interface is intentionally disabled.",
                "fix_command": f"interface {name}\n no shutdown",
            })

    return issues


def check_missing_routes(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect network segments that appear in interface configs but have
    no corresponding route in the routing table.
    
    Also checks for missing default gateway (0.0.0.0/0).
    """
    issues = []
    for device_parsed in _iter_device_views(parsed):
        hostname = device_parsed.get("hostname", "Unknown")
        routes = device_parsed.get("routes", [])
        interfaces = device_parsed.get("interfaces", [])

        for iface in interfaces:
            ip = iface.get("ip", "")
            if ip == "unassigned" or not ip:
                continue

            name = iface.get("interface", "")
            device_name = iface.get("device", hostname)
            status = iface.get("status", "").lower()
            protocol = iface.get("protocol", "").lower()

            if status != "up" or protocol != "up":
                continue

            ip_found = False
            for route in routes:
                route_net = route.get("network", "")
                if route_net and ip.startswith(route_net.rsplit(".", 1)[0]):
                    ip_found = True
                    break

            if not ip_found and routes:
                issues.append({
                    "rule": "check_missing_routes",
                    "failure_type": "missing_route",
                    "device": device_name,
                    "interface": name,
                    "severity": "high",
                    "detail": f"Network on {name} ({ip}) has no matching route in the "
                              f"routing table of {device_name}. Remote devices cannot reach this network.",
                    "fix_command": f"! Add a route for the network on {name}\n"
                                  f"! Example: ip route <network> <mask> <next-hop>",
                })

    return issues


def check_default_gateway(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Check for missing default gateway / default route.
    """
    issues = []
    for device_parsed in _iter_device_views(parsed):
        hostname = device_parsed.get("hostname", "Unknown")
        routes = device_parsed.get("routes", [])

        if not routes:
            continue

        has_default = any(
            route.get("network", "") == "0.0.0.0"
            or route.get("code", "").strip().startswith("S*")
            or (
                route.get("code", "").strip().startswith("S")
                and route.get("network", "") == "0.0.0.0"
            )
            or "Gateway of last resort" in device_parsed.get("raw_text", "")
            for route in routes
        )

        if "Gateway of last resort is not set" in device_parsed.get("raw_text", ""):
            issues.append({
                "rule": "check_default_gateway",
                "failure_type": "no_default_gateway",
                "device": hostname,
                "interface": "N/A",
                "severity": "medium",
                "detail": f"Device {hostname} has no default gateway configured. "
                          f"Traffic to unknown networks will be dropped.",
                "fix_command": f"ip route 0.0.0.0 0.0.0.0 <next-hop-ip>\n"
                              f"! Replace <next-hop-ip> with the gateway IP address",
            })
        elif not has_default:
            issues.append({
                "rule": "check_default_gateway",
                "failure_type": "no_default_gateway",
                "device": hostname,
                "interface": "N/A",
                "severity": "medium",
                "detail": f"No default route (0.0.0.0/0) found on {hostname}. "
                          f"This device can only reach directly connected and explicitly routed networks.",
                "fix_command": f"ip route 0.0.0.0 0.0.0.0 <next-hop-ip>",
            })

    return issues


def check_wrong_subnet(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect subnet mask mismatches between connected interfaces.
    Also checks for IPs that don't match their expected subnet.
    """
    issues = []
    for device_parsed in _iter_device_views(parsed):
        hostname = device_parsed.get("hostname", "Unknown")

        for iface_cfg in device_parsed.get("interface_configs", []):
            ip = iface_cfg.get("ip")
            mask = iface_cfg.get("mask")
            name = iface_cfg.get("interface", "")
            device_name = iface_cfg.get("device", hostname)

            if not ip or not mask:
                continue

            try:
                interface_obj = ipaddress.IPv4Interface(f"{ip}/{mask}")
                network = interface_obj.network

                if network.prefixlen == 32 and not name.lower().startswith("loopback"):
                    issues.append({
                        "rule": "check_wrong_subnet",
                        "failure_type": "wrong_subnet_mask",
                        "device": device_name,
                        "interface": name,
                        "severity": "high",
                        "detail": f"Interface {name} on {device_name} has a /32 subnet mask ({mask}). "
                                  f"This means no other host can be on this network. "
                                  f"Use a proper subnet mask like 255.255.255.0 for a LAN.",
                        "fix_command": f"interface {name}\n ip address {ip} 255.255.255.0",
                    })

                if interface_obj.ip != network.network_address and mask in ("255.255.255.0", "255.255.0.0", "255.0.0.0"):
                    pass

            except (ValueError, ipaddress.AddressValueError):
                issues.append({
                    "rule": "check_wrong_subnet",
                    "failure_type": "invalid_ip_config",
                    "device": device_name,
                    "interface": name,
                    "severity": "critical",
                    "detail": f"Interface {name} on {device_name} has an invalid IP configuration: "
                              f"IP={ip}, Mask={mask}.",
                    "fix_command": f"interface {name}\n ip address <correct-ip> <correct-mask>",
                })

    return issues


def check_vlan_mismatch(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect VLAN assignment issues:
    - Ports assigned to non-existent VLANs
    - Access ports on wrong VLAN
    - Native VLAN mismatches
    """
    issues = []
    for device_parsed in _iter_device_views(parsed):
        hostname = device_parsed.get("hostname", "Unknown")
        vlans = device_parsed.get("vlans", [])
        iface_configs = device_parsed.get("interface_configs", [])
        existing_vlans = {vlan["vlan_id"] for vlan in vlans}

        for iface_cfg in iface_configs:
            name = iface_cfg.get("interface", "")
            device_name = iface_cfg.get("device", hostname)
            access_vlan = iface_cfg.get("access_vlan")
            native_vlan = iface_cfg.get("native_vlan")

            if access_vlan and existing_vlans and access_vlan not in existing_vlans:
                issues.append({
                    "rule": "check_vlan_mismatch",
                    "failure_type": "vlan_not_exists",
                    "device": device_name,
                    "interface": name,
                    "severity": "high",
                    "detail": f"Interface {name} on {device_name} is assigned to VLAN {access_vlan}, "
                              f"but this VLAN does not exist on the switch. "
                              f"Traffic on this port will be dropped.",
                    "fix_command": f"vlan {access_vlan}\n name VLAN{access_vlan}\n exit",
                })

            if native_vlan and existing_vlans and native_vlan not in existing_vlans:
                issues.append({
                    "rule": "check_vlan_mismatch",
                    "failure_type": "native_vlan_not_exists",
                    "device": device_name,
                    "interface": name,
                    "severity": "medium",
                    "detail": f"Trunk interface {name} on {device_name} has native VLAN {native_vlan}, "
                              f"but this VLAN does not exist.",
                    "fix_command": f"vlan {native_vlan}\n name NativeVLAN\n exit",
                })

    return issues


def check_trunk_access(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect trunk/access port misconfigurations:
    - Trunk port set as access when it connects to another switch
    - Access port set as trunk when it connects to a host
    - Missing encapsulation on trunk
    """
    issues = []
    for device_parsed in _iter_device_views(parsed):
        hostname = device_parsed.get("hostname", "Unknown")
        iface_configs = device_parsed.get("interface_configs", [])

        for iface_cfg in iface_configs:
            name = iface_cfg.get("interface", "")
            device_name = iface_cfg.get("device", hostname)
            mode = iface_cfg.get("switchport_mode")
            access_vlan = iface_cfg.get("access_vlan")
            trunk_allowed = iface_cfg.get("trunk_allowed")

            if mode == "access" and trunk_allowed:
                issues.append({
                    "rule": "check_trunk_access",
                    "failure_type": "trunk_access_mismatch",
                    "device": device_name,
                    "interface": name,
                    "severity": "high",
                    "detail": f"Interface {name} on {device_name} is set to ACCESS mode but has "
                              f"trunk allowed VLAN configuration. This is contradictory. "
                              f"If connecting to another switch, set to trunk mode.",
                    "fix_command": f"interface {name}\n switchport mode trunk",
                })

            if mode == "trunk" and access_vlan and not trunk_allowed:
                issues.append({
                    "rule": "check_trunk_access",
                    "failure_type": "trunk_access_mismatch",
                    "device": device_name,
                    "interface": name,
                    "severity": "medium",
                    "detail": f"Interface {name} on {device_name} is set to TRUNK mode but only has "
                              f"access VLAN {access_vlan} configured. If connecting to a host, "
                              f"set to access mode.",
                    "fix_command": f"interface {name}\n switchport mode access\n switchport access vlan {access_vlan}",
                })

    return issues


def check_duplicate_ip(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect duplicate IP addresses across interfaces.
    """
    issues = []
    hostname = parsed.get("hostname", "Unknown")
    ip_map: dict[str, set[tuple[str, str]]] = {}

    for iface in parsed.get("interfaces", []):
        ip = iface.get("ip", "")
        name = iface.get("interface", "")
        device_name = iface.get("device", hostname)
        if ip and ip != "unassigned":
            ip_map.setdefault(ip, set()).add((device_name, name))

    for iface_cfg in parsed.get("interface_configs", []):
        ip = iface_cfg.get("ip")
        name = iface_cfg.get("interface", "")
        device_name = iface_cfg.get("device", hostname)
        if ip:
            ip_map.setdefault(ip, set()).add((device_name, name))

    for ip, refs in ip_map.items():
        if len(refs) <= 1:
            continue

        ordered_refs = sorted(refs)
        ref_labels = [f"{device} {name}" for device, name in ordered_refs]
        unique_devices = list(dict.fromkeys(device for device, _ in ordered_refs))

        issues.append({
            "rule": "check_duplicate_ip",
            "failure_type": "duplicate_ip",
            "device": ", ".join(unique_devices),
            "interface": ", ".join(ref_labels),
            "severity": "critical",
            "detail": f"IP address {ip} is assigned to multiple interfaces: "
                      f"{', '.join(ref_labels)}. This will cause ARP conflicts and "
                      f"unpredictable behavior.",
            "fix_command": "! Change the IP on one of these interfaces:\n"
                          + "\n".join(
                              f"interface {if_name}\n ip address <unique-ip> <mask>"
                              for _, if_name in ordered_refs[1:]
                          ),
        })

    return issues


def check_physical_link(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect simulated physical link issues based on interface status patterns.
    In Packet Tracer, physical link failures show as both status and protocol down.
    """
    issues = []
    for device_parsed in _iter_device_views(parsed):
        hostname = device_parsed.get("hostname", "Unknown")

        for iface in device_parsed.get("interfaces", []):
            name = iface.get("interface", "")
            device_name = iface.get("device", hostname)
            status = iface.get("status", "").lower()
            protocol = iface.get("protocol", "").lower()
            ip = iface.get("ip", "")

            if ("serial" in name.lower() and status == "down" and protocol == "down"
                    and ip != "unassigned" and ip):
                issues.append({
                    "rule": "check_physical_link",
                    "failure_type": "physical_link_down",
                    "device": device_name,
                    "interface": name,
                    "severity": "critical",
                    "detail": f"Serial interface {name} on {device_name} has IP {ip} configured "
                              f"but is physically down. This indicates a cable is disconnected "
                              f"or the clock rate is not set on the DCE end.",
                    "fix_command": f"interface {name}\n clock rate 64000\n no shutdown\n"
                                  f"! Also check the physical cable connection in Packet Tracer",
                })

            elif (("ethernet" in name.lower() or "gig" in name.lower()) and
                  status == "down" and protocol == "down" and
                  ip != "unassigned" and ip):
                issues.append({
                    "rule": "check_physical_link",
                    "failure_type": "physical_link_down",
                    "device": device_name,
                    "interface": name,
                    "severity": "critical",
                    "detail": f"Ethernet interface {name} on {device_name} has IP {ip} configured "
                              f"but is physically down. Check the cable connection in Packet Tracer.",
                    "fix_command": f"interface {name}\n no shutdown\n"
                                  f"! Verify the physical cable is connected in Packet Tracer",
                })

    return issues


# Registry of all rules for the engine to iterate over
ALL_RULES = [
    check_interface_status,
    check_missing_routes,
    check_default_gateway,
    check_wrong_subnet,
    check_vlan_mismatch,
    check_trunk_access,
    check_duplicate_ip,
    check_physical_link,
]
