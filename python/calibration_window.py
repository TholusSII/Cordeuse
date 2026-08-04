from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from calibration_config import SP55Calibration, SensorCalibration, write_calibration


@dataclass
class CoefficientControl:
    slider: QSlider
    spinbox: QDoubleSpinBox
    center: float
    span: float


class SensorCalibrationCard(QFrame):
    def __init__(self, sensor: SensorCalibration, parent=None) -> None:
        super().__init__(parent)
        self.sensor = sensor
        self.setObjectName("sensorCard")
        self.controls: list[CoefficientControl] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel(f"Capteur {sensor.index} — {sensor.name}")
        title.setStyleSheet("font:700 14px 'Segoe UI';color:#172033")
        unit = QLabel(sensor.unit)
        unit.setStyleSheet("color:#667085")
        self.enabled = QCheckBox("Actif")
        self.enabled.setChecked(sensor.enabled)
        header.addWidget(title)
        header.addWidget(unit)
        header.addStretch()
        header.addWidget(self.enabled)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setColumnStretch(2, 1)
        grid.setHorizontalSpacing(10)
        labels = ["Coefficient A", "Coefficient B", "Coefficient C", "Coefficient D"]
        for row, (label_text, value) in enumerate(zip(labels, sensor.coefficients)):
            label = QLabel(label_text)
            label.setMinimumWidth(92)

            spinbox = QDoubleSpinBox()
            spinbox.setDecimals(12)
            spinbox.setRange(-1.0e9, 1.0e9)
            spinbox.setSingleStep(max(abs(value) / 100.0, 0.001))
            spinbox.setValue(value)
            spinbox.setKeyboardTracking(False)
            spinbox.setMinimumWidth(180)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(-1000, 1000)
            slider.setValue(0)
            center = value
            span = max(abs(value) * 2.0, 1.0)
            control = CoefficientControl(slider, spinbox, center, span)
            self.controls.append(control)

            slider.valueChanged.connect(
                lambda raw, target=control: self._slider_changed(target, raw)
            )
            spinbox.valueChanged.connect(
                lambda current, target=control: self._spinbox_changed(target, current)
            )

            grid.addWidget(label, row, 0)
            grid.addWidget(spinbox, row, 1)
            grid.addWidget(slider, row, 2)
        layout.addLayout(grid)

    @staticmethod
    def _slider_changed(control: CoefficientControl, raw: int) -> None:
        value = control.center + (raw / 1000.0) * control.span
        control.spinbox.blockSignals(True)
        control.spinbox.setValue(value)
        control.spinbox.blockSignals(False)

    @staticmethod
    def _spinbox_changed(control: CoefficientControl, value: float) -> None:
        if control.span <= 0:
            return
        raw = round((value - control.center) / control.span * 1000.0)
        control.slider.blockSignals(True)
        control.slider.setValue(max(-1000, min(1000, raw)))
        control.slider.blockSignals(False)

    def apply_to_sensor(self) -> None:
        self.sensor.enabled = self.enabled.isChecked()
        self.sensor.coefficients = [control.spinbox.value() for control in self.controls]


class CalibrationDialog(QDialog):
    def __init__(self, config: SP55Calibration, path: Path, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.path = Path(path)
        self.cards: list[SensorCalibrationCard] = []
        self.setWindowTitle("Calibration des capteurs — SP55")
        self.resize(980, 760)
        self.setMinimumSize(820, 620)
        self.setStyleSheet(self._style())
        self._build_ui()

    @staticmethod
    def _style() -> str:
        return """
        QDialog{background:#f3f6fb;color:#172033;font-family:'Segoe UI'}
        QFrame#card,QFrame#sensorCard{background:white;border:1px solid #dfe6ef;border-radius:14px}
        QLabel#title{font:700 22px 'Segoe UI';color:#172033}
        QLabel#subtitle{color:#667085}
        QPushButton{background:white;border:1px solid #d8dee9;border-radius:9px;padding:9px 13px}
        QPushButton:hover{background:#f6f9ff;border-color:#9bbcf2}
        QPushButton#primary{background:#2563eb;color:white;border:none;font-weight:600}
        QLineEdit,QSpinBox,QDoubleSpinBox{background:white;border:1px solid #d8dee9;border-radius:8px;padding:7px}
        QSlider::groove:horizontal{height:6px;background:#dfe6ef;border-radius:3px}
        QSlider::sub-page:horizontal{background:#2563eb;border-radius:3px}
        QSlider::handle:horizontal{width:18px;margin:-6px 0;border-radius:9px;background:white;border:2px solid #2563eb}
        """

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("Calibration des capteurs")
        title.setObjectName("title")
        subtitle = QLabel(
            "Les valeurs sont chargées depuis sp55.cfg. Les curseurs permettent un réglage rapide autour de la valeur d'origine ; les champs numériques permettent une saisie précise."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        general = QFrame()
        general.setObjectName("card")
        general_layout = QGridLayout(general)
        general_layout.setContentsMargins(14, 12, 14, 12)
        general_layout.addWidget(QLabel("Fichier"), 0, 0)
        path_label = QLabel(str(self.path))
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        general_layout.addWidget(path_label, 0, 1, 1, 3)
        general_layout.addWidget(QLabel("N° de port historique"), 1, 0)
        self.serial_port_number = QSpinBox()
        self.serial_port_number.setRange(1, 256)
        self.serial_port_number.setValue(self.config.serial_port_number)
        general_layout.addWidget(self.serial_port_number, 1, 1)
        general_layout.addWidget(QLabel("Mot de passe"), 1, 2)
        self.password = QLineEdit(self.config.password)
        general_layout.addWidget(self.password, 1, 3)
        root.addWidget(general)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        sensors_layout = QVBoxLayout(container)
        sensors_layout.setContentsMargins(0, 0, 0, 0)
        sensors_layout.setSpacing(10)
        for sensor in self.config.sensors:
            card = SensorCalibrationCard(sensor)
            self.cards.append(card)
            sensors_layout.addWidget(card)
        sensors_layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        actions = QHBoxLayout()
        open_button = QPushButton("Charger un autre fichier…")
        open_button.clicked.connect(self.load_other_file)
        save_as = QPushButton("Enregistrer sous…")
        save_as.clicked.connect(self.save_as)
        close = QPushButton("Fermer")
        close.clicked.connect(self.reject)
        save = QPushButton("Enregistrer la calibration")
        save.setObjectName("primary")
        save.clicked.connect(self.save)
        actions.addWidget(open_button)
        actions.addWidget(save_as)
        actions.addStretch()
        actions.addWidget(close)
        actions.addWidget(save)
        root.addLayout(actions)

    def _collect(self) -> None:
        self.config.serial_port_number = self.serial_port_number.value()
        self.config.password = self.password.text()
        for card in self.cards:
            card.apply_to_sensor()

    def save(self) -> None:
        self._collect()
        try:
            write_calibration(self.path, self.config)
        except (OSError, UnicodeEncodeError, ValueError) as exc:
            QMessageBox.critical(self, "Enregistrement impossible", str(exc))
            return
        QMessageBox.information(self, "Calibration enregistrée", f"Le fichier a été enregistré :\n{self.path}")
        self.accept()

    def save_as(self) -> None:
        self._collect()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer la configuration SP55",
            str(self.path),
            "Configuration SP55 (*.cfg);;Tous les fichiers (*.*)",
        )
        if not file_name:
            return
        if not file_name.lower().endswith(".cfg"):
            file_name += ".cfg"
        try:
            write_calibration(file_name, self.config)
        except (OSError, UnicodeEncodeError, ValueError) as exc:
            QMessageBox.critical(self, "Enregistrement impossible", str(exc))
            return
        QMessageBox.information(self, "Calibration enregistrée", f"Le fichier a été créé :\n{file_name}")

    def load_other_file(self) -> None:
        QMessageBox.information(
            self,
            "Chargement",
            "Le changement de fichier sera pris en compte au prochain démarrage. Pour remplacer la configuration active, enregistrez le fichier choisi sous le nom sp55.cfg dans le dossier du logiciel.",
        )
