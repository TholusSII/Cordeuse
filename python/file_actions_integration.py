from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox, QPushButton


def install_file_actions(application_class) -> None:
    """Branche les boutons latéraux sur les opérations de fichiers MES."""
    if getattr(application_class, "_sp55_file_actions_installed", False):
        return
    application_class._sp55_file_actions_installed = True

    original_init = application_class.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        _connect_buttons(self)

    application_class.__init__ = patched_init


def _find_button(owner, *labels: str) -> QPushButton | None:
    normalized = {label.casefold() for label in labels}
    for button in owner.findChildren(QPushButton):
        text = button.text().replace("＋", "").replace("□", "").replace("▤", "")
        text = text.replace("×", "").strip().casefold()
        tooltip = button.toolTip().strip().casefold()
        if text in normalized or tooltip in normalized:
            return button
    return None


def _connect_once(button: QPushButton | None, callback) -> None:
    if button is None or button.property("sp55ActionConnected"):
        return
    button.clicked.connect(callback)
    button.setProperty("sp55ActionConnected", True)


def _connect_buttons(owner) -> None:
    # « Nouveau » n'a pas de sens dans ce logiciel : on le retire de la barre.
    new_button = _find_button(owner, "Nouveau", "Créer une nouvelle étude")
    if new_button is not None:
        new_button.hide()

    open_button = _find_button(owner, "Ouvrir", "Ouvrir un fichier de mesures")
    save_button = _find_button(owner, "Enregistrer", "Sauver", "Enregistrer l'étude")
    clear_button = _find_button(owner, "Effacer", "Effacer la sélection")

    _connect_once(open_button, lambda _checked=False: open_mes(owner))
    _connect_once(save_button, lambda _checked=False: save_mes_copy(owner))
    _connect_once(clear_button, lambda _checked=False: clear_current_measurement(owner))

    if open_button is not None:
        open_button.setToolTip("Ouvrir et charger un fichier de mesures .mes")
    if save_button is not None:
        save_button.setToolTip("Enregistrer une copie du fichier .mes chargé")
    if clear_button is not None:
        clear_button.setToolTip("Fermer et effacer la mesure actuellement chargée")


def open_mes(owner) -> None:
    if owner.choose_mes_file():
        owner._refresh()


def clear_current_measurement(owner) -> None:
    study = getattr(owner, "study", None)
    if study is None:
        owner.status.setText("Aucune mesure n'est actuellement chargée.")
        return

    for window in list(getattr(owner, "plot_windows", [])):
        try:
            window.close()
        except RuntimeError:
            pass
    if hasattr(owner, "plot_windows"):
        owner.plot_windows.clear()

    owner.study = None
    for index, check in enumerate(owner.measure_checks, start=1):
        check.setEnabled(True)
        check.setChecked(index == 1)

    owner.status.setText("Mesure effacée. Ouvrez un nouveau fichier .mes pour continuer.")
    owner._refresh()


def save_mes_copy(owner) -> None:
    study = getattr(owner, "study", None)
    if study is None:
        QMessageBox.information(
            owner,
            "Enregistrer",
            "Aucun fichier de mesures n'est chargé.",
        )
        return

    source = Path(study.path)
    target, _ = QFileDialog.getSaveFileName(
        owner,
        "Enregistrer une copie du fichier de mesures",
        str(source.with_name(f"{source.stem}_copie{source.suffix}")),
        "Mesures SP55 (*.mes);;Tous les fichiers (*.*)",
    )
    if not target:
        return

    destination = Path(target)
    if destination.suffix.lower() != ".mes":
        destination = destination.with_suffix(".mes")
    try:
        shutil.copy2(source, destination)
    except OSError as exc:
        QMessageBox.critical(owner, "Enregistrement impossible", str(exc))
        return

    owner.status.setText(f"Copie enregistrée : {destination.name}")
