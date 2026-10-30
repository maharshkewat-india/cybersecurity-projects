# BlueLab Toolkit v1 (Windows 11)

A Python desktop BLE scanner and GATT explorer with read/notification support and an explicitly allow-listed write workflow. This v1 targets Bluetooth Low Energy (BLE); it is **not** a universal classic Bluetooth or firmware editor.

## Requirements

- Windows 11 with Bluetooth enabled and a compatible BLE adapter.
- Python 3.11 or newer (64-bit recommended).
- Device powered on and in range. Some devices must be disconnected from their official app or paired through Windows before access works.

## Install and run

Open PowerShell in this folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

## Use

1. Click **Scan BLE Devices (8 sec)**. Only devices advertising in BLE mode may appear; classic-only speakers/headphones might not show.
2. Select a device and click **Connect Selected**.
3. Open **GATT Explorer** and inspect services and characteristics. The properties column shows advertised `read`, `write`, `notify`, etc.
4. Select a characteristic. **Read** is enabled only when `read` is advertised. Notifications are available only for `notify`/`indicate` characteristics.
5. Writes are blocked by default. To enable a write, add the exact characteristic UUID to `profiles/approved_gatt.json` only after verifying its meaning and payload in the manufacturer's documentation for your device. Keep `documented` set to `true`, provide a purpose/source and set a conservative `max_payload_bytes`. Restart the app after changing the profile. At runtime, BlueLab also verifies that the characteristic exists and advertises a write property, checks the payload length, and asks for confirmation.
6. Use **Activity Log** for operation status. The log file is written to `logs/bluelab.log`.

## Profile example (do not copy a guessed UUID)

```json
{
  "YOUR-DOCUMENTED-CHARACTERISTIC-UUID": {
    "documented": true,
    "name": "Example setting",
    "purpose": "Vendor-documented purpose",
    "max_payload_bytes": 2,
    "source": "Vendor manual, section 4.2"
  }
}
```

Replace the placeholder with the exact UUID and valid payload specification from documentation. The value above is a format example, not a real approved UUID. For binary payloads, enter hex bytes in the GUI, such as `01 00`, only if the device manual specifies that exact encoding.

## Troubleshooting

- **No devices found:** make sure Windows Bluetooth is on, device is advertising BLE, it is in range, and no other app is holding the connection. BLE advertisements are not the same as Windows' paired-device list.
- **Access denied / scan fails:** check Windows Settings → Privacy & security → Bluetooth and device permissions available on your Windows build, and update Bluetooth drivers.
- **Connect fails:** rescan to refresh the device object; close the vendor app; ensure the device permits another central connection; pair if the device requires it.
- **Read/write fails:** the characteristic may require pairing/encryption, the operation may not be supported, or the value may have protocol-specific requirements.
- **GUI closes or an OS Bluetooth error appears:** see `logs/bluelab.log` and run from PowerShell to view startup diagnostics.

## Safety and scope

- Use only with devices you own or have permission to test.
- BLE writes can change settings or disrupt device behavior. Do not write undocumented values or attempt repeated trial-and-error payloads.
- This app does not bypass pairing, encryption, authentication, secure boot, or vendor protections.
- It does not flash firmware or modify arbitrary internal device programming. Firmware updates require a separate device-specific, vendor-supported workflow.
- Classic Bluetooth profiles (for example A2DP audio) need a separate OS-specific adapter and are not implemented in v1.

## Tests

The app has a small profile-validation test suite. Run:

```powershell
pytest -q
```

Bluetooth hardware is not required for these basic tests.
