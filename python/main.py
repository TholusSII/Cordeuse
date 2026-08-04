# SP55 Modern UI — architecture double liaison série et calibration
from app import SP55ApplicationWindow, main
from calibration_integration import install_calibration
from dual_serial_integration import install_dual_serial
from measurement_integration import install_measurement_window
from ui_choix_parametres import ChoiceWindow


# Ordre d'installation :
# 1. double liaison série ;
# 2. fenêtre de mesure ;
# 3. chargement automatique et écran de calibration.
install_dual_serial(SP55ApplicationWindow, ChoiceWindow)
install_measurement_window(SP55ApplicationWindow)
install_calibration(SP55ApplicationWindow)


if __name__ == "__main__":
    main()
