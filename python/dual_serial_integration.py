from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QPushButton

from command_window import CommandModeDialog
from dual_serial_manager import DualSerialManager
from serial_configuration_dialog import SerialConfigurationDialog


def install_dual_serial(application_class, choice_window_class) -> None:
    """Branche le gestionnaire double-port sur l'application existante."""
    original_app_init = application_class.__init__

    def app_init(self, *args, **kwargs):
        # Le gestionnaire doit exister avant ChoiceWindow.__init__(), mais la
        # fenêtre n'est pas encore un QObject initialisé : le parent est donc
        # affecté juste après l'appel au constructeur d'origine.
        self.serial_manager = DualSerialManager()
        original_app_init(self, *args, **kwargs)
        self.serial_manager.setParent(self)
        self.serial_configuration_dialog = None
        for button in self.findChildren(QPushButton):
            if button.text() == "⚙":
                button.setToolTip("Configuration des deux liaisons série")
                button.clicked.connect(
                    lambda _checked=False: open_serial_configuration(self)
                )
                break
        update_main_status(self)

    application_class.__init__ = app_init

    def open_command_mode(self) -> None:
        dialog = CommandModeDialog(self)
        dialog.serial_manager = self.serial_manager
        dialog.refresh_ports()
        port_index = dialog.port_combo.findData(self.serial_manager.control.port)
        if port_index >= 0:
            dialog.port_combo.setCurrentIndex(port_index)
        dialog.baud_combo.setCurrentText(str(self.serial_manager.control.baudrate))
        self.command_dialog = dialog
        dialog.exec()

    choice_window_class.open_command_mode = open_command_mode

    original_validate = CommandModeDialog.validate_command

    def validate_command(self) -> None:
        manager = getattr(self, "serial_manager", None)
        if manager is None:
            original_validate(self)
            return

        port = str(self.port_combo.currentData() or "")
        baudrate = int(self.baud_combo.currentData())
        settings = self.current_settings()
        try:
            manager.configure_control(port, baudrate)
            answer = manager.send_control_command(settings)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Envoi impossible",
                "La commande destinée à l'Arduino Mega n'a pas pu être envoyée."
                f"\n\n{exc}",
            )
            return

        details = f"Port Arduino : {port} à {baudrate} bauds\nMode : {settings.mode}"
        if settings.mode == "BF":
            details += (
                f"\nKp = {settings.kp:.3f}"
                f"\nKi = {settings.ki:.3f}"
                f"\nKd = {settings.kd:.3f}"
            )
        details += (
            f"\n\nRéponse Arduino : {answer}"
            if answer
            else "\n\nCommande envoyée sans accusé de réception."
        )
        QMessageBox.information(self, "Commande validée", details)
        self.accept()

    CommandModeDialog.validate_command = validate_command


def open_serial_configuration(owner) -> None:
    dialog = SerialConfigurationDialog(owner.serial_manager, owner)
    owner.serial_configuration_dialog = dialog
    if dialog.exec():
        update_main_status(owner)


def update_main_status(owner) -> None:
    measure = owner.serial_manager.measurement
    control = owner.serial_manager.control
    measure_text = measure.port or "non configuré"
    control_text = control.port or "non configuré"
    owner.status.setText(
        f"Série — boîtier de mesure : {measure_text} / {measure.baudrate} bauds ; "
        f"Arduino Mega : {control_text} / {control.baudrate} bauds."
    )
