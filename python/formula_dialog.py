from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QVBoxLayout,
)

from formula_engine import validate_formula


class FormulaDialog(QDialog):
    formula_validated = Signal(str, str, str)

    def __init__(self, parent=None, expression: str = "", label: str = "Formule", unit: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Éditeur de formule")
        self.setMinimumWidth(620)
        self.setStyleSheet(
            "QDialog{background:#f3f6fb} QLabel{font-family:'Segoe UI'}"
            "QLineEdit{background:white;border:1px solid #d8dee9;border-radius:8px;padding:9px;font:13px 'Consolas'}"
            "QPushButton{background:white;border:1px solid #d8dee9;border-radius:8px;padding:8px 12px;font:12px 'Segoe UI'}"
            "QPushButton:hover{background:#eef4ff;border-color:#9bbcf2}"
            "QPushButton#primary{background:#2563eb;color:white;border:none;font-weight:600}"
        )

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Construisez la formule en cliquant sur les grandeurs et les opérateurs."))

        self.expression_edit = QLineEdit(expression)
        self.expression_edit.setPlaceholderText("Exemple : U*I")
        layout.addWidget(self.expression_edit)

        variables = ["U", "I", "Fc", "Fr", "Er", "Dch", "Vch", "theta_m", "theta_red", "omega_m", "omega_red", "t"]
        grid = QGridLayout()
        for index, token in enumerate(variables):
            button = QPushButton(token)
            button.clicked.connect(lambda _=False, value=token: self._append(value))
            grid.addWidget(button, index // 6, index % 6)
        layout.addLayout(grid)

        operators = QHBoxLayout()
        for token in ["+", "-", "*", "/", "(", ")", "**2"]:
            button = QPushButton(token)
            button.clicked.connect(lambda _=False, value=token: self._append(value))
            operators.addWidget(button)
        clear_button = QPushButton("Effacer")
        clear_button.clicked.connect(self.expression_edit.clear)
        back_button = QPushButton("⌫")
        back_button.clicked.connect(self.expression_edit.backspace)
        operators.addWidget(back_button)
        operators.addWidget(clear_button)
        layout.addLayout(operators)

        meta = QHBoxLayout()
        meta.addWidget(QLabel("Nom de la courbe"))
        self.label_edit = QLineEdit(label)
        self.label_edit.setPlaceholderText("Ex. Puissance")
        meta.addWidget(self.label_edit, 2)
        meta.addWidget(QLabel("Unité"))
        self.unit_edit = QLineEdit(unit)
        self.unit_edit.setMaximumWidth(100)
        self.unit_edit.setPlaceholderText("W")
        meta.addWidget(self.unit_edit)
        layout.addLayout(meta)

        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("Annuler")
        cancel.clicked.connect(self.reject)
        validate = QPushButton("Ajouter la formule")
        validate.setObjectName("primary")
        validate.clicked.connect(self._validate)
        actions.addWidget(cancel)
        actions.addWidget(validate)
        layout.addLayout(actions)

    def _append(self, token: str) -> None:
        self.expression_edit.insert(token)
        self.expression_edit.setFocus()

    def _validate(self) -> None:
        expression = self.expression_edit.text().strip()
        try:
            validate_formula(expression)
        except ValueError as exc:
            QMessageBox.warning(self, "Formule invalide", str(exc))
            return
        label = self.label_edit.text().strip() or expression
        unit = self.unit_edit.text().strip()
        self.formula_validated.emit(expression, label, unit)
        self.accept()
