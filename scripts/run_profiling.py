import os
import sys
import subprocess

def run_script(script_path):
    print(f"\n--- Running: {script_path} ---")
    res = subprocess.run([sys.executable, script_path])
    if res.returncode != 0:
        print(f"Error: Script {script_path} failed with exit code {res.returncode}")
        sys.exit(res.returncode)

def run_profiling():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    stages = [
        os.path.join(base_dir, 'profiling/disk.py'),
        os.path.join(base_dir, 'profiling/annual.py'),
        os.path.join(base_dir, 'profiling/evolution.py')
    ]
    print("Executing data profiling stage...")
    for stage in stages:
        run_script(stage)
    print("\nData profiling stage completed successfully!")

if __name__ == '__main__':
    run_profiling()
