"""BlueLab Toolkit v1 - BLE discovery and documented GATT controls."""
from __future__ import annotations

import asyncio
import json
import logging
import sys
import threading
from pathlib import Path
from typing import Any

import bleak
from bleak.backends.device import BLEDevice
from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (  # type: ignore[reportMissingImports]
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QTextEdit, QLineEdit, QComboBox, QMessageBox, QSpinBox,
    QGroupBox, QFormLayout, QHeaderView
)

APP_DIR = Path(__file__).resolve().parent
PROFILE_PATH = APP_DIR / "profiles" / "approved_gatt.json"
LOG_DIR = APP_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "bluelab.log", level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8"
)


def load_profiles() -> dict[str, Any]:
    """Load locally approved, documented GATT characteristics.

    Write operations are disabled unless the characteristic UUID appears in this
    file. Users should only add UUIDs documented for devices they own/are allowed
    to test, and should set a conservative max_payload_bytes limit.
    """
    try:
        data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError) as exc:
        logging.exception("Could not load approved GATT profile")
        return {}


class BluetoothWorker(QThread):
    devices_found = Signal(list)
    connected = Signal(str)
    disconnected = Signal()
    services_ready = Signal(list)
    value_read = Signal(str, str)
    notification = Signal(str, str)
    operation_result = Signal(str)
    error = Signal(str)
    log_message = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.client: bleak.BleakClient | None = None
        self.devices: dict[str, BLEDevice] = {}
        self._stop_event: asyncio.Event | None = None

    def run(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._stop_event = asyncio.Event()
        self.loop.run_forever()
        pending = asyncio.all_tasks(self.loop)
        for task in pending:
            task.cancel()
        if pending:
            self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        self.loop.close()

    def submit(self, coro) -> None:
        if not self.loop or not self.loop.is_running():
            self.error.emit("Bluetooth worker is not ready. Please wait and try again.")
            return
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    @Slot()
    def scan(self) -> None:
        self.submit(self._scan())

    async def _scan(self) -> None:
        try:
            self.log_message.emit("Scanning for BLE advertisements (8 seconds)…")
            found = await bleak.BleakScanner.discover(timeout=8.0, return_adv=True)
            rows = []
            self.devices.clear()
            for key, pair in found.items():
                device, adv = pair
                address = device.address
                self.devices[address] = device
                rows.append({
                    "name": device.name or adv.local_name or "(unnamed)",
                    "address": address,
                    "rssi": getattr(adv, "rssi", None),
                    "uuids": ", ".join(adv.service_uuids or []),
                })
            rows.sort(key=lambda x: (x["name"].lower(), x["address"]))
            self.devices_found.emit(rows)
            self.log_message.emit(f"Scan complete: {len(rows)} BLE device(s) found.")
        except Exception as exc:
            logging.exception("BLE scan failed")
            self.error.emit(f"BLE scan failed: {exc}\nCheck that Bluetooth is enabled and Windows permissions allow scanning.")

    @Slot(str)
    def connect_device(self, address: str) -> None:
        self.submit(self._connect(address))

    async def _connect(self, address: str) -> None:
        try:
            device = self.devices.get(address)
            if not device:
                # Bleak can also connect by address on Windows, but a fresh scan
                # is more reliable and avoids stale device objects.
                self.error.emit("Device is no longer in the scan list. Scan again and retry.")
                return
            await self._disconnect(silent=True)
            self.log_message.emit(f"Connecting to {address}…")
            self.client = bleak.BleakClient(device, timeout=20.0)
            await self.client.connect()
            if not self.client.is_connected:
                raise RuntimeError("The operating system did not establish a connection.")
            self.connected.emit(address)
            self.log_message.emit(f"Connected to {address}.")
            await self._emit_services()
        except Exception as exc:
            logging.exception("BLE connection failed")
            self.client = None
            self.error.emit(f"Connection failed: {exc}\nTry moving the device closer, disconnecting it from other apps, or pairing if required.")

    async def _emit_services(self) -> None:
        if not self.client or not self.client.is_connected:
            return
        rows = []
        try:
            services = self.client.services
            for service in services:
                chars = []
                for char in service.characteristics:
                    props = list(char.properties)
                    chars.append({
                        "uuid": char.uuid,
                        "description": char.description or "",
                        "properties": props,
                        "descriptors": [d.uuid for d in char.descriptors],
                    })
                rows.append({"uuid": service.uuid, "description": service.description or "", "characteristics": chars})
            self.services_ready.emit(rows)
        except Exception as exc:
            logging.exception("GATT service discovery failed")
            self.error.emit(f"Could not enumerate GATT services: {exc}")

    @Slot()
    def disconnect_device(self) -> None:
        self.submit(self._disconnect())

    async def _disconnect(self, silent: bool = False) -> None:
        if self.client:
            try:
                if self.client.is_connected:
                    await self.client.disconnect()
            except Exception as exc:
                logging.warning("Disconnect warning: %s", exc)
            finally:
                self.client = None
                if not silent:
                    self.disconnected.emit()
                    self.log_message.emit("Disconnected.")

    @Slot(str)
    def read_characteristic(self, uuid: str) -> None:
        self.submit(self._read(uuid))

    async def _read(self, uuid: str) -> None:
        try:
            if not self.client or not self.client.is_connected:
                raise RuntimeError("Connect to a device first.")
            data = await self.client.read_gatt_char(uuid)
            hex_value = bytes(data).hex(" ").upper()
            try:
                text_value = bytes(data).decode("utf-8", errors="strict")
                display = f"HEX: {hex_value}\nUTF-8: {text_value!r}"
            except UnicodeDecodeError:
                display = f"HEX: {hex_value}\nDECIMAL: {list(data)}"
            self.value_read.emit(uuid, display)
            self.log_message.emit(f"Read {len(data)} byte(s) from {uuid}.")
        except Exception as exc:
            logging.exception("GATT read failed")
            self.error.emit(f"Read failed for {uuid}: {exc}")

    @Slot(str, str)
    def write_characteristic(self, uuid: str, hex_payload: str) -> None:
        self.submit(self._write(uuid, hex_payload))

    async def _write(self, uuid: str, hex_payload: str) -> None:
        try:
            if not self.client or not self.client.is_connected:
                raise RuntimeError("Connect to a device first.")
            profiles = load_profiles()
            entry = profiles.get(uuid.lower()) or profiles.get(uuid.upper())
            if not isinstance(entry, dict) or not entry.get("documented"):
                raise PermissionError("Write blocked: this UUID is not marked as documented in profiles/approved_gatt.json.")
            payload = bytes.fromhex(hex_payload)
            max_len = int(entry.get("max_payload_bytes", 20))
            if not payload:
                raise ValueError("Empty writes are not allowed.")
            if len(payload) > max_len:
                raise ValueError(f"Payload is {len(payload)} bytes; profile limit is {max_len} bytes.")
            # Confirm that the current GATT database actually marks it writable.
            characteristic = self.client.services.get_characteristic(uuid)
            if characteristic is None:
                raise ValueError("Characteristic UUID is not present on this device.")
            props = set(characteristic.properties)
            if not ({"write", "write-without-response"} & props):
                raise PermissionError("The characteristic does not advertise a write property.")
            response = "write" in props
            await self.client.write_gatt_char(uuid, payload, response=response)
            self.operation_result.emit(f"Write sent to {uuid}: {payload.hex(' ').upper()} (response={response}).")
            self.log_message.emit(f"Wrote {len(payload)} byte(s) to approved characteristic {uuid}.")
        except Exception as exc:
            logging.exception("GATT write blocked or failed")
            self.error.emit(f"Write failed or blocked: {exc}")

    @Slot(str, bool)
    def subscribe(self, uuid: str, enabled: bool) -> None:
        self.submit(self._subscribe(uuid, enabled))

    async def _subscribe(self, uuid: str, enabled: bool) -> None:
        try:
            if not self.client or not self.client.is_connected:
                raise RuntimeError("Connect to a device first.")
            if enabled:
                def callback(_sender, data: bytearray) -> None:
                    self.notification.emit(uuid, bytes(data).hex(" ").upper())
                await self.client.start_notify(uuid, callback)
                self.operation_result.emit(f"Notifications enabled for {uuid}.")
            else:
                await self.client.stop_notify(uuid)
                self.operation_result.emit(f"Notifications stopped for {uuid}.")
        except Exception as exc:
            logging.exception("Notification operation failed")
            self.error.emit(f"Notification operation failed for {uuid}: {exc}")

    def shutdown(self) -> None:
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._disconnect(silent=True), self.loop).result(timeout=4)
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.wait(5000)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BlueLab Toolkit v1 — BLE Explorer")
        self.resize(1120, 760)
        self.worker = BluetoothWorker()
        self.worker.start()
        self.rows: list[dict[str, Any]] = []
        self.current_characteristic: dict[str, Any] | None = None
        self.profiles = load_profiles()
        self._build_ui()
        self.worker.devices_found.connect(self.show_devices)
        self.worker.connected.connect(self.on_connected)
        self.worker.disconnected.connect(self.on_disconnected)
        self.worker.services_ready.connect(self.show_services)
        self.worker.value_read.connect(self.show_read)
        self.worker.notification.connect(self.show_notification)
        self.worker.operation_result.connect(self.log)
        self.worker.log_message.connect(self.log)
        self.worker.error.connect(self.show_error)

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        header = QLabel("BlueLab Toolkit v1  |  BLE discovery, GATT inspection and approved controls")
        header.setStyleSheet("font-size: 18px; font-weight: 700; padding: 8px;")
        layout.addWidget(header)
        note = QLabel("BLE only in v1. Writes are blocked unless the UUID is explicitly approved in profiles/approved_gatt.json.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #9a6700; padding: 4px;")
        layout.addWidget(note)

        top = QHBoxLayout()
        self.scan_btn = QPushButton("Scan BLE Devices (8 sec)")
        self.scan_btn.clicked.connect(self.worker.scan)
        self.connect_btn = QPushButton("Connect Selected")
        self.connect_btn.clicked.connect(self.connect_selected)
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.worker.disconnect_device)
        self.disconnect_btn.setEnabled(False)
        self.status = QLabel("Status: idle")
        top.addWidget(self.scan_btn); top.addWidget(self.connect_btn); top.addWidget(self.disconnect_btn); top.addWidget(self.status, 1)
        layout.addLayout(top)

        self.tabs = QTabWidget()
        device_tab = QWidget(); device_layout = QVBoxLayout(device_tab)
        self.device_table = QTableWidget(0, 4)
        self.device_table.setHorizontalHeaderLabels(["Name", "Address / ID", "RSSI", "Advertised service UUIDs"])
        self.device_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.device_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        device_layout.addWidget(self.device_table)
        self.tabs.addTab(device_tab, "Devices")

        gatt_tab = QWidget(); gatt_layout = QHBoxLayout(gatt_tab)
        self.gatt_tree = QTreeWidget()
        self.gatt_tree.setHeaderLabels(["GATT services / characteristics", "Properties", "UUID"])
        self.gatt_tree.setMinimumWidth(520)
        self.gatt_tree.itemSelectionChanged.connect(self.on_characteristic_selected)
        gatt_layout.addWidget(self.gatt_tree, 3)
        right = QVBoxLayout()
        info_box = QGroupBox("Selected characteristic")
        info_form = QFormLayout(info_box)
        self.char_uuid = QLabel("—"); self.char_uuid.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.char_props = QLabel("—")
        self.char_desc = QLabel("—"); self.char_desc.setWordWrap(True)
        info_form.addRow("UUID:", self.char_uuid); info_form.addRow("Properties:", self.char_props); info_form.addRow("Description:", self.char_desc)
        right.addWidget(info_box)
        action_row = QHBoxLayout()
        self.read_btn = QPushButton("Read")
        self.read_btn.clicked.connect(self.read_selected)
        self.notify_btn = QPushButton("Start notifications")
        self.notify_btn.clicked.connect(self.toggle_notifications)
        action_row.addWidget(self.read_btn); action_row.addWidget(self.notify_btn)
        right.addLayout(action_row)
        write_box = QGroupBox("Approved write (hex bytes only)")
        write_form = QFormLayout(write_box)
        self.write_input = QLineEdit(); self.write_input.setPlaceholderText("e.g. 01 00")
        self.write_input.setToolTip("Hex byte pairs only; payload length is limited by the approved profile.")
        self.write_btn = QPushButton("Validate & Write…")
        self.write_btn.clicked.connect(self.write_selected)
        self.write_help = QLabel("Writes are enabled only for UUIDs listed in approved_gatt.json and writable on the connected device.")
        self.write_help.setWordWrap(True)
        write_form.addRow("Payload:", self.write_input); write_form.addRow(self.write_btn); write_form.addRow(self.write_help)
        right.addWidget(write_box)
        self.value_box = QTextEdit(); self.value_box.setReadOnly(True); self.value_box.setPlaceholderText("Read results and notifications appear here.")
        right.addWidget(self.value_box, 1)
        gatt_layout.addLayout(right, 2)
        self.tabs.addTab(gatt_tab, "GATT Explorer")

        log_tab = QWidget(); log_layout = QVBoxLayout(log_tab)
        self.log_box = QTextEdit(); self.log_box.setReadOnly(True)
        log_layout.addWidget(self.log_box)
        self.tabs.addTab(log_tab, "Activity Log")
        layout.addWidget(self.tabs, 1)
        self.setCentralWidget(root)
        self.setStatusBar(self.statusBar())
        self.log("Ready. Select Scan BLE Devices to begin.")

    def log(self, message: str) -> None:
        self.log_box.append(message)
        logging.info(message)

    def show_error(self, message: str) -> None:
        self.log("ERROR: " + message.replace("\n", " | "))
        QMessageBox.warning(self, "Bluetooth operation", message)

    def show_devices(self, rows: list) -> None:
        self.rows = rows
        self.device_table.setRowCount(len(rows))
        for r, device in enumerate(rows):
            values = [device["name"], device["address"], str(device["rssi"] if device["rssi"] is not None else "—"), device["uuids"]]
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                if c == 1:
                    item.setData(Qt.ItemDataRole.UserRole, device["address"])
                self.device_table.setItem(r, c, item)
        if rows:
            self.device_table.selectRow(0)

    def connect_selected(self) -> None:
        row = self.device_table.currentRow()
        if row < 0 or row >= len(self.rows):
            QMessageBox.information(self, "Select device", "Select a device from the scan results first.")
            return
        self.worker.connect_device(self.rows[row]["address"])

    def on_connected(self, address: str) -> None:
        self.status.setText(f"Status: connected to {address}")
        self.disconnect_btn.setEnabled(True)
        self.tabs.setCurrentIndex(1)

    def on_disconnected(self) -> None:
        self.status.setText("Status: disconnected")
        self.disconnect_btn.setEnabled(False)
        self.gatt_tree.clear()
        self.current_characteristic = None

    def show_services(self, services: list) -> None:
        self.gatt_tree.clear()
        for service in services:
            parent = QTreeWidgetItem([service["description"] or "Service", "", service["uuid"]])
            parent.setData(0, Qt.ItemDataRole.UserRole, {"type": "service", **service})
            self.gatt_tree.addTopLevelItem(parent)
            for char in service["characteristics"]:
                child = QTreeWidgetItem([char["description"] or "Characteristic", ", ".join(char["properties"]), char["uuid"]])
                child.setData(0, Qt.ItemDataRole.UserRole, {"type": "characteristic", **char})
                parent.addChild(child)
        self.gatt_tree.expandToDepth(1)
        self.log(f"Discovered {len(services)} GATT service(s).")

    def on_characteristic_selected(self) -> None:
        items = self.gatt_tree.selectedItems()
        if not items:
            self.current_characteristic = None
            self.char_uuid.setText("—"); self.char_props.setText("—"); self.char_desc.setText("—")
            return
        data = items[0].data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "characteristic":
            self.current_characteristic = None
            return
        self.current_characteristic = data
        uuid = data["uuid"]
        self.char_uuid.setText(uuid)
        self.char_props.setText(", ".join(data["properties"]) or "none")
        self.char_desc.setText(data["description"] or "No description advertised")
        can_read = "read" in data["properties"]
        can_notify = bool({"notify", "indicate"} & set(data["properties"]))
        approved = (self.profiles.get(uuid.lower()) or self.profiles.get(uuid.upper()) or {}).get("documented") is True
        can_write = approved and bool({"write", "write-without-response"} & set(data["properties"]))
        self.read_btn.setEnabled(can_read)
        self.notify_btn.setEnabled(can_notify)
        self.write_btn.setEnabled(can_write)
        self.write_help.setText("Approved profile found; runtime permissions are still checked before writing." if approved else "Write disabled: UUID is not approved/documented in profiles/approved_gatt.json.")

    def read_selected(self) -> None:
        if self.current_characteristic:
            self.worker.read_characteristic(self.current_characteristic["uuid"])

    def toggle_notifications(self) -> None:
        if not self.current_characteristic:
            return
        uuid = self.current_characteristic["uuid"]
        if self.notify_btn.text().startswith("Start"):
            self.worker.subscribe(uuid, True)
            self.notify_btn.setText("Stop notifications")
        else:
            self.worker.subscribe(uuid, False)
            self.notify_btn.setText("Start notifications")

    def write_selected(self) -> None:
        char = self.current_characteristic
        if not char:
            return
        uuid = char["uuid"]
        profile = self.profiles.get(uuid.lower()) or self.profiles.get(uuid.upper())
        if not profile or not profile.get("documented"):
            QMessageBox.warning(self, "Write blocked", "This UUID is not approved in the local device profile.")
            return
        payload = self.write_input.text().strip()
        try:
            raw = bytes.fromhex(payload)
            if not raw:
                raise ValueError("Enter at least one byte.")
            if len(raw) > int(profile.get("max_payload_bytes", 20)):
                raise ValueError("Payload exceeds the profile byte limit.")
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid payload", f"Enter hex byte pairs (for example 01 00). {exc}")
            return
        message = (f"Send {raw.hex(' ').upper()} to {uuid}?\n\nProfile: {profile.get('name', 'Unnamed')}\n"
                   f"Purpose: {profile.get('purpose', 'Not specified')}\n\nOnly continue if this matches the device documentation.")
        if QMessageBox.question(self, "Confirm device change", message, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.worker.write_characteristic(uuid, payload)

    def show_read(self, uuid: str, display: str) -> None:
        self.value_box.append(f"READ {uuid}\n{display}\n")

    def show_notification(self, uuid: str, value: str) -> None:
        self.value_box.append(f"NOTIFY {uuid}\nHEX: {value}\n")

    def closeEvent(self, event) -> None:
        try:
            self.worker.shutdown()
        except Exception:
            logging.exception("Worker shutdown issue")
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("BlueLab Toolkit")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
