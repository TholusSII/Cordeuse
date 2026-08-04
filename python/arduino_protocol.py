from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArduinoFrame:
    kind: str
    fields: dict[str, str]
    raw: str

    def number(self, name: str, default: float = 0.0) -> float:
        try:
            return float(self.fields.get(name, default))
        except (TypeError, ValueError):
            return float(default)


def parse_arduino_line(line: str) -> ArduinoFrame:
    """Décode une trame ASCII `TYPE;cle=valeur;...` émise par le Mega."""
    raw = line.strip()
    if not raw:
        return ArduinoFrame("EMPTY", {}, raw)
    parts = raw.split(";")
    kind = parts[0].upper()
    fields: dict[str, str] = {}
    unnamed = 0
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key.strip().lower()] = value.strip()
        elif part:
            fields[f"value{unnamed}"] = part.strip()
            unnamed += 1
    return ArduinoFrame(kind, fields, raw)


def encode_line(command: str) -> bytes:
    return (command.rstrip("\r\n") + "\n").encode("ascii", errors="strict")


def set_values_command(
    *,
    setpoint: float | None = None,
    pwm: int | None = None,
    effort_scale: float | None = None,
    current_scale: float | None = None,
    position_scale: float | None = None,
    corde_scale: float | None = None,
) -> bytes:
    values: list[str] = []
    if setpoint is not None:
        values.append(f"SETPOINT={setpoint:.6g}")
    if pwm is not None:
        values.append(f"PWM={max(0, min(255, int(pwm)))}")
    if effort_scale is not None:
        values.append(f"EFFORT_SCALE={effort_scale:.9g}")
    if current_scale is not None:
        values.append(f"CURRENT_SCALE={current_scale:.9g}")
    if position_scale is not None:
        values.append(f"POSITION_SCALE={position_scale:.9g}")
    if corde_scale is not None:
        values.append(f"CORDE_SCALE={corde_scale:.9g}")
    return encode_line("SET;" + ";".join(values))


def stream_command(enabled: bool, period_ms: int = 50) -> bytes:
    period = max(20, min(2000, int(period_ms)))
    return encode_line(f"STREAM;ON={1 if enabled else 0};PERIOD={period}")
