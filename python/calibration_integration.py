from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox, QToolBar

from calibration_config import default_calibration, load_or_create_calibration
from calibration_window import CalibrationDialog


def calibration_path() -> Path:
    """Retourne le fichier sp55.cfg placé à côté du programme lancé."""
    return Path(sys.argv[0]).resolve().parent / "sp55.cfg"


def install_calibration(application_class) -> None:
    original_init = application_class.__init__

    def patched_init(self, *args, **kwargs):
        path = calibration_path()
        created = False
        load_error: Exception | None = None
        try:
            config, created = load_or_create_calibration(path)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            # Un fichier existant mais invalide n'est jamais écrasé automatiquement.
            config = default_calibration()
            load_error = exc

        self.calibration_config = config
        self.calibration_path = path
        self.calibration_dialog = None

        original_init(self, *args, **kwargs)

        toolbar = QToolBar("Calibration", self)
        toolbar.setMovable(False)
        toolbar.setStyleSheet(
            "QToolBar{background:#f8fafc;border:0;border-bottom:1px solid #dfe6ef;spacing:8px;padding:5px}"
            "QToolButton{background:white;border:1px solid #d8dee9;border-radius:8px;padding:7px 12px;font:600 12px 'Segoe UI'}"
            "QToolButton:hover{background:#eef4ff;border-color:#9bbcf2}"
        )
        action = QAction("⚗  Calibration", self)
        action.setToolTip("Afficher et modifier la calibration des capteurs")
        action.triggered.connect(lambda: open_calibration(self))
        toolbar.addAction(action)
        self.addToolBar(toolbar)
        self.calibration_toolbar = toolbar

        if created:
            QTimer.singleShot(
                0,
                lambda: QMessageBox.warning(
                    self,
                    "Calibration nécessaire",
                    "Le fichier sp55.cfg était absent.\n\n"
                    "Un fichier de configuration de base a été créé avec les valeurs de référence fournies. "
                    "Il faut calibrer les capteurs avant toute utilisation réelle de la cordeuse.",
                ),
            )
        elif load_error is not None:
            QTimer.singleShot(
                0,
                lambda error=load_error: QMessageBox.critical(
                    self,
                    "Configuration illisible",
                    f"Le fichier {path.name} existe mais ne peut pas être lu :\n\n{error}\n\n"
                    "Il n'a pas été modifié. Les valeurs de référence sont chargées temporairement.",
                ),
            )

    application_class.__init__ = patched_init


def open_calibration(owner) -> None:
    dialog = CalibrationDialog(owner.calibration_config, owner.calibration_path, owner)
    owner.calibration_dialog = dialog
    if dialog.exec():
        owner.status.setText(
            f"Calibration chargée depuis {owner.calibration_path.name} — "
            f"{len(owner.calibration_config.sensors)} capteurs."
        )
