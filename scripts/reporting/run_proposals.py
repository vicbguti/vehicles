import os
import subprocess
import sys
from importlib import import_module

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

# `load_stage_groups` importa `scripts.reporting.stage_groups.*`, que solo
# resuelve con la raíz del repositorio en sys.path. Ningún invocador la ponía:
# ejecutar este archivo directamente deja sys.path[0] en scripts/reporting/, y
# scripts/run_reporting.py lo deja en scripts/.
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def run_script(script_path):
    print(f"\n--- Running: {script_path} ---")
    # Ensure the project root is in PYTHONPATH so internal imports work
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = PROJECT_ROOT + (os.pathsep + existing if existing else "")
    result = subprocess.run([sys.executable, script_path], env=env)
    if result.returncode != 0:
        print(f"Error: {script_path} failed (code {result.returncode})")
        sys.exit(result.returncode)


def load_stage_groups():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    groups = ["spatial", "temporal", "class_location"]
    stage_paths = []
    for grp in groups:
        mod = import_module(f"scripts.reporting.stage_groups.{grp}")
        for rel_path in mod.stages:
            stage_paths.append(os.path.join(base_dir, rel_path))
    return stage_paths


def run_proposals():
    """Compila los reportes de propuestas.

    El nombre importa: scripts/run_reporting.py hace
    ``from run_proposals import run_proposals``. Mientras esta función se llamó
    `main`, ese import fallaba y con él todo `scripts/run_pipeline.py`, que es
    el único comando que documenta el README.
    """
    print("Executing ML proposal report compilation…")
    for script in load_stage_groups():
        run_script(script)
    print("\nML proposal report compilation completed successfully!")


if __name__ == "__main__":
    run_proposals()
