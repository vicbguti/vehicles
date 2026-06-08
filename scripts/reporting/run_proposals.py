import os
import sys
import subprocess
from importlib import import_module

def run_script(script_path):
    print(f"\n--- Running: {script_path} ---")
    # Ensure the project root is in PYTHONPATH so internal imports work
    env = os.environ.copy()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    existing = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = project_root + (os.pathsep + existing if existing else '')
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

def main():
    print("Executing ML proposal report compilation…")
    for script in load_stage_groups():
        run_script(script)
    print("\nML proposal report compilation completed successfully!")

if __name__ == "__main__":
    main()