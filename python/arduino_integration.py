from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar

from arduino_measurement_window import ArduinoMeasurementWindow


def install_arduino_window(application_class) -> None:
    """Ajoute l'accès au pilotage et aux mesures Arduino Mega."""
    original_init = application_class.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.arduino_measurement_window = None
        toolbar = QToolBar("Arduino Mega", self)
        toolbar.setMovable(False)
        toolbar.setStyleSheet(
            "QToolBar{background:#f8fafc;border:0;border-bottom:1px solid #dfe6ef;spacing:8px;padding:5px}"
            "QToolButton{background:white;border:1px solid #d8dee9;border-radius:8px;padding:7px 12px;font:600 12px 'Segoe UI'}"
            "QToolButton:hover{background:#eef4ff;border-color:#9bbcf2}"
        )
        action = QAction("Arduino — mesures et pilotage", self)
        action.setToolTip("Afficher les mesures Arduino et piloter le cycle de traction")
        action.triggered.connect(lambda: open_arduino_window(self))
        toolbar.addAction(action)
        self.addToolBar(toolbar)
        self.arduino_toolbar = toolbar

    application_class.__init__ = patched_init


def open_arduino_window(owner) -> None:
    window = ArduinoMeasurementWindow(owner.serial_manager, owner)
    owner.arduino_measurement_window = window
    window.show()
    window.raise_()
    window.activateWindow()
