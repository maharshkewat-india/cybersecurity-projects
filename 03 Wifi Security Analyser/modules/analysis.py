"""Transparent deterministic metadata assessment; it is never a safety guarantee."""
from __future__ import annotations
from collections import Counter
from .network_model import Network

def analyse(network: Network, channels: Counter[int]) -> Network:
    security, issues = network.security_type.upper().replace(" ", ""), []
    if security in {"OPEN", "NONE"}: base, status = 15, "Vulnerable"; issues.append("Open network detected: no Wi-Fi encryption is reported.")
    elif security == "WEP": base, status = 5, "Vulnerable"; issues.append("Legacy WEP encryption detected.")
    elif security == "WPA": base, status = 35, "Moderate"; issues.append("WPA is outdated; prefer WPA2 or WPA3.")
    elif security == "WPA/WPA2": base, status = 60, "Moderate"; issues.append("Mixed WPA/WPA2 compatibility is reported.")
    elif security == "WPA2": base, status = 75, "Moderate"; issues.append("WPA2 is common, but metadata alone cannot prove safety.")
    elif security == "WPA2/WPA3": base, status = 80, "Moderate"; issues.append("Mixed WPA2/WPA3 compatibility is reported.")
    elif security in {"WPA3", "WPA2-ENTERPRISE", "WPA3-ENTERPRISE"}: base, status = 90, "Secure"
    else: base, status = 45, "Unknown"; issues.append("Security metadata is incomplete or unavailable.")
    if network.signal_strength is None: issues.append("Signal metadata is unavailable."); base -= 5
    elif network.signal_strength < 20: issues.append("Very weak signal may affect connection reliability."); base -= 5
    if network.channel is None: issues.append("Channel metadata is unavailable."); base -= 5
    elif channels[network.channel] >= 3: issues.append("Channel is heavily occupied."); base -= 8
    if network.vendor == "Unknown": issues.append("Vendor is unavailable from the local OUI lookup."); base -= 3
    network.health_score, network.security_status, network.detected_issues = max(0, min(100, base)), status, issues
    network.explanation = f"Score {network.health_score}/100 uses reported encryption, available signal/channel metadata, local channel occupancy, and vendor availability. It is not a guarantee of real-world security."
    return network

def analyse_all(networks: list[Network]) -> list[Network]:
    counts = Counter(x.channel for x in networks if x.channel is not None)
    return [analyse(network, counts) for network in networks]
