# SP55 Modern UI — double liaison série, mesures, formules et calibration

from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path


def _find_program_dir() -> Path:
    """Localise le dossier contenant app.py, y compris avec Run Module d'IDLE."""
    candidates: list[Path] = []

    frame = inspect.currentframe()
    if frame is not None:
        code_filename = frame.f_code.co_filename
        if code_filename and code_filename not in {"<string>", "<stdin>"}:
            candidates.append(Path(code_filename).resolve().parent)

    file_name = globals().get("__file__")
    if file_name:
        candidates.append(Path(str(file_name)).resolve().parent)

    if sys.argv and sys.argv[0] and sys.argv[0] not in {"-c", ""}:
        candidates.append(Path(sys.argv[0]).resolve().parent)

    current = Path.cwd().resolve()
    candidates.extend((current, current / "python"))
    candidates.append(Path(r"C:\github\cordeuse\python"))

    checked: list[Path] = []
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in checked:
            continue
        checked.append(candidate)
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
from machine_diagram import MachineDiagram
from measurement_integration import install_measurement_window
from ui_choix_parametres import ChoiceWindow
from visual_fixes import install_visual_fixes


# Les corrections visuelles sont installées avant la création de la fenêtre.
install_visual_fixes(ChoiceWindow, MachineDiagram)

# L'ordre est important : série, mesures, puis calibration.
install_dual_serial(SP55ApplicationWindow, ChoiceWindow)
install_measurement_window(SP55ApplicationWindow)
install_calibration(SP55ApplicationWindow)


if __name__ == "__main__":
    main()
