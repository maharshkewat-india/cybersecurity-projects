# Cybersecurity Projects

A portfolio of five practical security, privacy, forensics, and machine-learning projects. Each project is self-contained and includes its own source code, dependencies, and detailed documentation.

## Project directory

| # | Project | What it does | Main technologies |
| --- | --- | --- | --- |
| 01 | [LSB Steganography Mini-App](01%20lsb-steganography-app/README.md) | Hides and recovers text inside PNG images with least-significant-bit steganography. | Python, Tkinter, Pillow |
| 02 | [Digital Forensics Evidence Management System](02%20Digital%20Forensics%20Evidence%20Management%20System/README.md) | Manages investigation cases, evidence records, integrity hashes, custody events, users, and audit history. | FastAPI, Next.js, React, SQLite, Tailwind CSS |
| 03 | [Wi-Fi Security Analyzer](03%20Wifi%20Security%20Analyser/README.md) | Performs authorized, passive Wi-Fi discovery and analyzes reported wireless-network metadata. | Python, PyQt6, Matplotlib, Windows `netsh` |
| 04 | [BlueLab Toolkit](04%20bluelab-toolkit/README.md) | Scans BLE devices, explores GATT services, and supports carefully allow-listed characteristic writes. | Python, PySide6, Bleak |
| 05 | [Fake News Classifier](05%20fake_news_classifier/README.md) | Trains a text-pattern classifier and provides an interactive prediction interface. | Python, Streamlit, scikit-learn, pandas |

## Getting started

Clone the repository, then open a terminal in the project you want to run. Each project has separate requirements and setup instructions; do not install every project's dependencies into one environment.

```powershell
git clone https://github.com/maharshkewat-india/cybersecurity-projects.git
cd cybersecurity-projects
```

## 01 - LSB Steganography Mini-App

A beginner-friendly desktop application for hiding a UTF-8 text message in a PNG image and later recovering it. It uses the least significant bit of each red, green, and blue pixel channel, with a 32-bit message-length prefix.

**Key features**

- Separate Encode and Decode workflows in a Tkinter interface.
- PNG input/output, preserving the data through lossless image encoding.
- Clear success, capacity, and error feedback.
- Simple local operation with no network requirement.

**Run it**

```powershell
cd "01 lsb-steganography-app"
python -m pip install -r requirements.txt
python steg_app.py
```

**Important:** LSB steganography is data hiding, not encryption. JPEG recompression can destroy embedded data, so use PNG images. Read the [full project guide](01%20lsb-steganography-app/README.md) for capacity and troubleshooting details.

## 02 - Digital Forensics Evidence Management System

A web application for organizing an investigation while maintaining evidence records and a transparent chain of custody. The backend exposes a FastAPI API, while the frontend provides a responsive Next.js interface. SQLite supplies portable local storage.

**Key features**

- Case lifecycle management: create, edit, close, archive, search, filter, and assign cases.
- Evidence registration with streamed MD5 and SHA-256 calculation, later verification, and integrity-status tracking.
- Chain-of-custody timeline plus investigation notes and append-only audit logging.
- Authentication, PBKDF2-HMAC-SHA256 password hashing, JWT sessions, and role-based access controls.
- Dashboard, evidence, custody, audit, user-management, and JSON-report screens.

**Run it on Windows**

```powershell
cd "02 Digital Forensics Evidence Management System"
.\RUN_ME.bat
```

The launcher creates its environments, installs dependencies, initializes the local database, and starts the backend and frontend. For manual setup, API documentation, roles, and testing commands, see the [full project guide](02%20Digital%20Forensics%20Evidence%20Management%20System/README.md).

**Important:** This is an educational evidence-management system. It does not acquire disk images, replace write blockers, or establish legal admissibility of evidence.

## 03 - Wi-Fi Security Analyzer

A defensive desktop tool for observing nearby Wi-Fi metadata on Windows and presenting it in a readable, locally processed dashboard. It defaults to deterministic simulated data, so the interface can be explored without hardware access or a network connection.

**Key features**

- Demo mode with reproducible WPA3, WPA2, open, WEP, WPA, and enterprise-style examples.
- Optional passive real discovery through Windows `netsh wlan show networks mode=bssid`.
- Normalized SSID, BSSID, signal, channel, security, vendor, status, and first/last-seen data.
- Explainable 0-100 metadata-based score, sortable/filterable tables, charts, logs, and CSV export.
- JSON configuration for scan interval, demo mode, automatic scans, and log level.

**Run it**

```powershell
cd "03 Wifi Security Analyser"
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item config.json.example config.json
python GUI_Module.py
```

Only use real discovery where you are authorized to observe wireless networks. It does not capture traffic, collect passwords, inject packets, deauthenticate clients, or attempt network access. See the [full project guide](03%20Wifi%20Security%20Analyser/README.md) for Windows setup and score rules.

## 04 - BlueLab Toolkit

A Windows BLE desktop scanner and GATT explorer aimed at careful, authorized device inspection. Version 1 supports BLE devices only; it is not a classic-Bluetooth manager, firmware flasher, or universal device editor.

**Key features**

- BLE scanning, device selection, connection, and GATT service/characteristic exploration.
- Reads only when a characteristic advertises read support.
- Notification and indication support when the device advertises the corresponding property.
- Writes disabled by default and permitted only for explicitly documented UUIDs in `profiles/approved_gatt.json`.
- Runtime write checks for documented profiles, advertised write capability, payload-size limits, and user confirmation.
- Local activity log at `logs/bluelab.log` and profile-validation tests.

**Run it**

```powershell
cd "04 bluelab-toolkit"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Use it only with BLE devices you own or are authorized to test. Do not add guessed UUIDs or undocumented payloads to the write allow-list. Read the [full project guide](04%20bluelab-toolkit/README.md) before connecting to or modifying a device.

## 05 - Fake News Classifier

A Streamlit application and training pipeline for classifying text with TF-IDF unigram/bigram features and Logistic Regression. It includes dataset preparation, model training, held-out evaluation, saved model artifacts, and interactive predictions.

**Key features**

- CSV ingestion and preprocessing with required `text` and `label` columns.
- Support for `FAKE`/`REAL` or `0`/`1` labels.
- Train/test evaluation with accuracy, REAL-class precision, recall, F1, and a confusion matrix.
- Saved `joblib` pipeline and metrics JSON output.
- Streamlit UI with automatic first-run training when an appropriate dataset exists and a retrain control.
- An included synthetic sample dataset for workflow testing.

**Run it**

```powershell
cd "05 fake_news_classifier"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python train.py
streamlit run app.py
```

**Important:** This is a dataset-trained text-pattern classifier, not a fact-checking service. Its predictions cannot establish that a claim is true, validate sources, or guarantee performance on unfamiliar topics. Replace the synthetic sample with a sufficiently large, licensed, correctly labeled dataset before drawing meaningful evaluation conclusions. See the [full project guide](05%20fake_news_classifier/README.md) for the dataset format and training workflow.

## Repository layout

```text
01 lsb-steganography-app/                         PNG LSB steganography desktop app
02 Digital Forensics Evidence Management System/  Forensics case and evidence web app
03 Wifi Security Analyser/                        Passive Wi-Fi metadata analyzer
04 bluelab-toolkit/                               BLE scanner and GATT explorer
05 fake_news_classifier/                          Text-classification training and Streamlit app
LICENSE                                           Apache License 2.0
README.md                                         This repository guide
```

## Responsible use and limitations

- Run scans, Bluetooth operations, and device interactions only where you have clear permission.
- Treat the Wi-Fi analyzer's score as a metadata-based signal, not a security guarantee.
- Treat the Fake News Classifier as a screening tool, not a truth-verification system.
- Do not use the forensics application as a replacement for validated acquisition tools, legal procedures, or professional forensic certification.
- Keep the steganography app's limitations in mind: hidden data is not cryptographically protected.

## License

This repository is licensed under the [Apache License 2.0](LICENSE). Copyright 2026 MAHARSH KEWAT.
