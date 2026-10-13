"""Modern PyQt6 shell for passive Wi-Fi discovery and metadata analysis."""
from __future__ import annotations

import logging
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QFileDialog, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox,
    QSplitter, QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from modules.analysis import analyse_all
from modules.config import ROOT_DIR, config
from modules.demo_data import demo_networks
from modules.exporter import export_csv
from modules.network_model import Network
from modules.wifi_scanning import ScanDiagnostic, discover_networks

LOG_PATH = ROOT_DIR / "logs" / "wifi_analyzer.log"
LOG_PATH.parent.mkdir(exist_ok=True)
logging.basicConfig(filename=LOG_PATH, level=getattr(logging, config.get("log_level")),
                    format="%(asctime)s | %(levelname)s | %(message)s", encoding="utf-8")
logger = logging.getLogger("wifi_analyzer")


class ScanWorker(QThread):
    """Runs native Windows discovery outside the GUI and emits UI-safe events."""
    started = pyqtSignal()
    progress = pyqtSignal(str)
    network_found = pyqtSignal(dict)
    completed = pyqtSignal(list, object)
    error = pyqtSignal(str, str)
    stopped = pyqtSignal()

    def __init__(self, interval: int) -> None:
        super().__init__()
        self.interval, self.running = interval, True

    def run(self) -> None:
        while self.running:
            self.started.emit()
            outcome = discover_networks()
            self.progress.emit(outcome.diagnostic.details())
            if outcome.error:
                if self.running:
                    self.error.emit(outcome.error, outcome.diagnostic.details())
                break
            for row in outcome.networks:
                if not self.running:
                    break
                self.network_found.emit(row)
            if self.running:
                self.completed.emit(outcome.networks, outcome.diagnostic)
            for _ in range(self.interval * 10):
                if not self.running:
                    self.stopped.emit()
                    return
                self.msleep(100)
        self.stopped.emit()

    def stop(self) -> None:
        self.running = False


class NumericItem(QTableWidgetItem):
    """Friendly display text with a separate numeric ordering key."""
    def __init__(self, text: str, value: int | float) -> None:
        super().__init__(text)
        self.setData(Qt.ItemDataRole.UserRole, value)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        return self.data(Qt.ItemDataRole.UserRole) < other.data(Qt.ItemDataRole.UserRole)


class MainWindow(QMainWindow):
    """Application controller; scanner/analysis logic remains in modules."""
    def __init__(self) -> None:
        super().__init__()
        self.networks: list[Network] = []
        self.history: dict[str, Network] = {}
        self.worker: ScanWorker | None = None
        self.retired_workers: list[ScanWorker] = []
        self.pending_networks: list[dict] = []
        self.last_diagnostic = ScanDiagnostic()
        self.mode = "DEMO MODE - SIMULATED DATA" if config.get("demo_mode") else "REAL SCAN - WINDOWS WLAN"
        self.setWindowTitle("Wi-Fi Security Analyzer")
        self.resize(1440, 900)
        self._build_menu(); self._build_ui(); self._apply_style()
        self.clock = QTimer(self); self.clock.timeout.connect(self._update_clock); self.clock.start(1000)
        self._update_clock(); self._log("INFO", "Application started."); self._log("INFO", "Configuration loaded.")
        for note in config.messages:
            self._log("WARNING", note)
        if config.get("demo_mode"):
            self.start_demo()
        elif config.get("auto_scan"):
            self.start_real_scan()
        else:
            self._set_scan_state("Ready - click Scan Nearby Networks", "#69d2e7")

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        export_action = QAction("Export Results...", self); export_action.triggered.connect(self.export_results); file_menu.addAction(export_action)
        quit_action = QAction("Exit", self); quit_action.triggered.connect(self.close); file_menu.addAction(quit_action)

    def _build_ui(self) -> None:
        root = QWidget(); self.setCentralWidget(root); outer = QHBoxLayout(root); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(235); side = QVBoxLayout(sidebar); side.setContentsMargins(18, 24, 18, 18)
        title = QLabel("WI-FI\nSECURITY ANALYZER"); title.setObjectName("brand"); side.addWidget(title)
        side.addWidget(QLabel("DEFENSIVE WLAN METADATA")); side.addSpacing(24)
        self.nav_buttons: list[QPushButton] = []
        for index, text in enumerate(("Dashboard", "Network Scanner", "Security Analysis", "Visualizations", "Logs", "Settings")):
            button = QPushButton(text); button.setCheckable(True); button.clicked.connect(lambda checked, i=index: self._go_to(i)); side.addWidget(button); self.nav_buttons.append(button)
        side.addStretch(); safety = QLabel("Passive discovery only\nNo packets, credentials, or attacks."); safety.setWordWrap(True); safety.setObjectName("safety"); side.addWidget(safety)
        outer.addWidget(sidebar)
        content = QWidget(); main = QVBoxLayout(content); main.setContentsMargins(24, 20, 24, 20); main.setSpacing(16)
        header = QHBoxLayout(); heading = QLabel("Wi-Fi Security Analyzer"); heading.setObjectName("heading"); header.addWidget(heading); header.addStretch()
        self.mode_badge = QLabel(); self.mode_badge.setObjectName("modeBadge"); header.addWidget(self.mode_badge)
        self.clock_label = QLabel(); self.clock_label.setObjectName("clock"); header.addWidget(self.clock_label); main.addLayout(header)
        self.pages = QStackedWidget(); self.pages.addWidget(self._dashboard_page()); self.pages.addWidget(self._scanner_page()); self.pages.addWidget(self._analysis_page()); self.pages.addWidget(self._charts_page()); self.pages.addWidget(self._logs_page()); self.pages.addWidget(self._settings_page()); main.addWidget(self.pages)
        outer.addWidget(content); self._go_to(0); self._update_mode_badge()

    def _card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame(); frame.setObjectName("card"); layout = QVBoxLayout(frame); layout.setContentsMargins(18, 16, 18, 16); layout.setSpacing(8); label = QLabel(title.upper()); label.setObjectName("cardTitle"); layout.addWidget(label); return frame, layout

    def _dashboard_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); intro = QLabel("Live environment summary. Security assessment is based on available Wi-Fi metadata."); intro.setObjectName("subheading"); layout.addWidget(intro)
        grid = QGridLayout(); grid.setSpacing(14); self.cards: dict[str, QLabel] = {}
        for index, name in enumerate(("Networks Found", "Secure", "Warnings", "High Risk", "Average Score")):
            card, card_layout = self._card(name); value = QLabel("0"); value.setObjectName("cardValue"); card_layout.addWidget(value); self.cards[name] = value; grid.addWidget(card, 0, index)
        layout.addLayout(grid)
        panel, panel_layout = self._card("Quick start"); panel_layout.addWidget(QLabel("Use Demo Mode for a hardware-independent walkthrough, or select Network Scanner to run authorized passive Windows WLAN discovery.")); layout.addWidget(panel); layout.addStretch(); return page

    def _scanner_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setSpacing(14)
        controls, row = self._card("Real Wi-Fi discovery"); row_layout = QHBoxLayout(); row.addLayout(row_layout)
        self.scan_button = QPushButton("Scan Nearby Networks"); self.scan_button.setObjectName("primaryButton"); self.scan_button.clicked.connect(self.start_real_scan); row_layout.addWidget(self.scan_button)
        self.demo_button = QPushButton("Start Demo Mode"); self.demo_button.clicked.connect(self.start_demo); row_layout.addWidget(self.demo_button)
        self.stop_button = QPushButton("Stop"); self.stop_button.clicked.connect(self.stop_scan); self.stop_button.setEnabled(False); row_layout.addWidget(self.stop_button)
        self.retry_button = QPushButton("Retry Scan"); self.retry_button.clicked.connect(self.start_real_scan); self.retry_button.hide(); row_layout.addWidget(self.retry_button)
        self.export_button = QPushButton("Export CSV"); self.export_button.clicked.connect(self.export_results); row_layout.addWidget(self.export_button); row_layout.addStretch()
        self.scan_status = QLabel(); self.scan_status.setObjectName("scanStatus"); row.addWidget(self.scan_status)
        self.scan_meta = QLabel("Networks found: 0   |   Last scan: Never"); self.scan_meta.setObjectName("subheading"); row.addWidget(self.scan_meta); layout.addWidget(controls)
        splitter = QSplitter(Qt.Orientation.Horizontal); table_card, table_layout = self._card("Nearby networks - connected and available")
        search_row = QHBoxLayout(); search_row.addWidget(QLabel("Filter")); self.search = QLineEdit(); self.search.setPlaceholderText("SSID, security, vendor, status"); self.search.textChanged.connect(self.populate_table); search_row.addWidget(self.search); table_layout.addLayout(search_row)
        self.table = QTableWidget(0, 9); self.table.setHorizontalHeaderLabels(["SSID", "Signal", "Channel", "Security", "Connection", "Vendor", "Status", "Score", "Last Seen"]); self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection); self.table.setSortingEnabled(True); self.table.horizontalHeader().setStretchLastSection(True); self.table.itemSelectionChanged.connect(self._show_selected_network); table_layout.addWidget(self.table); splitter.addWidget(table_card)
        details_card, details_layout = self._card("Network details"); self.detail_labels: dict[str, QLabel] = {}; form = QFormLayout()
        for name in ("SSID", "BSSID", "Signal", "Channel", "Security", "Connection", "Vendor", "First Seen", "Last Seen", "Security Score", "Status"):
            value = QLabel("Select a network"); value.setWordWrap(True); self.detail_labels[name] = value; form.addRow(f"{name}:", value)
        details_layout.addLayout(form); details_layout.addWidget(QLabel("DETECTED ISSUES")); self.issues_view = QPlainTextEdit(); self.issues_view.setReadOnly(True); self.issues_view.setMaximumBlockCount(30); details_layout.addWidget(self.issues_view); splitter.addWidget(details_card); splitter.setSizes([900, 360]); layout.addWidget(splitter, 1)
        diagnostic = QGroupBox("Scan Diagnostics - View Details"); diagnostic_layout = QVBoxLayout(diagnostic); self.diagnostic_view = QPlainTextEdit(); self.diagnostic_view.setReadOnly(True); self.diagnostic_view.setMaximumHeight(135); diagnostic_layout.addWidget(self.diagnostic_view); layout.addWidget(diagnostic)
        self._refresh_diagnostic(); return page

    def _analysis_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); card, card_layout = self._card("Security analysis"); note = QLabel("Scores are heuristic assessments based on reported Wi-Fi metadata. They never prove a network is safe."); note.setWordWrap(True); card_layout.addWidget(note); self.analysis_text = QPlainTextEdit(); self.analysis_text.setReadOnly(True); card_layout.addWidget(self.analysis_text); layout.addWidget(card); return page

    def _charts_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); card, card_layout = self._card("Environment visualizations"); self.figure = Figure(facecolor="#151c2d"); self.canvas = FigureCanvas(self.figure); card_layout.addWidget(self.canvas); layout.addWidget(card); return page

    def _logs_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); card, card_layout = self._card("Application logs"); controls = QHBoxLayout(); clear = QPushButton("Clear Logs"); clear.clicked.connect(self.clear_logs); save = QPushButton("Save Logs..."); save.clicked.connect(self.save_logs); controls.addWidget(clear); controls.addWidget(save); controls.addStretch(); card_layout.addLayout(controls); self.log_view = QPlainTextEdit(); self.log_view.setReadOnly(True); card_layout.addWidget(self.log_view); layout.addWidget(card); return page

    def _settings_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); card, card_layout = self._card("Settings"); form = QFormLayout(); self.interval_input = QSpinBox(); self.interval_input.setRange(1, 3600); self.interval_input.setValue(config.get("scan_interval")); self.demo_input = QCheckBox("Start in Demo Mode"); self.demo_input.setChecked(config.get("demo_mode")); self.auto_input = QCheckBox("Start real scan automatically when Demo Mode is off"); self.auto_input.setChecked(config.get("auto_scan")); self.log_level = QComboBox(); self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"]); self.log_level.setCurrentText(config.get("log_level")); self.adapter_label = QLabel(self.last_diagnostic.adapter); form.addRow("Scan interval (seconds)", self.interval_input); form.addRow("Startup mode", self.demo_input); form.addRow("Auto scan", self.auto_input); form.addRow("Log level", self.log_level); form.addRow("Scanner", QLabel("Windows WLAN / netsh")); form.addRow("Scan type", QLabel("Passive discovery")); form.addRow("Wi-Fi adapter", self.adapter_label); card_layout.addLayout(form); save = QPushButton("Save Settings"); save.setObjectName("primaryButton"); save.clicked.connect(self.save_settings); card_layout.addWidget(save); card_layout.addStretch(); layout.addWidget(card); layout.addStretch()
        return page

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget { background:#0d1321; color:#e7eefb; font-family:Segoe UI, Arial; font-size:13px; }
            #sidebar { background:#101a2d; border-right:1px solid #253653; } #brand { color:#59d9ff; font-size:21px; font-weight:700; letter-spacing:1px; } #safety { color:#8da0bb; padding:12px; background:#16233a; border-radius:8px; }
            QPushButton { background:#1b2a44; border:1px solid #2b4266; padding:10px 13px; border-radius:7px; color:#e7eefb; text-align:left; } QPushButton:hover, QPushButton:checked { background:#203b61; border-color:#4fd8ff; } #primaryButton { background:#087ea4; border-color:#3cd9ff; font-weight:700; }
            #heading { font-size:24px; font-weight:700; } #modeBadge, #clock { padding:8px 12px; background:#18253c; border-radius:12px; } #card { background:#141f33; border:1px solid #233958; border-radius:11px; } #cardTitle { color:#85a1c5; font-size:11px; font-weight:700; letter-spacing:1px; } #cardValue { font-size:28px; font-weight:700; color:#57d7ff; } #subheading { color:#9eb2cf; } #scanStatus { font-weight:700; }
            QLineEdit, QPlainTextEdit, QTableWidget, QComboBox, QSpinBox { background:#0f1829; border:1px solid #2a4164; border-radius:6px; padding:7px; color:#edf5ff; } QTableWidget { gridline-color:#253754; } QHeaderView::section { background:#1c2a43; color:#9fc7ea; border:0; padding:9px; font-weight:700; } QGroupBox { border:1px solid #2a4164; border-radius:8px; margin-top:10px; padding-top:8px; color:#9fc7ea; } QGroupBox::title { left:12px; padding:0 4px; } QScrollBar:vertical { background:#101a2d; width:10px; } QScrollBar::handle:vertical { background:#365478; border-radius:5px; }
        """)

    def _go_to(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for item_index, button in enumerate(self.nav_buttons):
            button.setChecked(item_index == index)

    def _update_clock(self) -> None:
        self.clock_label.setText(datetime.now().strftime("%d %b %Y  %H:%M:%S"))

    def _update_mode_badge(self) -> None:
        is_demo = self.mode.startswith("DEMO"); self.mode_badge.setText(f"●  {self.mode}"); self.mode_badge.setStyleSheet(f"background:{'#155b4a' if is_demo else '#164b75'}; color:#ecfff8; padding:8px 12px; border-radius:12px; font-weight:700;")

    def _set_scan_state(self, text: str, color: str = "#69d2e7") -> None:
        self.scan_status.setText(f"● {text}"); self.scan_status.setStyleSheet(f"color:{color}; font-weight:700;")

    def _log(self, level: str, message: str) -> None:
        getattr(logger, level.lower())(message); self.log_view.appendPlainText(f"{datetime.now():%H:%M:%S}  {level:<7} {message}")

    def _refresh_diagnostic(self) -> None:
        self.diagnostic_view.setPlainText(self.last_diagnostic.details())
        if hasattr(self, "adapter_label"):
            self.adapter_label.setText(self.last_diagnostic.adapter)

    def start_demo(self) -> None:
        self.stop_scan(announce=False); self.mode = "DEMO MODE - SIMULATED DATA"; self._update_mode_badge(); self.retry_button.hide(); self._accept_rows(demo_networks()); self.last_diagnostic = ScanDiagnostic(adapter="Not required in Demo Mode", parser_note="Deterministic simulated data"); self._refresh_diagnostic(); self._set_scan_state("Demo data loaded", "#65e5a2"); self._log("INFO", "Demo mode started with six deterministic simulated networks.")

    def start_real_scan(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        self.stop_scan(announce=False); self.mode = "REAL SCAN - WINDOWS WLAN"; self._update_mode_badge(); self.pending_networks = []; self.retry_button.hide(); self.scan_button.setEnabled(False); self.stop_button.setEnabled(True); self._set_scan_state("Scanning nearby Wi-Fi networks...", "#55d8ff"); self._log("INFO", "Starting passive Windows Wi-Fi scan using netsh.")
        worker = ScanWorker(config.get("scan_interval", 10)); worker.started.connect(self._worker_started); worker.progress.connect(self._worker_progress); worker.network_found.connect(self._network_found); worker.completed.connect(self._scan_completed); worker.error.connect(self._scan_error); worker.stopped.connect(self._worker_stopped); worker.finished.connect(lambda w=worker: self._retire_worker(w)); self.worker = worker; worker.start()

    def stop_scan(self, announce: bool = True) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.stop(); self.retired_workers.append(self.worker)
        self.worker = None; self.stop_button.setEnabled(False); self.scan_button.setEnabled(True)
        if announce:
            self._set_scan_state("Scan stopped", "#f2bd5d"); self._log("INFO", "Scan stopped by user.")

    def _retire_worker(self, worker: ScanWorker) -> None:
        if worker in self.retired_workers:
            self.retired_workers.remove(worker)
        if self.worker is worker:
            self.worker = None
        worker.deleteLater()

    def _worker_started(self) -> None:
        self._set_scan_state("Scanning nearby Wi-Fi networks...", "#55d8ff")

    def _worker_progress(self, details: str) -> None:
        self.diagnostic_view.setPlainText(details)
        logger.info("Raw Windows WLAN diagnostics:\n%s", details)
        self._log("INFO", "Windows WLAN command completed; parser diagnostics updated.")

    def _network_found(self, row: dict) -> None:
        self.pending_networks.append(row); self.scan_meta.setText(f"Networks found: {len(self.pending_networks)}   |   Last scan: In progress"); self._log("INFO", f"Network discovered: {row.get('ssid', 'Hidden network')}")

    def _scan_completed(self, rows: list, diagnostic: object) -> None:
        if isinstance(diagnostic, ScanDiagnostic): self.last_diagnostic = diagnostic; self._refresh_diagnostic()
        self._accept_rows(rows); now = datetime.now().strftime("%H:%M:%S"); self.scan_meta.setText(f"Networks found: {len(rows)}   |   Last scan: {now}"); self._set_scan_state(f"Scan completed - {len(rows)} network(s) found", "#65e5a2"); self._log("INFO", f"Scan completed: {len(rows)} network(s) found.")

    def _scan_error(self, message: str, details: str) -> None:
        fixes = ("\n\nSuggested fixes:\n1. Check that Wi-Fi is enabled.\n2. Check that the Wi-Fi adapter is enabled.\n"
                 "3. Check the Windows WLAN AutoConfig service.\n4. Run `netsh wlan show networks mode=bssid` in Command Prompt.\n"
                 "5. Confirm that Windows itself can see nearby networks, then click Retry Scan.")
        self._set_scan_state(message, "#ff8a80"); self.retry_button.show(); self.diagnostic_view.setPlainText(details + fixes); self._log("ERROR", message); self._log("WARNING", "Open Scan Diagnostics for command, return code, and troubleshooting details.")

    def _worker_stopped(self) -> None:
        self.scan_button.setEnabled(True); self.stop_button.setEnabled(False)

    def _accept_rows(self, rows: list[dict]) -> None:
        normalized: list[Network] = []
        for index, row in enumerate(rows):
            safe = row if isinstance(row, dict) else {}; key = str(safe.get("bssid") or safe.get("ssid") or index); network = Network.from_scan(safe, self.history.get(key)); self.history[key] = network; normalized.append(network)
        self.networks = analyse_all(normalized); self.populate_table(); self.update_dashboard(); self.update_analysis(); self.update_charts()

    def populate_table(self) -> None:
        term = self.search.text().casefold(); visible = [n for n in self.networks if term in " ".join((n.ssid, n.security_type, n.vendor, n.security_status, "Connected" if n.connected else "Available")).casefold()]; self.table.setSortingEnabled(False); self.table.setRowCount(len(visible))
        for row, network in enumerate(visible):
            values = [network.ssid, "Unknown" if network.signal_strength is None else f"{network.signal_strength}%", "Unknown" if network.channel is None else str(network.channel), network.security_type, "Connected" if network.connected else "Available", network.vendor, network.security_status, str(network.health_score), network.last_seen]
            for column, value in enumerate(values):
                item = NumericItem(value, network.signal_strength if network.signal_strength is not None else -1) if column == 1 else NumericItem(value, network.channel if network.channel is not None else -1) if column == 2 else NumericItem(value, network.health_score) if column == 7 else QTableWidgetItem(value)
                if column == 0: item.setData(Qt.ItemDataRole.UserRole + 1, network.bssid)
                if column == 4: item.setBackground(QColor("#155b4a" if network.connected else "#24344d"))
                if column == 6: item.setBackground(QColor({"Secure":"#155b4a", "Moderate":"#6d5420", "Vulnerable":"#6b2c36"}.get(network.security_status, "#35445d")))
                self.table.setItem(row, column, item)
        self.table.setSortingEnabled(True)
        if not visible and self.mode.startswith("REAL"):
            self._set_scan_state("No nearby Wi-Fi networks were detected. Check diagnostics and retry.", "#f2bd5d"); self.retry_button.show()

    def _show_selected_network(self) -> None:
        row = self.table.currentRow()
        if row < 0: return
        ssid_item = self.table.item(row, 0)
        bssid = ssid_item.data(Qt.ItemDataRole.UserRole + 1) if ssid_item else None
        network = next((n for n in self.networks if n.ssid == ssid_item.text() and n.bssid == bssid), None) if ssid_item else None
        if not network: return
        values = {"SSID":network.ssid, "BSSID":network.bssid, "Signal":"Unknown" if network.signal_strength is None else f"{network.signal_strength}%", "Channel":network.channel if network.channel is not None else "Unknown", "Security":network.security_type, "Connection":"Connected" if network.connected else "Available", "Vendor":network.vendor, "First Seen":network.first_seen, "Last Seen":network.last_seen, "Security Score":f"{network.health_score}/100", "Status":network.security_status}
        for key, value in values.items(): self.detail_labels[key].setText(str(value))
        self.issues_view.setPlainText("\n".join(f"- {issue}" for issue in network.detected_issues) or "None detected from available scan metadata.")

    def update_dashboard(self) -> None:
        counts = Counter(n.security_status for n in self.networks); average = round(sum(n.health_score for n in self.networks) / len(self.networks)) if self.networks else 0; values = {"Networks Found":len(self.networks), "Secure":counts["Secure"], "Warnings":counts["Moderate"], "High Risk":counts["Vulnerable"], "Average Score":f"{average}/100"}
        for key, value in values.items(): self.cards[key].setText(str(value))

    def update_analysis(self) -> None:
        lines = ["Security assessment based on available Wi-Fi metadata; it is not a guarantee of safety.\n"]
        for network in self.networks:
            issues = "\n".join(f"  - {issue}" for issue in network.detected_issues) or "  - None detected from available metadata."
            lines.extend((f"{network.ssid} | Score: {network.health_score}/100 | {network.security_status}", issues, f"  {network.explanation}\n"))
        self.analysis_text.setPlainText("\n".join(lines))

    def update_charts(self) -> None:
        self.figure.clear(); axes = self.figure.subplots(1, 3); self.figure.patch.set_facecolor("#151c2d")
        for axis in axes: axis.set_facecolor("#151c2d"); axis.tick_params(colors="#c5d7ee"); axis.title.set_color("#eef6ff"); [spine.set_color("#40516c") for spine in axis.spines.values()]
        labels = [n.ssid.encode("ascii", "replace").decode("ascii") for n in self.networks]; axes[0].bar(labels, [n.signal_strength or 0 for n in self.networks], color="#52d6ff"); axes[0].set_title("Signal Strength"); axes[0].set_ylabel("Percent"); axes[0].set_ylim(0, 100); axes[0].tick_params(axis="x", rotation=65)
        statuses = Counter(n.security_status for n in self.networks)
        if statuses: axes[1].pie(statuses.values(), labels=statuses.keys(), autopct="%1.0f%%", colors=["#54d69c", "#f2bd5d", "#ff7c7c", "#8998b2"], textprops={"color":"#edf5ff"})
        else: axes[1].text(.5, .5, "No data", ha="center", color="#edf5ff")
        axes[1].set_title("Security Status")
        channels = Counter(n.channel for n in self.networks if n.channel is not None); axes[2].bar([str(value) for value in channels], channels.values(), color="#9a7dff"); axes[2].set_title("Channel Usage"); axes[2].set_xlabel("Channel")
        self.figure.tight_layout(); self.canvas.draw_idle()

    def export_results(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Results", "wifi-security-results.csv", "CSV files (*.csv)")
        if not path: return
        try:
            export_csv(path, self.networks); self.statusBar().showMessage(f"Export completed: {Path(path).name}", 5000); self._log("INFO", f"Export completed: {path}")
        except OSError as exc:
            self._log("ERROR", f"Could not export results: {exc}"); QMessageBox.warning(self, "Export failed", f"Could not write the CSV file.\n{exc}")

    def clear_logs(self) -> None:
        self.log_view.clear(); logger.info("Log display cleared.")

    def save_logs(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Logs", "wifi-analyzer-log.txt", "Text files (*.txt)")
        if not path: return
        try:
            Path(path).write_text(self.log_view.toPlainText(), encoding="utf-8"); self._log("INFO", f"Logs saved: {path}")
        except OSError as exc:
            self._log("ERROR", f"Could not save logs: {exc}"); QMessageBox.warning(self, "Save failed", f"Could not save logs.\n{exc}")

    def save_settings(self) -> None:
        config.set("scan_interval", self.interval_input.value()); config.set("demo_mode", self.demo_input.isChecked()); config.set("auto_scan", self.auto_input.isChecked()); config.set("log_level", self.log_level.currentText()); self._log("INFO", "Settings saved. Restart to apply startup settings and log level."); self.statusBar().showMessage("Settings saved", 4000)

    def closeEvent(self, event) -> None:
        self.stop_scan(announce=False)
        for worker in self.retired_workers:
            worker.wait()
        self._log("INFO", "Application closed."); event.accept()


def main() -> int:
    app = QApplication(sys.argv); app.setStyle("Fusion"); window = MainWindow(); window.show(); return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
