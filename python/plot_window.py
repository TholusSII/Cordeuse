from __future__ import annotations

from itertools import cycle

import pyqtgraph as pg
from PySide6.QtWidgets import QMainWindow

from mes_reader import MesStudy


PARAMETER_LABELS = {
    "Fc": ("Effort corde", "N"),
    "U": ("Tension moteur", "V"),
    "I": ("Courant moteur", "A"),
    "Er": ("Écrasement ressort", "mm"),
    "theta_red": ("Angle réducteur", "°"),
    "t": ("Temps", "s"),
    "Fr": ("Effort ressort", "N"),
    "Dch": ("Déplacement chariot", "mm"),
    "Vch": ("Vitesse chariot", "mm/s"),
    "theta_m": ("Angle moteur", "°"),
    "omega_m": ("Vitesse moteur", "tr/min"),
    "omega_red": ("Vitesse réducteur", "tr/min"),
}


class PlotWindow(QMainWindow):
    def __init__(
        self,
        study: MesStudy,
        abscissa_key: str,
        ordinate_keys: list[str],
        measurement_numbers: list[int],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Gestion des courbes — {study.path.name}")
        self.resize(1000, 680)

        pg.setConfigOptions(antialias=True)
        plot = pg.PlotWidget(background="w")
        self.setCentralWidget(plot)
        plot.showGrid(x=True, y=True, alpha=0.28)
        plot.addLegend(offset=(10, 10))

        x_label, x_unit = PARAMETER_LABELS[abscissa_key]
        plot.setLabel("bottom", x_label, units=x_unit or None)
        plot.setLabel("left", "Grandeurs sélectionnées")
        plot.setTitle(f"{study.path.name} — {study.count} mesure(s)")

        palette = cycle(
            [
                (160, 32, 240),
                (220, 40, 40),
                (20, 120, 210),
                (20, 150, 70),
                (230, 130, 20),
                (50, 50, 50),
                (190, 30, 130),
                (40, 170, 170),
            ]
        )

        for measurement_number in measurement_numbers:
            x = study.values(measurement_number, abscissa_key)
            for ordinate_key in ordinate_keys:
                y = study.values(measurement_number, ordinate_key)
                label, unit = PARAMETER_LABELS[ordinate_key]
                name = f"{label} — mesure n°{measurement_number}"
                if unit:
                    name += f" ({unit})"
                plot.plot(x, y, pen=pg.mkPen(next(palette), width=2), name=name)

        plot.enableAutoRange()
