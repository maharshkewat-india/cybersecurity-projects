"""Normalized Wi-Fi network record used by both scanners and the GUI."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class Network:
    ssid: str = "Hidden network"
    bssid: str = "Unknown"
    signal_strength: int | None = None
    channel: int | None = None
    security_type: str = "Unknown"
    security_status: str = "Unknown"
    connected: bool = False
    vendor: str = "Unknown"
    first_seen: str = ""
    last_seen: str = ""
    health_score: int = 0
    detected_issues: list[str] = field(default_factory=list)
    explanation: str = "Security metadata is incomplete; this is not a safety guarantee."
    @classmethod
    def from_scan(cls, values: dict[str, Any], previous: "Network | None" = None) -> "Network":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S"); signal = values.get("signal_strength")
        return cls(ssid=str(values.get("ssid") or "Hidden network"), bssid=str(values.get("bssid") or "Unknown"), signal_strength=signal if isinstance(signal, (int, float)) else None, channel=values.get("channel") if isinstance(values.get("channel"), int) else None, security_type=str(values.get("security_type") or "Unknown"), vendor=str(values.get("vendor") or "Unknown"), connected=bool(values.get("connected", False)), first_seen=previous.first_seen if previous else now, last_seen=now)
    def csv_row(self) -> dict[str, str | int]:
        """Map internal names to the stable, user-facing CSV schema."""
        return {
            "SSID": self.ssid, "BSSID": self.bssid,
            "Signal Strength": self.signal_strength if self.signal_strength is not None else "",
            "Channel": self.channel if self.channel is not None else "",
            "Security Type": self.security_type, "Security Status": self.security_status,
            "Connection": "Connected" if self.connected else "Available",
            "Vendor": self.vendor, "First Seen": self.first_seen, "Last Seen": self.last_seen,
            "Health Score": self.health_score, "Detected Issues": "; ".join(self.detected_issues),
        }
