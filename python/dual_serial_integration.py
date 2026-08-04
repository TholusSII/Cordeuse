from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QPushButton

from command_window import CommandModeDialog
from dual_serial_manager import DualSerialManager
from serial_configuration_dialog import SerialConfigurationDialog


def install_dual_serial(application_class, choice_window_class) -> None:
    """Branche le gestionnaire double-port sur l'application existante."""
    if getattr(application_class, "_sp55_dual_serial_installed", False):
        return
    application_class._sp55_dual_serial_installed = True

    original_app_init = application_class.__init__
    original_close_event = getattr(application_class, "closeEvent", None)

    def app_init(self, *args, **kwargs):
        self.serial_manager = DualSerialManager()
        original_app_init(self, *args, **kwargs)
        self.serial_manager.setParent(self)
        self.serial_configuration_dialog = None

        for button in self.findChildren(QPushButton):
            is_settings_button = (
                button.objectName() == "serialSettingsButton"
                or button.text() == "⚙"
                or button.toolTip() == "Configuration des liaisons série"
            )
            if is_settings_button:
                button.setToolTip("Configuration des deux liaisons série")
                if not button.property("sp55SerialSettingsConnected"):
                    button.clicked.connect(
                        lambda _checked=False: open_serial_configuration(self)
                    )
                    button.setProperty("sp55SerialSettingsConnected", True)
                break

        self.serial_manager.control_state_changed.connect(
            lambda _connected, _message: update_main_status(self)
        )
        update_main_status(self)

    def close_event(self, event) -> None:
        manager = getattr(self, "serial_manager", None)
        if manager is not None:
            manager.close_all()
        if original_close_event is not None:
            original_close_event(self, event)
        else:
            event.accept()

    application_class.__init__ = app_init
    application_class.closeEvent = close_event

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

    if not getattr(CommandModeDialog, "_sp55_shared_serial_installed", False):
        CommandModeDialog._sp55_shared_serial_installed = True
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

            details = (
                f"Port Arduino : {port} à {baudrate} bauds\n"
                f"Mode : {settings.mode}"
            )
            if settings.mode == "BF":
                details += (
                    f"\nKp = {settings.kp:.3f}"
                    f"\nKi = {settings.ki:.3f}"
                    f"\nKd = {settings.kd:.3f}"
                )
            details += f"\n\n{answer}"
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
    control_state = "connecté" if owner.serial_manager.control_is_open else "déconnecté"
    owner.status.setText(
        f"Série — boîtier de mesure : {measure_text} / {measure.baudrate} bauds ; "
        f"Arduino Mega : {control_text} / {control.baudrate} bauds ({control_state})."
    )
