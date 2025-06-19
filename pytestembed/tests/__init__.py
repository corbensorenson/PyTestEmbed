"""
PyTestEmbed Test Suite

Comprehensive tests for all PyTestEmbed components to ensure reliability
and correctness for production use.
"""

import sys
import os
from pathlib import Path

# Add pytestembed to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_DATA_DIR = test_dir / "fixtures"
TEST_OUTPUT_DIR = test_dir / "output"

# Ensure test directories exist
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_OUTPUT_DIR.mkdir(exist_ok=True)

# Test utilities
def get_test_file(filename: str) -> Path:
    """Get path to test fixture file."""
    return TEST_DATA_DIR / filename

def get_output_file(filename: str) -> Path:
    """Get path to test output file."""
    return TEST_OUTPUT_DIR / filename

def cleanup_test_files():
    """Clean up test output files."""
    if TEST_OUTPUT_DIR.exists():
        for file in TEST_OUTPUT_DIR.glob("*"):
            if file.is_file():
                file.unlink()
