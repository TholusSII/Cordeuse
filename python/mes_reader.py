from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


COLUMN_KEYS = (
    "theta_red",
    "Fc",
    "Er",
    "I",
    "U",
    "omega_red",
    "omega_m",
    "theta_m",
    "Fr",
    "Vch",
    "Dch",
)


@dataclass(frozen=True)
class MesStudy:
    path: Path
    version: str
    measurements: tuple[dict[str, np.ndarray], ...]

    @property
    def count(self) -> int:
        return len(self.measurements)

    def values(self, measurement_number: int, key: str) -> np.ndarray:
        if not 1 <= measurement_number <= self.count:
            raise IndexError(f"Mesure n°{measurement_number} indisponible")
        measurement = self.measurements[measurement_number - 1]
        if key == "t":
            return measurement["t"]
        try:
            return measurement[key]
        except KeyError as exc:
            raise KeyError(f"Grandeur inconnue : {key}") from exc


def read_mes(path: str | Path, acquisition_duration: float = 10.0) -> MesStudy:
    """Lit un fichier de mesures SP55 version 3.0.

    Le format contient un en-tête général, puis un bloc de 500 lignes par
    mesure. Chaque ligne comprend onze valeurs scientifiques. Le temps n'est
    pas enregistré : il est reconstruit sur la durée d'acquisition de 10 s.
    """
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="cp1252")
    except UnicodeDecodeError:
        text = file_path.read_text(encoding="latin-1")

    lines = text.splitlines()
    if len(lines) < 5 or not lines[0].startswith("SP55 Version"):
        raise ValueError("Ce fichier ne ressemble pas à un fichier SP55 .mes")

    version = lines[0].strip()
    try:
        declared_count = int(lines[2].split()[0])
    except (IndexError, ValueError) as exc:
        raise ValueError("Nombre de mesures illisible dans le fichier .mes") from exc

    header_indexes = [i for i, line in enumerate(lines) if line.startswith("IAngle motor")]
    if not header_indexes:
        raise ValueError("Aucun bloc de mesure trouvé")

    measurements: list[dict[str, np.ndarray]] = []
    for block_index, header_index in enumerate(header_indexes):
        end = header_indexes[block_index + 1] if block_index + 1 < len(header_indexes) else len(lines)
        rows: list[list[float]] = []
        for raw_line in lines[header_index + 1 : end]:
            if not raw_line.strip():
                continue
            try:
                values = [float(token) for token in raw_line.split()]
            except ValueError as exc:
                raise ValueError(f"Valeur numérique invalide vers la ligne {header_index + 2}") from exc
            if len(values) != len(COLUMN_KEYS):
                raise ValueError(
                    f"Bloc de mesure invalide : {len(values)} colonnes au lieu de {len(COLUMN_KEYS)}"
                )
            rows.append(values)

        if not rows:
            continue
        matrix = np.asarray(rows, dtype=float)
        sample_count = matrix.shape[0]
        time = np.arange(sample_count, dtype=float) * (acquisition_duration / sample_count)
        measurement = {key: matrix[:, column] for column, key in enumerate(COLUMN_KEYS)}
        measurement["t"] = time
        measurements.append(measurement)

    if declared_count != len(measurements):
        raise ValueError(
            f"Le fichier annonce {declared_count} mesure(s), mais {len(measurements)} bloc(s) ont été lus"
        )

    return MesStudy(file_path, version, tuple(measurements))
