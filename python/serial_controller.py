from __future__ import annotations

from dataclasses import dataclass

import serial
from serial.tools import list_ports


@dataclass(frozen=True)
class CommandSettings:
    """Commande à transmettre à la carte de pilotage."""

    mode: str
    kp: float = 0.0
    ki: float = 0.0
    kd: float = 0.0

    def encode(self) -> bytes:
        """Encode une commande ASCII terminée par un retour à la ligne."""
        mode = self.mode.upper().strip()
        if mode not in {"BO", "BF", "CONSTRUCTEUR"}:
            raise ValueError(f"Mode de commande inconnu : {self.mode}")
        payload = (
            f"CMD;MODE={mode};KP={self.kp:.4f};"
            f"KI={self.ki:.4f};KD={self.kd:.4f}\n"
        )
        return payload.encode("ascii")


def available_ports() -> list[tuple[str, str]]:
    """Retourne les ports série présents sous la forme (nom, description)."""
    ports = []
    for port in sorted(list_ports.comports(), key=lambda item: item.device):
        description = port.description or "Port série"
        ports.append((port.device, description))
    return ports


def send_command(
    port: str,
    baudrate: int,
    settings: CommandSettings,
    timeout: float = 1.0,
) -> str:
    """Envoie la commande et retourne l'éventuel accusé de réception."""
    if not port:
        raise ValueError("Aucun port série n'a été sélectionné.")

    payload = settings.encode()
    with serial.Serial(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        write_timeout=timeout,
    ) as connection:
        connection.reset_input_buffer()
        connection.write(payload)
        connection.flush()
        answer = connection.readline().decode("utf-8", errors="replace").strip()

    return answer
