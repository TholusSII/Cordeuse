from __future__ import annotations

import sys
from dataclasses import dataclass

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QWidget,
)


@dataclass
class State:
    consigne: float = 25.0
    mesure: float = 0.0
    vitesse: int = 2
    pre_etirage: int = 0
    noeud: int = 10
    actif: bool = False
    cordes: int = 0
    temps: float = 0.0


class Led(QLabel):
    def __init__(self, text: str, active: bool = False, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(118, 28)
        self.set_active(active)

    def set_active(self, active: bool):
        color = "#38e66b" if active else "#681f1f"
        self.setStyleSheet(
            f"background:{color}; color:white; border:2px inset #aaa;"
            "font:bold 12px Arial;"
        )


class MachineDrawing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0.0

    def set_value(self, value: float):
        self.value = value
        self.update()

    def paintEvent(self, event):  # noqa: N802
        del event
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#d9d9d1"))
        p.setPen(QPen(QColor("#4d4d4d"), 4))
        p.setBrush(QColor("#8b9298"))
        p.drawRoundedRect(90, 225, 430, 80, 12, 12)
        p.setBrush(QColor("#b8bdc1"))
        p.drawRoundedRect(125, 130, 360, 130, 18, 18)
        p.setPen(QPen(QColor("#555"), 10))
        p.drawLine(180, 135, 145, 55)
        p.drawLine(430, 135, 465, 55)
        p.setPen(QPen(QColor("#1d1d1d"), 4))
        p.setBrush(QColor("#d7d7d7"))
        p.drawEllipse(118, 36, 55, 55)
        p.drawEllipse(438, 36, 55, 55)
        p.setBrush(QColor("#333"))
        p.drawEllipse(137, 55, 17, 17)
        p.drawEllipse(457, 55, 17, 17)
        p.setPen(QPen(QColor("#d2c31b"), 3))
        p.drawLine(170, 64, 440, 64)
        p.setBrush(QColor("#23282d"))
        p.setPen(QPen(QColor("#0c0c0c"), 3))
        p.drawRoundedRect(245, 170, 120, 60, 8, 8)
        p.setPen(QColor("#67ff76"))
        p.setFont(QFont("Courier New", 18, QFont.Bold))
        p.drawText(260, 208, f"{self.value:04.1f}")
        p.setPen(QColor("#333"))
        p.setFont(QFont("Arial", 11, QFont.Bold))
        p.drawText(190, 335, "SCHÉMA SIMPLIFIÉ DE LA SP55")


class ClassicWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.state = State()
        self.setWindowTitle("DMS SP55 — Interface de commande")
        self.setFixedSize(1024, 768)
        self.setStyleSheet("QMainWindow{background:#102f58;} QLabel{font-family:Arial;}")

        central = QWidget()
        self.setCentralWidget(central)

        header = QLabel("DMS   —   CORDEUSE ÉLECTRONIQUE SP55", central)
        header.setGeometry(18, 12, 988, 58)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #e9edf2,stop:1 #8997a5);"
            "border:3px outset #e6e6e6; color:#153863; font:bold 27px Arial;"
        )

        self.pages = QStackedWidget(central)
        self.pages.setGeometry(18, 82, 790, 620)
        self.pages.addWidget(self._control_page())
        self.pages.addWidget(self._settings_page())
        self.pages.addWidget(self._diagnostic_page())

        nav = QFrame(central)
        nav.setGeometry(820, 82, 186, 620)
        nav.setStyleSheet("background:#c4c9ce; border:3px outset #f3f3f3;")
        buttons = [
            ("COMMANDE", 0),
            ("RÉGLAGES", 1),
            ("DIAGNOSTIC", 2),
        ]
        y = 22
        for text, index in buttons:
            b = self._button(text, nav)
            b.setGeometry(16, y, 154, 66)
            b.clicked.connect(lambda _, i=index: self.pages.setCurrentIndex(i))
            y += 82

        stop = self._button("ARRÊT\nD'URGENCE", nav, red=True)
        stop.setGeometry(16, 360, 154, 105)
        stop.clicked.connect(self.release)

        quit_button = self._button("QUITTER", nav)
        quit_button.setGeometry(16, 525, 154, 58)
        quit_button.clicked.connect(self.close)

        footer = QLabel("Mode démonstration — communication Arduino non activée", central)
        footer.setGeometry(18, 714, 988, 35)
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("background:#081b33;color:#dce7f2;border:2px inset #678;font:bold 13px Arial;")

        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

    def _panel(self, parent, x, y, w, h, title):
        panel = QFrame(parent)
        panel.setGeometry(x, y, w, h)
        panel.setStyleSheet("background:#c9cdd0;border:3px outset #f2f2f2;")
        label = QLabel(title, panel)
        label.setGeometry(8, 7, w - 16, 28)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background:#173d69;color:white;border:2px inset #91a4ba;font:bold 14px Arial;")
        return panel

    def _button(self, text, parent, red=False):
        button = QPushButton(text, parent)
        base = "#b52a2a" if red else "#d4d7da"
        hover = "#d63b3b" if red else "#eef0f2"
        color = "white" if red else "#17385d"
        button.setStyleSheet(
            f"QPushButton{{background:{base};color:{color};border:4px outset #eee;"
            "font:bold 15px Arial;}"
            f"QPushButton:hover{{background:{hover};}}"
            "QPushButton:pressed{border-style:inset;}"
        )
        return button

    def _display(self, parent, x, y, w, h, text="00.0"):
        label = QLabel(text, parent)
        label.setGeometry(x, y, w, h)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            "background:#07120b;color:#61ff70;border:4px inset #777;"
            "font:bold 42px 'Courier New';"
        )
        return label

    def _control_page(self):
        page = QWidget()
        page.setStyleSheet("background:#7e8993;")

        machine_panel = self._panel(page, 8, 8, 500, 390, "VISUALISATION DE LA MACHINE")
        self.machine = MachineDrawing(machine_panel)
        self.machine.setGeometry(10, 40, 480, 338)

        target = self._panel(page, 520, 8, 260, 210, "TENSION DE CONSIGNE")
        self.target_display = self._display(target, 26, 50, 208, 72, "25.0 kg")
        minus = self._button("−", target)
        minus.setGeometry(26, 138, 92, 52)
        minus.clicked.connect(lambda: self.change_target(-0.5))
        plus = self._button("+", target)
        plus.setGeometry(142, 138, 92, 52)
        plus.clicked.connect(lambda: self.change_target(0.5))

        measure = self._panel(page, 520, 230, 260, 168, "TENSION MESURÉE")
        self.measure_display = self._display(measure, 26, 55, 208, 78, "00.0 kg")

        params = self._panel(page, 8, 410, 500, 200, "PARAMÈTRES DE TIRAGE")
        QLabel("Pré-étirage", params).setGeometry(20, 50, 110, 28)
        QLabel("Nœud", params).setGeometry(20, 96, 110, 28)
        QLabel("Vitesse", params).setGeometry(20, 142, 110, 28)
        self.pre_led = Led("0 %", True, params); self.pre_led.move(145, 50)
        self.knot_led = Led("+10 %", True, params); self.knot_led.move(145, 96)
        self.speed_led = Led("VITESSE 2", True, params); self.speed_led.move(145, 142)
        for y, callback in [(50, self.cycle_pre), (96, self.cycle_knot), (142, self.cycle_speed)]:
            b = self._button("MODIFIER", params)
            b.setGeometry(300, y - 2, 170, 34)
            b.clicked.connect(callback)

        actions = self._panel(page, 520, 410, 260, 200, "COMMANDE")
        self.start = self._button("DÉMARRER\nLE TIRAGE", actions)
        self.start.setGeometry(25, 50, 210, 66)
        self.start.clicked.connect(self.toggle)
        release = self._button("RELÂCHER", actions)
        release.setGeometry(25, 126, 210, 48)
        release.clicked.connect(self.release)
        self.counter = QLabel("Cordes tirées : 0", actions)
        self.counter.setGeometry(25, 174, 210, 22)
        self.counter.setAlignment(Qt.AlignCenter)
        self.counter.setStyleSheet("font:bold 13px Arial;color:#20364e;")
        return page

    def _settings_page(self):
        page = QWidget(); page.setStyleSheet("background:#7e8993;")
        title = QLabel("RÉGLAGES GÉNÉRAUX", page)
        title.setGeometry(10, 12, 770, 48)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("background:#173d69;color:white;border:3px outset #aac;font:bold 22px Arial;")
        entries = ["UNITÉ : kg", "CONTRASTE AFFICHEUR", "CALIBRATION CAPTEUR", "PORT DE COMMUNICATION", "RETOUR PARAMÈTRES USINE"]
        y = 90
        for text in entries:
            b = self._button(text, page)
            b.setGeometry(135, y, 520, 72)
            y += 92
        return page

    def _diagnostic_page(self):
        page = QWidget(); page.setStyleSheet("background:#7e8993;")
        title = QLabel("DIAGNOSTIC ENTRÉES / SORTIES", page)
        title.setGeometry(10, 12, 770, 48)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("background:#173d69;color:white;border:3px outset #aac;font:bold 22px Arial;")
        names = ["ARDUINO MEGA", "CAPTEUR D'EFFORT", "FIN DE COURSE AVANT", "FIN DE COURSE ARRIÈRE", "COMMANDE MOTEUR", "ARRÊT D'URGENCE"]
        y = 92
        for i, name in enumerate(names):
            label = QLabel(name, page)
            label.setGeometry(120, y, 300, 42)
            label.setStyleSheet("background:#cbd0d4;border:2px inset #eee;padding-left:15px;font:bold 14px Arial;color:#17385d;")
            led = Led("OK" if i in (1, 2, 3) else "SIMULATION", i in (1, 2, 3), page)
            led.move(465, y + 7)
            y += 72
        return page

    def change_target(self, delta):
        self.state.consigne = max(5.0, min(40.0, self.state.consigne + delta))
        self.target_display.setText(f"{self.state.consigne:04.1f} kg")

    def cycle_pre(self):
        values = [0, 10, 20]
        self.state.pre_etirage = values[(values.index(self.state.pre_etirage) + 1) % len(values)]
        self.pre_led.setText(f"{self.state.pre_etirage} %")

    def cycle_knot(self):
        values = [0, 10, 20]
        self.state.noeud = values[(values.index(self.state.noeud) + 1) % len(values)]
        self.knot_led.setText(f"+{self.state.noeud} %")

    def cycle_speed(self):
        self.state.vitesse = self.state.vitesse % 3 + 1
        self.speed_led.setText(f"VITESSE {self.state.vitesse}")

    def toggle(self):
        self.state.actif = not self.state.actif
        self.state.temps = 0.0
        self.start.setText("ARRÊTER\nLE TIRAGE" if self.state.actif else "DÉMARRER\nLE TIRAGE")

    def release(self):
        self.state.actif = False
        self.state.mesure = 0.0
        self.start.setText("DÉMARRER\nLE TIRAGE")

    def tick(self):
        if self.state.actif:
            self.state.temps += 0.05
            target = self.state.consigne * (1 + self.state.pre_etirage / 100)
            self.state.mesure += (target - self.state.mesure) * (0.035 + 0.025 * self.state.vitesse)
            if self.state.temps > 2.5:
                self.state.actif = False
                self.state.cordes += 1
                self.start.setText("DÉMARRER\nLE TIRAGE")
        else:
            self.state.mesure *= 0.91
            if self.state.mesure < 0.03:
                self.state.mesure = 0.0
        self.measure_display.setText(f"{self.state.mesure:04.1f} kg")
        self.machine.set_value(self.state.mesure)
        self.counter.setText(f"Cordes tirées : {self.state.cordes}")


def main():
    app = QApplication(sys.argv)
    window = ClassicWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
