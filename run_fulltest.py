#!/usr/bin/env python3
"""
Runner for fullTest.py - handles PyTestEmbed syntax in the main script.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytestembed as ptb

def main():
    """Run fullTest.py using PyTestEmbed import system."""
    
    print("🚀 Running fullTest.py with PyTestEmbed...")
    
    # Import and run fullTest as a module
    fulltest = ptb.import_from("import fullTest")
    
    # Call the main function if it exists
    if hasattr(fulltest, 'main'):
        fulltest.main()
    else:
        print("✓ fullTest.py imported successfully!")
        print("  (No main() function found, but import worked)")

if __name__ == "__main__":
    main()
