from __future__ import annotations

import base64
import sys
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication,QCheckBox,QFrame,QGridLayout,QHBoxLayout,QHeaderView,QLabel,QMainWindow,QMessageBox,QPushButton,QSizePolicy,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget)


class SelectionMode(Enum):
    NONE = auto(); ABSCISSA = auto(); ORDINATE = auto()


@dataclass(frozen=True)
class Parameter:
    code: str; label: str; unit: str; color: str; symbol: str


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
QMainWindow,QWidget#root{background:#f3f6fb;color:#172033}QFrame#card{background:white;border:1px solid #dfe6ef;border-radius:14px}
QLabel#title{font:700 24px 'Segoe UI';color:#172033}QLabel#subtitle{font:12px 'Segoe UI';color:#667085}QLabel#section{font:600 13px 'Segoe UI';color:#344054}
QLabel#status{background:#edf4ff;border:1px solid #d7e6ff;border-radius:10px;padding:9px 12px;color:#2457a7}
QPushButton{background:white;border:1px solid #d8dee9;border-radius:9px;padding:8px 12px;font:12px 'Segoe UI';color:#24324a}
QPushButton:hover{background:#f6f9ff;border-color:#9bbcf2}QPushButton#primary{background:#2563eb;color:white;border:none;font-weight:600}QPushButton#danger{color:#b42318;background:#fff7f6;border-color:#f2c9c5}
QPushButton#modeActive{background:#eaf2ff;color:#1558d6;border-color:#8fb5ef;font-weight:600}
QTableWidget{background:white;border:1px solid #e0e6ef;border-radius:9px;gridline-color:#eef1f5;selection-background-color:#dce9ff;selection-color:#173b75}
QHeaderView::section{background:#f8fafc;border:0;border-bottom:1px solid #e5eaf1;padding:7px;font-weight:600}QCheckBox{spacing:8px;font:12px 'Segoe UI'}
"""


class ModernButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text,parent); self.setCursor(Qt.PointingHandCursor)


def icon_for(p: Parameter) -> QIcon:
    pm=QPixmap(30,30); pm.fill(Qt.transparent); q=QPainter(pm); q.setRenderHint(QPainter.Antialiasing)
    q.setPen(Qt.NoPen); q.setBrush(QColor(p.color)); q.drawRoundedRect(1,1,28,28,7,7)
    q.setPen(QColor("white")); f=QFont("Segoe UI Symbol",13); f.setBold(True); q.setFont(f); q.drawText(pm.rect(),Qt.AlignCenter,p.symbol); q.end(); return QIcon(pm)


class ParameterButton(ModernButton):
    selected=Signal(str)
    def __init__(self,key,parent):
        p=PARAMETERS[key]; super().__init__(f"{p.code}\n{p.label}",parent); self.key=key
        self.setIcon(icon_for(p)); self.setIconSize(QSize(28,28)); self.setToolTip(f"{p.label} ({p.unit})" if p.unit else p.label)
        self.setStyleSheet(f"QPushButton{{background:white;border:1px solid #dce3ec;border-left:4px solid {p.color};border-radius:9px;padding:4px 7px;text-align:left;font:600 11px 'Segoe UI'}}QPushButton:hover{{background:#f7faff;border-color:#9bbcf2}}")
        self.clicked.connect(lambda:self.selected.emit(self.key))


class MachineDiagram(QWidget):
    parameter_selected=Signal(str)
    def __init__(self):
        super().__init__(); self.setMinimumSize(760,560); self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding); self.buttons={}
        path=Path(__file__).resolve().parent/"assets"/"machine_sp55.b64"
        self.pixmap=QPixmap(); self.pixmap.loadFromData(base64.b64decode(path.read_text(encoding="ascii")),"JPG")
        for key,rect in {
            "Fc":QRect(18,14,132,52),"U":QRect(486,14,116,52),"I":QRect(610,14,116,52),
            "Er":QRect(28,420,124,52),"theta_red":QRect(600,420,132,52),
            "formula":QRect(8,492,84,54),"t":QRect(97,492,72,54),"Fr":QRect(174,492,78,54),"Dch":QRect(257,492,92,54),
            "Vch":QRect(354,492,88,54),"theta_m":QRect(447,492,88,54),"omega_m":QRect(540,492,92,54),"omega_red":QRect(637,492,100,54)}.items():
            b=ParameterButton(key,self); b.setGeometry(rect); b.selected.connect(self.parameter_selected); self.buttons[key]=b
    def resizeEvent(self,event):
        super().resizeEvent(event); w=self.width(); h=self.height(); self.buttons["U"].move(max(390,w-278),14); self.buttons["I"].move(max(515,w-154),14)
        self.buttons["Er"].move(28,h-140); self.buttons["theta_red"].move(max(560,w-142),h-140); x=8; y=h-68
        for k in ["formula","t","Fr","Dch","Vch","theta_m","omega_m","omega_red"]: self.buttons[k].move(x,y); x+=self.buttons[k].width()+5
    def paintEvent(self,event):
        super().paintEvent(event); q=QPainter(self); q.setRenderHint(QPainter.SmoothPixmapTransform); q.fillRect(self.rect(),QColor("#fbfcfe"))
        r=QRect(28,82,self.width()-56,self.height()-236); q.setPen(QPen(QColor("#d8e0ea"),1)); q.setBrush(QColor("#eef2f7")); q.drawRoundedRect(r.adjusted(-8,-8,8,8),14,14)
        pm=self.pixmap.scaled(r.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation); q.drawPixmap(r.x()+(r.width()-pm.width())//2,r.y()+(r.height()-pm.height())//2,pm)


class ChoiceWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.mode=SelectionMode.NONE; self.abscissa_key="t"; self.ordinate_keys=["Fr","Er","Fc"]
        self.setWindowTitle("Cordeuse de raquettes SP55 — Modern UI")
        s=QGuiApplication.primaryScreen(); g=s.availableGeometry() if s else None
        self.resize(max(1320,min(int(g.width()*.93),1680)) if g else 1440,max(790,min(int(g.height()*.90),980)) if g else 860); self.setMinimumSize(1240,740); self.setStyleSheet(STYLE)
        self._build_ui(); self._refresh()
    def _card(self): f=QFrame(); f.setObjectName("card"); return f
    def _build_ui(self):
        root=QWidget(); root.setObjectName("root"); self.setCentralWidget(root); outer=QHBoxLayout(root); outer.setContentsMargins(18,18,18,18); outer.setSpacing(16)
        side=self._card(); side.setFixedWidth(92); sl=QVBoxLayout(side); brand=QLabel("SP55"); brand.setAlignment(Qt.AlignCenter); brand.setStyleSheet("font:700 19px 'Segoe UI';color:#1558d6;padding:8px"); sl.addWidget(brand)
        for sym,tip in [("＋","Nouveau"),("▣","Ouvrir"),("▤","Sauver"),("✕","Effacer"),("◉","Mesures"),("⌁","Courbes")]: b=ModernButton(sym); b.setToolTip(tip); b.setFixedHeight(50); b.setStyleSheet("font-size:20px"); sl.addWidget(b)
        sl.addStretch(); sl.addWidget(ModernButton("⚙")); outer.addWidget(side)
        content=QVBoxLayout(); content.setSpacing(14); outer.addLayout(content,1); t=QLabel("Choix des paramètres"); t.setObjectName("title"); st=QLabel("Sélectionnez les grandeurs à visualiser sur le schéma réel de la cordeuse SP55."); st.setObjectName("subtitle"); content.addWidget(t); content.addWidget(st)
        body=QHBoxLayout(); body.setSpacing(14); content.addLayout(body,1); mc=self._card(); ml=QVBoxLayout(mc); self.diagram=MachineDiagram(); self.diagram.parameter_selected.connect(self.parameter_clicked); ml.addWidget(self.diagram); body.addWidget(mc,5)
        right=QVBoxLayout(); right.setSpacing(14); body.addLayout(right,3); sc=self._card(); sL=QVBoxLayout(sc); sec=QLabel("Paramètres d’affichage"); sec.setObjectName("section"); sL.addWidget(sec)
        modes=QHBoxLayout(); self.abscissa_button=ModernButton("→ Abscisse"); self.ordinate_button=ModernButton("↑ Ordonnée"); self.abscissa_button.clicked.connect(lambda:self.set_mode(SelectionMode.ABSCISSA)); self.ordinate_button.clicked.connect(lambda:self.set_mode(SelectionMode.ORDINATE)); modes.addWidget(self.abscissa_button); modes.addWidget(self.ordinate_button); sL.addLayout(modes)
        self.abscissa_label=QLabel(); self.abscissa_label.setStyleSheet("background:#f8fafc;border:1px solid #e1e7ef;border-radius:8px;padding:9px;font-weight:600"); sL.addWidget(self.abscissa_label)
        row=QHBoxLayout(); row.addWidget(QLabel("Ordonnées sélectionnées")); row.addStretch(); self.delete_button=ModernButton("Supprimer"); self.delete_button.setObjectName("danger"); self.delete_button.clicked.connect(self.remove_ordinate); row.addWidget(self.delete_button); sL.addLayout(row)
        self.table=QTableWidget(0,2); self.table.setHorizontalHeaderLabels(["N°","Paramètre"]); self.table.verticalHeader().setVisible(False); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeToContents); self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch); sL.addWidget(self.table,1)
        actions=QHBoxLayout(); self.trace_button=ModernButton("Tracer les courbes"); self.trace_button.setObjectName("primary"); self.trace_button.clicked.connect(self.trace); actions.addWidget(self.trace_button,2); actions.addWidget(ModernButton("Éditer"),1); sL.addLayout(actions); right.addWidget(sc,3)
        meas=self._card(); mL=QVBoxLayout(meas); mh=QHBoxLayout(); mt=QLabel("Mesures"); mt.setObjectName("section"); mh.addWidget(mt); mh.addStretch(); clear=ModernButton("Tout désélectionner"); clear.clicked.connect(self.clear_measures); reset=ModernButton("Réinitialiser"); reset.clicked.connect(self.restore_default); mh.addWidget(clear); mh.addWidget(reset); mL.addLayout(mh)
        grid=QGridLayout(); self.measure_checks=[]
        for i in range(1,11): c=QCheckBox(f"Mesure n°{i}"); c.setChecked(i==1); c.stateChanged.connect(self._refresh_trace_state); self.measure_checks.append(c); grid.addWidget(c,(i-1)//2,(i-1)%2)
        mL.addLayout(grid); right.addWidget(meas,2)
        foot=QHBoxLayout(); self.status=QLabel("Cliquez sur Abscisse ou Ordonnée puis sur une grandeur."); self.status.setObjectName("status"); foot.addWidget(self.status,1); helpb=ModernButton("Aide"); helpb.clicked.connect(self.show_help); close=ModernButton("Fermer"); close.clicked.connect(self.close); foot.addWidget(helpb); foot.addWidget(close); content.addLayout(foot)
    def set_mode(self,mode):
        self.mode=mode; self.abscissa_button.setObjectName("modeActive" if mode is SelectionMode.ABSCISSA else ""); self.ordinate_button.setObjectName("modeActive" if mode is SelectionMode.ORDINATE else "")
        for b in (self.abscissa_button,self.ordinate_button): b.style().unpolish(b); b.style().polish(b)
        self.status.setText("Sélection de l'abscisse : cliquez sur une grandeur du schéma." if mode is SelectionMode.ABSCISSA else "Sélection des ordonnées : cliquez sur une ou plusieurs grandeurs." if mode is SelectionMode.ORDINATE else self.status.text())
    def parameter_clicked(self,key):
        if self.mode is SelectionMode.ABSCISSA: self.abscissa_key=key; self.mode=SelectionMode.NONE; self.status.setText(f"Abscisse sélectionnée : {self.parameter_text(key)}")
        elif self.mode is SelectionMode.ORDINATE:
            if key!=self.abscissa_key and key not in self.ordinate_keys: self.ordinate_keys.append(key)
            self.status.setText(f"Ordonnée ajoutée : {self.parameter_text(key)}")
        else: self.status.setText(f"{PARAMETERS[key].label} — unité : {PARAMETERS[key].unit or 'sans unité'}")
        self._refresh()
    @staticmethod
    def parameter_text(key): p=PARAMETERS[key]; return f"{p.label} ({p.unit})" if p.unit else p.label
    def remove_ordinate(self):
        r=self.table.currentRow()
        if 0<=r<len(self.ordinate_keys): self.ordinate_keys.pop(r); self._refresh()
    def clear_measures(self):
        for c in self.measure_checks: c.setChecked(False)
    def restore_default(self):
        self.abscissa_key="t"; self.ordinate_keys=["Fr","Er","Fc"]
        for i,c in enumerate(self.measure_checks,1): c.setChecked(i==1)
        self._refresh()
    def show_help(self): QMessageBox.information(self,"Aide","1. Choisissez l'abscisse.\n2. Ajoutez les ordonnées.\n3. Cochez les mesures.\n4. Cliquez sur Tracer.")
    def trace(self): QMessageBox.information(self,"Tracer","Sélection prête pour le tracé.")
    def _refresh_trace_state(self): self.trace_button.setEnabled(bool(self.ordinate_keys) and any(c.isChecked() for c in self.measure_checks))
    def _refresh(self):
        self.abscissa_label.setText(self.parameter_text(self.abscissa_key)); self.table.setRowCount(len(self.ordinate_keys))
        for r,k in enumerate(self.ordinate_keys): self.table.setItem(r,0,QTableWidgetItem(str(r+1))); self.table.setItem(r,1,QTableWidgetItem(self.parameter_text(k)))
        if self.ordinate_keys: self.table.selectRow(0)
        self.delete_button.setEnabled(bool(self.ordinate_keys)); self._refresh_trace_state()


def main():
    app=QApplication(sys.argv); app.setStyle("Fusion"); app.setFont(QFont("Segoe UI",10)); w=ChoiceWindow(); w.show(); sys.exit(app.exec())


if __name__=="__main__": main()
