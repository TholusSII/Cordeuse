from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QSpinBox, QVBoxLayout, QWidget,
)

from mes_reader import COLUMN_KEYS
from mes_writer import write_mes

try:
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    list_ports = None


class StatusLamp(QLabel):
    def __init__(self, label: str, color: str) -> None:
        super().__init__(f"●  {label}")
        self.color = color
        self.set_active(False)

    def set_active(self, active: bool) -> None:
        visible = self.color if active else "#98a2b3"
        self.setStyleSheet(f"font:600 12px 'Segoe UI';color:{visible};padding:5px")


class MeasurementWindow(QMainWindow):
    measurement_saved = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Réalisation des mesures — SP55")
        self.resize(720, 520)
        self.setMinimumSize(650, 460)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._simulation_step)
        self.current_sample = 0
        self.sample_count = 500
        self.measurement: dict[str, np.ndarray] | None = None
        self._build_ui()
        self.refresh_ports()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            "QMainWindow,QWidget{background:#f4f7fb;color:#172033;font-family:'Segoe UI'}"
            "QFrame#card{background:white;border:1px solid #dfe6ef;border-radius:14px}"
            "QPushButton{background:white;border:1px solid #d8dee9;border-radius:9px;padding:9px 14px}"
            "QPushButton:hover{background:#f4f8ff;border-color:#9bbcf2}"
            "QPushButton#primary{background:#2563eb;color:white;border:none;font-weight:600}"
            "QPlainTextEdit{background:#fbfcfe;border:1px solid #dfe6ef;border-radius:9px;padding:8px}"
        )
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("Réalisation des mesures")
        title.setStyleSheet("font:700 22px 'Segoe UI'")
        layout.addWidget(title)

        connection = QFrame(); connection.setObjectName("card")
        row = QHBoxLayout(connection)
        self.port = QComboBox(); self.baud = QComboBox()
        self.baud.addItems(["9600", "19200", "38400", "57600", "115200"])
        refresh = QPushButton("Actualiser les ports"); refresh.clicked.connect(self.refresh_ports)
        self.simulation = QCheckBox("Mode simulation")
        self.simulation.setChecked(True)
        row.addWidget(QLabel("Port série")); row.addWidget(self.port, 1)
        row.addWidget(QLabel("Vitesse")); row.addWidget(self.baud)
        row.addWidget(refresh); row.addWidget(self.simulation)
        layout.addWidget(connection)

        status = QFrame(); status.setObjectName("card")
        status_layout = QHBoxLayout(status)
        self.emit_lamp = StatusLamp("Émission", "#16a34a")
        self.receive_lamp = StatusLamp("Réception", "#ef4444")
        self.counter = QLabel("0 / 500 points")
        status_layout.addWidget(self.emit_lamp)
        status_layout.addWidget(self.receive_lamp)
        status_layout.addStretch()
        status_layout.addWidget(self.counter)
        layout.addWidget(status)

        self.progress = QProgressBar()
        self.progress.setRange(0, self.sample_count)
        self.progress.setValue(0)
        self.progress.setFormat("Réception : %v / %m points — %p %")
        layout.addWidget(self.progress)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Les informations d'émission et de réception apparaîtront ici.")
        layout.addWidget(self.log, 1)

        actions = QHBoxLayout()
        self.start = QPushButton("Initialiser et lancer la mesure")
        self.start.setObjectName("primary")
        self.start.clicked.connect(self.start_measurement)
        self.save = QPushButton("Enregistrer sous…")
        self.save.setEnabled(False)
        self.save.clicked.connect(self.save_measurement)
        close = QPushButton("Fermer"); close.clicked.connect(self.close)
        actions.addWidget(self.start, 2); actions.addWidget(self.save); actions.addStretch(); actions.addWidget(close)
        layout.addLayout(actions)

    def refresh_ports(self) -> None:
        current = self.port.currentText()
        self.port.clear()
        ports = [p.device for p in list_ports.comports()] if list_ports else []
        self.port.addItems(ports)
        if current in ports:
            self.port.setCurrentText(current)
        if not ports:
            self.port.addItem("Aucun port détecté")

    def start_measurement(self) -> None:
        if not self.simulation.isChecked():
            QMessageBox.information(
                self, "Protocole série",
                "Le protocole d'acquisition réel n'est pas encore connu. Activez le mode simulation pour tester l'interface et le fichier .mes.",
            )
            return
        self.current_sample = 0
        self.measurement = self._make_simulated_measurement()
        self.progress.setValue(0)
        self.counter.setText(f"0 / {self.sample_count} points")
        self.log.clear()
        self.log.appendPlainText("TX  Initialisation de la mesure (simulation)")
        self.emit_lamp.set_active(True)
        self.receive_lamp.set_active(False)
        self.start.setEnabled(False)
        self.save.setEnabled(False)
        self.timer.start(12)

    def _simulation_step(self) -> None:
        self.emit_lamp.set_active(False)
        self.receive_lamp.set_active(True)
        self.current_sample = min(self.current_sample + 5, self.sample_count)
        self.progress.setValue(self.current_sample)
        self.counter.setText(f"{self.current_sample} / {self.sample_count} points")
        if self.current_sample % 50 == 0:
            self.log.appendPlainText(f"RX  {self.current_sample} points reçus")
        if self.current_sample >= self.sample_count:
            self.timer.stop()
            self.receive_lamp.set_active(False)
            self.start.setEnabled(True)
            self.save.setEnabled(True)
            self.log.appendPlainText("Acquisition terminée — mesure prête à être enregistrée.")

    def _make_simulated_measurement(self) -> dict[str, np.ndarray]:
        t = np.linspace(0.0, 10.0, self.sample_count, endpoint=False)
        data = {
            "theta_red": 12.0 * np.sin(0.8 * t),
            "Fc": 180.0 + 45.0 * np.tanh(t - 2.0),
            "Er": 4.0 + 0.8 * np.sin(0.9 * t),
            "I": 1.8 + 0.35 * np.sin(1.4 * t),
            "U": 12.0 + 0.6 * np.sin(0.5 * t),
            "omega_red": 75.0 + 18.0 * np.sin(0.7 * t),
            "omega_m": 920.0 + 210.0 * np.sin(0.7 * t),
            "theta_m": 360.0 * t,
            "Fr": 170.0 + 40.0 * np.tanh(t - 2.2),
            "Vch": 18.0 * np.exp(-0.25 * t) * np.sin(1.2 * t),
            "Dch": 35.0 * (1.0 - np.exp(-0.45 * t)),
        }
        return {key: np.asarray(data[key], dtype=float) for key in COLUMN_KEYS}

    def save_measurement(self) -> None:
        if self.measurement is None:
            return
        default = str(Path.cwd() / "333.mes")
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer la mesure", default, "Mesures SP55 (*.mes)"
        )
        if not file_name:
            return
        if not file_name.lower().endswith(".mes"):
            file_name += ".mes"
        try:
            path = write_mes(file_name, [self.measurement])
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Enregistrement impossible", str(exc))
            return
        self.log.appendPlainText(f"Fichier enregistré : {path}")
        self.measurement_saved.emit(str(path))
        QMessageBox.information(self, "Mesure enregistrée", f"Le fichier a été créé :\n{path}")
