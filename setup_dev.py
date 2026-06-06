"""
setup_dev.py — Appelé par `pixi run setup`
Clone PyMoDAQ branche 5.0.x et installe les packages en mode éditable.
Idempotent : peut être relancé sans problème.
"""

import subprocess
import sys
from pathlib import Path

PYMODAQ_REPO = "https://github.com/PyMoDAQ/PyMoDAQ"
PYMODAQ_BRANCH = "5.0.x"
PYMODAQ_DIR = Path(__file__).parent / ".pymodaq_dev"

PYMODAQ_PACKAGES = [
    "pymodaq_utils",
    "pymodaq_data",
    "pymodaq_gui",
    "pymodaq",
]


def run(cmd: list[str], **kwargs) -> None:
    print(f"  > {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def clone_or_update() -> None:
    if PYMODAQ_DIR.exists():
        print(f"[PyMoDAQ] Mise à jour de la branche '{PYMODAQ_BRANCH}'...")
        run(["git", "pull"], cwd=PYMODAQ_DIR)
    else:
        print(f"[PyMoDAQ] Clonage de la branche '{PYMODAQ_BRANCH}'...")
        run(["git", "clone", "-b", PYMODAQ_BRANCH, PYMODAQ_REPO, str(PYMODAQ_DIR)])


def install_packages() -> None:
    packages_dir = PYMODAQ_DIR / "packages"
    if packages_dir.exists():
        print("[PyMoDAQ] Installation des packages en mode éditable...")
        for pkg in PYMODAQ_PACKAGES:
            pkg_path = packages_dir / pkg
            if pkg_path.exists():
                print(f"  pip install -e {pkg}")
                run([sys.executable, "-m", "pip", "install", "-e", str(pkg_path)])
            else:
                print(f"  (ignoré : {pkg} non trouvé)")
    else:
        print("[PyMoDAQ] Installation depuis la racine...")
        run([sys.executable, "-m", "pip", "install", "-e", str(PYMODAQ_DIR)])

    # Installer ce plugin en mode éditable
    plugin_dir = Path(__file__).parent
    print(f"  pip install -e . (plugin Arduino)")
    run([sys.executable, "-m", "pip", "install", "-e", str(plugin_dir)])


def verify() -> None:
    print("\n[Vérification]")
    import importlib.util
    for module, label in [
        ("pymodaq_utils", "pymodaq_utils"),
        ("pymodaq", "pymodaq"),
        ("pymodaq_plugins_arduino", "pymodaq_plugins_arduino"),
        ("PyQt6", "PyQt6"),
        ("tables", "tables (HDF5)"),
    ]:
        spec = importlib.util.find_spec(module)
        if spec is not None:
            print(f"  ✓ {label} ({spec.origin})")
        else:
            print(f"  ✗ {label} — NON TROUVÉ")


if __name__ == "__main__":
    print("=" * 55)
    print("  Setup PyMoDAQ Arduino Plugin — mode contributeur")
    print("  Branche PyMoDAQ : 5.0.x")
    print("=" * 55)

    clone_or_update()
    install_packages()
    verify()

    print()
    print("  Tout est prêt !")
    print("  Vérifier la version : pixi run python -c \"import pymodaq; print(pymodaq.__version__)\"")
    print("  Lancer les tests    : pixi run test")
    print("=" * 55)
