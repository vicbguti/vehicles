import os
import sys
from run_profiling import run_profiling
from run_reporting import run_reporting

def main():
    print("==============================================================")
    print("Executing complete vehicle data profiling and reporting pipeline")
    print("==============================================================")
    
    # 1. Run Profiling
    run_profiling()
    
    print("\n--------------------------------------------------------------")
    
    # 2. Run Reporting
    run_reporting()
    
    print("\n==============================================================")
    print("Pipeline execution completed successfully!")
    print("==============================================================")

if __name__ == '__main__':
    main()
