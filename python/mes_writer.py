from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from mes_reader import COLUMN_KEYS


COLUMN_HEADER = (
    "IAngle motor  IString force  ISpring compression  IMotor current  "
    "IMotor voltage  IGearbox speed  IMotor speed  IMotor angle  "
    "ISpring force  ICarriage speed  ICarriage displacement"
)


def write_mes(
    path: str | Path,
    measurements: Sequence[Mapping[str, np.ndarray]],
    version: str = "SP55 Version 3.0",
) -> Path:
    """Écrit des mesures dans un fichier compatible avec ``read_mes``.

    Le temps n'est pas écrit dans le format historique. Chaque bloc contient
    les onze colonnes définies par ``COLUMN_KEYS``.
    """
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    lines = [version, "", f"{len(measurements)} mesure(s)", ""]
    for measurement in measurements:
        arrays = [np.asarray(measurement[key], dtype=float) for key in COLUMN_KEYS]
        if not arrays:
            raise ValueError("Aucune grandeur à enregistrer")
        sample_count = len(arrays[0])
        if sample_count == 0:
            raise ValueError("La mesure ne contient aucun échantillon")
        if any(len(values) != sample_count for values in arrays):
            raise ValueError("Toutes les grandeurs doivent avoir le même nombre de points")

        lines.append(COLUMN_HEADER)
        matrix = np.column_stack(arrays)
        for row in matrix:
            lines.append(" ".join(f"{value:.8e}" for value in row))
        lines.append("")

    output.write_text("\r\n".join(lines), encoding="cp1252")
    return output
