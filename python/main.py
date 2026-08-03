# SP55 Modern UI — republication complète 2026-08-03
from app import SP55ApplicationWindow, main
from measurement_integration import install_measurement_window


install_measurement_window(SP55ApplicationWindow)


if __name__ == "__main__":
    main()
