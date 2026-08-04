from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFrame, QPushButton, QSizePolicy


SIDE_BUTTONS = {
    "Nouveau": ("＋  Nouveau", "Créer une nouvelle étude"),
    "Ouvrir": ("□  Ouvrir", "Ouvrir un fichier de mesures"),
    "Sauver": ("▤  Enregistrer", "Enregistrer l'étude"),
    "Effacer": ("×  Effacer", "Effacer la sélection"),
    "Mesures": ("●  Mesures", "Mesures"),
    "Courbes": ("⌁  Courbes", "Afficher les courbes"),
    "Mode de commande": ("↻  Commande", "Mode de commande"),
}


def _style_side_button(button: QPushButton, highlighted: bool = False) -> None:
    background = "#eef4ff" if highlighted else "white"
    color = "#1558d6" if highlighted else "#24324a"
    border = "#b7cff5" if highlighted else "#d8dee9"
    button.setMinimumHeight(44)
    button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    button.setStyleSheet(
        "QPushButton{"
        f"background:{background};color:{color};border:1px solid {border};"
        "border-radius:9px;text-align:left;padding:8px 9px;"
        "font:600 11px 'Segoe UI';}"
        "QPushButton:hover{background:#eef4ff;color:#1558d6;border-color:#9bbcf2}"
    )


def install_visual_fixes(choice_window_class, machine_diagram_class) -> None:
    """Applique les corrections visuelles sans modifier la logique métier."""

    original_build_ui = choice_window_class._build_ui

    def build_ui(self) -> None:
        original_build_ui(self)

        # Une hauteur minimale trop importante provoquait le rognage des deux
        # dernières rangées sur les écrans de 900 px avec la barre Calibration.
        self.setMinimumSize(1180, 720)
        self.diagram.setMinimumSize(700, 520)

        side_frame: QFrame | None = None
        for button in self.findChildren(QPushButton):
            tooltip = button.toolTip()
            if tooltip in SIDE_BUTTONS:
                text, new_tooltip = SIDE_BUTTONS[tooltip]
                button.setText(text)
                button.setToolTip(new_tooltip)
                _style_side_button(button, tooltip == "Mode de commande")
                if isinstance(button.parentWidget(), QFrame):
                    side_frame = button.parentWidget()

        # Le bouton des réglages doit rester identifiable par l'intégration
        # série, même si son texte devient explicite.
        for button in self.findChildren(QPushButton):
            if button.text() == "⚙":
                button.setText("⚙  Réglages")
                button.setToolTip("Configuration des liaisons série")
                button.setObjectName("serialSettingsButton")
                _style_side_button(button)
                if isinstance(button.parentWidget(), QFrame):
                    side_frame = button.parentWidget()
                break

        if side_frame is not None:
            side_frame.setFixedWidth(128)
            layout = side_frame.layout()
            if layout is not None:
                layout.setContentsMargins(10, 10, 10, 10)
                layout.setSpacing(7)

    choice_window_class._build_ui = build_ui

    # Le dessin original laissait volontairement un vide entre les deux
    # segments de corde au-dessus du chariot. On complète uniquement ce vide.
    original_paint_event = machine_diagram_class.paintEvent

    def paint_event(self, event) -> None:
        original_paint_event(self, event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor("#6b7280"), 2))

        top = 90
        left = 36
        right = self.width() - 36
        machine_center = left + (right - left) // 2
        carriage_left = machine_center - 70
        carriage_right = carriage_left + 140
        rope_y = top + 64
        painter.drawLine(carriage_left - 15, rope_y, carriage_right, rope_y)
        painter.end()

    machine_diagram_class.paintEvent = paint_event
