"""Deterministic local records for hardware-independent demonstrations."""
from __future__ import annotations
from typing import Any

def demo_networks() -> list[dict[str, Any]]:
    return [
        {"ssid":"Northstar-WPA3", "bssid":"20:4E:7F:18:22:01", "signal_strength":92, "channel":36, "security_type":"WPA3", "vendor":"Netgear"},
        {"ssid":"MapleHome", "bssid":"3C:84:6A:91:04:11", "signal_strength":76, "channel":6, "security_type":"WPA2", "vendor":"TP-Link"},
        {"ssid":"Coffee_Guest", "bssid":"A4:5E:60:22:19:02", "signal_strength":64, "channel":6, "security_type":"Open", "vendor":"Ubiquiti"},
        {"ssid":"Legacy-WEP", "bssid":"00:14:22:71:90:33", "signal_strength":52, "channel":11, "security_type":"WEP", "vendor":"Cisco"},
        {"ssid":"OldOffice", "bssid":"B8:27:EB:66:03:20", "signal_strength":18, "channel":1, "security_type":"WPA", "vendor":"Raspberry Pi"},
        {"ssid":"Acme-Enterprise", "bssid":"F4:F5:D8:02:77:10", "signal_strength":88, "channel":44, "security_type":"WPA3-Enterprise", "vendor":"Aruba"},
    ]
