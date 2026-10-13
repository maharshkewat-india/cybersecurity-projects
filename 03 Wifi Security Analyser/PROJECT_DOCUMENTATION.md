# Wi-Fi Security Analyzer

## 1. Project identity

| Item | Description |
|---|---|
| Title | **Wi-Fi Security Analyzer** |
| Full form | Wi-Fi means *Wireless Fidelity*; the project has no longer expanded acronym. |
| Type | Defensive desktop network-discovery and security-metadata analysis application. |
| Domain | Cybersecurity, wireless networking, and desktop software. |
| Technology | Python, PyQt6, Matplotlib, JSON, CSV, and Windows `netsh`. |
| Target users | Students, teachers, cybersecurity learners, IT staff, and authorized network administrators. |
| Main objective | Show nearby or simulated Wi-Fi metadata, explain basic security concerns, and present them clearly. |

**Viva introduction:** “Wi-Fi Security Analyzer is a Python desktop application that passively reads nearby Wi-Fi metadata on Windows or displays deterministic demo data. It assigns a transparent heuristic score from encryption and available metadata, then presents results in a table, charts, logs, and a CSV export. It is defensive: it does not attempt to access, attack, or recover credentials from networks.”

## 2. What the project does

### Simple explanation

Think of the app as a health-check dashboard for Wi-Fi names visible around a device. It tells the user which networks appear open, obsolete, modern, or unknown **from the information that Windows reports**. It does not prove a network is safe and it does not join it.

### Technical explanation

The application obtains a list of networks from one of two sources:

1. `demo_networks()` returns six fixed local records.
2. On Windows, `scan_networks()` executes `netsh wlan show networks mode=bssid`, parses its text output, and normalizes discovered BSSIDs into dictionaries.

Each dictionary becomes a `Network` object. `analyse_all()` applies deterministic rules to security type, signal/channel availability, vendor availability, and channel occupancy. The GUI displays the enriched objects.

**Collected:** SSID, BSSID when Windows supplies it, the Windows-reported signal percentage, channel, authentication/encryption-derived security type, connection status (Connected or Available), first/last seen times, and vendor information from a small offline OUI map when available. **Not collected:** passwords, encryption keys, web traffic, packets, credentials, device contents, client identities, handshakes, or location.

| Term | Plain meaning | Actual project meaning |
|---|---|---|
| Network discovery | Listing available Wi-Fi networks. | Demo records or Windows `netsh` output. |
| Passive scanning | Observing/listing rather than transmitting attacks. | The app asks Windows for its available-network list; it does not inject frames or capture traffic. |
| Security status | A readable category. | `Secure`, `Moderate`, `Vulnerable`, or `Unknown` based on `security_type`. |
| Security score | A helpful estimate, not a guarantee. | A bounded 0–100 heuristic calculated by `modules/analysis.py`. |
| Demo Mode | A safe simulation. | Six deterministic local records, no adapter/admin/internet needed. |

## 3. Motivation, scope, and ethical boundary

Checking a Wi-Fi environment manually can be confusing: encryption labels, signal values, and channel choices are spread across operating-system output. This app groups those facts, flags open/WEP/WPA metadata, provides a simple score, makes trends visible through charts, keeps an event record, and lets a user export an inventory as CSV. Demo Mode makes the concepts demonstrable on a computer with no suitable adapter.

This is **security analysis**, not penetration testing. Security analysis here means interpreting observed network metadata. It is not a complete vulnerability assessment because it does not verify configuration, patch level, passwords, access controls, or live traffic. It is not an attack tool: no password cracking, key recovery, deauthentication, packet injection, evil-twin creation, credential harvesting, handshake cracking, exploitation, or unauthorized access is implemented.

Use real scanning only where you are authorized to observe the wireless environment: for example, your own home, a permitted college lab, a managed office, or a classroom demonstration.

## 4. When, where, and who

Useful situations include cybersecurity education, viva demonstrations, laboratory exercises, home/office Wi-Fi awareness, authorized basic network inventory, and learning the difference between Open, WEP, WPA, WPA2, and WPA3 labels. Demo Mode is best for a first demonstration, an unsupported computer, or any presentation where real data is not desired. Real Scan is suitable for an authorized Windows environment with a functioning Wi-Fi adapter.

Demo Mode needs only basic computer skills. Real scanning also requires awareness of local authorization, Windows services, adapter/driver limitations, and the fact that results are metadata. Understanding the score requires basic familiarity with encryption names and Wi-Fi channels; the analysis tab supplies plain-language issue text.

## 5. How it works

```text
START
  |
Load config.json (or safe defaults)
  |
Create QApplication, MainWindow, tabs, log file
  |
Demo Mode enabled? ---- yes ---> demo_networks()
  | no / user clicks Real Scan
  v
ScanWorker thread -> Windows netsh -> parsed dictionaries
  |
Network.from_scan() -> Network objects -> analyse_all()
  |
Dashboard + sortable table + analysis text + charts + logs
  |
Optional: CSV save dialog / log save dialog / settings save
  |
END
```

At startup `modules.config.Config` reads `config.json`. `MainWindow` constructs tabs and logging, then either starts Demo Mode (`demo_mode: true`) or optionally starts the worker (`auto_scan: true`). The worker never calls GUI widgets directly: it emits Qt signals; Qt delivers those results to `_accept_rows()` on the GUI side. `_accept_rows()` preserves a first-seen timestamp for a repeated BSSID/SSID key, performs analysis, and refreshes all visual components.

## 6. Architecture and data flow

```text
Demo data -------------------+
                             v
Windows Wi-Fi adapter -> netsh -> wifi_scanning.py
                             | normalized dictionaries
                             v
                    network_model.Network
                             |
                    analysis.analyse_all
                             | score, status, issues
                             v
       GUI_Module.MainWindow -> dashboard/table/analysis/charts/logs
                             |
                       exporter.export_csv
```

The supplied reference diagram may show items such as a threat monitor, packet analysis, ML/vulnerability prediction, a web dashboard, a separate error handler, or network-history/performance modules. **Those are not part of this final implementation.** The final project deliberately uses a smaller architecture: no packet capture, no Scapy, no traffic monitor, no machine-learning model, no web server, and no separate vendor database. History is limited to the in-memory `MainWindow.history` dictionary used to preserve `first_seen`; it is not a separate historical database or screen.

| Component | File | Input → processing → output |
|---|---|---|
| GUI | `GUI_Module.py` | User actions/results → widgets and refresh methods → visible dashboard/tabs. |
| Configuration | `modules/config.py` | JSON → validate/merge defaults → configuration values and warning messages. |
| Demo data | `modules/demo_data.py` | None → fixed records → six network dictionaries. |
| Real scanner | `modules/wifi_scanning.py` | Windows command output → text parser → normalized dictionaries or friendly error. |
| Network model | `modules/network_model.py` | Dictionary + prior item → safe typed `Network` → CSV-ready row. |
| Security analysis | `modules/analysis.py` | `Network` objects + channel counts → statuses, score, explanation, issues. |
| Visualizations | `GUI_Module.py` | Current analyzed records → Matplotlib plots → embedded chart canvas. |
| Logging | `GUI_Module.py` / Python `logging` | App events → visible text and `logs/wifi_analyzer.log`. |
| Export | `modules/exporter.py` | Analyzed records + chosen path → UTF-8 BOM CSV. |

## 7. Folder and source-file guide

```text
GUI_Module.py                 Main executable GUI and ScanWorker
wifi_analyzer.py              Compatibility launcher; calls GUI_Module.main
run_wifi_analyzer.bat         Double-click Windows launcher
modules/
  __init__.py                 Package marker/documentation
  config.py                   Safe JSON configuration
  demo_data.py                Six simulated input records
  wifi_scanning.py            Passive Windows parser
  network_model.py            Network dataclass/CSV mapping
  analysis.py                 Deterministic status and score rules
  exporter.py                 CSV writer
requirements.txt              PyQt6 and Matplotlib dependencies
config.json.example           Example startup settings
README.md                     Short project overview
WINDOWS_SETUP.md              Windows setup and limitations
PROJECT_DOCUMENTATION.md      This complete guide
LICENSE                       Existing MIT license
```

`GUI_Module.py` imports the modules listed above, creates `ScanWorker`, `NumericItem`, and `MainWindow`, and defines `main()`. `NumericItem` stores a numeric Qt user-role value so signal, channel, and score sort numerically rather than alphabetically. `wifi_analyzer.py` has no separate logic; it imports and executes `main()`.

`Config.load()` returns a validated dictionary. `Config.get()` returns one value, and `Config.set()` writes an allowed setting to `config.json`. `demo_networks()` returns a list of dictionaries. `scan_networks()` returns `(list[dict], error_message_or_None)`. `Network.from_scan()` accepts incomplete dictionaries safely and returns a `Network`; `csv_row()` returns the exact export schema. `analyse()` mutates/returns one enriched network, `analyse_all()` returns all enriched networks, and `export_csv()` writes them.

`run_wifi_analyzer.bat` changes to its own folder, creates `.venv` when missing, installs dependencies once, copies `config.json.example` when needed, then runs `GUI_Module.py`. Its `.dependencies-installed` marker means that after changing `requirements.txt`, delete that marker or run pip manually to reinstall dependencies.

## 8. GUI and controls

The main window uses a tab widget and a mode banner. Demo has a green banner; real discovery uses a blue banner. The Dashboard has six cards: Networks Found, Secure Networks, Warning Networks, High-Risk Networks, Average Security Score, and Last Scan Time.

| Control | User result | Internal behavior |
|---|---|---|
| Start Demo Mode | Loads sample results. | Stops an active worker, calls `demo_networks()`, then `_accept_rows()`. |
| Start Real Scan | Requests repeated passive discovery. | Starts `ScanWorker` with configured interval. |
| Stop Scan | Stops future worker work. | Sets worker `running=False`; a currently running OS command returns naturally. |
| Clear Results | Empties displayed results. | Clears only `self.networks`, then refreshes widgets. |
| Search | Filters displayed table rows. | Case-insensitive match on SSID, security type, vendor, or status. |
| Column header | Sorts rows. | Qt sorting; signal/channel/score use `NumericItem`. |
| Export CSV | Chooses CSV destination. | Calls `export_csv()` if the dialog returns a path. |
| Clear Logs | Clears the log tab. | Clears visible text; an INFO message remains in the file logger. |
| Save Logs | Saves displayed log text. | Uses a save dialog and `Path.write_text()`. |
| File → Settings | Changes startup options. | Valid settings are persisted through `Config.set()`. |

The table contains SSID, Signal, Channel, Security, Vendor, Status, Score, and Last Seen. Status cells are green (`Secure`), yellow (`Moderate`), orange/red (`Vulnerable`), or grey (`Unknown`). The Security Analysis tab describes every displayed network and repeats that the score is not a safety guarantee.

## 9. Demo Mode

Demo Mode is a local, deterministic simulation. It needs **no Wi-Fi hardware, administrator privileges, packet capture, internet connection, or Windows `netsh` result**. Its six records are:

| SSID | Security | Signal | Channel | Vendor |
|---|---:|---:|---:|---|
| Northstar-WPA3 | WPA3 | 92% | 36 | Netgear |
| MapleHome | WPA2 | 76% | 6 | TP-Link |
| Coffee_Guest | Open | 64% | 6 | Ubiquiti |
| Legacy-WEP | WEP | 52% | 11 | Cisco |
| OldOffice | WPA | 18% | 1 | Raspberry Pi |
| Acme-Enterprise | WPA3-Enterprise | 88% | 44 | Aruba |

The sample function itself does not contain timestamps. `Network.from_scan()` assigns first/last seen timestamps at the time Demo Mode is loaded. Its fixed signal, channel, and vendor values are sample metadata, not measurements. The GUI mode banner explicitly identifies the data as simulated.

## 10. Real Wi-Fi scanning

The actual Windows command is:

```powershell
netsh wlan show networks mode=bssid
```

`subprocess.run()` executes it with captured text output, UTF-8 decoding with replacement for invalid characters, a 15-second timeout, and no shell. The parser recognizes:

- `SSID <number> :` → SSID; empty names become `Hidden network`.
- `Authentication :` → security text.
- `BSSID <number> :` → BSSID; each BSSID becomes one record.
- `Signal : <percent>%` → the original 0–100 percentage, clamped to 100. The project does not fabricate a dBm value.
- `Channel :` → integer channel.

Authentication/encryption text containing WPA3, WPA2, WPA, or WEP maps to that security type; mixed WPA2/WPA3 and WPA/WPA2 are retained. `OPEN` or `NONE` maps to `Open`; otherwise it maps to `Unknown`. A deliberately small offline OUI map may identify a known BSSID prefix; unmatched prefixes display `Unknown`. Missing signal/channel fields become `None`, render as `Unknown`, and add corresponding issue text. The scanner also retains command, return-code, stdout, stderr, parser, adapter, and Windows details for the diagnostic panel.

Requirements: Windows, a functioning Wi-Fi adapter/driver, Windows WLAN capability, and authorization to observe nearby networks. Administrator rights are not normally required for this `netsh` approach, though device policy/drivers may restrict results. On non-Windows systems, command failures, timeout, non-zero return, or no results, the scanner returns a friendly message directing the user to Demo Mode; the GUI remains open.

## 11. Network data model

| Field | Meaning / example | Source and display |
|---|---|---|
| SSID | Network name, e.g. `MapleHome`. | Demo or `netsh`; table, charts, CSV. |
| BSSID | Access-point radio MAC, e.g. `3C:84:...`. | Demo or `netsh`; CSV and in-memory history key. |
| Signal Strength | Windows-style signal percentage, e.g. `76%`. | Demo or original Windows percent; table/chart. |
| Channel | Radio channel, e.g. `6`. | Demo or `netsh`; table/channel chart. |
| Security Type | Encryption/authentication label, e.g. WPA2. | Demo or parsed authentication. |
| Security Status | Readable assessment category. | Set by `analyse()`. |
| Vendor | Demo vendor or `Unknown`. | No real OUI lookup exists. |
| First Seen / Last Seen | Local application timestamps. | Assigned by `from_scan()`; first time is preserved during repeat results in the running app. |
| Health Score | 0–100 heuristic. | Set by `analyse()`; table/dashboard/CSV. |
| Detected Issues | Plain-language reasons. | Set by `analyse()`; analysis tab/CSV. |

## 12. Security rules and score

The score is entirely deterministic. It is a metadata heuristic; it does not state that a network is 100% safe.

| Security input | Base score | Status | Rule/issue |
|---|---:|---|---|
| Open or None | 15 | Vulnerable | “Open network detected: traffic may be exposed.” |
| WEP | 5 | Vulnerable | “WEP is obsolete and should not be trusted.” |
| WPA | 35 | Moderate | “WPA is outdated; prefer WPA2 or WPA3.” |
| WPA2 | 75 | Moderate | Adds caution that metadata cannot prove safety. |
| WPA3 / WPA2-Enterprise / WPA3-Enterprise | 90 | Secure | No encryption-specific issue is added. |
| Other/Unknown | 45 | Unknown | Security metadata incomplete/unavailable. |

After the base score, the code applies these deductions:

| Condition | Deduction | Issue |
|---|---:|---|
| Signal missing | -5 | Signal metadata unavailable. |
| Signal below 20% | -5 | Very weak signal may affect reliability. |
| Channel missing | -5 | Channel metadata unavailable. |
| At least 3 visible networks use same channel | -8 | Channel is heavily occupied. |
| Vendor is `Unknown` | -3 | Vendor metadata unavailable. |

The final value is clamped with `max(0, min(100, base))`. Status is determined by security type, not by numerical thresholds. Example Demo results (there are only two networks on channel 6, so no congestion deduction):

| Network | Calculation | Result |
|---|---|---:|
| Northstar-WPA3 | 90 | 90, Secure |
| MapleHome | 75 | 75, Moderate |
| Coffee_Guest | 15 | 15, Vulnerable |
| Legacy-WEP | 5 | 5, Vulnerable |
| OldOffice | 35 - 5 very weak signal | 30, Moderate |
| Acme-Enterprise | 90 | 90, Secure |

The vendor penalty does not apply to the demo examples because each has a vendor. Real scan records normally have `Unknown` vendor, so a WPA3 real record with complete signal/channel metadata will typically score 87.

## 13. Visualizations

The Visualizations tab is refreshed every time `_accept_rows()` receives results.

| Chart | Input / axes | Value to user |
|---|---|---|
| Signal Strength | SSID on x-axis, percentage on y-axis. | Compares Windows-reported signal levels. |
| Security Status | Count of each status as a pie chart. | Shows the distribution of Secure/Moderate/Vulnerable/Unknown. |
| Channel Usage | Channel number on x-axis, network count on y-axis. | Highlights locally crowded visible channels. |

Matplotlib labels are converted to ASCII replacement characters for the chart only, avoiding a crash/warning from unsupported SSID glyphs in default fonts. This does not change the table or exported SSID.

## 14. Logging and CSV export

Python `logging` writes to `logs/wifi_analyzer.log`; `_log()` also adds timestamped lines to the Logs tab. The configured level can be `DEBUG`, `INFO`, `WARNING`, or `ERROR`; the current code emits INFO for startup/configuration/demo/scan/export/settings events, WARNING for unavailable or invalid configuration/scanning, and ERROR for export/log-save failures. Do not add passwords, keys, raw packet payloads, or other credentials to logs.

CSV export begins with a normal save-file dialog. Cancel returns an empty path and does nothing. A file write failure is caught as `OSError`, logged as ERROR, and shown in a warning dialog. The file is UTF-8 with BOM, useful for spreadsheet compatibility.

```csv
SSID,BSSID,Signal Strength,Channel,Security Type,Security Status,Vendor,First Seen,Last Seen,Health Score,Detected Issues
MapleHome,3C:84:6A:91:04:11,-57,6,WPA2,Moderate,TP-Link,2026-...,2026-...,75,"WPA2 is common, but metadata alone cannot prove safety."
```

## 15. Configuration

`config.json` is optional. Missing/invalid files return safe in-memory defaults and produce a warning in the visible log. A missing file is not automatically written at startup; Settings or `run_wifi_analyzer.bat` can create it.

| Key | Type/default | Valid range | Effect |
|---|---|---|---|
| `scan_interval` | integer, `10` | 1–3600 seconds | Interval between worker scans after the current scan finishes. |
| `demo_mode` | boolean, `true` | `true` / `false` | Starts deterministic Demo Mode at launch. |
| `auto_scan` | boolean, `false` | `true` / `false` | With Demo Mode off, starts real scanning at launch. |
| `log_level` | string, `INFO` | DEBUG/INFO/WARNING/ERROR | Initial Python logger threshold. |

Unknown JSON keys are ignored. Missing supported keys retain defaults. Wrong booleans, invalid interval, invalid level, non-object JSON, or invalid JSON cause a safe fallback/value replacement and a recorded message. Settings UI changes `scan_interval`, `demo_mode`, and `auto_scan`; it does **not** expose a log-level control.

## 16. Technology stack

| Technology | What/where | Advantage and limitation |
|---|---|---|
| Python 3.10+ | Entire application. | Fast development, readable modular code; needs interpreter/environment. |
| PyQt6 | Window, tabs, widgets, signals, dialogs, QThread. | Native-style desktop GUI; Python package required. |
| Matplotlib | Three embedded charts. | Familiar static plotting; current charts refresh whole figure. |
| JSON | `config.json`. | Human-readable configuration; malformed JSON must be handled. |
| CSV / `csv` module | Results export. | Spreadsheet-friendly; not a database/history system. |
| Windows `netsh` | Real scanner only. | No packet library required; Windows-specific and output/adapter dependent. |

Python is suitable because it supports GUI work, subprocess invocation, data transformation, charting, and clear modular teaching examples. PyQt6 supplies layouts, tables, dialogs, signals/slots, and a thread class. Matplotlib turns numeric and categorical results into readable visual summaries.

## 17. Installation and user guide

### Fastest Windows launch

Double-click `run_wifi_analyzer.bat`. The first run needs Python and internet access to install PyQt6/Matplotlib.

### Manual PowerShell installation

```powershell
cd E:\project
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item config.json.example config.json
python GUI_Module.py
```

In Command Prompt, activate with `.venv\Scripts\activate.bat`. If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process Bypass` in that PowerShell window, then activate. The compatibility command `python wifi_analyzer.py` opens the same GUI.

### Use Demo Mode

1. Launch the application; default config loads Demo Mode.
2. Or choose **Network Scanner → Start Demo Mode**.
3. Review the green demo banner, Dashboard, table, Security Analysis, Visualizations, and Logs.
4. Click headers to sort and type SSID/security/vendor text in Search to filter.

### Use Real Scan

1. Confirm that observing the current Wi-Fi environment is authorized.
2. Launch the app and select **Start Real Scan**.
3. Review Windows-reported results; use **Stop Scan** when finished.
4. If the log says it is unavailable/no networks, use Demo Mode; do not try to bypass permissions or driver restrictions.

### Analysis, export, logs, and settings

Open **Security Analysis** to read the score and detected issues. Open **Visualizations** for the three charts. Use **Export CSV...** and select a writable file. Open **Logs**, choose **Save Logs...** to write visible text, or **Clear Logs** to clear only the display. Choose **File → Settings...**, change values, select Save, and restart to apply startup mode; the scan interval applies to subsequently created workers.

## 18. Complete example workflow

1. A student double-clicks `run_wifi_analyzer.bat`; it prepares the virtual environment and opens the GUI.
2. The default `demo_mode: true` makes six records appear. Each receives local first/last seen timestamps and an analyzed status/score.
3. The student sorts Score. `Legacy-WEP` appears at 5 and `Coffee_Guest` at 15 because WEP/open metadata are marked Vulnerable.
4. In Security Analysis, the student reads why `OldOffice` scores 30: WPA base 35 minus 5 for a signal below 20%.
5. Charts show the status split, per-SSID signal, and channel counts.
6. Logs show startup, configuration loaded, and Demo Mode start. The student saves visible logs and exports results to CSV.
7. In Settings, the student changes interval to 20 seconds and disables Demo Mode. After restart, Real Scan is only started automatically if `auto_scan` is also true; otherwise the student clicks Start Real Scan.

## 19. Errors, recovery, performance, and limitations

| Situation | Detection/recovery |
|---|---|
| Missing config | Safe defaults, warning log; app continues. |
| Invalid config/type | Safe defaults or corrected value, warning log; app continues. |
| Unsupported OS/no adapter/command failure/timeout | Scanner returns friendly Demo Mode message; GUI remains open. |
| No networks | Friendly message; no crash. |
| Malformed scanner item | `_accept_rows()` converts non-dictionaries to empty data; `Network.from_scan()` supplies defaults. |
| CSV/log permission error | `OSError` is logged and shown in a warning dialog. |
| Empty results | Dashboard/table/analysis/charts render stable empty states. |

Real discovery runs inside `ScanWorker(QThread)`, so `netsh` does not block normal GUI interaction. The worker checks `running` every 100 ms during its configured wait. Stopping does not forcibly kill an in-progress OS call; the window waits for stopping workers on close. Results/history live in memory only. On large environments, full table/chart redraws may become slower because the project redraws the complete data set after every accepted result.

Important limitations: real scanning is Windows-only; signal is an approximate conversion; real vendor information is not derived; metadata cannot determine actual network safety; the score is a heuristic; there is no persistent network database; no scan cancellation mechanism interrupts `netsh` mid-call; and there is no live packet or traffic analysis.

## 20. Testing record

| ID | Test | Expected / actual result | Status |
|---|---|---|---|
| T01 | Syntax compilation | Main/launcher/modules compiled. | Pass |
| T02 | Headless GUI construction | MainWindow opened with six demo rows. | Pass |
| T03 | Demo Mode | Six fixed WPA3/WPA2/Open/WEP/WPA/Enterprise examples loaded. | Pass |
| T04 | Numeric sorting | Score sort placed WEP score 5 first. | Pass |
| T05 | Analysis | Vulnerable, Moderate, and Secure statuses calculated. | Pass |
| T06 | CSV | Header began `SSID,BSSID`; output wrote successfully. | Pass |
| T07 | Invalid config | Invalid JSON produced defaults/messages. | Pass |
| T08 | Clear logs | Visible log view became empty. | Pass |
| T09 | Real worker | Windows worker start/stop test completed without GUI crash. | Pass |
| T10 | Safety scan | No Scapy/PyShark/Flask/ML/attack keywords in active Python/dependency files. | Pass |

Interactive save dialogs and diverse hardware/driver combinations should additionally be tested manually on the target user machine.

## 21. Advantages, comparison, and future scope

Advantages: beginner-friendly Demo Mode, no special hardware for demonstrations, modular Python design, clear defensive boundary, dashboard/table/charts/logging/CSV, and transparent rules. Disadvantages are the limitations listed above.

| Tool type | Difference |
|---|---|
| This analyzer | Passively lists/analyzes available metadata and visualizes it. |
| Basic Wi-Fi scanner | May only list SSID/signal; this app adds deterministic status, score, charts, logs, and export. |
| Network monitoring tool | Usually observes managed devices/traffic over time; this app has no traffic monitoring or persistent history. |
| Penetration-testing tool | Tests/attacks authorized targets; this application does not attack or access any network. |

**Future suggestions, not implemented:** short term—Settings UI for log level, export tests, accessibility labels; medium term—optional persistent history, documented vendor/OUI database, configurable scoring, Linux/macOS adapters; long term—report generation, richer authorized inventory, and additional defensive visualizations. Offensive features are intentionally outside scope.

## 22. Viva preparation: 50 short questions and answers

1. **What is the project?** A defensive desktop Wi-Fi metadata analyzer.
2. **What language is used?** Python.
3. **What GUI framework is used?** PyQt6.
4. **Why Matplotlib?** To draw signal, status, and channel charts.
5. **What is Demo Mode?** Six fixed local sample networks.
6. **Does Demo Mode need Wi-Fi hardware?** No.
7. **Does it need internet in Demo Mode?** No.
8. **What is an SSID?** The Wi-Fi network name.
9. **What is a BSSID?** The access point radio MAC address.
10. **What is a channel?** The radio frequency channel used by Wi-Fi.
11. **What is passive discovery?** Listing/observing networks without attacking them.
12. **Which command supports real scan?** `netsh wlan show networks mode=bssid`.
13. **Which OS has real scan implementation?** Windows.
14. **Does it use Scapy?** No.
15. **Does it capture packets?** No.
16. **Does it crack passwords?** No.
17. **Why is Open risky?** It has no Wi-Fi encryption indicator.
18. **Why is WEP flagged?** It is obsolete.
19. **How is WPA handled?** Moderate with an outdated-encryption warning.
20. **How is WPA2 handled?** Moderate; metadata cannot prove safety.
21. **How is WPA3 handled?** Secure with base score 90.
22. **What is the score range?** 0 to 100.
23. **Is the score a guarantee?** No, it is a metadata heuristic.
24. **What lowers score for weak signal?** Signal below 20% lowers it by 5.
25. **What is channel congestion here?** Three or more displayed networks on one channel.
26. **What is its penalty?** 8 points.
27. **What happens when vendor is unknown?** Score loses 3 points and an issue is shown.
28. **How is real signal represented?** The original Windows percentage is retained.
29. **Why is that a limitation?** It is not a calibrated radio measurement.
30. **How is GUI blocking avoided?** Real scan runs in `QThread`.
31. **What are Qt signals?** Safe notifications from worker to GUI.
32. **Why use a dataclass?** It provides a consistent network record.
33. **How are incomplete results handled?** Defaults like Unknown/Hidden network are used.
34. **Where is config stored?** `config.json` in project root.
35. **What if config is malformed?** Safe defaults are used and a warning is logged.
36. **What controls repeat scan frequency?** `scan_interval`.
37. **What does auto_scan do?** Starts real scan at launch when Demo Mode is off.
38. **What file stores logs?** `logs/wifi_analyzer.log`.
39. **What does Clear Logs clear?** The visible log tab.
40. **How are results exported?** UTF-8 BOM CSV through a save dialog.
41. **Why use CSV?** It opens in spreadsheets and supports sharing/inventory.
42. **What is first_seen?** The first local time a key was seen during the running app.
43. **Is history saved after closing?** No.
44. **What charts exist?** Signal bar, security-status pie, channel-usage bar.
45. **What does the search box filter?** SSID, security type, vendor, and status.
46. **Why use NumericItem?** To sort numeric columns correctly.
47. **Can real vendor be identified?** Not by the current code; it is Unknown.
48. **What authorization is required?** Permission to observe the wireless environment.
49. **What is the main ethical boundary?** No access, attack, or credential collection.
50. **What is a realistic future improvement?** Persistent authorized history or configurable scoring.

## 23. Presentation and report outline

Suggested 20-slide deck: 1 Title; 2 Introduction; 3 Problem; 4 Objective; 5 Motivation; 6 Scope/ethics; 7 Proposed system; 8 Architecture; 9 Technology stack; 10 Modules; 11 Workflow; 12 Demo Mode; 13 Windows Real Scan; 14 Data model; 15 Scoring; 16 GUI/charts; 17 Logging/export; 18 Testing; 19 Limitations/future scope; 20 Conclusion. On each slide, state what is implemented and avoid describing removed packet/ML/web features.

Formal report chapters: Introduction; Problem Statement; Objectives; Existing/Proposed System; Requirements; Architecture; Module Description; Implementation; Security Analysis; Testing; Results; Limitations; Future Scope; Conclusion; References (Python, PyQt6, Matplotlib, Microsoft `netsh` documentation, and the repository license/source).

## 24. Spoken explanations

**One minute:** “My project is a Wi-Fi Security Analyzer desktop application written in Python. It can show six simulated networks in Demo Mode or passively read available-network metadata from Windows using netsh. Every record is normalized and given a status and 0–100 heuristic score based on the reported security type, missing metadata, weak signal, and crowded channel. The GUI provides a table, dashboard, charts, logs, settings, and CSV export. It is strictly defensive: it does not capture packets, crack passwords, or access networks.”

**Three minutes:** Start with the one-minute introduction. Explain that Demo Mode makes the project usable without hardware or permissions. Then describe the flow: config loads, GUI starts, demo data or a QThread Windows scan produces dictionaries, `Network.from_scan()` handles missing fields, and `analyse_all()` applies transparent rules. Give WEP score 5 and WPA3 score 90 as examples. Explain that charts summarize signals/statuses/channels, logs record events, and CSV supports reporting. End with Windows-only real scanning and the fact that score is not proof of safety.

**Five minutes:** Add architecture detail: `wifi_scanning.py` uses `subprocess.run` with the Windows command, parses SSID/BSSID/authentication/signal/channel, returns friendly errors, and does not capture frames. Describe the exact deductions: missing/weak signal, missing/congested channel, and unknown vendor. Explain user workflow: start demo/real scan, filter/sort, inspect analysis, view charts, save logs/export CSV, configure startup. End with limitations—no vendor lookup, no persistent history, no cross-platform scanner, approximate signal—and ethical authorization.

## 25. Final summary

| Question | Answer |
|---|---|
| What? | A defensive Wi-Fi metadata analyzer desktop app. |
| Why? | To make basic nearby-network security awareness and education easier. |
| When/where? | Authorized home, lab, classroom, office, and demonstration environments. |
| Who? | Students, educators, learners, and authorized IT/security staff. |
| How? | Demo data or Windows `netsh` → model → deterministic analysis → GUI/charts/logs/CSV. |
| With what? | Python, PyQt6, Matplotlib, JSON, CSV, Windows `netsh`. |
| Result? | A filterable table, status/score explanation, charts, logs, and export. |
| Limitations? | Windows-only real scan, metadata-only heuristic, no real vendor lookup/persistent history/traffic analysis. |
| Future? | Safer usability, history, vendor enrichment, configurable rules, and cross-platform support. |
