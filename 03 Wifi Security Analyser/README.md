# Wi-Fi Security Analyzer

A defensive desktop application for passive, authorized Wi-Fi discovery and local security-metadata analysis. It does not collect passwords, capture traffic, inject packets, deauthenticate clients, or attempt access to any network.

## Quick start (Windows)

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item config.json.example config.json
python GUI_Module.py
```

The application opens in **DEMO MODE — SIMULATED DATA** by default. It needs no Wi-Fi adapter, administrator privileges, Npcap, or internet access. Select **Start Demo Mode** at any time.

To request authorized, passive real discovery, run the same command and select **Start Real Scan**. On Windows this uses the built-in `netsh wlan show networks mode=bssid` command; results depend on your adapter, driver, WLAN service, and local permissions. An unsupported system shows a friendly message and leaves the app usable.

## Features

- Normalized results with SSID, BSSID, signal, channel, security type/status, vendor, first/last seen time, score, and issues.
- Transparent 0–100 score based on encryption metadata, missing fields, weak signal, and local channel occupancy. It is never a security guarantee.
- Sortable/filterable network table, dashboard cards, security analysis, signal/security/channel charts, live application log, CSV export, and JSON settings.
- Real scans list all nearby networks Windows reports and mark the active access point **Connected**; other results are marked **Available**.
- Deterministic demo data: WPA3, WPA2, open, WEP, WPA, and enterprise-style examples.

## Configuration

`config.json` is optional; safe defaults apply when it is missing or invalid.

```json
{
  "scan_interval": 10,
  "demo_mode": true,
  "auto_scan": false,
  "log_level": "INFO"
}
```

Use **File → Settings** to update scan interval and startup mode. `scan_interval` accepts 1–3600 seconds. Invalid values are reported in Logs and replaced safely.

## Export and logs

Use **File → Export Results** or **Export CSV** to choose a CSV path. The file contains SSID, BSSID, signal strength, channel, security data, connection status, timestamps, score, and detected issues. Use **Logs → Save Logs** to save the displayed log; **Clear Logs** only clears the display.

## Requirements

Python 3.10+ with PyQt6 and Matplotlib. See [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for detailed Windows troubleshooting. The project remains MIT licensed.

For a source-accurate architecture explanation, user manual, score rules, testing record, viva questions, and presentation/report outline, see [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md).
