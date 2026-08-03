from __future__ import annotations

import math
import sys
from dataclasses import dataclass

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QSizePolicy, QStackedWidget,
    QVBoxLayout, QWidget,
)

STYLE = """
QMainWindow,QWidget{background:#20262c;color:#eef2f5;font-family:Arial}
QFrame#panel{background:#2c343c;border:2px solid #11161a;border-radius:8px}
QLabel#title{font-size:28px;font-weight:700}
QLabel#subtitle{color:#aab5be;font-size:13px}
QLabel#digital{background:#07100b;color:#64ff92;border:3px inset #56625c;
border-radius:5px;font:700 48px Consolas;padding:8px 14px}
QPushButton{min-height:46px;background:#46525d;color:white;border:2px outset #6a7883;
border-radius:6px;padding:6px 12px;font-size:15px;font-weight:700}
QPushButton:hover{background:#586773} QPushButton:pressed{border-style:inset;background:#303941}
QPushButton:checked{background:#155b87;border-color:#55b6e9}
QPushButton#danger{background:#991f1f;border-color:#df6262}
QPushButton#action{background:#146d3e;border-color:#50c880}
QPushButton#key{min-width:72px;font-size:22px}
QLabel#ok{color:#67e58d;font-weight:700} QLabel#warn{color:#ffcc66;font-weight:700}
"""


@dataclass
class State:
    target: float = 25.0
    measured: float = 0.0
    prestretch: int = 0
    knots: int = 10
    speed: int = 2
    running: bool = False
    elapsed: float = 0.0
    count: int = 0


class Gauge(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.value = 0.0
        self.setMinimumSize(280, 220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_value(self, value: float) -> None:
        self.value = max(0.0, min(40.0, value))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(20, 15, -20, -10)
        c = r.center()
        radius = min(r.width(), r.height()) * 0.43
        for width, color in ((18, "#0d1013"), (13, "#53636f")):
            p.setPen(QPen(QColor(color), width, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(int(c.x()-radius), int(c.y()-radius), int(2*radius), int(2*radius), 30*16, 120*16)
        for i in range(9):
            angle = math.radians(210-i*15)
            inner = radius-(18 if i % 2 == 0 else 12)
            x1, y1 = c.x()+math.cos(angle)*inner, c.y()-math.sin(angle)*inner
            x2, y2 = c.x()+math.cos(angle)*(radius+2), c.y()-math.sin(angle)*(radius+2)
            p.setPen(QPen(QColor("#e0e6ea"), 2))
            p.drawLine(int(x1), int(y1), int(x2), int(y2))
            if i % 2 == 0:
                tx, ty = c.x()+math.cos(angle)*(radius-38), c.y()-math.sin(angle)*(radius-38)
                p.setFont(QFont("Arial", 9, QFont.Bold))
                p.drawText(int(tx-12), int(ty-8), 24, 16, Qt.AlignCenter, str(i*5))
        angle = math.radians(210-(self.value/40.0)*120)
        nx, ny = c.x()+math.cos(angle)*(radius-28), c.y()-math.sin(angle)*(radius-28)
        p.setPen(QPen(QColor("#ef4444"), 5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(c.x(), c.y(), int(nx), int(ny))
        p.setBrush(QColor("#ef4444")); p.setPen(Qt.NoPen); p.drawEllipse(c, 9, 9)
        p.setPen(QColor("#edf2f6")); p.setFont(QFont("Arial", 13, QFont.Bold))
        p.drawText(r.adjusted(0, 125, 0, 0), Qt.AlignHCenter | Qt.AlignTop, "TENSION MESURÉE")


class ControlPage(QWidget):
    def __init__(self, state: State) -> None:
        super().__init__(); self.state = state
        grid = QGridLayout(self); grid.setContentsMargins(18,18,18,18); grid.setSpacing(14)
        grid.addWidget(self._target_panel(), 0, 0, 2, 1)
        grid.addWidget(self._gauge_panel(), 0, 1, 2, 1)
        grid.addWidget(self._parameters_panel(), 0, 2)
        grid.addWidget(self._actions_panel(), 1, 2)
        grid.setColumnStretch(0,3); grid.setColumnStretch(1,4); grid.setColumnStretch(2,3)
        self.timer = QTimer(self); self.timer.setInterval(50); self.timer.timeout.connect(self.simulate); self.timer.start()

    def _panel(self) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame(); frame.setObjectName("panel"); return frame, QVBoxLayout(frame)

    def _target_panel(self) -> QFrame:
        f, l = self._panel(); title = QLabel("CONSIGNE DE TENSION"); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:16px;font-weight:700")
        self.target_display = QLabel(); self.target_display.setObjectName("digital"); self.target_display.setAlignment(Qt.AlignCenter)
        row = QHBoxLayout()
        for text, delta in (("−",-0.5),("+",0.5)):
            b=QPushButton(text); b.setObjectName("key"); b.clicked.connect(lambda _, d=delta:self.change_target(d)); row.addWidget(b)
        l.addWidget(title); l.addWidget(self.target_display); l.addLayout(row); self.refresh_target(); return f

    def _gauge_panel(self) -> QFrame:
        f,l=self._panel(); self.gauge=Gauge(); self.measured=QLabel("00.0 kg")
        self.measured.setObjectName("digital"); self.measured.setAlignment(Qt.AlignCenter)
        l.addWidget(self.gauge,1); l.addWidget(self.measured); return f

    def _choice(self, title: str, labels: list[str], selected: int, callback) -> QWidget:
        w=QWidget(); l=QVBoxLayout(w); t=QLabel(title); t.setStyleSheet("font-weight:700"); row=QHBoxLayout(); group=QButtonGroup(w)
        for i,text in enumerate(labels):
            b=QPushButton(text); b.setCheckable(True); b.setChecked(i==selected); b.clicked.connect(lambda _,x=i:callback(x)); group.addButton(b); row.addWidget(b)
        l.addWidget(t); l.addLayout(row); return w

    def _parameters_panel(self) -> QFrame:
        f,l=self._panel()
        l.addWidget(self._choice("PRÉ-ÉTIRAGE",["0 %","10 %","20 %"],0,lambda i:setattr(self.state,"prestretch",[0,10,20][i])))
        l.addWidget(self._choice("NŒUD",["+0 %","+10 %","+20 %"],1,lambda i:setattr(self.state,"knots",[0,10,20][i])))
        l.addWidget(self._choice("VITESSE",["1","2","3"],1,lambda i:setattr(self.state,"speed",i+1))); l.addStretch(); return f

    def _actions_panel(self) -> QFrame:
        f,l=self._panel(); self.start=QPushButton("DÉMARRER LE TIRAGE"); self.start.setObjectName("action"); self.start.clicked.connect(self.toggle)
        release=QPushButton("RELÂCHER"); release.clicked.connect(self.release)
        self.counter=QLabel("CORDES TIRÉES : 0"); self.counter.setAlignment(Qt.AlignCenter); self.counter.setStyleSheet("font-size:18px;font-weight:700")
        l.addWidget(self.start); l.addWidget(release); l.addWidget(self.counter); return f

    def change_target(self, delta: float) -> None:
        self.state.target=max(0.0,min(40.0,self.state.target+delta)); self.refresh_target()

    def refresh_target(self) -> None: self.target_display.setText(f"{self.state.target:04.1f} kg")

    def _style_start(self) -> None:
        self.start.setText("ARRÊTER LE TIRAGE" if self.state.running else "DÉMARRER LE TIRAGE")
        self.start.setObjectName("danger" if self.state.running else "action"); self.start.style().unpolish(self.start); self.start.style().polish(self.start)

    def toggle(self) -> None: self.state.running=not self.state.running; self.state.elapsed=0.0; self._style_start()
    def release(self) -> None: self.state.running=False; self.state.measured=0.0; self._style_start()

    def simulate(self) -> None:
        target=self.state.target*(1+self.state.prestretch/100)
        if self.state.running:
            self.state.elapsed+=0.05; delta=target-self.state.measured; self.state.measured+=delta*[0.045,0.075,0.11][self.state.speed-1]
            if self.state.elapsed>2.2:
                self.state.running=False; self.state.count+=1; self._style_start()
        else:
            self.state.measured*=0.92
            if self.state.measured<0.03:self.state.measured=0.0
        self.gauge.set_value(self.state.measured); self.measured.setText(f"{self.state.measured:04.1f} kg"); self.counter.setText(f"CORDES TIRÉES : {self.state.count}")


class SimplePage(QWidget):
    def __init__(self, title: str, entries: list[tuple[str,str]]) -> None:
        super().__init__(); grid=QGridLayout(self); grid.setContentsMargins(24,24,24,24); grid.setSpacing(16)
        heading=QLabel(title); heading.setObjectName("title"); grid.addWidget(heading,0,0,1,2)
        for i,(name,value) in enumerate(entries):
            f=QFrame(); f.setObjectName("panel"); l=QVBoxLayout(f); n=QLabel(name); n.setStyleSheet("font-size:16px;font-weight:700"); b=QPushButton(value)
            b.clicked.connect(lambda _,x=name:QMessageBox.information(self,x,"Fonction prévue pour une prochaine itération.")); l.addWidget(n); l.addWidget(b); grid.addWidget(f,1+i//2,i%2)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__(); self.setWindowTitle("DMS SP55 — Interface de commande"); self.resize(1280,760); self.setMinimumSize(1024,650); state=State()
        central=QWidget(); self.setCentralWidget(central); root=QVBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        header=QFrame(); header.setStyleSheet("background:#151a1f;border-bottom:2px solid #080a0c"); h=QHBoxLayout(header); brand=QVBoxLayout()
        title=QLabel("DMS SP55"); title.setObjectName("title"); subtitle=QLabel("CORDEUSE DE RAQUETTES — INTERFACE DE COMMANDE"); subtitle.setObjectName("subtitle")
        brand.addWidget(title); brand.addWidget(subtitle); h.addLayout(brand); h.addStretch(); status=QLabel("● MODE SIMULATION"); status.setObjectName("ok"); h.addWidget(status); root.addWidget(header)
        body=QHBoxLayout(); body.setContentsMargins(0,0,0,0); body.setSpacing(0); nav=QFrame(); nav.setFixedWidth(210); nav.setStyleSheet("background:#181e24;border-right:2px solid #0d1115"); nl=QVBoxLayout(nav); nl.setContentsMargins(12,18,12,18)
        self.pages=QStackedWidget(); self.pages.addWidget(ControlPage(state)); self.pages.addWidget(SimplePage("RÉGLAGES",[("UNITÉ","kg / lb"),("CALIBRATION","Accès protégé"),("COMMUNICATION","Non configurée"),("MODE","Simulation")]))
        self.pages.addWidget(SimplePage("DIAGNOSTIC",[("CAPTEUR D'EFFORT","Simulation"),("FINS DE COURSE","Inactives"),("COMMANDE MOTEUR","Simulation"),("ARDUINO MEGA","Non connecté")]))
        group=QButtonGroup(self)
        for text,index in (("COMMANDE",0),("RÉGLAGES",1),("DIAGNOSTIC",2)):
            b=QPushButton(text); b.setCheckable(True); b.setChecked(index==0); b.clicked.connect(lambda _,i=index:self.pages.setCurrentIndex(i)); group.addButton(b); nl.addWidget(b)
        nl.addStretch(); quit_button=QPushButton("QUITTER"); quit_button.setObjectName("danger"); quit_button.clicked.connect(self.close); nl.addWidget(quit_button)
        body.addWidget(nav); body.addWidget(self.pages,1); root.addLayout(body,1)

    def closeEvent(self,event) -> None:  # noqa: N802
        answer=QMessageBox.question(self,"Quitter","Fermer l’interface SP55 ?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        event.accept() if answer==QMessageBox.Yes else event.ignore()


def main() -> int:
    app=QApplication(sys.argv); app.setStyleSheet(STYLE); window=MainWindow(); window.show(); return app.exec()


if __name__ == "__main__": raise SystemExit(main())
