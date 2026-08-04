from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from app_icon import application_icon, ensure_icon_files, logo_pixmap


def install_logo(choice_window_class) -> None:
    """Installe le logo dans la fenêtre et comme icône de l'application."""
    if getattr(choice_window_class, "_sp55_logo_installed", False):
        return
    choice_window_class._sp55_logo_installed = True

    original_build_ui = choice_window_class._build_ui

    def build_ui(self) -> None:
        original_build_ui(self)
        icon = application_icon()
        self.setWindowIcon(icon)
        app = QApplication.instance()
        if app is not None:
            app.setWindowIcon(icon)

        for label in self.findChildren(QLabel):
            if label.text().strip() == "SP55":
                label.setText("")
                label.setPixmap(logo_pixmap(78))
                label.setAlignment(Qt.AlignCenter)
                label.setFixedHeight(84)
                label.setToolTip("Cordeuse de raquettes SP55")
                break

        ensure_icon_files()

    choice_window_class._build_ui = build_ui
