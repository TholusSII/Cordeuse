from __future__ import annotations

from dataclasses import dataclass
from itertools import cycle

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

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


@dataclass
class CurveData:
    name: str
    unit: str
    x: np.ndarray
    y: np.ndarray
    color: tuple[int, int, int]
    marker_a: pg.ScatterPlotItem
    marker_b: pg.ScatterPlotItem


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
        self.resize(1050, 720)

        pg.setConfigOptions(antialias=True)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)
        self.setCentralWidget(central)

        self.plot = pg.PlotWidget(background="w")
        layout.addWidget(self.plot, 1)

        self.values_label = QLabel()
        self.values_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.values_label.setWordWrap(True)
        self.values_label.setMinimumHeight(72)
        self.values_label.setStyleSheet(
            "QLabel { background: white; border: 1px solid #808080; "
            "padding: 6px; font-family: Consolas, 'Courier New', monospace; }"
        )
        layout.addWidget(self.values_label)

        self.plot.showGrid(x=True, y=True, alpha=0.28)
        self.plot.addLegend(offset=(10, 10))

        self.x_label, self.x_unit = PARAMETER_LABELS[abscissa_key]
        self.plot.setLabel("bottom", self.x_label, units=self.x_unit or None)
        self.plot.setLabel("left", "Grandeurs sélectionnées")
        self.plot.setTitle(f"{study.path.name} — {study.count} mesure(s)")

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

        self.curves: list[CurveData] = []
        all_x: list[np.ndarray] = []

        for measurement_number in measurement_numbers:
            x = np.asarray(study.values(measurement_number, abscissa_key), dtype=float)
            all_x.append(x)

            for ordinate_key in ordinate_keys:
                y = np.asarray(study.values(measurement_number, ordinate_key), dtype=float)
                label, unit = PARAMETER_LABELS[ordinate_key]
                name = f"{label} — mesure n°{measurement_number}"
                legend_name = f"{name} ({unit})" if unit else name
                color = next(palette)

                self.plot.plot(
                    x,
                    y,
                    pen=pg.mkPen(color, width=2),
                    name=legend_name,
                )

                marker_a = pg.ScatterPlotItem(
                    size=10,
                    pen=pg.mkPen(color, width=2),
                    brush=pg.mkBrush(255, 255, 255),
                    symbol="o",
                )
                marker_b = pg.ScatterPlotItem(
                    size=10,
                    pen=pg.mkPen(color, width=2),
                    brush=pg.mkBrush(color),
                    symbol="s",
                )
                self.plot.addItem(marker_a)
                self.plot.addItem(marker_b)

                self.curves.append(
                    CurveData(
                        name=name,
                        unit=unit,
                        x=x,
                        y=y,
                        color=color,
                        marker_a=marker_a,
                        marker_b=marker_b,
                    )
                )

        if not all_x:
            raise ValueError("Aucune donnée à tracer.")

        finite_x = np.concatenate([x[np.isfinite(x)] for x in all_x if x.size])
        if finite_x.size == 0:
            raise ValueError("Les données d'abscisse ne contiennent aucune valeur valide.")

        xmin = float(np.min(finite_x))
        xmax = float(np.max(finite_x))
        span = xmax - xmin

        self.cursor_a = pg.InfiniteLine(
            pos=xmin + span / 3 if span else xmin,
            angle=90,
            movable=True,
            pen=pg.mkPen((20, 90, 210), width=2),
            hoverPen=pg.mkPen((20, 90, 210), width=3),
            label="A",
            labelOpts={"position": 0.94},
        )
        self.cursor_b = pg.InfiniteLine(
            pos=xmin + 2 * span / 3 if span else xmin,
            angle=90,
            movable=True,
            pen=pg.mkPen((210, 70, 30), width=2),
            hoverPen=pg.mkPen((210, 70, 30), width=3),
            label="B",
            labelOpts={"position": 0.88},
        )

        self.plot.addItem(self.cursor_a, ignoreBounds=True)
        self.plot.addItem(self.cursor_b, ignoreBounds=True)
        self.cursor_a.setBounds((xmin, xmax))
        self.cursor_b.setBounds((xmin, xmax))

        self.cursor_a.sigPositionChanged.connect(self._update_cursor_values)
        self.cursor_b.sigPositionChanged.connect(self._update_cursor_values)

        self.plot.scene().sigMouseClicked.connect(self._mouse_clicked)
        self.plot.enableAutoRange()
        self._update_cursor_values()

    def _mouse_clicked(self, event) -> None:
        """Un clic place A ; Maj+clic place B."""
        if event.button() != Qt.LeftButton:
            return
        if not self.plot.sceneBoundingRect().contains(event.scenePos()):
            return

        mouse_point = self.plot.plotItem.vb.mapSceneToView(event.scenePos())
        if event.modifiers() & Qt.ShiftModifier:
            self.cursor_b.setValue(mouse_point.x())
        else:
            self.cursor_a.setValue(mouse_point.x())

    @staticmethod
    def _nearest_index(x: np.ndarray, position: float) -> int:
        valid = np.isfinite(x)
        if not np.any(valid):
            return 0
        valid_indices = np.flatnonzero(valid)
        local_index = int(np.argmin(np.abs(x[valid] - position)))
        return int(valid_indices[local_index])

    @staticmethod
    def _format_value(value: float) -> str:
        if not np.isfinite(value):
            return "—"
        absolute = abs(value)
        if absolute != 0 and (absolute >= 10000 or absolute < 0.001):
            return f"{value:.4e}"
        return f"{value:.4f}"

    def _sample_curve(self, curve: CurveData, cursor_position: float) -> tuple[float, float]:
        index = self._nearest_index(curve.x, cursor_position)
        return float(curve.x[index]), float(curve.y[index])

    def _update_cursor_values(self) -> None:
        pos_a = float(self.cursor_a.value())
        pos_b = float(self.cursor_b.value())

        rows = [
            "<b>Curseurs :</b> clic = placer A ; Maj+clic = placer B ; "
            "les deux lignes peuvent aussi être glissées.",
            "<table cellspacing='4' cellpadding='2'>",
            "<tr><th align='left'>Courbe</th>"
            "<th align='right'>A</th><th align='right'>B</th>"
            "<th align='right'>Δ(B−A)</th></tr>",
        ]

        displayed_x_a = pos_a
        displayed_x_b = pos_b

        for curve in self.curves:
            x_a, y_a = self._sample_curve(curve, pos_a)
            x_b, y_b = self._sample_curve(curve, pos_b)
            displayed_x_a = x_a
            displayed_x_b = x_b

            curve.marker_a.setData([x_a], [y_a])
            curve.marker_b.setData([x_b], [y_b])

            suffix = f" {curve.unit}" if curve.unit else ""
            rows.append(
                "<tr>"
                f"<td>{curve.name}</td>"
                f"<td align='right'>{self._format_value(y_a)}{suffix}</td>"
                f"<td align='right'>{self._format_value(y_b)}{suffix}</td>"
                f"<td align='right'>{self._format_value(y_b - y_a)}{suffix}</td>"
                "</tr>"
            )

        rows.append("</table>")
        x_suffix = f" {self.x_unit}" if self.x_unit else ""
        rows.insert(
            1,
            f"<b>{self.x_label}</b> : "
            f"A = {self._format_value(displayed_x_a)}{x_suffix} — "
            f"B = {self._format_value(displayed_x_b)}{x_suffix} — "
            f"Δx = {self._format_value(displayed_x_b - displayed_x_a)}{x_suffix}",
        )
        self.values_label.setText("<br>".join(rows))
