import os
import sys
# Ensure package imports work when script is executed directly
# Add the parent directory (solution_visuals) to sys.path so that the
# "temporal" package can be imported.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from temporal.trends.by_class import main as run

if __name__ == '__main__':
    run()
