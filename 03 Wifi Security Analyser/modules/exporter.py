"""Safe UTF-8 CSV exports for normalized results."""
from __future__ import annotations
import csv
from pathlib import Path
from .network_model import Network
FIELDS = ["SSID", "BSSID", "Signal Strength", "Channel", "Security Type", "Security Status", "Connection", "Vendor", "First Seen", "Last Seen", "Health Score", "Detected Issues"]
def export_csv(path: str, networks: list[Network]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS); writer.writeheader()
        for network in networks: writer.writerow(network.csv_row())
