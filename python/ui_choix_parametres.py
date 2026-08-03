from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum, auto

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QMainWindow, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from command_window import CommandModeDialog
from machine_diagram import MachineDiagram


class SelectionMode(Enum):
    NONE = auto()
    ABSCISSA = auto()
    ORDINATE = auto()


@dataclass(frozen=True)
class Parameter:
    code: str
    label: str
    unit: str
    color: str
    symbol: str


PARAMETERS = {
    "Fc": Parameter("Fc", "Effort corde", "N", "#ef4444", "↔"),
    "U": Parameter("U", "Tension moteur", "V", "#2563eb", "ϟ"),
    "I": Parameter("I", "Courant moteur", "A", "#eab308", "→"),
    "Er": Parameter("Er", "Écrasement ressort", "mm", "#16a34a", "≋"),
    "theta_red": Parameter("θred", "Angle réducteur", "°", "#14b8a6", "↻"),
    "t": Parameter("t", "Temps", "s", "#7c3aed", "◷"),
    "formula": Parameter("Y=f", "Formule", "", "#64748b", "ƒ"),
    "Fr": Parameter("Fr", "Effort ressort", "N", "#22c55e", "≋"),
    "Dch": Parameter("Dch", "Déplacement chariot", "mm", "#0ea5e9", "↔"),
    "Vch": Parameter("Vch", "Vitesse chariot", "mm/s", "#0891b2", "»"),
    "theta_m": Parameter("θm", "Angle moteur", "°", "#8b5cf6", "↻"),
    "omega_m": Parameter("Ωm", "Vitesse moteur", "tr/min", "#f97316", "Ω"),
    "omega_red": Parameter("Ωred", "Vitesse réducteur", "tr/min", "#ec4899", "Ω"),
}

STYLE = """
QMainWindow,QWidget#root{background:#f3f6fb;color:#172033}
QFrame#card{background:white;border:1px solid #dfe6ef;border-radius:14px}
QLabel#title{font:700 24px 'Segoe UI';color:#172033}
QLabel#subtitle{font:12px 'Segoe UI';color:#667085}
QLabel#section{font:600 13px 'Segoe UI';color:#344054}
QLabel#status{background:#edf4ff;border:1px solid #d7e6ff;border-radius:10px;padding:9px 12px;color:#2457a7}
QPushButton{background:white;border:1px solid #d8dee9;border-radius:9px;padding:8px 12px;font:12px 'Segoe UI';color:#24324a}
QPushButton:hover{background:#f6f9ff;border-color:#9bbcf2}
QPushButton#primary{background:#2563eb;color:white;border:none;font-weight:600}
QPushButton#danger{color:#b42318;background:#fff7f6;border-color:#f2c9c5}
QPushButton#modeActive{background:#eaf2ff;color:#1558d6;border-color:#8fb5ef;font-weight:600}
QTableWidget{background:white;border:1px solid #e0e6ef;border-radius:9px;gridline-color:#eef1f5;selection-background-color:#dce9ff;selection-color:#173b75}
QHeaderView::section{background:#f8fafc;border:0;border-bottom:1px solid #e5eaf1;padding:7px;font-weight:600}
QCheckBox{spacing:8px;font:12px 'Segoe UI'}
"""


class ModernButton(QPushButton):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)


class ChoiceWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.mode = SelectionMode.NONE
        self.abscissa_key = "t"
        self.ordinate_keys = ["Fr", "Er", "Fc"]
        self.command_dialog: CommandModeDialog | None = None
        self.setWindowTitle("Cordeuse de raquettes SP55 — Modern UI")

        screen = QGuiApplication.primaryScreen()
        geometry = screen.availableGeometry() if screen else None
        if geometry:
            self.resize(
                min(int(geometry.width() * 0.97), 1800),
                min(int(geometry.height() * 0.94), 1050),
            )
        else:
            self.resize(1600, 920)
        self.setMinimumSize(1380, 820)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._refresh()

    @staticmethod
    def _card() -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        return frame

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(14)

        side = self._card()
        side.setFixedWidth(96)
        side_layout = QVBoxLayout(side)
        brand = QLabel("SP55")
        brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet("font:700 19px 'Segoe UI';color:#1558d6;padding:8px")
        side_layout.addWidget(brand)
        for symbol, tooltip in [
            ("＋", "Nouveau"), ("▣", "Ouvrir"), ("▤", "Sauver"),
            ("✕", "Effacer"), ("◉", "Mesures"), ("⌁", "Courbes"),
        ]:
            button = ModernButton(symbol)
            button.setToolTip(tooltip)
            button.setFixedHeight(50)
            button.setStyleSheet("font-size:20px")
            side_layout.addWidget(button)
        command_button = ModernButton("⟲")
        command_button.setToolTip("Mode de commande")
        command_button.setFixedHeight(50)
        command_button.setStyleSheet("font-size:24px;color:#1558d6;background:#eef4ff")
        command_button.clicked.connect(self.open_command_mode)
        side_layout.addWidget(command_button)
        side_layout.addStretch()
        side_layout.addWidget(ModernButton("⚙"))
        outer.addWidget(side)

        content = QVBoxLayout()
        content.setSpacing(12)
        outer.addLayout(content, 1)
        title = QLabel("Choix des paramètres")
        title.setObjectName("title")
        subtitle = QLabel("Disposition fidèle au logiciel SP55, avec un habillage Windows 11.")
        subtitle.setObjectName("subtitle")
        content.addWidget(title)
        content.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(14)
        content.addLayout(body, 1)

        machine_card = self._card()
        machine_layout = QVBoxLayout(machine_card)
        machine_layout.setContentsMargins(12, 12, 12, 12)
        self.diagram = MachineDiagram(PARAMETERS)
        self.diagram.parameter_selected.connect(self.parameter_clicked)
        machine_layout.addWidget(self.diagram)
        body.addWidget(machine_card, 7)

        right = QVBoxLayout()
        right.setSpacing(14)
        body.addLayout(right, 4)

        selection_card = self._card()
        selection_layout = QVBoxLayout(selection_card)
        section = QLabel("Paramètres d’affichage")
        section.setObjectName("section")
        selection_layout.addWidget(section)
        modes = QHBoxLayout()
        self.abscissa_button = ModernButton("→ Abscisse")
        self.ordinate_button = ModernButton("↑ Ordonnée")
        self.abscissa_button.clicked.connect(lambda: self.set_mode(SelectionMode.ABSCISSA))
        self.ordinate_button.clicked.connect(lambda: self.set_mode(SelectionMode.ORDINATE))
        modes.addWidget(self.abscissa_button)
        modes.addWidget(self.ordinate_button)
        selection_layout.addLayout(modes)
        self.abscissa_label = QLabel()
        self.abscissa_label.setStyleSheet(
            "background:#f8fafc;border:1px solid #e1e7ef;border-radius:8px;"
            "padding:9px;font-weight:600"
        )
        selection_layout.addWidget(self.abscissa_label)
        row = QHBoxLayout()
        row.addWidget(QLabel("Ordonnées sélectionnées"))
        row.addStretch()
        self.delete_button = ModernButton("Supprimer")
        self.delete_button.setObjectName("danger")
        self.delete_button.clicked.connect(self.remove_ordinate)
        row.addWidget(self.delete_button)
        selection_layout.addLayout(row)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["N°", "Paramètre"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        selection_layout.addWidget(self.table, 1)
        actions = QHBoxLayout()
        self.trace_button = ModernButton("Tracer les courbes")
        self.trace_button.setObjectName("primary")
        self.trace_button.clicked.connect(self.trace)
        actions.addWidget(self.trace_button, 2)
        actions.addWidget(ModernButton("Éditer"), 1)
        selection_layout.addLayout(actions)
        right.addWidget(selection_card, 3)

        measures_card = self._card()
        measures_layout = QVBoxLayout(measures_card)
        measures_title = QLabel("Mesures")
        measures_title.setObjectName("section")
        measures_layout.addWidget(measures_title)
        grid = QGridLayout()
        self.measure_checks: list[QCheckBox] = []
        for index in range(1, 11):
            check = QCheckBox(f"Mesure n°{index}")
            check.setChecked(index == 1)
            check.stateChanged.connect(self._refresh_trace_state)
            self.measure_checks.append(check)
            grid.addWidget(check, (index - 1) // 5, (index - 1) % 5)
        measures_layout.addLayout(grid)
        buttons = QHBoxLayout()
        clear = ModernButton("Tout désélectionner")
        clear.clicked.connect(self.clear_measures)
        reset = ModernButton("Réinitialiser")
        reset.clicked.connect(self.restore_default)
        buttons.addWidget(clear)
        buttons.addWidget(reset)
        measures_layout.addLayout(buttons)
        right.addWidget(measures_card, 1)

        footer = QHBoxLayout()
        self.status = QLabel("Cliquez sur Abscisse ou Ordonnée puis sur une grandeur.")
        self.status.setObjectName("status")
        footer.addWidget(self.status, 1)
        help_button = ModernButton("Aide")
        help_button.clicked.connect(self.show_help)
        close_button = ModernButton("Fermer")
        close_button.clicked.connect(self.close)
        footer.addWidget(help_button)
        footer.addWidget(close_button)
        content.addLayout(footer)

    def open_command_mode(self) -> None:
        self.command_dialog = CommandModeDialog(self)
        self.command_dialog.exec()

    def set_mode(self, mode: SelectionMode) -> None:
        self.mode = mode
        for button, active in (
            (self.abscissa_button, mode is SelectionMode.ABSCISSA),
            (self.ordinate_button, mode is SelectionMode.ORDINATE),
        ):
            button.setObjectName("modeActive" if active else "")
            button.style().unpolish(button)
            button.style().polish(button)
        if mode is SelectionMode.ABSCISSA:
            self.status.setText("Sélection de l'abscisse : cliquez sur une grandeur du schéma.")
        elif mode is SelectionMode.ORDINATE:
            self.status.setText("Sélection des ordonnées : cliquez sur une ou plusieurs grandeurs.")

    def parameter_clicked(self, key: str) -> None:
        if self.mode is SelectionMode.ABSCISSA:
            self.abscissa_key = key
            self.mode = SelectionMode.NONE
            self.status.setText(f"Abscisse sélectionnée : {self.parameter_text(key)}")
        elif self.mode is SelectionMode.ORDINATE:
            if key != self.abscissa_key and key not in self.ordinate_keys:
                self.ordinate_keys.append(key)
            self.status.setText(f"Ordonnée ajoutée : {self.parameter_text(key)}")
        else:
            self.status.setText(
                f"{PARAMETERS[key].label} — unité : {PARAMETERS[key].unit or 'sans unité'}"
            )
        self._refresh()

    @staticmethod
    def parameter_text(key: str) -> str:
        parameter = PARAMETERS[key]
        return f"{parameter.label} ({parameter.unit})" if parameter.unit else parameter.label

    def remove_ordinate(self) -> None:
        row = self.table.currentRow()
        if 0 <= row < len(self.ordinate_keys):
            self.ordinate_keys.pop(row)
            self._refresh()

    def clear_measures(self) -> None:
        for check in self.measure_checks:
            check.setChecked(False)

    def restore_default(self) -> None:
        self.abscissa_key = "t"
        self.ordinate_keys = ["Fr", "Er", "Fc"]
        for index, check in enumerate(self.measure_checks, 1):
            check.setChecked(index == 1)
        self._refresh()

    def show_help(self) -> None:
        QMessageBox.information(
            self,
            "Aide",
            "1. Choisissez l'abscisse.\n"
            "2. Ajoutez les ordonnées.\n"
            "3. Cochez les mesures.\n"
            "4. Cliquez sur Tracer.",
        )

    def trace(self) -> None:
        QMessageBox.information(self, "Tracer", "Sélection prête pour le tracé.")

    def _refresh_trace_state(self) -> None:
        self.trace_button.setEnabled(
            bool(self.ordinate_keys) and any(check.isChecked() for check in self.measure_checks)
        )

    def _refresh(self) -> None:
        self.abscissa_label.setText(self.parameter_text(self.abscissa_key))
        self.table.setRowCount(len(self.ordinate_keys))
        for row, key in enumerate(self.ordinate_keys):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(self.parameter_text(key)))
        if self.ordinate_keys:
            self.table.selectRow(0)
        self.delete_button.setEnabled(bool(self.ordinate_keys))
        self._refresh_trace_state()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = ChoiceWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
