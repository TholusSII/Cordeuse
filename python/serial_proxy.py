from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import serial
from serial import SerialException
from serial.tools import list_ports
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


BAUD_RATES = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]


def ascii_view(data: bytes) -> str:
    return "".join(chr(byte) if 32 <= byte <= 126 else {9: "\\t", 10: "\\n", 13: "\\r"}.get(byte, ".") for byte in data)


def hex_view(data: bytes) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


class SerialBridge(QObject):
    log = Signal(str)
    stopped = Signal()
    error = Signal(str)

    def __init__(self, virtual_port: str, physical_port: str, baudrate: int) -> None:
        super().__init__()
        self.virtual_port = virtual_port
        self.physical_port = physical_port
        self.baudrate = baudrate
        self.running = False
        self.virtual_serial: serial.Serial | None = None
        self.physical_serial: serial.Serial | None = None

    def stop(self) -> None:
        self.running = False

    def run(self) -> None:
        try:
            self.virtual_serial = serial.Serial(
                self.virtual_port,
                self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.02,
                write_timeout=1,
            )
            self.physical_serial = serial.Serial(
                self.physical_port,
                self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.02,
                write_timeout=1,
            )
            self.running = True
            self.log.emit(
                f"Pont actif : {self.virtual_port} ↔ {self.physical_port} à {self.baudrate} bauds"
            )

            while self.running:
                if self.virtual_serial.in_waiting:
                    data = self.virtual_serial.read(self.virtual_serial.in_waiting)
                    if data:
                        self.physical_serial.write(data)
                        self._emit_packet("ANCIEN SP55 → CARTE", data)

                if self.physical_serial.in_waiting:
                    data = self.physical_serial.read(self.physical_serial.in_waiting)
                    if data:
                        self.virtual_serial.write(data)
                        self._emit_packet("CARTE → ANCIEN SP55", data)

        except (SerialException, OSError) as exc:
            self.error.emit(str(exc))
        finally:
            for port in (self.virtual_serial, self.physical_serial):
                if port is not None and port.is_open:
                    port.close()
            self.stopped.emit()

    def _emit_packet(self, direction: str, data: bytes) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log.emit(
            f"[{timestamp}] {direction}\n"
            f"ASCII : {ascii_view(data)}\n"
            f"HEX   : {hex_view(data)}\n"
        )


class SerialProxyWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SP55 — Proxy série")
        self.resize(960, 700)
        self.thread: QThread | None = None
        self.bridge: SerialBridge | None = None

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Capture bidirectionnelle du port série SP55")
        title.setStyleSheet("font:700 20px 'Segoe UI';")
        layout.addWidget(title)

        explanation = QLabel(
            "Port virtuel : côté ancien logiciel. Port physique : côté carte. "
            "Le proxy transmet les données dans les deux sens et journalise ASCII + HEX."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        grid = QGridLayout()
        grid.addWidget(QLabel("Port virtuel (ex. COM11)"), 0, 0)
        self.virtual_combo = QComboBox()
        self.virtual_combo.setEditable(True)
        grid.addWidget(self.virtual_combo, 0, 1)

        grid.addWidget(QLabel("Port physique carte"), 1, 0)
        self.physical_combo = QComboBox()
        self.physical_combo.setEditable(True)
        grid.addWidget(self.physical_combo, 1, 1)

        grid.addWidget(QLabel("Vitesse"), 2, 0)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems([str(value) for value in BAUD_RATES])
        self.baud_combo.setCurrentText("9600")
        grid.addWidget(self.baud_combo, 2, 1)

        refresh = QPushButton("Actualiser les ports")
        refresh.clicked.connect(self.refresh_ports)
        grid.addWidget(refresh, 0, 2, 2, 1)
        layout.addLayout(grid)

        actions = QHBoxLayout()
        self.start_button = QPushButton("Démarrer la capture")
        self.start_button.clicked.connect(self.start_bridge)
        self.stop_button = QPushButton("Arrêter")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_bridge)
        clear_button = QPushButton("Effacer le journal")
        clear_button.clicked.connect(lambda: self.log_view.clear())
        save_button = QPushButton("Enregistrer le journal")
        save_button.clicked.connect(self.save_log)
        actions.addWidget(self.start_button)
        actions.addWidget(self.stop_button)
        actions.addStretch()
        actions.addWidget(clear_button)
        actions.addWidget(save_button)
        layout.addLayout(actions)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_view, 1)

        self.refresh_ports()

    def refresh_ports(self) -> None:
        current_virtual = self.virtual_combo.currentText()
        current_physical = self.physical_combo.currentText()
        ports = [port.device for port in list_ports.comports()]
        self.virtual_combo.clear()
        self.physical_combo.clear()
        self.virtual_combo.addItems(ports)
        self.physical_combo.addItems(ports)
        if current_virtual:
            self.virtual_combo.setCurrentText(current_virtual)
        if current_physical:
            self.physical_combo.setCurrentText(current_physical)

    def append_log(self, text: str) -> None:
        self.log_view.appendPlainText(text)

    def start_bridge(self) -> None:
        virtual_port = self.virtual_combo.currentText().strip()
        physical_port = self.physical_combo.currentText().strip()
        if not virtual_port or not physical_port:
            QMessageBox.warning(self, "Ports manquants", "Sélectionne les deux ports COM.")
            return
        if virtual_port.upper() == physical_port.upper():
            QMessageBox.warning(self, "Ports identiques", "Les deux ports doivent être différents.")
            return

        self.thread = QThread(self)
        self.bridge = SerialBridge(virtual_port, physical_port, int(self.baud_combo.currentText()))
        self.bridge.moveToThread(self.thread)
        self.thread.started.connect(self.bridge.run)
        self.bridge.log.connect(self.append_log)
        self.bridge.error.connect(self.on_error)
        self.bridge.stopped.connect(self.thread.quit)
        self.bridge.stopped.connect(self.on_stopped)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_bridge(self) -> None:
        if self.bridge is not None:
            self.bridge.stop()

    def on_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erreur série", message)

    def on_stopped(self) -> None:
        self.append_log("Pont série arrêté.\n")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.bridge = None
        self.thread = None

    def save_log(self) -> None:
        default_name = Path.cwd() / f"capture_sp55_{datetime.now():%Y%m%d_%H%M%S}.txt"
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le journal", str(default_name), "Fichier texte (*.txt)"
        )
        if file_name:
            Path(file_name).write_text(self.log_view.toPlainText(), encoding="utf-8")

    def closeEvent(self, event) -> None:  # noqa: N802
        self.stop_bridge()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = SerialProxyWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
