from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import serial
from PySide6.QtCore import QObject, QSettings, Signal
from serial.tools import list_ports

from serial_controller import CommandSettings


@dataclass
class SerialEndpoint:
    """Configuration d'une liaison série de la cordeuse."""

    port: str = ""
    baudrate: int = 115200
    timeout: float = 1.0


class DualSerialManager(QObject):
    """Gère séparément le boîtier SP55 et l'Arduino Mega.

    Le protocole du boîtier de mesure est volontairement laissé hors de cette
    classe : elle fournit les octets bruts à un futur décodeur. La liaison
    Arduino dispose déjà d'un encodage de commande texte, mais celui-ci reste
    centralisé et pourra être remplacé lorsque le firmware sera figé.
    """

    measurement_state_changed = Signal(bool, str)
    control_state_changed = Signal(bool, str)
    measurement_bytes_received = Signal(bytes)
    control_bytes_received = Signal(bytes)
    communication_error = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.measurement = SerialEndpoint(baudrate=9600)
        self.control = SerialEndpoint(baudrate=115200)
        self._measurement_serial: serial.Serial | None = None
        self._control_serial: serial.Serial | None = None
        self._settings = QSettings("TholusSII", "CordeuseSP55")
        self.load_settings()

    @staticmethod
    def available_ports() -> list[tuple[str, str]]:
        return [
            (item.device, item.description or "Port série")
            for item in sorted(list_ports.comports(), key=lambda value: value.device)
        ]

    def load_settings(self) -> None:
        self.measurement.port = str(self._settings.value("serial/measurement_port", ""))
        self.measurement.baudrate = int(
            self._settings.value("serial/measurement_baud", 9600)
        )
        self.control.port = str(self._settings.value("serial/control_port", ""))
        self.control.baudrate = int(
            self._settings.value("serial/control_baud", 115200)
        )

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
        self.control.port = port.strip()
        self.control.baudrate = int(baudrate)
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

    def send_control_command(self, settings: CommandSettings) -> str:
        """Envoie une commande à l'Arduino sur sa liaison dédiée."""
        if not self.control.port:
            raise ValueError("Aucun port n'est configuré pour l'Arduino Mega.")
        payload = settings.encode()
        try:
            with serial.Serial(
                self.control.port,
                self.control.baudrate,
                timeout=self.control.timeout,
                write_timeout=self.control.timeout,
            ) as connection:
                self.control_state_changed.emit(True, self.control.port)
                connection.reset_input_buffer()
                connection.write(payload)
                connection.flush()
                answer_bytes = connection.readline()
        except (OSError, serial.SerialException) as exc:
            self.control_state_changed.emit(False, str(exc))
            self.communication_error.emit("control", str(exc))
            raise
        finally:
            self.control_state_changed.emit(False, "Port libéré")

        if answer_bytes:
            self.control_bytes_received.emit(answer_bytes)
        return answer_bytes.decode("utf-8", errors="replace").strip()

    def poll_control_once(self, callback: Callable[[bytes], None] | None = None) -> bytes:
        """Lit une trame complémentaire émise spontanément par l'Arduino.

        Cette méthode pourra être appelée par un QTimer lorsque le format des
        mesures Arduino sera connu.
        """
        if not self.control.port:
            return b""
        try:
            with serial.Serial(
                self.control.port,
                self.control.baudrate,
                timeout=0.05,
            ) as connection:
                payload = connection.read(max(1, connection.in_waiting))
        except (OSError, serial.SerialException):
            return b""
        if payload:
            self.control_bytes_received.emit(payload)
            if callback:
                callback(payload)
        return payload

    def close_all(self) -> None:
        self.close_measurement()
        if self._control_serial:
            self._control_serial.close()
            self._control_serial = None
