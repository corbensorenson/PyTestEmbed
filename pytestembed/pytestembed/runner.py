"""Test runner for PyTestEmbed."""

import os
import sys
import tempfile
import subprocess
import unittest
from typing import List, Dict, Any, Optional
from pathlib import Path

from .parser import ParsedProgram, PyTestEmbedParser
from .generator import TestGenerator
from .utils import is_file_cached, cache_file_hash, get_cache_dir


class TestRunner:
    """Runs tests generated from PyTestEmbed structures."""

    def __init__(self, use_cache: bool = True, verbose: bool = False):
        """Initialize the test runner.

        Args:
            use_cache: Whether to use caching to avoid reparsing unchanged files
            verbose: Whether to output verbose information
        """
        self.use_cache = use_cache
        self.verbose = verbose
        self.parser = PyTestEmbedParser()
        self.generator = TestGenerator()

    def run_tests_from_file(self, file_path: str) -> bool:
        """Run tests from a PyTestEmbed file.

        Args:
            file_path: Path to the PyTestEmbed file

        Returns:
            True if all tests passed, False otherwise
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check cache first
        parsed_program = None
        if self.use_cache:
            parsed_program = self._get_cached_program(file_path)

        if parsed_program is None:
            if self.verbose:
                print(f"Parsing {file_path}...")
            parsed_program = self.parser.parse_file(file_path)

            if self.use_cache:
                self._cache_program(file_path, parsed_program)
        elif self.verbose:
            print(f"Using cached parse result for {file_path}")

        return self.run_tests(parsed_program, file_path)

    def run_tests(self, parsed_program: ParsedProgram, original_file: Optional[str] = None) -> bool:
        """Run tests from parsed program.

        Args:
            parsed_program: The parsed PyTestEmbed program
            original_file: Path to the original file (for imports)

        Returns:
            True if all tests passed, False otherwise
        """
        if self.verbose:
            print("Generating test code...")

        # Generate test code
        test_code = self.generator.generate_tests(parsed_program)

        # If no tests were generated, consider it a success
        if "class Test" not in test_code:
            if self.verbose:
                print("No tests found to run.")
            return True

        # Prepare the test environment
        return self._execute_tests(test_code, original_file)

    def _execute_tests(self, test_code: str, original_file: Optional[str] = None) -> bool:
        """Execute the generated test code.

        Args:
            test_code: The generated unittest code
            original_file: Path to the original file for imports

        Returns:
            True if all tests passed, False otherwise
        """
        # Create temporary files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            # If we have an original file, copy it to temp directory for imports
            if original_file:
                original_path = Path(original_file)
                module_name = original_path.stem

                # Create cleaned version of original file (without test/doc blocks)
                with open(original_file, 'r') as f:
                    original_content = f.read()

                cleaned_content = self._remove_test_doc_blocks(original_content)

                # Write cleaned file to temp directory
                temp_original = temp_dir_path / f"{module_name}.py"
                with open(temp_original, 'w') as f:
                    f.write(cleaned_content)

                # Add import statement to test code
                import_line = f"from {module_name} import *\n\n"
                full_test_code = import_line + test_code
            else:
                full_test_code = test_code

            # Write test file
            test_file = temp_dir_path / "test_generated.py"
            with open(test_file, 'w') as f:
                f.write(full_test_code)

            # Run the tests
            if self.verbose:
                print("Running tests...")

            try:
                result = subprocess.run(
                    [sys.executable, str(test_file)],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )

                # Print output if verbose or if there were failures
                if self.verbose or result.returncode != 0:
                    if result.stdout:
                        print(result.stdout)
                    if result.stderr:
                        print(result.stderr, file=sys.stderr)

                return result.returncode == 0

            except subprocess.TimeoutExpired:
                print("Test execution timed out", file=sys.stderr)
                return False
            except Exception as e:
                print(f"Error running tests: {e}", file=sys.stderr)
                return False

    def _remove_test_doc_blocks(self, content: str) -> str:
        """Remove test: and doc: blocks from content."""
        lines = content.split('\n')
        result_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Check if this is a test: or doc: block
            if stripped in ['test:', 'doc:']:
                # Skip this line and all indented lines that follow
                base_indent = len(line) - len(line.lstrip())
                i += 1

                while i < len(lines):
                    next_line = lines[i]
                    if next_line.strip() == '':
                        # Skip empty lines within the block
                        i += 1
                        continue

                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent > base_indent:
                        # This line is part of the test/doc block, skip it
                        i += 1
                    else:
                        # This line is not part of the block, process it normally
                        break
            else:
                result_lines.append(line)
                i += 1

        return '\n'.join(result_lines)

    def _get_cached_program(self, file_path: str) -> Optional[ParsedProgram]:
        """Get cached parsed program if available and up to date."""
        if not is_file_cached(file_path):
            return None

        # For now, we'll skip actual caching of parsed objects
        # In a full implementation, we'd serialize/deserialize the ParsedProgram
        return None

    def _cache_program(self, file_path: str, parsed_program: ParsedProgram) -> None:
        """Cache the parsed program."""
        # Cache the file hash to track changes
        cache_file_hash(file_path)

        # For now, we only cache the file hash
        # In a full implementation, we'd serialize the ParsedProgram object


# Alias for backward compatibility and clearer naming
PyTestEmbedRunner = TestRunner
