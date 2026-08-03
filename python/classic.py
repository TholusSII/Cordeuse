from __future__ import annotations

import importlib.util
from pathlib import Path


_SOURCE = Path(__file__).resolve().parents[1] / "cordeuse" / "python" / "classic.py"


def _load_original_module():
    if not _SOURCE.exists():
        raise FileNotFoundError(f"Interface introuvable : {_SOURCE}")
    spec = importlib.util.spec_from_file_location("sp55_classic_original", _SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Impossible de charger {_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    module = _load_original_module()
    module.main()


if __name__ == "__main__":
    main()
