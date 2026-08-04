from __future__ import annotations

from collections import deque

import pyqtgraph as pg
import serial
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QCheckBox, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from arduino_protocol import encode_line, parse_arduino_line, set_values_command, stream_command


CHANNELS = {
    "effort": ("Effort HX711", "unité calibrée"),
    "effort_raw": ("Effort brut", "points"),
    "current": ("Courant moteur", "unité calibrée"),
    "current_raw": ("Courant brut", "points"),
    "position": ("Position / vitesse", "unité calibrée"),
    "position_raw": ("Position brute", "points"),
    "corde": ("Potentiomètre corde", "unité calibrée"),
    "corde_raw": ("Potentiomètre brut", "points"),
    "pwm": ("Commande moteur", "PWM"),
    "fc_min": ("Fin de course mini", "0/1"),
    "fc_max": ("Fin de course maxi", "0/1"),
    "bp": ("Bouton traction", "0/1"),
}


class ArduinoMeasurementWindow(QMainWindow):
    """Pilotage et tracé temps réel des mesures émises par l'Arduino Mega."""

    MAX_POINTS = 4000

    def __init__(self, serial_manager, parent=None) -> None:
        super().__init__(parent)
        self.manager = serial_manager
        self.connection: serial.Serial | None = None
        self.rx_buffer = bytearray()
        self.times = deque(maxlen=self.MAX_POINTS)
        self.values = {key: deque(maxlen=self.MAX_POINTS) for key in CHANNELS}
        self.curves: dict[str, pg.PlotDataItem] = {}
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.poll_serial)
        self.setWindowTitle("Mesures Arduino Mega — SP55")
        self.resize(1200, 760)
        self.setMinimumSize(980, 650)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Pilotage et mesures de l’Arduino Mega")
        title.setStyleSheet("font:700 22px 'Segoe UI';color:#172033")
        self.status = QLabel("Déconnecté")
        self.status.setStyleSheet("color:#667085")
        layout.addWidget(title)
        layout.addWidget(self.status)

        settings = QFrame()
        settings.setStyleSheet("QFrame{background:white;border:1px solid #dfe6ef;border-radius:12px}")
        grid = QGridLayout(settings)
        self.setpoint = QDoubleSpinBox()
        self.setpoint.setRange(-100000.0, 100000.0)
        self.setpoint.setDecimals(3)
        self.setpoint.setValue(100.0)
        self.pwm = QSpinBox()
        self.pwm.setRange(0, 255)
        self.pwm.setValue(120)
        self.period = QSpinBox()
        self.period.setRange(20, 2000)
        self.period.setValue(50)
        self.period.setSuffix(" ms")
        grid.addWidget(QLabel("Consigne BF"), 0, 0)
        grid.addWidget(self.setpoint, 0, 1)
        grid.addWidget(QLabel("PWM BO"), 0, 2)
        grid.addWidget(self.pwm, 0, 3)
        grid.addWidget(QLabel("Période mesures"), 0, 4)
        grid.addWidget(self.period, 0, 5)
        apply_values = QPushButton("Mettre à jour les valeurs")
        apply_values.clicked.connect(self.apply_values)
        grid.addWidget(apply_values, 0, 6)
        layout.addWidget(settings)

        body = QHBoxLayout()
        selection = QFrame()
        selection.setFixedWidth(260)
        selection.setStyleSheet("QFrame{background:white;border:1px solid #dfe6ef;border-radius:12px}")
        side = QVBoxLayout(selection)
        side.addWidget(QLabel("Grandeurs à tracer"))
        self.checks: dict[str, QCheckBox] = {}
        for key, (label, unit) in CHANNELS.items():
            check = QCheckBox(f"{label} ({unit})")
            check.setChecked(key in {"effort", "current", "position", "pwm"})
            check.toggled.connect(self.refresh_curves)
            self.checks[key] = check
            side.addWidget(check)
        side.addStretch()
        body.addWidget(selection)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("w")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setLabel("bottom", "Temps", units="s")
        self.plot.addLegend()
        body.addWidget(self.plot, 1)
        layout.addLayout(body, 1)

        actions = QHBoxLayout()
        self.connect_button = QPushButton("Connecter et recevoir")
        self.connect_button.clicked.connect(self.toggle_connection)
        start_button = QPushButton("Démarrer traction")
        start_button.clicked.connect(lambda: self.send_command("START"))
        stop_button = QPushButton("Arrêter / retour")
        stop_button.clicked.connect(lambda: self.send_command("STOP"))
        tare_button = QPushButton("Tare effort")
        tare_button.clicked.connect(lambda: self.send_command("TARE"))
        clear_button = QPushButton("Effacer les courbes")
        clear_button.clicked.connect(self.clear_data)
        actions.addWidget(self.connect_button)
        actions.addWidget(start_button)
        actions.addWidget(stop_button)
        actions.addWidget(tare_button)
        actions.addStretch()
        actions.addWidget(clear_button)
        layout.addLayout(actions)
        self.refresh_curves()

    def toggle_connection(self) -> None:
        if self.connection and self.connection.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self) -> None:
        endpoint = self.manager.control
        if not endpoint.port:
            QMessageBox.warning(self, "Arduino", "Configurez d'abord le port de l'Arduino Mega dans Réglages.")
            return
        try:
            self.connection = serial.Serial(endpoint.port, endpoint.baudrate, timeout=0, write_timeout=1)
            self.connection.reset_input_buffer()
            self.connection.write(encode_line("HELLO?"))
            self.connection.write(stream_command(True, self.period.value()))
            self.connection.flush()
        except (OSError, serial.SerialException) as exc:
            self.connection = None
            QMessageBox.critical(self, "Connexion impossible", str(exc))
            return
        self.timer.start()
        self.connect_button.setText("Déconnecter")
        self.status.setText(f"Connecté à {endpoint.port} — {endpoint.baudrate} bauds")

    def disconnect_serial(self) -> None:
        self.timer.stop()
        if self.connection:
            try:
                if self.connection.is_open:
                    self.connection.write(stream_command(False, self.period.value()))
                    self.connection.close()
            except (OSError, serial.SerialException):
                pass
        self.connection = None
        self.connect_button.setText("Connecter et recevoir")
        self.status.setText("Déconnecté")

    def send_command(self, command: str) -> None:
        if not self.connection or not self.connection.is_open:
            QMessageBox.information(self, "Arduino", "Connectez d'abord l'Arduino Mega.")
            return
        try:
            self.connection.write(encode_line(command))
            self.connection.flush()
        except (OSError, serial.SerialException) as exc:
            QMessageBox.critical(self, "Envoi impossible", str(exc))
            self.disconnect_serial()

    def apply_values(self) -> None:
        if not self.connection or not self.connection.is_open:
            QMessageBox.information(self, "Arduino", "Connectez d'abord l'Arduino Mega.")
            return
        try:
            self.connection.write(set_values_command(setpoint=self.setpoint.value(), pwm=self.pwm.value()))
            self.connection.write(stream_command(True, self.period.value()))
            self.connection.flush()
        except (OSError, serial.SerialException) as exc:
            QMessageBox.critical(self, "Mise à jour impossible", str(exc))

    def poll_serial(self) -> None:
        if not self.connection or not self.connection.is_open:
            return
        try:
            waiting = self.connection.in_waiting
            if waiting:
                self.rx_buffer.extend(self.connection.read(waiting))
        except (OSError, serial.SerialException):
            self.disconnect_serial()
            return
        while b"\n" in self.rx_buffer:
            raw, _, remainder = self.rx_buffer.partition(b"\n")
            self.rx_buffer = bytearray(remainder)
            line = raw.decode("utf-8", errors="replace").strip()
            frame = parse_arduino_line(line)
            if frame.kind == "MEAS":
                self.add_measurement(frame)
            elif frame.kind in {"HELLO", "ACK", "EVENT", "ERR"}:
                self.status.setText(frame.raw)

    def add_measurement(self, frame) -> None:
        t = frame.number("t") / 1000.0
        self.times.append(t)
        for key in CHANNELS:
            self.values[key].append(frame.number(key))
        self.update_plot()
        mode = frame.fields.get("mode", "?")
        state = frame.fields.get("state", "?")
        self.status.setText(f"Réception — mode {mode}, état {state}, {len(self.times)} points")

    def refresh_curves(self) -> None:
        selected = {key for key, check in self.checks.items() if check.isChecked()}
        for key in list(self.curves):
            if key not in selected:
                self.plot.removeItem(self.curves.pop(key))
        pens = ["#2563eb", "#ef4444", "#16a34a", "#f59e0b", "#7c3aed", "#0891b2", "#ec4899", "#64748b"]
        for index, key in enumerate(selected):
            if key not in self.curves:
                self.curves[key] = self.plot.plot([], [], pen=pg.mkPen(pens[index % len(pens)], width=2), name=CHANNELS[key][0])
        self.update_plot()

    def update_plot(self) -> None:
        x = list(self.times)
        for key, curve in self.curves.items():
            curve.setData(x, list(self.values[key]))

    def clear_data(self) -> None:
        self.times.clear()
        for values in self.values.values():
            values.clear()
        self.update_plot()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.disconnect_serial()
        super().closeEvent(event)
