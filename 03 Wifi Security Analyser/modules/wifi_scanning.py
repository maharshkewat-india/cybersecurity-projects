"""Passive, Windows-native Wi-Fi discovery with testable netsh parsing.

The module only asks Windows for its visible WLAN list.  It does not capture,
inject, transmit, authenticate to, or otherwise access a wireless network.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import platform
import re
import subprocess
from typing import Any

NETSH_COMMAND = ("netsh", "wlan", "show", "networks", "mode=bssid")
MAC_PATTERN = re.compile(r"(?i)(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}")
PERCENT_PATTERN = re.compile(r"(?<!\d)(\d{1,3})\s*%")

# Small offline convenience map. A value not listed here deliberately remains
# Unknown; this project does not claim an exhaustive or online OUI database.
OUI_VENDORS = {
    "001422": "Cisco", "3C846A": "TP-Link", "A45E60": "Ubiquiti",
    "204E7F": "Netgear", "F4F5D8": "Aruba", "B827EB": "Raspberry Pi",
}


@dataclass
class ScanDiagnostic:
    """Command evidence retained for a user-readable diagnostics panel."""
    command: str = " ".join(NETSH_COMMAND)
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    adapter: str = "Unknown"
    connected_ssid: str = ""
    windows_version: str = platform.platform()
    parser_note: str = "Not scanned yet"

    def details(self) -> str:
        output = self.stdout.strip() or "(no standard output)"
        error = self.stderr.strip() or "(no standard error)"
        return (f"Command: {self.command}\nReturn code: {self.return_code}\n"
                f"Adapter: {self.adapter}\nConnected SSID: {self.connected_ssid or 'None detected'}\nWindows: {self.windows_version}\n"
                f"Parser: {self.parser_note}\n\nstdout:\n{output}\n\nstderr:\n{error}")


@dataclass
class ScanOutcome:
    networks: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    diagnostic: ScanDiagnostic = field(default_factory=ScanDiagnostic)


def _canonical_label(label: str) -> str | None:
    """Recognize common English and selected localized netsh field labels."""
    normalized = re.sub(r"\s+", " ", label.casefold()).strip()
    if re.search(r"(?<!b)ssid", normalized):
        return "ssid"
    if "bssid" in normalized or "mac" in normalized:
        return "bssid"
    if any(word in normalized for word in ("signal", "señal", "sinal", "signalstärke", "signaal")):
        return "signal"
    if any(word in normalized for word in ("channel", "kanal", "canal", "canale")):
        return "channel"
    if any(word in normalized for word in ("authentication", "authentification", "autentic", "autenticação", "sicherheit")):
        return "authentication"
    if any(word in normalized for word in ("encryption", "verschlüssel", "chiffrement", "cifrado", "criptografia")):
        return "encryption"
    return None


def normalize_security(authentication: str | None, encryption: str | None = None) -> str:
    """Turn Windows authentication/encryption text into the app's safe labels."""
    text = " ".join(value for value in (authentication, encryption) if value).upper()
    has_wpa3, has_wpa2 = "WPA3" in text, "WPA2" in text
    if has_wpa3 and has_wpa2:
        return "WPA2/WPA3"
    if has_wpa3:
        return "WPA3-Enterprise" if "ENTERPRISE" in text else "WPA3"
    if has_wpa2:
        return "WPA2-Enterprise" if "ENTERPRISE" in text else "WPA2"
    if "WPA" in text:
        return "WPA/WPA2" if "WPA2" in text else "WPA"
    if "WEP" in text:
        return "WEP"
    if any(word in text for word in ("OPEN", "NONE", "NO SECURITY", "UNSECURED")):
        return "Open"
    return "Unknown"


def vendor_from_bssid(bssid: str | None) -> str:
    """Perform a deliberately limited offline OUI lookup."""
    prefix = re.sub(r"[^0-9A-Fa-f]", "", bssid or "").upper()[:6]
    return OUI_VENDORS.get(prefix, "Unknown")


def parse_netsh_output(output: str) -> list[dict[str, Any]]:
    """Parse variant netsh output without requiring every field to exist.

    A separate record is produced for each BSSID.  An SSID with no BSSID is
    preserved as an Unknown-BSSID record rather than discarded.
    """
    networks: list[dict[str, Any]] = []
    current: dict[str, Any] = {"ssid": "Hidden network", "authentication": "", "encryption": ""}
    bssid_record: dict[str, Any] | None = None

    def emit_bssid() -> None:
        nonlocal bssid_record
        if bssid_record is None:
            return
        auth = str(current.get("authentication", ""))
        encryption = str(current.get("encryption", ""))
        bssid_record["security_type"] = normalize_security(auth, encryption)
        bssid_record["authentication"] = auth or "Unknown"
        bssid_record["encryption"] = encryption or "Unknown"
        bssid_record["vendor"] = vendor_from_bssid(bssid_record.get("bssid"))
        networks.append(bssid_record)
        bssid_record = None

    def emit_ssid_without_bssid() -> None:
        if current.get("has_ssid") and not current.get("had_bssid"):
            auth = str(current.get("authentication", "")); encryption = str(current.get("encryption", ""))
            networks.append({"ssid": current.get("ssid") or "Hidden network", "bssid": "Unknown",
                             "signal_strength": None, "channel": None,
                             "security_type": normalize_security(auth, encryption),
                             "authentication": auth or "Unknown", "encryption": encryption or "Unknown",
                             "vendor": "Unknown"})

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        label, separator, value = line.partition(":")
        field = _canonical_label(label) if separator else None
        if field == "ssid" and not MAC_PATTERN.search(line):
            emit_bssid(); emit_ssid_without_bssid()
            current = {"ssid": value.strip() or "Hidden network", "authentication": "", "encryption": "", "has_ssid": True, "had_bssid": False}
        elif field == "authentication":
            current["authentication"] = value.strip()
        elif field == "encryption":
            current["encryption"] = value.strip()
        elif field == "bssid" or (bssid_record is None and MAC_PATTERN.search(line)):
            emit_bssid()
            match = MAC_PATTERN.search(value if separator else line)
            if match:
                current["had_bssid"] = True
                bssid_record = {"ssid": current.get("ssid") or "Hidden network", "bssid": match.group(0).replace("-", ":").lower(), "signal_strength": None, "channel": None}
        elif bssid_record is not None and field == "signal":
            match = PERCENT_PATTERN.search(value)
            bssid_record["signal_strength"] = min(100, int(match.group(1))) if match else None
        elif bssid_record is not None and field == "channel":
            match = re.search(r"\d+", value)
            bssid_record["channel"] = int(match.group()) if match else None
    emit_bssid(); emit_ssid_without_bssid()
    return networks


def parse_interface_output(output: str) -> tuple[str, str, str]:
    """Parse adapter name and connected SSID/BSSID from netsh output."""
    name, description, ssid, bssid, state = "Unknown", "", "", "", ""
    for line in output.splitlines():
        label, separator, value = line.partition(":")
        if not separator:
            continue
        field = label.strip().casefold()
        if field == "name":
            name = value.strip() or "Unknown"
        elif field == "description":
            description = value.strip()
        elif field == "ssid":
            ssid = value.strip()
        elif field == "bssid":
            bssid = value.strip().lower()
        elif field == "state":
            state = value.strip().casefold()
    connected = state == "connected"
    return description or name, ssid if connected else "", bssid if connected else ""


def mark_connected_networks(networks: list[dict[str, Any]], ssid: str, bssid: str = "") -> None:
    """Mark the active access point and preserve it if the nearby list omits it."""
    matched = False
    for network in networks:
        network["connected"] = bool(ssid) and (
            network.get("bssid", "").casefold() == bssid.casefold()
            if bssid
            else network.get("ssid", "").casefold() == ssid.casefold()
        )
        matched = matched or network["connected"]
    if ssid and not matched:
        networks.append({
            "ssid": ssid, "bssid": bssid or "Unknown", "signal_strength": None,
            "channel": None, "security_type": "Unknown", "authentication": "Unknown",
            "encryption": "Unknown", "vendor": vendor_from_bssid(bssid), "connected": True,
        })


def get_windows_interface_info() -> tuple[str, str, str]:
    """Return the active adapter and connected SSID/BSSID when available."""
    try:
        result = subprocess.run(("netsh", "wlan", "show", "interfaces"), capture_output=True,
                                text=True, timeout=10, check=False, encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return "Unknown", "", ""
    return parse_interface_output(result.stdout)


def get_windows_adapter() -> str:
    """Best-effort adapter name for diagnostics; failure is non-fatal."""
    return get_windows_interface_info()[0]


def discover_networks() -> ScanOutcome:
    """Execute passive Windows discovery and return records plus diagnostics."""
    adapter, connected_ssid, connected_bssid = get_windows_interface_info()
    diagnostic = ScanDiagnostic(adapter=adapter, connected_ssid=connected_ssid)
    if platform.system() != "Windows":
        diagnostic.parser_note = "Unsupported operating system"
        return ScanOutcome(error="Windows Wi-Fi discovery is unavailable on this system. Use Demo Mode to explore the application.", diagnostic=diagnostic)
    try:
        result = subprocess.run(NETSH_COMMAND, capture_output=True, text=True, timeout=15,
                                check=False, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired as exc:
        diagnostic.stderr = str(exc); diagnostic.parser_note = "Command timed out"
        return ScanOutcome(error="Windows Wi-Fi discovery timed out. Check the Wi-Fi adapter and WLAN AutoConfig service.", diagnostic=diagnostic)
    except OSError as exc:
        diagnostic.stderr = str(exc); diagnostic.parser_note = "Could not start netsh"
        return ScanOutcome(error="Windows Wi-Fi discovery failed because netsh could not be started.", diagnostic=diagnostic)
    diagnostic.return_code, diagnostic.stdout, diagnostic.stderr = result.returncode, result.stdout, result.stderr
    if result.returncode != 0:
        diagnostic.parser_note = "netsh returned an error"
        return ScanOutcome(error="Windows Wi-Fi discovery failed. Open Scan Diagnostics for the command result and suggested fixes.", diagnostic=diagnostic)
    networks = parse_netsh_output(result.stdout)
    mark_connected_networks(networks, connected_ssid, connected_bssid)
    diagnostic.parser_note = f"Parsed {len(networks)} network record(s)"
    if not networks:
        return ScanOutcome(error="No nearby Wi-Fi networks were detected. Check Wi-Fi, the adapter, and WLAN AutoConfig, then retry.", diagnostic=diagnostic)
    return ScanOutcome(networks=networks, diagnostic=diagnostic)


def scan_networks() -> tuple[list[dict[str, Any]], str | None]:
    """Compatibility wrapper for older callers."""
    outcome = discover_networks()
    return outcome.networks, outcome.error
