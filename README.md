# Cybersecurity Projects

A collection of practical cybersecurity and software projects. Each project has its own documentation, setup instructions, and requirements.

## Projects

| Project | Overview | Main technologies |
| --- | --- | --- |
| [01 — LSB Steganography Mini-App](01%20lsb-steganography-app/README.md) | Desktop app for hiding and recovering text in PNG images using least significant bit (LSB) steganography. | Python, Tkinter, Pillow |
| [02 — Digital Forensics Evidence Management System](02%20Digital%20Forensics%20Evidence%20Management%20System/README.md) | Web app for managing investigation cases, evidence records, integrity hashes, custody events, and audit history. | FastAPI, Next.js, SQLite |
| [03 — Wi-Fi Security Analyzer](03%20Wifi%20Security%20Analyser/README.md) | Desktop app for simulated demonstrations and authorized, passive Windows Wi-Fi discovery with metadata-based analysis. | Python, PyQt6, Matplotlib, Windows `netsh` |

## Quick start

Choose a project and follow its own README for complete setup and usage instructions.

### LSB Steganography Mini-App

```bash
cd "01 lsb-steganography-app"
python -m pip install -r requirements.txt
python steg_app.py
```

Use PNG images to preserve encoded data. This is an educational demonstration of steganography; it does not encrypt messages.

### Digital Forensics Evidence Management System

On Windows, run `RUN_ME.bat` from the project folder. It sets up and starts the backend and frontend. For manual setup, platform requirements, and demo login details, see the [project guide](02%20Digital%20Forensics%20Evidence%20Management%20System/README.md).

This is an educational evidence-management tool. It is not certified forensic acquisition software and is not a substitute for validated forensic procedures.

### Wi-Fi Security Analyzer

```powershell
cd "03 Wifi Security Analyser"
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item config.json.example config.json
python GUI_Module.py
```

It opens in simulated Demo Mode. Real discovery uses Windows' built-in WLAN listing command and should only be used where you are authorized to observe the networks.

## Repository layout

```text
01 lsb-steganography-app/                 PNG LSB steganography desktop app
02 Digital Forensics Evidence Management System/
                                          Evidence management web app
03 Wifi Security Analyser/                Passive Wi-Fi metadata analyzer
README.md                                 Repository project index
```

## Scope and responsible use

These projects are intended for learning and authorized use. The Wi-Fi analyzer reads network metadata and does not capture traffic or attempt access to networks. The forensics system manages records and hashes but does not acquire or certify digital evidence. The steganography app demonstrates data hiding and does not provide cryptographic protection.

See each project directory for its detailed documentation, dependencies, limitations, and project-specific license information.
