from __future__ import annotations

from dataclasses import dataclass

import serial
from PySide6.QtCore import QObject, QSettings, QTimer, Signal
from serial.tools import list_ports

from serial_controller import CommandSettings


@dataclass
class SerialEndpoint:
    """Configuration d'une liaison série de la cordeuse."""

    port: str = ""
    baudrate: int = 115200
    timeout: float = 1.0


class DualSerialManager(QObject):
    """Gère les deux ports série et partage une connexion Arduino unique."""

    measurement_state_changed = Signal(bool, str)
    control_state_changed = Signal(bool, str)
    measurement_bytes_received = Signal(bytes)
    control_bytes_received = Signal(bytes)
    control_line_received = Signal(str)
    communication_error = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.measurement = SerialEndpoint(baudrate=9600)
        self.control = SerialEndpoint(baudrate=115200, timeout=0.0)
        self._measurement_serial: serial.Serial | None = None
        self._control_serial: serial.Serial | None = None
        self._control_rx_buffer = bytearray()
        self._settings = QSettings("TholusSII", "CordeuseSP55")
        self._control_timer = QTimer(self)
        self._control_timer.setInterval(15)
        self._control_timer.timeout.connect(self._poll_control)
        self.load_settings()

    @staticmethod
    def available_ports() -> list[tuple[str, str]]:
        return [
            (item.device, item.description or "Port série")
            for item in sorted(list_ports.comports(), key=lambda value: value.device)
        ]

    def load_settings(self) -> None:
        self.measurement.port = str(self._settings.value("serial/measurement_port", ""))
        self.measurement.baudrate = int(self._settings.value("serial/measurement_baud", 9600))
        self.control.port = str(self._settings.value("serial/control_port", ""))
        self.control.baudrate = int(self._settings.value("serial/control_baud", 115200))

    def save_settings(self) -> None:
        self._settings.setValue("serial/measurement_port", self.measurement.port)
        self._settings.setValue("serial/measurement_baud", self.measurement.baudrate)
        self._settings.setValue("serial/control_port", self.control.port)
        self._settings.setValue("serial/control_baud", self.control.baudrate)
        self._settings.sync()

    def configure_measurement(self, port: str, baudrate: int) -> None:
        self._validate_pair(port, self.control.port, "boîtier de mesure")
        self.measurement.port = port.strip()
        self.measurement.baudrate = int(baudrate)
        self.save_settings()

    def configure_control(self, port: str, baudrate: int) -> None:
        self._validate_pair(port, self.measurement.port, "Arduino Mega")
        new_port = port.strip()
        new_baud = int(baudrate)
        changed = new_port != self.control.port or new_baud != self.control.baudrate
        if changed:
            self.close_control()
        self.control.port = new_port
        self.control.baudrate = new_baud
        self.save_settings()

    @staticmethod
    def _validate_pair(candidate: str, other: str, label: str) -> None:
        if candidate and other and candidate.casefold() == other.casefold():
            raise ValueError(
                f"Le port {candidate} est déjà affecté à l'autre liaison. "
                f"Choisissez un port distinct pour {label}."
            )

    def open_measurement(self) -> serial.Serial:
        if self._measurement_serial and self._measurement_serial.is_open:
            return self._measurement_serial
        if not self.measurement.port:
            raise ValueError("Aucun port n'est configuré pour le boîtier de mesure.")
        try:
            self._measurement_serial = serial.Serial(
                self.measurement.port,
                self.measurement.baudrate,
                timeout=self.measurement.timeout,
                write_timeout=self.measurement.timeout,
            )
        except (OSError, serial.SerialException) as exc:
            self.measurement_state_changed.emit(False, str(exc))
            self.communication_error.emit("measurement", str(exc))
            raise
        self.measurement_state_changed.emit(True, self.measurement.port)
        return self._measurement_serial

    def close_measurement(self) -> None:
        if self._measurement_serial:
            try:
                self._measurement_serial.close()
            finally:
                self._measurement_serial = None
        self.measurement_state_changed.emit(False, "Déconnecté")

    def write_measurement(self, payload: bytes) -> None:
        connection = self.open_measurement()
        connection.write(payload)
        connection.flush()

    def read_measurement_raw(self, size: int | None = None) -> bytes:
        connection = self.open_measurement()
        count = size if size is not None else max(1, connection.in_waiting)
        payload = connection.read(count)
        if payload:
            self.measurement_bytes_received.emit(payload)
        return payload

    @property
    def control_is_open(self) -> bool:
        return bool(self._control_serial and self._control_serial.is_open)

    def open_control(self) -> serial.Serial:
        """Ouvre une seule fois le port Arduino et le conserve pour toute l'application."""
        if self.control_is_open:
            return self._control_serial  # type: ignore[return-value]
        if not self.control.port:
            raise ValueError("Aucun port n'est configuré pour l'Arduino Mega.")
        try:
            self._control_serial = serial.Serial(
                self.control.port,
                self.control.baudrate,
                timeout=0,
                write_timeout=1.0,
            )
            self._control_serial.reset_input_buffer()
        except (OSError, serial.SerialException) as exc:
            self._control_serial = None
            self.control_state_changed.emit(False, str(exc))
            self.communication_error.emit("control", str(exc))
            raise
        self._control_rx_buffer.clear()
        self._control_timer.start()
        self.control_state_changed.emit(True, self.control.port)
        return self._control_serial

    def close_control(self) -> None:
        self._control_timer.stop()
        if self._control_serial:
            try:
                self._control_serial.close()
            finally:
                self._control_serial = None
        self._control_rx_buffer.clear()
        self.control_state_changed.emit(False, "Déconnecté")

    def write_control(self, payload: bytes) -> None:
        connection = self.open_control()
        try:
            connection.write(payload)
            connection.flush()
        except (OSError, serial.SerialException) as exc:
            self.communication_error.emit("control", str(exc))
            self.close_control()
            raise

    def write_control_line(self, line: str) -> None:
        self.write_control((line.rstrip("\r\n") + "\n").encode("utf-8"))

    def send_control_command(self, settings: CommandSettings) -> str:
        """Envoie BO/BF/Constructeur sur la connexion Arduino partagée."""
        self.write_control(settings.encode())
        return "Commande envoyée sur la connexion Arduino partagée."

    def _poll_control(self) -> None:
        connection = self._control_serial
        if not connection or not connection.is_open:
            self._control_timer.stop()
            return
        try:
            waiting = connection.in_waiting
            if not waiting:
                return
            payload = connection.read(waiting)
        except (OSError, serial.SerialException) as exc:
            self.communication_error.emit("control", str(exc))
            self.close_control()
            return
        if not payload:
            return
        self.control_bytes_received.emit(payload)
        self._control_rx_buffer.extend(payload)
        while b"\n" in self._control_rx_buffer:
            raw, _, remainder = self._control_rx_buffer.partition(b"\n")
            self._control_rx_buffer = bytearray(remainder)
            line = raw.decode("utf-8", errors="replace").strip()
            if line:
                self.control_line_received.emit(line)

    def close_all(self) -> None:
        self.close_measurement()
        self.close_control()
