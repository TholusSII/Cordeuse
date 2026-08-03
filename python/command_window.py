from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from serial_controller import CommandSettings, available_ports, send_command


@dataclass
class PIDControl:
    slider: QSlider
    spinbox: QDoubleSpinBox


class CommandModeDialog(QDialog):
    """Fenêtre de sélection du mode de commande et des coefficients PID."""

    PID_MIN = 0.0
    PID_MAX = 1.0
    PID_STEP = 0.001
    SLIDER_MAX = 1000

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Mode de commande — SP55")
        self.setModal(True)
        self.resize(720, 620)
        self.setMinimumSize(680, 580)
        self.setStyleSheet(self._style())
        self.controls: dict[str, PIDControl] = {}
        self._build_ui()
        self.refresh_ports()
        self._mode_changed()

    @staticmethod
    def _style() -> str:
        return """
        QDialog { background:#f3f6fb; color:#172033; }
        QFrame#card, QGroupBox {
            background:white; border:1px solid #dfe6ef; border-radius:14px;
        }
        QGroupBox {
            margin-top:14px; padding:16px 14px 14px 14px;
            font:600 13px 'Segoe UI';
        }
        QGroupBox::title { subcontrol-origin:margin; left:14px; padding:0 6px; }
        QLabel#title { font:700 22px 'Segoe UI'; color:#172033; }
        QLabel#subtitle { font:12px 'Segoe UI'; color:#667085; }
        QLabel#warning {
            background:#fff7ed; border:1px solid #fed7aa; border-radius:10px;
            padding:10px; color:#9a3412;
        }
        QPushButton {
            background:white; border:1px solid #d8dee9; border-radius:9px;
            padding:9px 13px; font:12px 'Segoe UI'; color:#24324a;
        }
        QPushButton:hover { background:#f6f9ff; border-color:#9bbcf2; }
        QPushButton#primary { background:#2563eb; color:white; border:none; font-weight:600; }
        QPushButton#primary:hover { background:#1d4ed8; }
        QComboBox, QDoubleSpinBox {
            background:white; border:1px solid #d8dee9; border-radius:8px;
            padding:7px; min-height:22px;
        }
        QRadioButton { spacing:8px; font:12px 'Segoe UI'; }
        QSlider::groove:horizontal {
            height:6px; background:#dfe6ef; border-radius:3px;
        }
        QSlider::sub-page:horizontal { background:#2563eb; border-radius:3px; }
        QSlider::handle:horizontal {
            width:18px; margin:-6px 0; border-radius:9px;
            background:white; border:2px solid #2563eb;
        }
        """

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("Mode de commande")
        title.setObjectName("title")
        subtitle = QLabel(
            "Choisissez le pilotage de la cordeuse et, en boucle fermée, "
            "réglez les coefficients du correcteur PID."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        mode_card = QGroupBox("Pilotage")
        mode_layout = QGridLayout(mode_card)
        mode_layout.setHorizontalSpacing(20)
        mode_layout.setVerticalSpacing(10)

        self.bo_radio = QRadioButton("BO — Boucle ouverte")
        self.bf_radio = QRadioButton("BF — Boucle fermée")
        self.constructor_radio = QRadioButton("Constructeur")
        self.constructor_radio.setChecked(True)

        mode_layout.addWidget(self.bo_radio, 0, 0)
        mode_layout.addWidget(self.bf_radio, 0, 1)
        mode_layout.addWidget(self.constructor_radio, 0, 2)
        root.addWidget(mode_card)

        self.pid_group = QGroupBox("Correcteur PID — actif uniquement en BF")
        pid_layout = QGridLayout(self.pid_group)
        pid_layout.setColumnStretch(1, 1)
        pid_layout.setHorizontalSpacing(12)
        pid_layout.setVerticalSpacing(14)

        defaults = {"Kp": 0.500, "Ki": 0.000, "Kd": 0.000}
        for row, (name, value) in enumerate(defaults.items()):
            label = QLabel(name)
            label.setStyleSheet("font:700 13px 'Segoe UI'; color:#24324a;")

            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, self.SLIDER_MAX)
            slider.setValue(round(value / self.PID_STEP))

            spinbox = QDoubleSpinBox()
            spinbox.setDecimals(3)
            spinbox.setRange(self.PID_MIN, self.PID_MAX)
            spinbox.setSingleStep(self.PID_STEP)
            spinbox.setValue(value)
            spinbox.setSuffix("")
            spinbox.setKeyboardTracking(False)
            spinbox.setFixedWidth(120)

            slider.valueChanged.connect(
                lambda raw, target=spinbox: target.setValue(raw * self.PID_STEP)
            )
            spinbox.valueChanged.connect(
                lambda current, target=slider: target.setValue(
                    round(current / self.PID_STEP)
                )
            )

            pid_layout.addWidget(label, row, 0)
            pid_layout.addWidget(slider, row, 1)
            pid_layout.addWidget(spinbox, row, 2)
            self.controls[name.lower()] = PIDControl(slider, spinbox)

        root.addWidget(self.pid_group)

        warning = QLabel(
            "Sécurité : les coefficients sont limités ici entre 0 et 1. "
            "Validez les réglages sur la machine uniquement avec le protocole "
            "d'essai prévu et les sécurités mécaniques en place."
        )
        warning.setObjectName("warning")
        warning.setWordWrap(True)
        root.addWidget(warning)

        serial_group = QGroupBox("Liaison série")
        serial_layout = QGridLayout(serial_group)
        serial_layout.setColumnStretch(1, 1)

        serial_layout.addWidget(QLabel("Port"), 0, 0)
        self.port_combo = QComboBox()
        serial_layout.addWidget(self.port_combo, 0, 1)
        refresh_button = QPushButton("Actualiser")
        refresh_button.clicked.connect(self.refresh_ports)
        serial_layout.addWidget(refresh_button, 0, 2)

        serial_layout.addWidget(QLabel("Vitesse"), 1, 0)
        self.baud_combo = QComboBox()
        for baud in (9600, 19200, 38400, 57600, 115200):
            self.baud_combo.addItem(str(baud), baud)
        self.baud_combo.setCurrentText("115200")
        serial_layout.addWidget(self.baud_combo, 1, 1)

        root.addWidget(serial_group)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        self.validate_button = QPushButton("Valider la commande")
        self.validate_button.setObjectName("primary")
        self.validate_button.clicked.connect(self.validate_command)
        buttons.addWidget(cancel_button)
        buttons.addWidget(self.validate_button)
        root.addLayout(buttons)

        for radio in (self.bo_radio, self.bf_radio, self.constructor_radio):
            radio.toggled.connect(self._mode_changed)

    def refresh_ports(self) -> None:
        current = self.port_combo.currentData()
        self.port_combo.clear()
        for device, description in available_ports():
            self.port_combo.addItem(f"{device} — {description}", device)
        if self.port_combo.count() == 0:
            self.port_combo.addItem("Aucun port série détecté", "")
        elif current:
            index = self.port_combo.findData(current)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

    def selected_mode(self) -> str:
        if self.bo_radio.isChecked():
            return "BO"
        if self.bf_radio.isChecked():
            return "BF"
        return "CONSTRUCTEUR"

    def _mode_changed(self) -> None:
        self.pid_group.setEnabled(self.bf_radio.isChecked())

    def current_settings(self) -> CommandSettings:
        if self.selected_mode() != "BF":
            return CommandSettings(mode=self.selected_mode())
        return CommandSettings(
            mode="BF",
            kp=self.controls["kp"].spinbox.value(),
            ki=self.controls["ki"].spinbox.value(),
            kd=self.controls["kd"].spinbox.value(),
        )

    def validate_command(self) -> None:
        port = str(self.port_combo.currentData() or "")
        baudrate = int(self.baud_combo.currentData())
        settings = self.current_settings()

        try:
            answer = send_command(port, baudrate, settings)
        except (OSError, ValueError, Exception) as exc:
            QMessageBox.critical(
                self,
                "Envoi impossible",
                f"La commande n'a pas pu être envoyée.\n\n{exc}",
            )
            return

        details = f"Mode : {settings.mode}"
        if settings.mode == "BF":
            details += (
                f"\nKp = {settings.kp:.3f}"
                f"\nKi = {settings.ki:.3f}"
                f"\nKd = {settings.kd:.3f}"
            )
        if answer:
            details += f"\n\nRéponse de la carte : {answer}"
        else:
            details += "\n\nCommande envoyée sans accusé de réception."

        QMessageBox.information(self, "Commande validée", details)
        self.accept()
