from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum, auto

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QMainWindow, QMessageBox, QPushButton, QSizePolicy,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)


class SelectionMode(Enum):
    NONE = auto()
    ABSCISSA = auto()
    ORDINATE = auto()


@dataclass(frozen=True)
class Parameter:
    code: str
    label: str
    unit: str
    accent: str


PARAMETERS = {
    "Fc": Parameter("Fc", "Effort corde", "N", "#ef4444"),
    "U": Parameter("U", "Tension moteur", "V", "#2563eb"),
    "I": Parameter("I", "Courant moteur", "A", "#eab308"),
    "Er": Parameter("Er", "Écrasement ressort", "mm", "#16a34a"),
    "theta_red": Parameter("θred", "Angle réducteur", "°", "#14b8a6"),
    "t": Parameter("t", "Temps", "s", "#7c3aed"),
    "formula": Parameter("Y=f", "Formule", "", "#64748b"),
    "Fr": Parameter("Fr", "Effort ressort", "N", "#22c55e"),
    "Dch": Parameter("Dch", "Déplacement chariot", "mm", "#0ea5e9"),
    "Vch": Parameter("Vch", "Vitesse chariot", "mm/s", "#0891b2"),
    "theta_m": Parameter("θm", "Angle moteur", "°", "#8b5cf6"),
    "omega_m": Parameter("Ωm", "Vitesse moteur", "tr/min", "#f97316"),
    "omega_red": Parameter("Ωred", "Vitesse réducteur", "tr/min", "#ec4899"),
}


APP_STYLE = """
QMainWindow, QWidget#root { background:#f4f7fb; color:#172033; }
QMenuBar { background:#ffffff; border-bottom:1px solid #e4e9f2; padding:4px 8px; font:13px 'Segoe UI'; }
QMenuBar::item { padding:6px 10px; border-radius:6px; }
QMenuBar::item:selected { background:#eef4ff; color:#1558d6; }
QMenu { background:white; border:1px solid #dfe5ef; padding:6px; }
QMenu::item { padding:7px 28px 7px 10px; border-radius:5px; }
QMenu::item:selected { background:#eaf2ff; color:#1558d6; }
QFrame#card { background:#ffffff; border:1px solid #e0e6ef; border-radius:14px; }
QLabel#title { font:700 22px 'Segoe UI'; color:#15233d; }
QLabel#subtitle { font:12px 'Segoe UI'; color:#667085; }
QLabel#section { font:600 13px 'Segoe UI'; color:#344054; }
QLabel#status { background:#edf4ff; border:1px solid #d7e6ff; border-radius:10px; padding:8px 12px; color:#2457a7; font:12px 'Segoe UI'; }
QPushButton { background:#ffffff; border:1px solid #d8dee9; border-radius:9px; padding:8px 12px; font:12px 'Segoe UI'; color:#24324a; }
QPushButton:hover { background:#f6f9ff; border-color:#9bbcf2; }
QPushButton:pressed { background:#e8f0fd; }
QPushButton:disabled { color:#a0a8b8; background:#f5f6f8; border-color:#e5e7eb; }
QPushButton#primary { background:#2563eb; color:white; border:none; font-weight:600; }
QPushButton#primary:hover { background:#1d4ed8; }
QPushButton#danger { color:#b42318; background:#fff7f6; border-color:#f2c9c5; }
QPushButton#modeActive { background:#eaf2ff; color:#1558d6; border:1px solid #8fb5ef; font-weight:600; }
QTableWidget { background:white; border:1px solid #e0e6ef; border-radius:9px; gridline-color:#eef1f5; selection-background-color:#dce9ff; selection-color:#173b75; font:12px 'Segoe UI'; }
QHeaderView::section { background:#f8fafc; border:0; border-bottom:1px solid #e5eaf1; padding:7px; font:600 11px 'Segoe UI'; color:#475467; }
QCheckBox { spacing:8px; font:12px 'Segoe UI'; color:#344054; }
QCheckBox::indicator { width:17px; height:17px; border:1px solid #b7c0cf; border-radius:5px; background:white; }
QCheckBox::indicator:checked { background:#2563eb; border-color:#2563eb; }
QToolTip { background:#1f2937; color:white; border:none; padding:5px; }
"""


class ModernButton(QPushButton):
    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)


class ParameterButton(ModernButton):
    selected = Signal(str)

    def __init__(self, key: str, parent: QWidget):
        parameter = PARAMETERS[key]
        super().__init__(f"{parameter.code}\n{parameter.label}", parent)
        self.key = key
        self.setToolTip(
            f"{parameter.label} ({parameter.unit})" if parameter.unit else parameter.label
        )
        self.setStyleSheet(
            f"QPushButton{{background:white;border:1px solid #dce3ec;"
            f"border-left:4px solid {parameter.accent};border-radius:9px;"
            "padding:4px 7px;text-align:left;font:600 11px 'Segoe UI';color:#24324a;}"
            "QPushButton:hover{background:#f7faff;border-color:#9bbcf2;}"
            "QPushButton:pressed{background:#eaf2ff;}"
        )
        self.clicked.connect(lambda: self.selected.emit(self.key))


class MachineDiagram(QWidget):
    parameter_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumSize(610, 460)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.buttons: dict[str, ParameterButton] = {}
        self._create_buttons()

    def _button(self, key: str, rect: QRect) -> None:
        button = ParameterButton(key, self)
        button.setGeometry(rect)
        button.selected.connect(self.parameter_selected)
        self.buttons[key] = button

    def _create_buttons(self) -> None:
        self._button("Fc", QRect(18, 16, 128, 50))
        self._button("U", QRect(364, 16, 112, 50))
        self._button("I", QRect(482, 16, 112, 50))
        self._button("Er", QRect(24, 350, 118, 50))
        self._button("theta_red", QRect(476, 350, 118, 50))
        keys = ["formula", "t", "Fr", "Dch", "Vch", "theta_m", "omega_m", "omega_red"]
        widths = [78, 68, 72, 86, 82, 80, 84, 92]
        x = 10
        for key, width in zip(keys, widths):
            self._button(key, QRect(x, 408, width, 48))
            x += width + 5

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#fbfcfe"))

        painter.setPen(QPen(QColor("#d9e0ea"), 1))
        painter.setBrush(QColor("#f2f5f9"))
        painter.drawRoundedRect(QRect(16, 78, self.width() - 32, 258), 16, 16)
        painter.setBrush(QColor("#23262d"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRect(54, 170, self.width() - 108, 122), 8, 8)
        painter.setBrush(QColor("#76c9c8"))
        painter.drawRoundedRect(QRect(58, 190, self.width() - 116, 18), 8, 8)
        painter.setBrush(QColor("#ee8f95"))
        painter.drawRoundedRect(QRect(238, 110, 130, 130), 10, 10)
        painter.setBrush(QColor("#d86f78"))
        painter.drawRoundedRect(QRect(224, 190, 158, 28), 8, 8)
        painter.setBrush(QColor("#9ca3af"))
        painter.drawRoundedRect(QRect(280, 228, 54, 55), 8, 8)
        painter.setBrush(QColor("white"))
        painter.drawEllipse(QRect(260, 135, 22, 22))
        painter.drawEllipse(QRect(320, 135, 22, 22))

        painter.setPen(QPen(QColor("#b0893a"), 3))
        x0, y0 = 242, 262
        for index in range(12):
            x = x0 + index * 10
            painter.drawLine(x, y0, x + 5, y0 - 22)
            painter.drawLine(x + 5, y0 - 22, x + 10, y0)
        painter.setPen(QPen(QColor("#8b6f2f"), 2))
        painter.drawLine(236, 264, 366, 264)

        painter.setPen(QPen(QColor("#475467"), 3))
        painter.setBrush(QColor("#eef2f7"))
        painter.drawEllipse(QRect(self.width() - 126, 220, 48, 48))
        painter.setBrush(QColor("#d7deea"))
        painter.drawEllipse(QRect(self.width() - 111, 235, 18, 18))

        painter.setPen(QPen(QColor("#2563eb"), 2))
        painter.drawLine(80, 66, 104, 118)
        painter.drawLine(104, 118, 160, 145)
        painter.drawLine(82, 350, 220, 270)
        painter.drawLine(self.width() - 74, 350, self.width() - 101, 266)
        painter.setPen(QPen(QColor("#667085"), 2))
        painter.drawLine(430, 66, 365, 106)
        painter.drawLine(540, 66, 468, 122)


class ChoiceWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.mode = SelectionMode.NONE
        self.abscissa_key = "t"
        self.ordinate_keys = ["Fr", "Er", "Fc"]
        self.setWindowTitle("Cordeuse de raquettes SP55")
        self.resize(1180, 760)
        self.setMinimumSize(1040, 680)
        self.setStyleSheet(APP_STYLE)
        self._build_menu()
        self._build_ui()
        self._refresh()

    def _build_menu(self) -> None:
        bar = self.menuBar()
        bar.setNativeMenuBar(False)
        menus = {
            "Fichier": ["Nouveau", "Ouvrir", "Sauver"],
            "Mesures": ["Acquisition", "Sélectionner tout"],
            "Courbes": ["Choix des paramètres", "Tracer"],
            "Aide": ["Aide", "À propos"],
        }
        for title, action_names in menus.items():
            menu = bar.addMenu(title)
            for action_name in action_names:
                menu.addAction(QAction(action_name, self))

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(16)

        side = QFrame()
        side.setObjectName("card")
        side.setFixedWidth(92)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(12, 16, 12, 16)
        side_layout.setSpacing(10)
        brand = QLabel("SP55")
        brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet("font:700 19px 'Segoe UI';color:#1558d6;padding:8px;")
        side_layout.addWidget(brand)
        for symbol, tooltip in [
            ("＋", "Nouveau"), ("📂", "Ouvrir"), ("💾", "Sauver"),
            ("✕", "Effacer"), ("◉", "Mesures"), ("⌁", "Courbes"),
        ]:
            button = ModernButton(symbol)
            button.setToolTip(tooltip)
            button.setFixedHeight(50)
            button.setStyleSheet(
                "QPushButton{font-size:20px;padding:0;}"
                "QPushButton:hover{background:#eaf2ff;}"
            )
            side_layout.addWidget(button)
        side_layout.addStretch()
        configuration_button = ModernButton("⚙")
        configuration_button.setToolTip("Configuration")
        configuration_button.setFixedHeight(50)
        side_layout.addWidget(configuration_button)
        outer.addWidget(side)

        content = QVBoxLayout()
        content.setSpacing(14)
        outer.addLayout(content, 1)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Choix des paramètres")
        title.setObjectName("title")
        subtitle = QLabel(
            "Sélectionnez les grandeurs à visualiser comme dans le logiciel SP55 d’origine."
        )
        subtitle.setObjectName("subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch()
        content.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(14)
        content.addLayout(body, 1)

        machine_card = QFrame()
        machine_card.setObjectName("card")
        machine_layout = QVBoxLayout(machine_card)
        machine_layout.setContentsMargins(14, 14, 14, 14)
        self.diagram = MachineDiagram()
        self.diagram.parameter_selected.connect(self.parameter_clicked)
        machine_layout.addWidget(self.diagram)
        body.addWidget(machine_card, 3)

        right = QVBoxLayout()
        right.setSpacing(14)
        body.addLayout(right, 2)

        selection_card = QFrame()
        selection_card.setObjectName("card")
        selection_layout = QVBoxLayout(selection_card)
        selection_layout.setContentsMargins(16, 16, 16, 16)
        selection_layout.setSpacing(10)
        section = QLabel("Paramètres d’affichage")
        section.setObjectName("section")
        selection_layout.addWidget(section)

        mode_row = QHBoxLayout()
        self.abscissa_button = ModernButton("→  Abscisse")
        self.ordinate_button = ModernButton("↑  Ordonnée")
        self.abscissa_button.clicked.connect(
            lambda: self.set_mode(SelectionMode.ABSCISSA)
        )
        self.ordinate_button.clicked.connect(
            lambda: self.set_mode(SelectionMode.ORDINATE)
        )
        mode_row.addWidget(self.abscissa_button)
        mode_row.addWidget(self.ordinate_button)
        selection_layout.addLayout(mode_row)

        self.abscissa_label = QLabel()
        self.abscissa_label.setStyleSheet(
            "background:#f8fafc;border:1px solid #e1e7ef;border-radius:8px;"
            "padding:9px;font:600 12px 'Segoe UI';"
        )
        selection_layout.addWidget(self.abscissa_label)

        ordinate_row = QHBoxLayout()
        ordinate_row.addWidget(QLabel("Ordonnées sélectionnées"))
        ordinate_row.addStretch()
        self.delete_button = ModernButton("Supprimer")
        self.delete_button.setObjectName("danger")
        self.delete_button.clicked.connect(self.remove_ordinate)
        ordinate_row.addWidget(self.delete_button)
        selection_layout.addLayout(ordinate_row)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["N°", "Paramètre"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setMinimumHeight(150)
        selection_layout.addWidget(self.table)

        action_row = QHBoxLayout()
        self.trace_button = ModernButton("Tracer les courbes")
        self.trace_button.setObjectName("primary")
        self.trace_button.clicked.connect(self.trace)
        edit_button = ModernButton("Éditer")
        edit_button.clicked.connect(
            lambda: QMessageBox.information(
                self, "Éditer", "Édition des paramètres sélectionnés."
            )
        )
        action_row.addWidget(self.trace_button, 2)
        action_row.addWidget(edit_button, 1)
        selection_layout.addLayout(action_row)
        right.addWidget(selection_card, 3)

        measure_card = QFrame()
        measure_card.setObjectName("card")
        measure_layout = QVBoxLayout(measure_card)
        measure_layout.setContentsMargins(16, 14, 16, 14)
        measure_layout.setSpacing(8)
        measure_header = QHBoxLayout()
        measure_title = QLabel("Mesures")
        measure_title.setObjectName("section")
        measure_header.addWidget(measure_title)
        measure_header.addStretch()
        clear_button = ModernButton("Tout désélectionner")
        clear_button.clicked.connect(self.clear_measures)
        reset_button = ModernButton("Réinitialiser")
        reset_button.clicked.connect(self.restore_default)
        measure_header.addWidget(clear_button)
        measure_header.addWidget(reset_button)
        measure_layout.addLayout(measure_header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)
        self.measure_checks: list[QCheckBox] = []
        for index in range(1, 11):
            check = QCheckBox(f"Mesure n°{index}")
            check.setChecked(index == 1)
            check.stateChanged.connect(self._refresh_trace_state)
            self.measure_checks.append(check)
            grid.addWidget(check, (index - 1) // 5, (index - 1) % 5)
        measure_layout.addLayout(grid)
        right.addWidget(measure_card, 1)

        footer = QHBoxLayout()
        self.status = QLabel(
            "Cliquez sur Abscisse ou Ordonnée puis sur une grandeur."
        )
        self.status.setObjectName("status")
        footer.addWidget(self.status, 1)
        help_button = ModernButton("Aide")
        help_button.clicked.connect(self.show_help)
        close_button = ModernButton("Fermer")
        close_button.clicked.connect(self.close)
        footer.addWidget(help_button)
        footer.addWidget(close_button)
        content.addLayout(footer)

    def set_mode(self, mode: SelectionMode) -> None:
        self.mode = mode
        self.abscissa_button.setObjectName(
            "modeActive" if mode is SelectionMode.ABSCISSA else ""
        )
        self.ordinate_button.setObjectName(
            "modeActive" if mode is SelectionMode.ORDINATE else ""
        )
        for button in (self.abscissa_button, self.ordinate_button):
            button.style().unpolish(button)
            button.style().polish(button)
        if mode is SelectionMode.ABSCISSA:
            self.status.setText(
                "Sélection de l'abscisse : cliquez sur une grandeur du schéma."
            )
        elif mode is SelectionMode.ORDINATE:
            self.status.setText(
                "Sélection des ordonnées : cliquez sur une ou plusieurs grandeurs."
            )

    def parameter_clicked(self, key: str) -> None:
        if self.mode is SelectionMode.ABSCISSA:
            self.abscissa_key = key
            self.mode = SelectionMode.NONE
            self.status.setText(
                f"Abscisse sélectionnée : {self.parameter_text(key)}"
            )
        elif self.mode is SelectionMode.ORDINATE:
            if key != self.abscissa_key and key not in self.ordinate_keys:
                self.ordinate_keys.append(key)
            self.status.setText(f"Ordonnée ajoutée : {self.parameter_text(key)}")
        else:
            self.status.setText(
                f"{PARAMETERS[key].label} — unité : "
                f"{PARAMETERS[key].unit or 'sans unité'}"
            )
        if self.mode is SelectionMode.NONE:
            self.set_mode(SelectionMode.NONE)
        self._refresh()

    @staticmethod
    def parameter_text(key: str) -> str:
        parameter = PARAMETERS[key]
        return (
            f"{parameter.label} ({parameter.unit})"
            if parameter.unit else parameter.label
        )

    def remove_ordinate(self) -> None:
        row = self.table.currentRow()
        if 0 <= row < len(self.ordinate_keys):
            removed = self.ordinate_keys.pop(row)
            self.status.setText(
                f"Paramètre supprimé : {self.parameter_text(removed)}"
            )
            self._refresh()

    def clear_measures(self) -> None:
        for check in self.measure_checks:
            check.setChecked(False)
        self.status.setText("Toutes les mesures ont été désélectionnées.")

    def restore_default(self) -> None:
        self.abscissa_key = "t"
        self.ordinate_keys = ["Fr", "Er", "Fc"]
        for index, check in enumerate(self.measure_checks, start=1):
            check.setChecked(index == 1)
        self.status.setText("Sélection par défaut restaurée.")
        self._refresh()

    def show_help(self) -> None:
        QMessageBox.information(
            self,
            "Aide — Choix des paramètres",
            "1. Cliquez sur Abscisse puis sur une grandeur.\n"
            "2. Cliquez sur Ordonnée puis sur les grandeurs à tracer.\n"
            "3. Cochez au moins une mesure.\n"
            "4. Cliquez sur Tracer les courbes.",
        )

    def trace(self) -> None:
        selected = [
            str(index + 1)
            for index, check in enumerate(self.measure_checks)
            if check.isChecked()
        ]
        curves = "\n".join(
            f"• {self.parameter_text(key)}" for key in self.ordinate_keys
        )
        QMessageBox.information(
            self,
            "Tracer",
            f"Abscisse : {self.parameter_text(self.abscissa_key)}\n\n"
            f"Ordonnées :\n{curves}\n\nMesures : {', '.join(selected)}",
        )

    def _refresh_trace_state(self) -> None:
        self.trace_button.setEnabled(
            bool(self.ordinate_keys)
            and any(check.isChecked() for check in self.measure_checks)
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
