from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QDockWidget, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from formula_engine import evaluate_formula, validate_formula
from mes_reader import MesStudy, read_mes
from plot_window import PARAMETER_LABELS, PlotWindow
from ui_choix_parametres import ChoiceWindow, PARAMETERS


@dataclass
class FormulaCurve:
    expression: str
    label: str
    unit: str


class FormulaStudyProxy:
    """Ajoute des grandeurs calculées sans modifier les données MES originales."""

    def __init__(self, study: MesStudy, formulas: dict[str, FormulaCurve]) -> None:
        self._study = study
        self._formulas = formulas
        self.path = study.path
        self.count = study.count
        self.measurements = study.measurements

    def values(self, measurement_number: int, key: str):
        if key not in self._formulas:
            return self._study.values(measurement_number, key)
        formula = self._formulas[key]
        values = {
            name: np.asarray(self._study.values(measurement_number, name), dtype=float)
            for name in PARAMETERS
            if name != "formula"
        }
        return evaluate_formula(formula.expression, values)


class FormulaDock(QDockWidget):
    def __init__(self, parent: "SP55ApplicationWindow") -> None:
        super().__init__("Éditeur de formule", parent)
        self.owner = parent
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)

        hint = QLabel(
            "Cliquez sur les grandeurs du schéma et sur les opérateurs pour construire la formule."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#667085")
        layout.addWidget(hint)

        self.expression = QLineEdit()
        self.expression.setPlaceholderText("Exemple : U*I")
        self.expression.setStyleSheet(
            "QLineEdit{background:white;border:1px solid #9bbcf2;border-radius:8px;"
            "padding:10px;font:600 14px Consolas}"
        )
        layout.addWidget(self.expression)

        operators = QGridLayout()
        for index, token in enumerate(["+", "-", "*", "/", "(", ")", "**2", "⌫"]):
            button = QPushButton(token)
            button.setFixedHeight(38)
            if token == "⌫":
                button.clicked.connect(self.expression.backspace)
            else:
                button.clicked.connect(
                    lambda _checked=False, value=token: self.append_token(value)
                )
            operators.addWidget(button, index // 4, index % 4)
        layout.addLayout(operators)

        layout.addWidget(QLabel("Nom de la courbe"))
        self.label = QLineEdit("Formule")
        self.label.setPlaceholderText("Exemple : Puissance")
        layout.addWidget(self.label)

        layout.addWidget(QLabel("Unité"))
        self.unit = QLineEdit()
        self.unit.setPlaceholderText("Exemple : W")
        layout.addWidget(self.unit)

        actions = QHBoxLayout()
        clear = QPushButton("Effacer")
        clear.clicked.connect(self.clear)
        add = QPushButton("Ajouter au tracé")
        add.setStyleSheet(
            "QPushButton{background:#2563eb;color:white;border:none;border-radius:8px;"
            "padding:9px 12px;font-weight:600}QPushButton:hover{background:#1d4ed8}"
        )
        add.clicked.connect(self.validate_and_add)
        actions.addWidget(clear)
        actions.addWidget(add)
        layout.addLayout(actions)
        layout.addStretch()

        self.setWidget(root)
        self.setMinimumWidth(310)

    def append_token(self, token: str) -> None:
        self.expression.insert(token)
        self.expression.setFocus()

    def clear(self) -> None:
        self.expression.clear()
        self.label.setText("Formule")
        self.unit.clear()

    def validate_and_add(self) -> None:
        expression = self.expression.text().strip()
        try:
            validate_formula(expression)
        except ValueError as exc:
            QMessageBox.warning(self, "Formule invalide", str(exc))
            return
        self.owner.add_formula(
            expression,
            self.label.text().strip() or expression,
            self.unit.text().strip(),
        )


class SP55ApplicationWindow(ChoiceWindow):
    def __init__(self) -> None:
        super().__init__()
        self.study: MesStudy | None = None
        self.plot_windows: list[PlotWindow] = []
        self.formulas: dict[str, FormulaCurve] = {}
        self.formula_mode = False
        self.formula_dock = FormulaDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.formula_dock)
        self.formula_dock.hide()
        self.status.setText(
            "Sélectionnez les grandeurs et mesures, puis cliquez sur Tracer."
        )

    def parameter_clicked(self, key: str) -> None:
        if key == "formula":
            self.formula_mode = True
            self.formula_dock.show()
            self.formula_dock.raise_()
            self.formula_dock.expression.setFocus()
            self.status.setText(
                "Mode formule : cliquez sur les grandeurs puis sur +, −, *, / dans le panneau de droite."
            )
            return
        if self.formula_mode and self.formula_dock.isVisible():
            token = PARAMETERS[key].code
            aliases = {
                "θred": "theta_red", "θm": "theta_m",
                "Ωm": "omega_m", "Ωred": "omega_red",
            }
            self.formula_dock.append_token(aliases.get(token, token))
            self.status.setText(f"Grandeur ajoutée à la formule : {PARAMETERS[key].label}")
            return
        super().parameter_clicked(key)

    def add_formula(self, expression: str, label: str, unit: str) -> None:
        key = f"formula_{len(self.formulas) + 1}"
        self.formulas[key] = FormulaCurve(expression, label, unit)
        PARAMETER_LABELS[key] = (f"{label} [{expression}]", unit)
        if key not in self.ordinate_keys:
            self.ordinate_keys.append(key)
        self.formula_mode = False
        self._refresh()
        self.status.setText(
            f"Formule ajoutée : {label} = {expression}. Elle sera tracée comme une courbe."
        )

    def parameter_text(self, key: str) -> str:
        if key in self.formulas:
            formula = self.formulas[key]
            suffix = f" ({formula.unit})" if formula.unit else ""
            return f"{formula.label} = {formula.expression}{suffix}"
        return super().parameter_text(key)

    def choose_mes_file(self) -> bool:
        initial_dir = str(Path.cwd())
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir un fichier de mesures SP55",
            initial_dir,
            "Mesures SP55 (*.mes);;Tous les fichiers (*.*)",
        )
        if not file_name:
            return False
        try:
            self.study = read_mes(file_name)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Lecture impossible", str(exc))
            return False

        for index, check in enumerate(self.measure_checks, start=1):
            check.setEnabled(index <= self.study.count)
            if index > self.study.count:
                check.setChecked(False)
        self.status.setText(
            f"Fichier chargé : {Path(file_name).name} — {self.study.count} mesure(s), "
            f"{len(self.study.measurements[0]['t'])} points par mesure."
        )
        return True

    def trace(self) -> None:
        if self.study is None and not self.choose_mes_file():
            return
        assert self.study is not None

        selected_measurements = [
            index + 1
            for index, check in enumerate(self.measure_checks)
            if check.isChecked() and index < self.study.count
        ]
        if not selected_measurements:
            QMessageBox.warning(self, "Tracer", "Sélectionnez au moins une mesure disponible.")
            return
        if not self.ordinate_keys:
            QMessageBox.warning(self, "Tracer", "Sélectionnez au moins une grandeur en ordonnée.")
            return
        if self.abscissa_key == "formula":
            QMessageBox.warning(self, "Abscisse", "Une formule ne peut pas encore être utilisée en abscisse.")
            return

        proxy = FormulaStudyProxy(self.study, self.formulas)
        try:
            window = PlotWindow(
                proxy,
                self.abscissa_key,
                list(self.ordinate_keys),
                selected_measurements,
                self,
            )
        except (KeyError, IndexError, ValueError, ZeroDivisionError) as exc:
            QMessageBox.critical(self, "Tracé impossible", str(exc))
            return

        window.show()
        self.plot_windows.append(window)
        self.status.setText(
            f"Courbes tracées depuis {self.study.path.name} : "
            f"mesures {', '.join(map(str, selected_measurements))}."
        )


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = SP55ApplicationWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
