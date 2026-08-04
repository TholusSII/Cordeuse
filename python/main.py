# SP55 Modern UI — double liaison série, mesures, formules et calibration

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
