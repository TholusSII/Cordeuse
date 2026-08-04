from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QPushButton

from measurement_window import MeasurementWindow
from mes_reader import read_mes


def install_measurement_window(application_class) -> None:
    """Ajoute la fenêtre d'acquisition sur la liaison dédiée au boîtier SP55."""
    original_init = application_class.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.measurement_window = None
        for button in self.findChildren(QPushButton):
            if button.toolTip() == "Mesures":
                button.clicked.connect(lambda _checked=False: open_measurement(self))
                break

    application_class.__init__ = patched_init


def open_measurement(owner) -> None:
    window = MeasurementWindow(owner)
    window.serial_manager = getattr(owner, "serial_manager", None)
    if window.serial_manager is not None:
        endpoint = window.serial_manager.measurement
        window.refresh_ports()
        index = window.port.findText(endpoint.port)
        if index >= 0:
            window.port.setCurrentIndex(index)
        window.baud.setCurrentText(str(endpoint.baudrate))
        window.setWindowTitle("Réalisation des mesures — boîtier SP55")
        window.log.appendPlainText(
            f"Liaison dédiée au boîtier de mesure : "
            f"{endpoint.port or 'non configurée'} / {endpoint.baudrate} bauds"
        )

    owner.measurement_window = window
    window.measurement_saved.connect(lambda path: load_saved_measurement(owner, path))
    window.show()
    window.raise_()
    window.activateWindow()


def load_saved_measurement(owner, path: str) -> None:
    study = read_mes(path)
    owner.study = study
    for index, check in enumerate(owner.measure_checks, start=1):
        available = index <= study.count
        check.setEnabled(available)
        check.setChecked(index == 1 and available)
    owner.status.setText(
        f"Mesure chargée : {Path(path).name} — {study.count} mesure(s), "
        f"{len(study.measurements[0]['t'])} points."
    )
