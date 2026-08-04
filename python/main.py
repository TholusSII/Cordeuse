# SP55 Modern UI — architecture double liaison série
from app import SP55ApplicationWindow, main
from dual_serial_integration import install_dual_serial
from measurement_integration import install_measurement_window
from ui_choix_parametres import ChoiceWindow


# Le gestionnaire série est installé avant la fenêtre de mesure afin que cette
# dernière reçoive automatiquement la liaison dédiée au boîtier SP55.
install_dual_serial(SP55ApplicationWindow, ChoiceWindow)
install_measurement_window(SP55ApplicationWindow)


if __name__ == "__main__":
    main()
