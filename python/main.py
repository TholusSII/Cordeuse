# SP55 Modern UI — double liaison série, mesures, formules et calibration

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_program_dir() -> Path:
    """Localise le dossier contenant app.py, même quand IDLE ne définit pas __file__."""
    candidates: list[Path] = []

    file_name = globals().get("__file__")
    if file_name:
        candidates.append(Path(str(file_name)).resolve().parent)

    if sys.argv and sys.argv[0]:
        candidates.append(Path(sys.argv[0]).resolve().parent)

    current = Path.cwd().resolve()
    candidates.extend((current, current / "python"))

    # Supprime les doublons tout en conservant l'ordre.
    checked: set[Path] = set()
    for candidate in candidates:
        if candidate in checked:
            continue
        checked.add(candidate)
        if (candidate / "app.py").is_file():
            return candidate

    locations = "\n".join(f"- {path}" for path in checked)
    raise RuntimeError(
        "Impossible de localiser le dossier du logiciel SP55 contenant app.py.\n"
        "Lancez main.py depuis le dossier python du projet.\n\n"
        f"Emplacements examinés :\n{locations}"
    )


PROGRAM_DIR = _find_program_dir()
if str(PROGRAM_DIR) not in sys.path:
    sys.path.insert(0, str(PROGRAM_DIR))
os.chdir(PROGRAM_DIR)

from app import SP55ApplicationWindow, main
from calibration_integration import install_calibration
from dual_serial_integration import install_dual_serial
from measurement_integration import install_measurement_window
from ui_choix_parametres import ChoiceWindow


# L'ordre est important :
# 1. installation du gestionnaire des deux ports série ;
# 2. branchement de la fenêtre de mesure ;
# 3. chargement automatique de sp55.cfg et écran de calibration.
install_dual_serial(SP55ApplicationWindow, ChoiceWindow)
install_measurement_window(SP55ApplicationWindow)
install_calibration(SP55ApplicationWindow)


if __name__ == "__main__":
    main()
