import os
import sys
import subprocess

def run_script(script_path):
    print(f"\n--- Running: {script_path} ---")
    res = subprocess.run([sys.executable, script_path])
    if res.returncode != 0:
        print(f"Error: Script {script_path} failed with exit code {res.returncode}")
        sys.exit(res.returncode)

def run_audits():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    stages = [
        os.path.join(base_dir, 'audits/summary.py'),
        os.path.join(base_dir, 'audits/quality.py'),
        os.path.join(base_dir, 'audits/visuals.py'),
        os.path.join(base_dir, 'audits/volume/storage.py'),
        os.path.join(base_dir, 'audits/volume/growth_trends.py'),
        os.path.join(base_dir, 'audits/volume/memory_profile.py')
    ]
    print("Executing data audits report compilation...")
    for stage in stages:
        run_script(stage)
    print("\nData audits report compilation completed successfully!")

if __name__ == '__main__':
    run_audits()
