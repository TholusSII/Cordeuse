from __future__ import annotations

# SP55 Modern UI — republication complète 2026-08-03

import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from mes_reader import MesStudy, read_mes
from plot_window import PlotWindow
from ui_choix_parametres import ChoiceWindow


class SP55ApplicationWindow(ChoiceWindow):
    def __init__(self) -> None:
        super().__init__()
        self.study: MesStudy | None = None
        self.plot_windows: list[PlotWindow] = []
        self.status.setText(
            "Sélectionnez les grandeurs et mesures, puis cliquez sur Tracer."
        )

    def choose_mes_file(self) -> bool:
        initial_dir = str(Path.cwd())
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir un fichier de mesures SP55",
            initial_dir,
            "Mesures SP55 (*.mes);;Tous les fichiers (*.*)",
        )
        if not file_name:
            return False
        try:
            self.study = read_mes(file_name)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Lecture impossible", str(exc))
            return False

        for index, check in enumerate(self.measure_checks, start=1):
            check.setEnabled(index <= self.study.count)
            if index > self.study.count:
                check.setChecked(False)
        self.status.setText(
            f"Fichier chargé : {Path(file_name).name} — {self.study.count} mesure(s), "
            f"{len(self.study.measurements[0]['t'])} points par mesure."
        )
        return True

    def trace(self) -> None:
        if self.study is None and not self.choose_mes_file():
            return
        assert self.study is not None

        selected_measurements = [
            index + 1
            for index, check in enumerate(self.measure_checks)
            if check.isChecked() and index < self.study.count
        ]
        if not selected_measurements:
            QMessageBox.warning(
                self, "Tracer", "Sélectionnez au moins une mesure disponible."
            )
            return
        if not self.ordinate_keys:
            QMessageBox.warning(
                self, "Tracer", "Sélectionnez au moins une grandeur en ordonnée."
            )
            return
        if "formula" in self.ordinate_keys or self.abscissa_key == "formula":
            QMessageBox.information(
                self,
                "Formule",
                "Le calcul des formules personnalisées sera ajouté dans une étape suivante.",
            )
            return

        try:
            window = PlotWindow(
                self.study,
                self.abscissa_key,
                list(self.ordinate_keys),
                selected_measurements,
                self,
            )
        except (KeyError, IndexError, ValueError) as exc:
            QMessageBox.critical(self, "Tracé impossible", str(exc))
            return

        window.show()
        self.plot_windows.append(window)
        self.status.setText(
            f"Courbes tracées depuis {self.study.path.name} : "
            f"mesures {', '.join(map(str, selected_measurements))}."
        )


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = SP55ApplicationWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
