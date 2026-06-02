import os
import sys
import subprocess

def run_script(script_path):
    print(f"\n--- Running: {script_path} ---")
    res = subprocess.run([sys.executable, script_path])
    if res.returncode != 0:
        print(f"Error: Script {script_path} failed with exit code {res.returncode}")
        sys.exit(res.returncode)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List pipeline stages in execution order
    stages = [
        # 1. Profiling
        os.path.join(base_dir, 'profiling/disk.py'),
        os.path.join(base_dir, 'profiling/annual.py'),
        os.path.join(base_dir, 'profiling/evolution.py'),
        # 2. Reporting
        os.path.join(base_dir, 'reporting/summary.py'),
        os.path.join(base_dir, 'reporting/quality.py'),
        os.path.join(base_dir, 'reporting/volume.py'),
        os.path.join(base_dir, 'reporting/proposals.py')
    ]
    
    print("Executing complete vehicle data profiling and reporting pipeline...")
    for stage in stages:
        run_script(stage)
        
    print("\nPipeline execution completed successfully!")

if __name__ == '__main__':
    main()
