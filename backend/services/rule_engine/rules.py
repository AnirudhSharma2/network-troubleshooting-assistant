"""
Network Diagnostic Rules.

Each rule function takes parsed network data and returns a list of
issue dicts: {rule, failure_type, device, interface, severity, detail, fix_command}.

Severity levels: critical, high, medium, low
"""

from typing import Any
import ipaddress


def check_interface_status(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect interfaces that are administratively down or have protocol down.
    
    Maps to real Packet Tracer scenario: 'show ip interface brief' shows
    interfaces with status 'administratively down' or protocol 'down'.
    """
    issues = []
    hostname = parsed.get("hostname", "Unknown")

    for iface in parsed.get("interfaces", []):
        name = iface.get("interface", "")
        status = iface.get("status", "").lower()
        protocol = iface.get("protocol", "").lower()

        if "administratively" in status and "down" in status:
            issues.append({
                "rule": "check_interface_status",
                "failure_type": "interface_admin_down",
                "device": hostname,
                "interface": name,
                "severity": "high",
                "detail": f"Interface {name} on {hostname} is administratively shut down. "
                          f"No traffic can pass through this interface.",
                "fix_command": f"interface {name}\n no shutdown",
            })
        elif status == "up" and protocol == "down":
            issues.append({
                "rule": "check_interface_status",
                "failure_type": "interface_protocol_down",
                "device": hostname,
                "interface": name,
                "severity": "critical",
                "detail": f"Interface {name} on {hostname} is UP but protocol is DOWN. "
                          f"This usually indicates a Layer 2 issue — cable disconnected, "
                          f"speed/duplex mismatch, or the remote end is down.",
                "fix_command": f"! Check physical connection on {name}\n"
                              f"! Verify cable is connected and remote device port is up",
            })
        elif status == "down" and protocol == "down":
            issues.append({
                "rule": "check_interface_status",
                "failure_type": "interface_down",
                "device": hostname,
                "interface": name,
                "severity": "critical",
                "detail": f"Interface {name} on {hostname} is completely DOWN. "
                          f"Physical link failure or interface not configured.",
                "fix_command": f"interface {name}\n no shutdown",
            })

    # Also check running-config for shutdown commands
    for iface_cfg in parsed.get("interface_configs", []):
        if iface_cfg.get("shutdown", False):
            name = iface_cfg.get("interface", "")
            # Avoid duplicates if already detected above
            already_found = any(
                i["interface"] == name and i["failure_type"] == "interface_admin_down"
                for i in issues
            )
            if not already_found:
                issues.append({
                    "rule": "check_interface_status",
                    "failure_type": "interface_admin_down",
                    "device": hostname,
                    "interface": name,
                    "severity": "high",
                    "detail": f"Interface {name} on {hostname} has 'shutdown' in config. "
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
    hostname = parsed.get("hostname", "Unknown")
    routes = parsed.get("routes", [])
    interfaces = parsed.get("interfaces", [])

    # Collect all routed networks from routing table
    routed_networks = set()
    has_default_route = False
    for route in routes:
        net = route.get("network", "")
        if net == "0.0.0.0":
            has_default_route = True
        routed_networks.add(net)

    # Check interface IPs against routing table
    for iface in interfaces:
        ip = iface.get("ip", "")
        if ip == "unassigned" or not ip:
            continue

        name = iface.get("interface", "")
        status = iface.get("status", "").lower()
        protocol = iface.get("protocol", "").lower()

        # Only flag if interface is up but network not routed
        if status == "up" and protocol == "up":
            # Check if any route covers this IP
            ip_found = False
            for route in routes:
                route_net = route.get("network", "")
                if route_net and ip.startswith(route_net.rsplit(".", 1)[0]):
                    ip_found = True
                    break

            if not ip_found and routes:  # Only flag if we have a routing table
                issues.append({
                    "rule": "check_missing_routes",
                    "failure_type": "missing_route",
                    "device": hostname,
                    "interface": name,
                    "severity": "high",
                    "detail": f"Network on {name} ({ip}) has no matching route in the "
                              f"routing table of {hostname}. Remote devices cannot reach this network.",
                    "fix_command": f"! Add a route for the network on {name}\n"
                                  f"! Example: ip route <network> <mask> <next-hop>",
                })

    return issues


def check_default_gateway(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Check for missing default gateway / default route.
    """
    issues = []
    hostname = parsed.get("hostname", "Unknown")
    routes = parsed.get("routes", [])

    if not routes:
        return issues  # No routing table to analyze

    has_default = any(
        r.get("network", "") == "0.0.0.0" or
        r.get("code", "").strip().startswith("S*") or
        "Gateway of last resort" in parsed.get("raw_text", "")
        for r in routes
    )

    # Check if 'Gateway of last resort is not set' appears
    if "Gateway of last resort is not set" in parsed.get("raw_text", ""):
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
    elif not has_default and len(routes) > 0:
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
    hostname = parsed.get("hostname", "Unknown")

    for iface_cfg in parsed.get("interface_configs", []):
        ip = iface_cfg.get("ip")
        mask = iface_cfg.get("mask")
        name = iface_cfg.get("interface", "")

        if not ip or not mask:
            continue

        try:
            interface_obj = ipaddress.IPv4Interface(f"{ip}/{mask}")
            network = interface_obj.network

            # Common misconfiguration: /32 mask on a LAN interface
            if network.prefixlen == 32 and not name.lower().startswith("loopback"):
                issues.append({
                    "rule": "check_wrong_subnet",
                    "failure_type": "wrong_subnet_mask",
                    "device": hostname,
                    "interface": name,
                    "severity": "high",
                    "detail": f"Interface {name} on {hostname} has a /32 subnet mask ({mask}). "
                              f"This means no other host can be on this network. "
                              f"Use a proper subnet mask like 255.255.255.0 for a LAN.",
                    "fix_command": f"interface {name}\n ip address {ip} 255.255.255.0",
                })

            # Check for common mistake: host bits set in network portion
            if interface_obj.ip != network.network_address and mask in ("255.255.255.0", "255.255.0.0", "255.0.0.0"):
                pass  # This is normal for host IPs

        except (ValueError, ipaddress.AddressValueError):
            issues.append({
                "rule": "check_wrong_subnet",
                "failure_type": "invalid_ip_config",
                "device": hostname,
                "interface": name,
                "severity": "critical",
                "detail": f"Interface {name} on {hostname} has an invalid IP configuration: "
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
    hostname = parsed.get("hostname", "Unknown")
    vlans = parsed.get("vlans", [])
    iface_configs = parsed.get("interface_configs", [])

    # Build set of existing VLAN IDs
    existing_vlans = {v["vlan_id"] for v in vlans}

    for iface_cfg in iface_configs:
        name = iface_cfg.get("interface", "")
        access_vlan = iface_cfg.get("access_vlan")
        native_vlan = iface_cfg.get("native_vlan")
        mode = iface_cfg.get("switchport_mode")

        # Port assigned to VLAN that doesn't exist
        if access_vlan and existing_vlans and access_vlan not in existing_vlans:
            issues.append({
                "rule": "check_vlan_mismatch",
                "failure_type": "vlan_not_exists",
                "device": hostname,
                "interface": name,
                "severity": "high",
                "detail": f"Interface {name} on {hostname} is assigned to VLAN {access_vlan}, "
                          f"but this VLAN does not exist on the switch. "
                          f"Traffic on this port will be dropped.",
                "fix_command": f"vlan {access_vlan}\n name VLAN{access_vlan}\n exit",
            })

        # Native VLAN on trunk doesn't exist
        if native_vlan and existing_vlans and native_vlan not in existing_vlans:
            issues.append({
                "rule": "check_vlan_mismatch",
                "failure_type": "native_vlan_not_exists",
                "device": hostname,
                "interface": name,
                "severity": "medium",
                "detail": f"Trunk interface {name} on {hostname} has native VLAN {native_vlan}, "
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
    hostname = parsed.get("hostname", "Unknown")
    iface_configs = parsed.get("interface_configs", [])

    for iface_cfg in iface_configs:
        name = iface_cfg.get("interface", "")
        mode = iface_cfg.get("switchport_mode")
        access_vlan = iface_cfg.get("access_vlan")
        trunk_allowed = iface_cfg.get("trunk_allowed")
        commands = iface_cfg.get("commands", [])

        # Has trunk config but mode is access
        if mode == "access" and trunk_allowed:
            issues.append({
                "rule": "check_trunk_access",
                "failure_type": "trunk_access_mismatch",
                "device": hostname,
                "interface": name,
                "severity": "high",
                "detail": f"Interface {name} on {hostname} is set to ACCESS mode but has "
                          f"trunk allowed VLAN configuration. This is contradictory. "
                          f"If connecting to another switch, set to trunk mode.",
                "fix_command": f"interface {name}\n switchport mode trunk",
            })

        # Has access VLAN config but mode is trunk
        if mode == "trunk" and access_vlan and not trunk_allowed:
            issues.append({
                "rule": "check_trunk_access",
                "failure_type": "trunk_access_mismatch",
                "device": hostname,
                "interface": name,
                "severity": "medium",
                "detail": f"Interface {name} on {hostname} is set to TRUNK mode but only has "
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

    # Collect all IPs from interfaces
    ip_map: dict[str, list[str]] = {}

    for iface in parsed.get("interfaces", []):
        ip = iface.get("ip", "")
        name = iface.get("interface", "")
        if ip and ip != "unassigned":
            ip_map.setdefault(ip, []).append(name)

    for iface_cfg in parsed.get("interface_configs", []):
        ip = iface_cfg.get("ip")
        name = iface_cfg.get("interface", "")
        if ip:
            if ip in ip_map and name not in ip_map[ip]:
                ip_map[ip].append(name)
            elif ip not in ip_map:
                ip_map[ip] = [name]

    for ip, ifaces in ip_map.items():
        if len(ifaces) > 1:
            issues.append({
                "rule": "check_duplicate_ip",
                "failure_type": "duplicate_ip",
                "device": hostname,
                "interface": ", ".join(ifaces),
                "severity": "critical",
                "detail": f"IP address {ip} is assigned to multiple interfaces on {hostname}: "
                          f"{', '.join(ifaces)}. This will cause routing conflicts and "
                          f"unpredictable behavior.",
                "fix_command": f"! Change the IP on one of these interfaces:\n"
                              + "\n".join(
                                  f"interface {if_name}\n ip address <unique-ip> <mask>"
                                  for if_name in ifaces[1:]
                              ),
            })

    return issues


def check_physical_link(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect simulated physical link issues based on interface status patterns.
    In Packet Tracer, physical link failures show as both status and protocol down.
    """
    issues = []
    hostname = parsed.get("hostname", "Unknown")

    for iface in parsed.get("interfaces", []):
        name = iface.get("interface", "")
        status = iface.get("status", "").lower()
        protocol = iface.get("protocol", "").lower()
        ip = iface.get("ip", "")

        # Serial interfaces with down/down but assigned IP = cable issue
        if ("serial" in name.lower() and status == "down" and protocol == "down"
                and ip != "unassigned" and ip):
            issues.append({
                "rule": "check_physical_link",
                "failure_type": "physical_link_down",
                "device": hostname,
                "interface": name,
                "severity": "critical",
                "detail": f"Serial interface {name} on {hostname} has IP {ip} configured "
                          f"but is physically down. This indicates a cable is disconnected "
                          f"or the clock rate is not set on the DCE end.",
                "fix_command": f"interface {name}\n clock rate 64000\n no shutdown\n"
                              f"! Also check the physical cable connection in Packet Tracer",
            })

        # GigabitEthernet / FastEthernet with IP but down/down
        elif (("ethernet" in name.lower() or "gig" in name.lower()) and
              status == "down" and protocol == "down" and
              ip != "unassigned" and ip):
            issues.append({
                "rule": "check_physical_link",
                "failure_type": "physical_link_down",
                "device": hostname,
                "interface": name,
                "severity": "critical",
                "detail": f"Ethernet interface {name} on {hostname} has IP {ip} configured "
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
