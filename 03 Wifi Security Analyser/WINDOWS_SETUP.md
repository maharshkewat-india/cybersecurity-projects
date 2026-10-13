# Windows setup

## Install and run

1. Install Python 3.10 or later from [python.org](https://www.python.org/downloads/windows/) and select **Add Python to PATH**.
2. Open PowerShell in this project directory.
3. Create and activate a virtual environment:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item config.json.example config.json
python GUI_Module.py
```

If PowerShell prevents activation, run `Set-ExecutionPolicy -Scope Process Bypass` for the current shell, then activate again.

## Demo Mode

Demo Mode starts by default. It is completely local and requires no administrator access, Wi-Fi adapter, Npcap, packet capture, or internet connection. The green banner **DEMO MODE — SIMULATED DATA** makes the simulated nature of the results explicit.

## Authorized real scanning

Choose **Start Real Scan** in the application. The program makes one passive request through Windows' built-in `netsh wlan show networks mode=bssid` command; it does not capture traffic or transmit Wi-Fi frames. Results require a working Wi-Fi adapter, drivers, the Windows WLAN AutoConfig service, and a location where Windows can report nearby networks. Administrator access is not normally required for this method, but an organization or device driver may restrict it.

If scanning is unavailable, the application reports the reason in Logs and remains open. Return to Demo Mode to use every dashboard feature.

Npcap is not used or required by this version.

## Settings and files

`config.json` controls `scan_interval` (1–3600 seconds), `demo_mode`, `auto_scan`, and `log_level`. Missing or invalid configuration safely falls back to defaults. Application log files are stored under `logs/`; the Logs tab can also save its visible contents anywhere you choose. CSV export uses the save-file dialog and supports cancellation safely.
