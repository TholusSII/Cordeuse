from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum, auto

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPen, QPolygon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)


FACE = "#d4d0c8"
LIGHT = "#ffffff"
SHADOW = "#808080"
DARK = "#404040"
TITLE_BLUE = "#0a246a"
SELECTION_BLUE = "#000080"


class SelectionMode(Enum):
    NONE = auto()
    ABSCISSA = auto()
    ORDINATE = auto()


@dataclass(frozen=True)
class Parameter:
    code: str
    label: str
    unit: str


PARAMETERS = {
    "Fc": Parameter("Fc", "Effort corde", "N"),
    "U": Parameter("U", "Tension moteur", "V"),
    "I": Parameter("I", "Courant moteur", "A"),
    "Er": Parameter("Er", "Écrasement ressort", "mm"),
    "theta_red": Parameter("θred", "Angle réducteur", "°"),
    "t": Parameter("t", "Temps", "s"),
    "formula": Parameter("Y=√", "Formule", ""),
    "Fr": Parameter("Fr", "Effort ressort", "N"),
    "Dch": Parameter("Dch", "Déplacement chariot", "mm"),
    "Vch": Parameter("Vch", "Vitesse chariot", "mm/s"),
    "theta_m": Parameter("θm", "Angle moteur", "°"),
    "omega_m": Parameter("Ωm", "Vitesse moteur", "tr/min"),
    "omega_red": Parameter("Ωred", "Vitesse réducteur", "tr/min"),
}


class RaisedButton(QPushButton):
    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setStyleSheet(
            "QPushButton{background:#d4d0c8;color:black;border:2px outset #efefef;"
            "padding:2px;font:11px 'MS Sans Serif';text-align:center;}"
            "QPushButton:pressed{border:2px inset #efefef;}"
            "QPushButton:disabled{color:#808080;}"
        )


class ParameterButton(RaisedButton):
    selected = Signal(str)

    def __init__(self, key: str, parent: QWidget):
        super().__init__(PARAMETERS[key].code, parent)
        self.key = key
        self.setToolTip(f"{PARAMETERS[key].label} ({PARAMETERS[key].unit})".strip())
        self.clicked.connect(lambda: self.selected.emit(self.key))
        self.setStyleSheet(
            "QPushButton{background:#d4d0c8;border:2px outset #efefef;"
            "font:bold 15px 'Times New Roman';padding:0;}"
            "QPushButton:pressed{border:2px inset #efefef;background:#c0c0c0;}"
        )


class LeftToolButton(RaisedButton):
    def __init__(self, symbol: str, tooltip: str, parent: QWidget):
        super().__init__(symbol, parent)
        self.setToolTip(tooltip)
        self.setFixedSize(36, 36)
        self.setStyleSheet(
            "QPushButton{background:#d4d0c8;border:2px outset #efefef;"
            "font:bold 17px 'MS Sans Serif';padding:0;}"
            "QPushButton:pressed{border:2px inset #efefef;}"
        )


class MachineDiagram(QWidget):
    parameter_selected = Signal(str)

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setStyleSheet("background:#efefef;border:1px solid #b8b8b8;")
        self.buttons: dict[str, ParameterButton] = {}
        self._create_buttons()

    def _button(self, key: str, rect: QRect) -> None:
        button = ParameterButton(key, self)
        button.setGeometry(rect)
        button.selected.connect(self.parameter_selected)
        self.buttons[key] = button

    def _create_buttons(self) -> None:
        self._button("Fc", QRect(8, 5, 48, 32))
        self._button("U", QRect(266, 5, 45, 32))
        self._button("I", QRect(317, 5, 45, 32))
        self._button("Er", QRect(18, 284, 52, 34))
        self._button("theta_red", QRect(310, 284, 58, 34))
        self._button("formula", QRect(0, 332, 50, 36))
        self._button("t", QRect(52, 332, 44, 36))
        self._button("Fr", QRect(116, 332, 47, 36))
        self._button("Dch", QRect(165, 332, 47, 36))
        self._button("Vch", QRect(214, 332, 47, 36))
        self._button("theta_m", QRect(263, 332, 47, 36))
        self._button("omega_m", QRect(312, 332, 47, 36))
        self._button("omega_red", QRect(361, 332, 55, 36))

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Fond du bâti, proche de la capture 800x600 d'origine.
        painter.fillRect(QRect(13, 112, 392, 166), QColor("#252525"))
        painter.fillRect(QRect(22, 125, 374, 12), QColor("#545454"))
        painter.fillRect(QRect(22, 144, 374, 13), QColor("#7a7a7a"))
        painter.fillRect(QRect(22, 251, 374, 13), QColor("#777777"))

        # Barre/chariot.
        painter.fillRect(QRect(14, 139, 393, 13), QColor("#68b9b9"))
        painter.setPen(QPen(QColor("#aef0ef"), 2))
        painter.drawLine(16, 141, 405, 141)
        painter.setPen(QPen(QColor("#333333"), 1))
        painter.drawRect(QRect(14, 139, 393, 13))

        # Chariot rose et coulisseau.
        painter.fillRect(QRect(143, 75, 82, 91), QColor("#ef8f8f"))
        painter.fillRect(QRect(151, 150, 71, 71), QColor("#e98f8f"))
        painter.fillRect(QRect(147, 144, 86, 14), QColor("#db7777"))
        painter.fillRect(QRect(172, 216, 32, 44), QColor("#a7a7a7"))
        painter.setPen(QPen(QColor("#666666"), 1))
        painter.drawRect(QRect(143, 75, 82, 91))
        painter.drawRect(QRect(151, 150, 71, 71))

        # Deux trous blancs visibles sur le chariot.
        painter.setBrush(QColor("white"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRect(158, 94, 17, 17))
        painter.drawEllipse(QRect(194, 94, 17, 17))

        # Ressort calibré.
        painter.setPen(QPen(QColor("#6c5424"), 2))
        x0, y0 = 160, 210
        for i in range(11):
            x = x0 + i * 6
            painter.drawLine(x, y0, x + 3, y0 - 15)
            painter.drawLine(x + 3, y0 - 15, x + 6, y0)
        painter.setPen(QPen(QColor("#c7a752"), 2))
        painter.drawLine(153, 211, 232, 211)

        # Capteur/potentiomètre à droite.
        painter.setBrush(QColor("#ececec"))
        painter.setPen(QPen(QColor("#353535"), 2))
        painter.drawEllipse(QRect(358, 178, 33, 33))
        painter.setBrush(QColor("#dadada"))
        painter.drawEllipse(QRect(368, 188, 12, 12))

        # Petites pièces et vis du bâti.
        painter.setBrush(QColor("#d6d6d6"))
        painter.setPen(Qt.NoPen)
        for x, y in [(25, 232), (25, 245), (399, 178), (399, 220), (349, 248)]:
            painter.drawEllipse(QRect(x, y, 7, 7))

        # Corde et fils/capteurs.
        painter.setPen(QPen(QColor("#707070"), 2))
        painter.drawLine(53, 51, 132, 69)
        painter.drawLine(132, 69, 180, 74)
        painter.drawLine(225, 75, 336, 43)
        painter.drawLine(336, 43, 345, 29)

        # Traits bleus reliant les icônes aux zones correspondantes.
        painter.setPen(QPen(QColor("#0000aa"), 2))
        painter.drawLine(34, 38, 42, 64)
        painter.drawLine(42, 64, 72, 70)
        painter.drawLine(42, 284, 125, 216)
        painter.drawLine(339, 284, 374, 207)

        # Légers détails noirs en partie haute.
        painter.fillRect(QRect(98, 115, 31, 10), QColor("#111111"))
        painter.fillRect(QRect(247, 115, 31, 10), QColor("#111111"))


class ChoiceWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.mode = SelectionMode.NONE
        self.abscissa_key = "t"
        self.ordinate_keys = ["Fr", "Er", "Fc"]

        self.setWindowTitle("Cordeuse de raquettes SP55")
        self.setFixedSize(800, 600)
        self.setStyleSheet("QMainWindow{background:#d4d0c8;} QToolTip{font:11px 'MS Sans Serif';}")
        self._build_menu()
        self._build_ui()
        self._refresh()

    def _build_menu(self) -> None:
        bar = self.menuBar()
        bar.setNativeMenuBar(False)
        bar.setStyleSheet(
            "QMenuBar{background:#d4d0c8;color:#303030;font:11px 'MS Sans Serif';padding:1px;}"
            "QMenuBar::item{padding:2px 7px;}QMenuBar::item:selected{background:#0a246a;color:white;}"
            "QMenu{background:#d4d0c8;font:11px 'MS Sans Serif';}"
        )
        for title in ["Fichier", "Effacer", "Mesures", "Courbes", "Aide"]:
            menu = bar.addMenu(title)
            action = QAction(title, self)
            menu.addAction(action)

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)
        root.setStyleSheet("background:#d4d0c8;")

        # Barre d'outils verticale d'origine.
        toolbar = QFrame(root)
        toolbar.setGeometry(0, 0, 42, 522)
        toolbar.setStyleSheet("background:#d4d0c8;border-right:1px solid #808080;")
        symbols = [
            ("□", "Nouveau"), ("▰", "Ouvrir"), ("▣", "Sauver"),
            ("✎", "Effacer"), ("⌁", "Mesures"), ("⌁", "Courbes"),
        ]
        y = 8
        for symbol, tip in symbols:
            button = LeftToolButton(symbol, tip, toolbar)
            button.move(3, y)
            y += 43
        config = LeftToolButton("▥", "Configuration", toolbar)
        config.move(3, 318)

        # Fenêtre enfant bleue « Choix des paramètres ».
        child = QFrame(root)
        child.setGeometry(54, 8, 730, 448)
        child.setStyleSheet("background:#d4d0c8;border:1px solid #808080;")

        title = QLabel("  Choix des paramètres", child)
        title.setGeometry(1, 1, 728, 20)
        title.setStyleSheet("background:#0a246a;color:white;font:11px 'MS Sans Serif';border:0;")
        for text, x in [("_", 660), ("□", 683), ("×", 706)]:
            b = QLabel(text, child)
            b.setGeometry(x, 2, 21, 18)
            b.setAlignment(Qt.AlignCenter)
            b.setStyleSheet("background:#d4d0c8;color:black;border:1px outset white;font:bold 11px Arial;")

        # Schéma machine cliquable.
        self.diagram = MachineDiagram(child)
        self.diagram.setGeometry(8, 29, 418, 372)
        self.diagram.parameter_selected.connect(self.parameter_clicked)

        # Panneau de choix à droite.
        panel = QFrame(child)
        panel.setGeometry(432, 29, 218, 372)
        panel.setStyleSheet("background:#d4d0c8;border:1px inset #ffffff;")

        self.abscissa_button = RaisedButton("→ Abscisse", panel)
        self.abscissa_button.setGeometry(7, 8, 98, 29)
        self.abscissa_button.clicked.connect(lambda: self.set_mode(SelectionMode.ABSCISSA))

        self.abscissa_label = QLabel(panel)
        self.abscissa_label.setGeometry(7, 40, 204, 22)
        self.abscissa_label.setStyleSheet("background:white;border:1px inset #d4d0c8;font:11px Arial;padding-left:3px;")

        self.ordinate_button = RaisedButton("↑ Ordonnée", panel)
        self.ordinate_button.setGeometry(7, 68, 94, 28)
        self.ordinate_button.clicked.connect(lambda: self.set_mode(SelectionMode.ORDINATE))

        self.delete_button = RaisedButton("✎  Supprimer", panel)
        self.delete_button.setGeometry(112, 68, 99, 28)
        self.delete_button.clicked.connect(self.remove_ordinate)

        self.table = QTableWidget(panel)
        self.table.setGeometry(7, 100, 204, 121)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["N°", "Paramètre"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setShowGrid(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setStyleSheet(
            "QTableWidget{background:white;border:1px inset #d4d0c8;font:11px Arial;gridline-color:#c0c0c0;}"
            "QTableWidget::item:selected{background:#000080;color:white;}"
            "QHeaderView::section{background:#d4d0c8;border:1px outset white;font:11px Arial;padding:1px;}"
        )

        self.trace_button = RaisedButton("⌁  Tracer", panel)
        self.trace_button.setGeometry(7, 329, 78, 35)
        self.trace_button.clicked.connect(self.trace)

        edit_button = RaisedButton("▤  Éditer", panel)
        edit_button.setGeometry(87, 329, 78, 35)
        edit_button.clicked.connect(lambda: QMessageBox.information(self, "Éditer", "Édition des paramètres sélectionnés."))

        # Colonne « Mesures ».
        measures = QFrame(child)
        measures.setGeometry(653, 29, 70, 372)
        measures.setStyleSheet("background:#d4d0c8;border:1px inset #ffffff;")
        label = QLabel("Mesures", measures)
        label.setGeometry(5, 2, 60, 20)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font:bold 11px Arial;border:0;")

        self.measure_checks: list[QCheckBox] = []
        for i in range(1, 11):
            check = QCheckBox(f"n°{i}", measures)
            check.setGeometry(8, 20 + (i - 1) * 21, 52, 20)
            check.setStyleSheet("font:11px Arial;border:0;")
            check.setChecked(i == 1)
            check.stateChanged.connect(self._refresh_trace_state)
            self.measure_checks.append(check)

        for text, yy, callback in [
            ("▣", 235, lambda: None),
            ("✕", 264, self.clear_measures),
            ("↶", 293, self.restore_default),
            ("?  Aide", 322, self.show_help),
            ("▥  Fermer", 351, self.close),
        ]:
            button = RaisedButton(text, measures)
            button.setGeometry(5, yy, 60, 26)
            button.clicked.connect(callback)

        # Bas de la fenêtre, logo ACTIA.
        logo = QLabel("ACTIA▦", root)
        logo.setGeometry(395, 530, 151, 39)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            "background:black;color:white;border:3px outset #efefef;"
            "font:bold 25px 'Times New Roman';"
        )

        self.status = QLabel("Cliquez sur Abscisse ou Ordonnée puis sur une grandeur.", root)
        self.status.setGeometry(55, 462, 720, 24)
        self.status.setStyleSheet("font:11px 'MS Sans Serif';border:0;")

    def set_mode(self, mode: SelectionMode) -> None:
        self.mode = mode
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
            self.status.setText(f"{PARAMETERS[key].label} — unité : {PARAMETERS[key].unit or 'sans unité'}")
        self._refresh()

    @staticmethod
    def parameter_text(key: str) -> str:
        parameter = PARAMETERS[key]
        return f"{parameter.label} ({parameter.unit})" if parameter.unit else parameter.label

    def remove_ordinate(self) -> None:
        row = self.table.currentRow()
        if 0 <= row < len(self.ordinate_keys):
            removed = self.ordinate_keys.pop(row)
            self.status.setText(f"Paramètre supprimé : {self.parameter_text(removed)}")
            self._refresh()

    def clear_measures(self) -> None:
        for check in self.measure_checks:
            check.setChecked(False)
        self.status.setText("Toutes les mesures ont été désélectionnées.")

    def restore_default(self) -> None:
        self.abscissa_key = "t"
        self.ordinate_keys = ["Fr", "Er", "Fc"]
        for i, check in enumerate(self.measure_checks, start=1):
            check.setChecked(i == 1)
        self.status.setText("Sélection par défaut restaurée.")
        self._refresh()

    def show_help(self) -> None:
        QMessageBox.information(
            self,
            "Aide — Choix des paramètres",
            "1. Cliquez sur Abscisse puis sur une grandeur.\n"
            "2. Cliquez sur Ordonnée puis sur les grandeurs à tracer.\n"
            "3. Cochez au moins une mesure.\n"
            "4. Cliquez sur Tracer.",
        )

    def trace(self) -> None:
        selected = [str(i + 1) for i, check in enumerate(self.measure_checks) if check.isChecked()]
        curves = "\n".join(f"• {self.parameter_text(key)}" for key in self.ordinate_keys)
        QMessageBox.information(
            self,
            "Tracer",
            f"Abscisse : {self.parameter_text(self.abscissa_key)}\n\n"
            f"Ordonnées :\n{curves}\n\nMesures : {', '.join(selected)}",
        )

    def _refresh_trace_state(self) -> None:
        self.trace_button.setEnabled(bool(self.ordinate_keys) and any(c.isChecked() for c in self.measure_checks))

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
    app.setStyle("Windows")
    app.setFont(QFont("MS Sans Serif", 8))
    window = ChoiceWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
