from __future__ import annotations

import math
import sys
from dataclasses import dataclass

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


APP_STYLE = """
QMainWindow, QWidget {
    background: #1f252b;
    color: #edf2f6;
    font-family: Arial;
}
QFrame#panel {
    background: #2a323a;
    border: 2px solid #101419;
    border-radius: 8px;
}
QLabel#title {
    font-size: 28px;
    font-weight: 700;
    color: #f3f6f8;
}
QLabel#subtitle {
    color: #aab6c0;
    font-size: 13px;
}
QLabel#digital {
    background: #09110d;
    color: #62ff91;
    border: 3px inset #53605a;
    border-radius: 5px;
    font-family: Consolas, monospace;
    font-size: 50px;
    font-weight: 700;
    padding: 8px 16px;
}
QLabel#unit {
    color: #cfd7de;
    font-size: 18px;
    font-weight: 700;
}
QPushButton {
    min-height: 48px;
    background: #45515c;
    color: white;
    border: 2px outset #687681;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 15px;
    font-weight: 700;
}
QPushButton:hover { background: #566572; }
QPushButton:pressed { border-style: inset; background: #313a42; }
QPushButton:checked { background: #155b87; border-color: #55b6e9; }
QPushButton#danger { background: #9a1e1e; border-color: #e46666; }
QPushButton#danger:hover { background: #b52a2a; }
QPushButton#action { background: #136e3d; border-color: #50c880; }
QPushButton#action:hover { background: #19844b; }
QPushButton#key { min-width: 72px; font-size: 20px; }
QLabel#statusOk { color: #67e58d; font-weight: 700; }
QLabel#statusOff { color: #ffcc66; font-weight: 700; }
"""


@dataclass
class MachineState:
    target_tension: float = 25.0
    measured_tension: float = 0.0
    prestretch_percent: int = 0
    knots_percent: int = 10
    speed: int = 2
    motor_running: bool = False
    cycle_seconds: float = 0.0
    strings_done: int = 0


class TensionGauge(QWidget):
    """Jauge dessinée en Qt, sans image externe."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value = 0.0
        self._maximum = 40.0
        self.setMinimumSize(280, 210)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(self._maximum, value))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(22, 18, -22, -12)
        center = rect.center()
        radius = min(rect.width(), rect.height()) * 0.44

        painter.setPen(QPen(QColor("#0d1013"), 18, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(
            int(center.x() - radius),
            int(center.y() - radius),
            int(radius * 2),
            int(radius * 2),
            30 * 16,
            120 * 16,
        )
        painter.setPen(QPen(QColor("#4f5f6b"), 13, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(
            int(center.x() - radius),
            int(center.y() - radius),
            int(radius * 2),
            int(radius * 2),
            30 * 16,
            120 * 16,
        )

        for i in range(9):
            value = i * 5
            angle = math.radians(210 - i * 15)
            inner = radius - (18 if i % 2 == 0 else 12)
            outer = radius + 2
            x1 = center.x() + math.cos(angle) * inner
            y1 = center.y() - math.sin(angle) * inner
            x2 = center.x() + math.cos(angle) * outer
            y2 = center.y() - math.sin(angle) * outer
            painter.setPen(QPen(QColor("#e0e6ea"), 2))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            if i % 2 == 0:
                tx = center.x() + math.cos(angle) * (radius - 38)
                ty = center.y() - math.sin(angle) * (radius - 38)
                painter.setPen(QColor("#cfd7de"))
                painter.setFont(QFont("Arial", 9, QFont.Bold))
                painter.drawText(int(tx - 12), int(ty - 8), 24, 16, Qt.AlignCenter, str(value))

        ratio = self._value / self._maximum
        angle = math.radians(210 - ratio * 120)
        needle = radius - 28
        nx = center.x() + math.cos(angle) * needle
        ny = center.y() - math.sin(angle) * needle
        painter.setPen(QPen(QColor("#ef4444"), 5, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(center, nx, ny)
        painter.setBrush(QColor("#ef4444"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, 9, 9)

        painter.setPen(QColor("#edf2f6"))
        painter.setFont(QFont("Arial", 13, QFont.Bold))
        painter.drawText(rect.adjusted(0, 120, 0, 0), Qt.AlignHCenter | Qt.AlignTop, "TENSION MESURÉE")


class ValuePanel(QFrame):
    changed = Signal(float)

    def __init__(self, title: str, value: float, step: float = 0.5, unit: str = "kg") -> None:
        super().__init__()
        self.setObjectName("panel")
        self._value = value
        self._step = step
        self._unit = unit

        layout = QVBoxLayout(self)
        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; font-weight: 700;")
        self.display = QLabel()
        self.display.setObjectName("digital")
        self.display.setAlignment(Qt.AlignCenter)

        controls = QHBoxLayout()
        minus = QPushButton("−")
        plus = QPushButton("+")
        minus.setObjectName("key")
        plus.setObjectName("key")
        minus.clicked.connect(lambda: self.set_value(self._value - self._step))
        plus.clicked.connect(lambda: self.set_value(self._value + self._step))
        controls.addWidget(minus)
        controls.addWidget(plus)

        layout.addWidget(label)
        layout.addWidget(self.display)
        layout.addLayout(controls)
        self.set_value(value, emit=False)

    def set_value(self, value: float, emit: bool = True) -> None:
        self._value = max(0.0, min(40.0, value))
        self.display.setText(f"{self._value:04.1f} {self._unit}")
        if emit:
            self.changed.emit(self._value)


class MainControlPage(QWidget):
    state_changed = Signal()

    def __init__(self, state: MachineState) -> None:
        super().__init__()
        self.state = state

        root = QGridLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        self.target_panel = ValuePanel("CONSIGNE DE TENSION", state.target_tension)
        self.target_panel.changed.connect(self._target_changed)
        root.addWidget(self.target_panel, 0, 0, 2, 1)

        gauge_panel = QFrame()
        gauge_panel.setObjectName("panel")
        gauge_layout = QVBoxLayout(gauge_panel)
        self.gauge = TensionGauge()
        self.measured_label = QLabel("00.0 kg")
        self.measured_label.setObjectName("digital")
        self.measured_label.setAlignment(Qt.AlignCenter)
        gauge_layout.addWidget(self.gauge, 1)
        gauge_layout.addWidget(self.measured_label)
        root.addWidget(gauge_panel, 0, 1, 2, 1)

        params = QFrame()
        params.setObjectName("panel")
        params_layout = QVBoxLayout(params)
        params_layout.addWidget(self._parameter_row("PRÉ-ÉTIRAGE", ["0 %", "10 %", "20 %"], 0, self._set_prestretch))
        params_layout.addWidget(self._parameter_row("NŒUD", ["+0 %", "+10 %", "+20 %"], 1, self._set_knots))
        params_layout.addWidget(self._parameter_row("VITESSE", ["1", "2", "3"], 1, self._set_speed))
        params_layout.addStretch()
        root.addWidget(params, 0, 2, 1, 1)

        action_panel = QFrame()
        action_panel.setObjectName("panel")
        action_layout = QVBoxLayout(action_panel)
        self.start_button = QPushButton("DÉMARRER LE TIRAGE")
        self.start_button.setObjectName("action")
        self.start_button.clicked.connect(self.toggle_motor)
        release_button = QPushButton("RELÂCHER")
        release_button.clicked.connect(self.release)
        self.counter = QLabel("CORDES TIRÉES : 0")
        self.counter.setAlignment(Qt.AlignCenter)
        self.counter.setStyleSheet("font-size: 18px; font-weight: 700;")
        action_layout.addWidget(self.start_button)
        action_layout.addWidget(release_button)
        action_layout.addWidget(self.counter)
        root.addWidget(action_panel, 1, 2, 1, 1)

        root.setColumnStretch(0, 3)
        root.setColumnStretch(1, 4)
        root.setColumnStretch(2, 3)

        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self._simulate)
        self.timer.start()

    def _parameter_row(self, title: str, choices: list[str], checked: int, callback) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        label = QLabel(title)
        label.setStyleSheet("font-weight: 700;")
        buttons_layout = QHBoxLayout()
        group = QButtonGroup(box)
        group.setExclusive(True)
        for index, text in enumerate(choices):
            button = QPushButton(text)
            button.setCheckable(True)
            button.setChecked(index == checked)
            button.clicked.connect(lambda _, i=index: callback(i))
            group.addButton(button)
            buttons_layout.addWidget(button)
        layout.addWidget(label)
        layout.addLayout(buttons_layout)
        return box

    def _target_changed(self, value: float) -> None:
        self.state.target_tension = value
        self.state_changed.emit()

    def _set_prestretch(self, index: int) -> None:
        self.state.prestretch_percent = [0, 10, 20][index]

    def _set_knots(self, index: int) -> None:
        self.state.knots_percent = [0, 10, 20][index]

    def _set_speed(self, index: int) -> None:
        self.state.speed = index + 1

    def toggle_motor(self) -> None:
        self.state.motor_running = not self.state.motor_running
        self.state.cycle_seconds = 0.0
        self.start_button.setText("ARRÊTER LE TIRAGE" if self.state.motor_running else "DÉMARRER LE TIRAGE")
        self.start_button.setObjectName("danger" if self.state.motor_running else "action")
        self.start_button.style().unpolish(self.start_button)
        self.start_button.style().polish(self.start_button)

    def release(self) -> None:
        self.state.motor_running = False
        self.state.measured_tension = 0.0
        self.start_button.setText("DÉMARRER LE TIRAGE")
        self.start_button.setObjectName("action")
        self.start_button.style().unpolish(self.start_button)
        self.start_button.style().polish(self.start_button)

    def _simulate(self) -> None:
        target = self.state.target_tension * (1 + self.state.prestretch_percent / 100)
        if self.state.motor_running:
            self.state.cycle_seconds += 0.05
            speed_factor = [0.045, 0.075, 0.11][self.state.speed - 1]
            delta = target - self.state.measured_tension
            self.state.measured_tension += delta * speed_factor
            if abs(delta) < 0.08 and self.state.cycle_seconds > 1.0:
                self.state.measured_tension = target
            if self.state.cycle_seconds > 2.2:
                self.state.motor_running = False
                self.state.strings_done += 1
                self.start_button.setText("DÉMARRER LE TIRAGE")
                self.start_button.setObjectName("action")
                self.start_button.style().unpolish(self.start_button)
                self.start_button.style().polish(self.start_button)
        else:
            self.state.measured_tension *= 0.92
            if self.state.measured_tension < 0.03:
                self.state.measured_tension = 0.0

        self.gauge.set_value(self.state.measured_tension)
        self.measured_label.setText(f"{self.state.measured_tension:04.1f} kg")
        self.counter.setText(f"CORDES TIRÉES : {self.state.strings_done}")


class SettingsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        root = QGridLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)
        settings = [
            ("UNITÉ DE TENSION", "kg / lb"),
            ("CALIBRATION CAPTEUR", "Accès protégé"),
            ("PORT DE COMMUNICATION", "Non configuré"),
            ("MODE DE FONCTIONNEMENT", "Simulation"),
            ("VERSION INTERFACE", "PyQt V1"),
            ("SAUVEGARDE PARAMÈTRES", "Automatique"),
        ]
        for i, (title, value) in enumerate(settings):
            panel = QFrame()
            panel.setObjectName("panel")
            layout = QVBoxLayout(panel)
            label = QLabel(title)
            label.setStyleSheet("font-size: 16px; font-weight: 700;")
            button = QPushButton(value)
            button.clicked.connect(lambda _, t=title: QMessageBox.information(self, t, "Fonction prévue pour une prochaine itération."))
            layout.addWidget(label)
            layout.addWidget(button)
            root.addWidget(panel, i // 2, i % 2)


class DiagnosticsPage(QWidget):
    def __init__(self, state: MachineState) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        title = QLabel("DIAGNOSTIC DES ENTRÉES / SORTIES")
        title.setObjectName("title")
        root.addWidget(title)
        grid = QGridLayout()
        names = [
            "Capteur d'effort",
            "Fin de course avant",
            "Fin de course arrière",
            "Commande moteur",
            "Arrêt d'urgence",
            "Arduino Mega USB",
        ]
        self.values: list[QLabel] = []
        for row, name in enumerate(names):
            panel = QFrame()
            panel.setObjectName("panel")
            layout = QHBoxLayout(panel)
            label = QLabel(name)
            value = QLabel("INACTIF")
            value.setObjectName("statusOff")
            layout.addWidget(label)
            layout.addStretch()
            layout.addWidget(value)
            self.values.append(value)
            grid.addWidget(panel, row // 2, row % 2)
        root.addLayout(grid)
        root.addStretch()

        timer = QTimer(self)
        timer.setInterval(200)
        timer.timeout.connect(lambda: self._refresh(state))
        timer.start()

    def _refresh(self, state: MachineState) -> None:
        statuses = [
            f"{state.measured_tension:04.1f} kg",
            "ACTIF" if state.measured_tension > 39 else "INACTIF",
            "ACTIF" if state.measured_tension == 0 else "INACTIF",
            "ACTIF" if state.motor_running else "INACTIF",
            "RELÂCHÉ",
            "SIMULATION",
        ]
        for label, text in zip(self.values, statuses):
            label.setText(text)
            label.setObjectName("statusOk" if text not in {"INACTIF"} else "statusOff")
            label.style().unpolish(label)
            label.style().polish(label)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DMS SP55 — Interface de commande")
        self.resize(1280, 760)
        self.setMinimumSize(1024, 650)
        self.state = MachineState()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("background: #151a1f; border-bottom: 2px solid #080a0c;")
        header_layout = QHBoxLayout(header)
        brand = QVBoxLayout()
        title = QLabel("DMS SP55")
        title.setObjectName("title")
        subtitle = QLabel("CORDEUSE DE RAQUETTES — INTERFACE DE COMMANDE")
        subtitle.setObjectName("subtitle")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header_layout.addLayout(brand)
        header_layout.addStretch()
        self.connection = QLabel("● MODE SIMULATION")
        self.connection.setObjectName("statusOk")
        header_layout.addWidget(self.connection)
        root.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        navigation = QFrame()
        navigation.setFixedWidth(210)
        navigation.setStyleSheet("background: #181e24; border-right: 2px solid #0d1115;")
        nav_layout = QVBoxLayout(navigation)
        nav_layout.setContentsMargins(12, 18, 12, 18)
        nav_layout.setSpacing(10)
        buttons = [
            ("COMMANDE", 0),
            ("RÉGLAGES", 1),
            ("DIAGNOSTIC", 2),
        ]
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for text, index in buttons:
            button = QPushButton(text)
            button.setCheckable(True)
            button.setChecked(index == 0)
            button.clicked.connect(lambda _, i=index: self.pages.setCurrentIndex(i))
            self.nav_group.addButton(button)
            nav_layout.addWidget(button)
        nav_layout.addStretch()
        quit_button = QPushButton("QUITTER")
        quit_button.setObjectName("danger")
        quit_button.clicked.connect(self.close)
        nav_layout.addWidget(quit_button)

        self.pages = QStackedWidget()
        self.pages.addWidget(MainControlPage(self.state))
        self.pages.addWidget(SettingsPage())
        self.pages.addWidget(DiagnosticsPage(self.state))
        body.addWidget(navigation)
        body.addWidget(self.pages, 1)
        root.addLayout(body, 1)

    def closeEvent(self, event) -> None:  # noqa: N802
        answer = QMessageBox.question(
            self,
            "Quitter",
            "Fermer l’interface SP55 ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
