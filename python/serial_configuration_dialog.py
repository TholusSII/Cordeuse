from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from dual_serial_manager import DualSerialManager


class SerialConfigurationDialog(QDialog):
    def __init__(self, manager: DualSerialManager, parent=None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Configuration des liaisons série")
        self.resize(680, 430)
        self.setMinimumSize(620, 390)
        self.setStyleSheet(
            "QDialog{background:#f3f6fb;color:#172033;font-family:'Segoe UI'}"
            "QGroupBox{background:white;border:1px solid #dfe6ef;border-radius:12px;"
            "margin-top:14px;padding:16px 12px 12px 12px;font-weight:600}"
            "QGroupBox::title{subcontrol-origin:margin;left:14px;padding:0 6px}"
            "QComboBox{background:white;border:1px solid #d8dee9;border-radius:8px;padding:7px}"
            "QPushButton{background:white;border:1px solid #d8dee9;border-radius:8px;padding:8px 12px}"
            "QPushButton#primary{background:#2563eb;color:white;border:none;font-weight:600}"
        )
        self._build_ui()
        self.refresh_ports()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("Deux liaisons série indépendantes")
        title.setStyleSheet("font:700 22px 'Segoe UI';color:#172033")
        subtitle = QLabel(
            "Le boîtier SP55 fournit les mesures historiques. L'Arduino Mega assure "
            "le pilotage et pourra transmettre des mesures complémentaires."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#667085")
        root.addWidget(title)
        root.addWidget(subtitle)

        self.measure_port, self.measure_baud = self._endpoint_group(
            root,
            "Boîtier de mesure SP55",
            "Réception des données de mesure — protocole à identifier",
        )
        self.control_port, self.control_baud = self._endpoint_group(
            root,
            "Arduino Mega — pilotage",
            "Commande BO/BF/Constructeur, PID et futures mesures Arduino",
        )

        actions = QHBoxLayout()
        refresh = QPushButton("Actualiser les ports")
        refresh.clicked.connect(self.refresh_ports)
        actions.addWidget(refresh)
        actions.addStretch()
        cancel = QPushButton("Annuler")
        cancel.clicked.connect(self.reject)
        validate = QPushButton("Enregistrer la configuration")
        validate.setObjectName("primary")
        validate.clicked.connect(self.save)
        actions.addWidget(cancel)
        actions.addWidget(validate)
        root.addLayout(actions)

    def _endpoint_group(self, root, title: str, description: str):
        group = QGroupBox(title)
        layout = QGridLayout(group)
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color:#667085;font-weight:400")
        layout.addWidget(description_label, 0, 0, 1, 3)
        layout.addWidget(QLabel("Port"), 1, 0)
        port = QComboBox()
        layout.addWidget(port, 1, 1, 1, 2)
        layout.addWidget(QLabel("Vitesse"), 2, 0)
        baud = QComboBox()
        for value in (1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200):
            baud.addItem(str(value), value)
        layout.addWidget(baud, 2, 1)
        layout.setColumnStretch(1, 1)
        root.addWidget(group)
        return port, baud

    def refresh_ports(self) -> None:
        measurement_current = self.measure_port.currentData() or self.manager.measurement.port
        control_current = self.control_port.currentData() or self.manager.control.port
        ports = self.manager.available_ports()
        for combo, current in (
            (self.measure_port, measurement_current),
            (self.control_port, control_current),
        ):
            combo.clear()
            combo.addItem("— Non configuré —", "")
            for device, description in ports:
                combo.addItem(f"{device} — {description}", device)
            index = combo.findData(current)
            if index >= 0:
                combo.setCurrentIndex(index)

        self.measure_baud.setCurrentText(str(self.manager.measurement.baudrate))
        self.control_baud.setCurrentText(str(self.manager.control.baudrate))

    def save(self) -> None:
        measurement_port = str(self.measure_port.currentData() or "")
        control_port = str(self.control_port.currentData() or "")
        try:
            self.manager.configure_measurement(
                measurement_port, int(self.measure_baud.currentData())
            )
            self.manager.configure_control(
                control_port, int(self.control_baud.currentData())
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Configuration invalide", str(exc))
            return
        self.accept()
