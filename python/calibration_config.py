from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class SensorCalibration:
    index: int
    name: str
    unit: str
    coefficients: list[float] = field(default_factory=lambda: [1.0, 0.0, 1.0, 0.0])
    enabled: bool = True


@dataclass
class SP55Calibration:
    version: str = "SP55 Version 3.0"
    product_name: str = "SP55"
    serial_port_number: int = 1
    password: str = "SP55"
    declared_sensor_count: int = 11
    sensors: list[SensorCalibration] = field(default_factory=list)


DEFAULT_SENSORS = [
    SensorCalibration(0, "Temps", "(s)", [1.99999995529652e-2, 0.0, 1.0, 0.0], True),
    SensorCalibration(1, "Angle motoréducteur", "(degres)", [1.0, 0.0, -5.23599982261658e-1, 2.02633190917969e3], True),
    SensorCalibration(2, "Effort corde", "(N)", [1.0, 0.0, -1.95301666855812e-1, 4.01262512207031e2], True),
    SensorCalibration(3, "Ecrasement ressort", "(mm)", [1.0, 0.0, 7.45379971340299e-3, -1.53289051055908e1], True),
    SensorCalibration(4, "Courant moteur", "(A)", [1.0, 0.0, -1.00000001490116e-1, 3.06800018310547e2], True),
    SensorCalibration(5, "Tension moteur", "(V)", [1.0, 0.0, 1.09999999403953e-2, -2.25282192230225e1], True),
    SensorCalibration(6, "Vitesse réducteur", "(tr/min)", [1.0, 0.0, 1.0, 0.0], True),
    SensorCalibration(7, "Vitesse moteur", "(tr/min)", [1.0, 0.0, 1.0, 0.0], True),
    SensorCalibration(8, "Angle moteur", "(°)", [1.0, 0.0, 1.0, 0.0], True),
    SensorCalibration(9, "Effort ressort", "(N)", [1.0, 0.0, 1.0, 0.0], True),
    SensorCalibration(10, "Vitesse chariot", "(mm/s)", [1.0, 0.0, 1.0, 0.0], True),
    SensorCalibration(11, "Translation chariot", "(mm)", [1.0, 0.0, 1.0, 0.0], True),
]


def default_calibration() -> SP55Calibration:
    return SP55Calibration(
        sensors=[
            SensorCalibration(s.index, s.name, s.unit, list(s.coefficients), s.enabled)
            for s in DEFAULT_SENSORS
        ]
    )


def read_calibration(path: str | Path) -> SP55Calibration:
    file_path = Path(path)
    text = file_path.read_bytes().decode("cp1252")
    lines = [line.rstrip("\r") for line in text.split("\n")]
    if not lines or not lines[0].startswith("SP55 Version"):
        raise ValueError("Le fichier ne ressemble pas à une configuration SP55.")

    config = SP55Calibration(version=lines[0].strip())
    config.product_name = lines[1].strip() if len(lines) > 1 else "SP55"

    def value_after(section: str, offset: int = 1) -> str:
        try:
            index = lines.index(section)
        except ValueError as exc:
            raise ValueError(f"Section absente : {section}") from exc
        if index + offset >= len(lines):
            raise ValueError(f"Valeur absente après {section}")
        return lines[index + offset].strip()

    port_line = value_after("[Communication port RS 232]")
    match = re.match(r"([+-]?\d+)", port_line)
    config.serial_port_number = int(match.group(1)) if match else 1
    config.password = value_after("[Mot de passe]")
    config.declared_sensor_count = int(value_after("[Capteurs]"))

    sensors: list[SensorCalibration] = []
    section_pattern = re.compile(r"^\[Capteur (\d+)\]$")
    for index, line in enumerate(lines):
        match = section_pattern.match(line.strip())
        if not match:
            continue
        sensor_index = int(match.group(1))
        try:
            name = lines[index + 1].strip()
            unit = lines[index + 2].strip()
            coefficients = [float(lines[index + 3 + i].strip()) for i in range(4)]
            enabled = bool(int(lines[index + 7].strip()))
        except (IndexError, ValueError) as exc:
            raise ValueError(f"Bloc Capteur {sensor_index} invalide.") from exc
        sensors.append(SensorCalibration(sensor_index, name, unit, coefficients, enabled))

    if not sensors:
        raise ValueError("Aucun capteur n'a été trouvé dans la configuration.")
    config.sensors = sensors
    return config


def _format_float(value: float) -> str:
    return f"{value: .14E}"


def write_calibration(path: str | Path, config: SP55Calibration) -> Path:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        config.version,
        config.product_name,
        "[Communication port RS 232]",
        f"{config.serial_port_number}         n° du port série",
        "",
        "[Mot de passe]",
        config.password,
        "",
        "[Capteurs]",
        str(config.declared_sensor_count),
        "",
    ]
    for sensor in sorted(config.sensors, key=lambda item: item.index):
        lines.extend([
            f"[Capteur {sensor.index}]",
            sensor.name,
            sensor.unit,
            *[_format_float(value) for value in sensor.coefficients],
            "1" if sensor.enabled else "0",
        ])
    lines.append("")
    file_path.write_bytes("\r\n".join(lines).encode("cp1252"))
    return file_path


def load_or_create_calibration(path: str | Path) -> tuple[SP55Calibration, bool]:
    file_path = Path(path)
    if file_path.exists():
        return read_calibration(file_path), False
    config = default_calibration()
    write_calibration(file_path, config)
    return config, True
