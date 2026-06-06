import os
import sys

# Add the reporting directory to Python path to import sub-runners
sys.path.append(os.path.join(os.path.dirname(__file__), 'reporting'))

from run_audits import run_audits
from run_proposals import run_proposals

def run_reporting():
    print("==============================================================")
    print("Executing report compilation phase")
    print("==============================================================")
    
    # 1. Run Data Audits
    run_audits()
    
    print("\n--------------------------------------------------------------")
    
    # 2. Run ML Proposals
    run_proposals()
    
    print("\n==============================================================")
    print("Report compilation phase completed successfully!")
    print("==============================================================")

if __name__ == '__main__':
    run_reporting()
