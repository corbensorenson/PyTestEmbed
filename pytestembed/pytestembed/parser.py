"""PyTestEmbed Parser - Parses custom syntax with embedded tests and documentation."""

import re
import ast
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Import performance optimizations
try:
    from .cache_manager import get_cache_manager
    from .performance_optimizer import get_incremental_parser, get_performance_monitor
    PERFORMANCE_ENABLED = True
except ImportError:
    # Graceful fallback if performance modules not available
    PERFORMANCE_ENABLED = False


@dataclass
class TestCase:
    """Represents a single test case."""
    statements: List[str]
    assertion: str
    message: str
    line_number: int


@dataclass
class TestBlock:
    """Represents a test: block."""
    test_cases: List[TestCase]
    context: str  # 'method', 'class', or 'function'
    parent_name: Optional[str] = None
    line_number: int = 0


@dataclass
class DocBlock:
    """Represents a doc: block."""
    content: List[str]
    context: str  # 'method', 'class', or 'function'
    parent_name: Optional[str] = None
    line_number: int = 0


@dataclass
class MethodDef:
    """Represents a method definition."""
    name: str
    parameters: List[str]
    body: List[str]
    test_blocks: List[TestBlock]
    doc_blocks: List[DocBlock]
    line_number: int


@dataclass
class ClassDef:
    """Represents a class definition."""
    name: str
    methods: List[MethodDef]
    test_blocks: List[TestBlock]
    doc_blocks: List[DocBlock]
    line_number: int


@dataclass
class FunctionDef:
    """Represents a function definition."""
    name: str
    parameters: List[str]
    body: List[str]
    test_blocks: List[TestBlock]
    doc_blocks: List[DocBlock]
    line_number: int


@dataclass
class ParsedProgram:
    """Represents the entire parsed program."""
    classes: List[ClassDef]
    functions: List[FunctionDef]
    global_test_blocks: List[TestBlock]
    global_doc_blocks: List[DocBlock]


class PyTestEmbedParser:
    """Parser for PyTestEmbed custom syntax with performance optimizations."""

    def __init__(self):
        self.current_line = 0
        self.lines = []

        # Performance optimization components
        if PERFORMANCE_ENABLED:
            self.cache_manager = get_cache_manager()
            self.incremental_parser = get_incremental_parser()
            self.performance_monitor = get_performance_monitor()
        else:
            self.cache_manager = None
            self.incremental_parser = None
            self.performance_monitor = None
    
    def parse_file(self, file_path: str) -> ParsedProgram:
        """Parse a PyTestEmbed file with caching and performance monitoring."""
        if self.performance_monitor:
            self.performance_monitor.start_timer(f"parse_file_{file_path}")

        try:
            # Try incremental parsing first
            if self.incremental_parser:
                result = self.incremental_parser.parse_incrementally(file_path, self._parse_file_content)
                if result:
                    return result

            # Fallback to regular parsing
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            result = self.parse_content(content)

            # Cache the result
            if self.cache_manager:
                self.cache_manager.set_parsed_file_cache(file_path, result)

            return result

        finally:
            if self.performance_monitor:
                self.performance_monitor.end_timer(f"parse_file_{file_path}")

    def _parse_file_content(self, content: str) -> ParsedProgram:
        """Internal method for parsing file content (used by incremental parser)."""
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> ParsedProgram:
        """Parse PyTestEmbed content with performance monitoring."""
        if self.performance_monitor:
            self.performance_monitor.start_timer("parse_content")

        try:
            self.lines = content.split('\n')
            self.current_line = 0

            return self._parse_program()

        finally:
            if self.performance_monitor:
                self.performance_monitor.end_timer("parse_content")

    def _parse_program(self) -> ParsedProgram:
        """Internal method to parse the program structure."""
        
        classes = []
        functions = []
        global_test_blocks = []
        global_doc_blocks = []
        
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].strip()

            if line.startswith('class '):
                class_def = self._parse_class()
                if class_def:
                    classes.append(class_def)
            elif line.startswith('def '):
                func_def = self._parse_function()
                if func_def:
                    functions.append(func_def)
            elif line == 'test:':
                test_block = self._parse_test_block('global')
                if test_block:
                    global_test_blocks.append(test_block)
            elif line == 'doc:':
                doc_block = self._parse_doc_block('global')
                if doc_block:
                    global_doc_blocks.append(doc_block)
            else:
                self.current_line += 1
        
        return ParsedProgram(
            classes=classes,
            functions=functions,
            global_test_blocks=global_test_blocks,
            global_doc_blocks=global_doc_blocks
        )
    
    def _parse_class(self) -> Optional[ClassDef]:
        """Parse a class definition."""
        line = self.lines[self.current_line].strip()
        start_line = self.current_line

        # Extract class name
        match = re.match(r'class\s+(\w+)\s*:', line)
        if not match:
            self.current_line += 1
            return None

        class_name = match.group(1)
        self.current_line += 1

        methods = []
        test_blocks = []
        doc_blocks = []

        # Parse class body - collect methods and their associated test/doc blocks
        while (self.current_line < len(self.lines)):
            line = self.lines[self.current_line].strip()
            indent = self._get_indent_level(self.current_line)

            # If we hit a line with no indentation, check if it's a class-level test/doc block
            if line and indent == 0:
                if line in ['test:', 'doc:']:
                    # This is a class-level test or doc block
                    if line == 'test:':
                        test_block = self._parse_test_block('class', class_name)
                        if test_block:
                            test_blocks.append(test_block)
                    elif line == 'doc:':
                        doc_block = self._parse_doc_block('class', class_name)
                        if doc_block:
                            doc_blocks.append(doc_block)
                    # Continue to next iteration to check for more class-level blocks
                    continue
                else:
                    # We've hit something else at global level, done with class
                    break

            # Skip empty lines
            elif not line:
                self.current_line += 1
                continue

            # Class-level content should be indented 4 spaces
            elif indent == 4:
                if line.startswith('def '):
                    # Parse method and its associated test/doc blocks
                    method = self._parse_method_with_blocks()
                    if method:
                        methods.append(method)
                elif line == 'test:':
                    test_block = self._parse_test_block('class', class_name)
                    if test_block:
                        test_blocks.append(test_block)
                elif line == 'doc:':
                    doc_block = self._parse_doc_block('class', class_name)
                    if doc_block:
                        doc_blocks.append(doc_block)
                else:
                    self.current_line += 1
            else:
                self.current_line += 1

        return ClassDef(
            name=class_name,
            methods=methods,
            test_blocks=test_blocks,
            doc_blocks=doc_blocks,
            line_number=start_line + 1
        )

    def _parse_method_with_blocks(self) -> Optional[MethodDef]:
        """Parse a method definition along with its test and doc blocks."""
        line = self.lines[self.current_line].strip()
        start_line = self.current_line

        # Extract method name and parameters
        match = re.match(r'def\s+(\w+)\s*\((.*?)\)\s*:', line)
        if not match:
            self.current_line += 1
            return None

        method_name = match.group(1)
        params_str = match.group(2)
        parameters = [p.strip() for p in params_str.split(',') if p.strip()]

        self.current_line += 1

        body = []
        test_blocks = []
        doc_blocks = []

        # First, parse the method body (8-space indented lines)
        while (self.current_line < len(self.lines)):
            line = self.lines[self.current_line].strip()
            indent = self._get_indent_level(self.current_line)

            # Skip empty lines
            if not line:
                self.current_line += 1
                continue

            # Method body should be indented 8 spaces
            if indent == 8:
                body.append(line)
                self.current_line += 1
            else:
                # We've hit something that's not method body
                break

        # Now parse any test: or doc: blocks that immediately follow at 4-space indentation
        while (self.current_line < len(self.lines)):
            line = self.lines[self.current_line].strip()
            indent = self._get_indent_level(self.current_line)

            # Skip empty lines
            if not line:
                self.current_line += 1
                continue

            # Check for test: or doc: blocks at 4-space indentation
            if indent == 4 and line in ['test:', 'doc:']:
                if line == 'test:':
                    test_block = self._parse_test_block('method', method_name)
                    if test_block:
                        test_blocks.append(test_block)
                elif line == 'doc:':
                    doc_block = self._parse_doc_block('method', method_name)
                    if doc_block:
                        doc_blocks.append(doc_block)
            elif indent < 4 and line:
                # We've hit something at global level (0 indentation), stop parsing this method
                break
            elif indent == 4 and line and not line.startswith(('test:', 'doc:')):
                # We've hit something else at class level, stop parsing this method
                break
            else:
                # Continue to next line for other cases
                self.current_line += 1

        return MethodDef(
            name=method_name,
            parameters=parameters,
            body=body,
            test_blocks=test_blocks,
            doc_blocks=doc_blocks,
            line_number=start_line + 1
        )

    def _parse_method(self) -> Optional[MethodDef]:
        """Parse a method definition."""
        line = self.lines[self.current_line].strip()
        start_line = self.current_line

        # Extract method name and parameters
        match = re.match(r'def\s+(\w+)\s*\((.*?)\)\s*:', line)
        if not match:
            self.current_line += 1
            return None

        method_name = match.group(1)
        params_str = match.group(2)
        parameters = [p.strip() for p in params_str.split(',') if p.strip()]

        self.current_line += 1

        body = []
        test_blocks = []
        doc_blocks = []

        # Parse method body - expect 8-space indentation for method content
        while (self.current_line < len(self.lines)):
            line = self.lines[self.current_line].strip()
            indent = self._get_indent_level(self.current_line)

            # If we hit a line with 4 or fewer spaces (or 0), we're done with the method
            if line and indent <= 4:
                break

            # Skip empty lines
            if not line:
                self.current_line += 1
                continue

            # Method body should be indented 8 spaces, test/doc blocks at 4 spaces
            if indent == 4 and line in ['test:', 'doc:']:
                if line == 'test:':
                    test_block = self._parse_test_block('method', method_name)
                    if test_block:
                        test_blocks.append(test_block)
                elif line == 'doc:':
                    doc_block = self._parse_doc_block('method', method_name)
                    if doc_block:
                        doc_blocks.append(doc_block)
            elif indent == 8 and line and not line.startswith(('test:', 'doc:')):
                body.append(line)
                self.current_line += 1
            else:
                self.current_line += 1

        return MethodDef(
            name=method_name,
            parameters=parameters,
            body=body,
            test_blocks=test_blocks,
            doc_blocks=doc_blocks,
            line_number=start_line + 1
        )
    
    def _parse_function(self) -> Optional[FunctionDef]:
        """Parse a function definition along with its test and doc blocks."""
        line = self.lines[self.current_line].strip()
        start_line = self.current_line

        # Extract function name and parameters
        match = re.match(r'def\s+(\w+)\s*\((.*?)\)\s*:', line)
        if not match:
            self.current_line += 1
            return None

        func_name = match.group(1)
        params_str = match.group(2)
        parameters = [p.strip() for p in params_str.split(',') if p.strip()]

        self.current_line += 1

        body = []
        test_blocks = []
        doc_blocks = []

        # First, parse the function body (4+ space indented lines)
        while (self.current_line < len(self.lines)):
            line = self.lines[self.current_line].strip()
            indent = self._get_indent_level(self.current_line)

            # Skip empty lines
            if not line:
                self.current_line += 1
                continue

            # Function body should be indented 4 or more spaces
            if indent >= 4:
                body.append(line)
                self.current_line += 1
            else:
                # We've hit something that's not function body (0-space indented)
                break

        # Now parse any test: or doc: blocks that immediately follow at 0-space indentation
        while (self.current_line < len(self.lines)):
            line = self.lines[self.current_line].strip()
            indent = self._get_indent_level(self.current_line)

            # Skip empty lines
            if not line:
                self.current_line += 1
                continue

            # Check for test: or doc: blocks at 0-space indentation
            if indent == 0 and line in ['test:', 'doc:']:
                if line == 'test:':
                    test_block = self._parse_test_block('function', func_name)
                    if test_block:
                        test_blocks.append(test_block)
                elif line == 'doc:':
                    doc_block = self._parse_doc_block('function', func_name)
                    if doc_block:
                        doc_blocks.append(doc_block)
            else:
                # We've hit something else, stop parsing this function
                break

        return FunctionDef(
            name=func_name,
            parameters=parameters,
            body=body,
            test_blocks=test_blocks,
            doc_blocks=doc_blocks,
            line_number=start_line + 1
        )
    
    def _parse_test_block(self, context: str, parent_name: Optional[str] = None) -> Optional[TestBlock]:
        """Parse a test: block."""
        start_line = self.current_line
        test_line_indent = self._get_indent_level(self.current_line)
        self.current_line += 1  # Skip 'test:' line

        test_cases = []
        current_statements = []

        # Test content is always indented 4 spaces from the test: line
        # For method-level: test: at 4 spaces, content at 8 spaces
        # For class-level (inside class): test: at 4 spaces, content at 8 spaces
        # For class-level (after class): test: at 0 spaces, content at 4 spaces
        # For global: test: at 0 spaces, content at 4 spaces
        expected_indent = test_line_indent + 4

        while (self.current_line < len(self.lines)):
            line = self.lines[self.current_line].strip()
            indent = self._get_indent_level(self.current_line)

            # If we hit a line with less indentation than expected, we're done
            if line and indent < expected_indent:
                break

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                self.current_line += 1
                continue

            # Only process lines with the expected indentation
            if indent == expected_indent:
                # Check if this line contains an assertion
                # Look for any comparison operator followed by a colon and message
                comparison_operators = ['==', '!=', '<', '>', '<=', '>=', ' in ', ' not in ', ' is ', ' is not ']
                has_comparison = any(op in line for op in comparison_operators)

                if has_comparison and ':' in line:
                    # This is an assertion line
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        assertion_part = parts[0].strip()
                        message_part = parts[1].strip().rstrip(',')

                        test_case = TestCase(
                            statements=current_statements.copy(),
                            assertion=assertion_part,
                            message=message_part,
                            line_number=self.current_line + 1
                        )
                        test_cases.append(test_case)
                        current_statements = []
                else:
                    # This is a statement line
                    current_statements.append(line.rstrip(','))

            self.current_line += 1

        if not test_cases:
            return None

        return TestBlock(
            test_cases=test_cases,
            context=context,
            parent_name=parent_name,
            line_number=start_line + 1
        )
    
    def _parse_doc_block(self, context: str, parent_name: Optional[str] = None) -> Optional[DocBlock]:
        """Parse a doc: block."""
        start_line = self.current_line
        doc_line_indent = self._get_indent_level(self.current_line)
        self.current_line += 1  # Skip 'doc:' line

        content = []

        # Doc content is always indented 4 spaces from the doc: line
        # For method-level: doc: at 4 spaces, content at 8 spaces
        # For class-level (inside class): doc: at 4 spaces, content at 8 spaces
        # For class-level (after class): doc: at 0 spaces, content at 4 spaces
        # For global: doc: at 0 spaces, content at 4 spaces
        expected_indent = doc_line_indent + 4

        while (self.current_line < len(self.lines)):
            line = self.lines[self.current_line].strip()
            indent = self._get_indent_level(self.current_line)

            # If we hit a line with less indentation than expected, we're done
            if line and indent < expected_indent:
                break

            # Only process lines with the expected indentation
            if indent == expected_indent and line:
                content.append(line)

            self.current_line += 1

        if not content:
            return None

        return DocBlock(
            content=content,
            context=context,
            parent_name=parent_name,
            line_number=start_line + 1
        )
    
    def _get_indent_level(self, line_index: int) -> int:
        """Get the indentation level of a line."""
        if line_index >= len(self.lines):
            return 0
        
        line = self.lines[line_index]
        if not line.strip():
            return 0
        
        indent = 0
        for char in line:
            if char == ' ':
                indent += 1
            elif char == '\t':
                indent += 4
            else:
                break
        
        return indent

    def extract_test_expression_from_line(self, line_text: str) -> Optional[str]:
        """
        Extract test expression from a line of code.
        This replaces the VSCode extension's extractTestExpression function.

        Args:
            line_text: The line of code to parse

        Returns:
            The test expression if found, None otherwise
        """
        line = line_text.strip()

        # Check for PyTestEmbed test syntax: expression == expected: "description"
        # Look for comparison operators followed by a colon and message
        comparison_operators = ['==', '!=', '<', '>', '<=', '>=', ' in ', ' not in ', ' is ', ' is not ']
        has_comparison = any(op in line for op in comparison_operators)

        if has_comparison and ':' in line:
            # Split on the first colon to separate assertion from message
            parts = line.split(':', 1)
            if len(parts) == 2:
                assertion_part = parts[0].strip()
                message_part = parts[1].strip()

                # Verify the message part looks like a quoted string
                if (message_part.startswith('"') and message_part.rstrip(',').endswith('"')) or \
                   (message_part.startswith("'") and message_part.rstrip(',').endswith("'")):
                    return assertion_part

        return None

    def discover_all_tests_in_file(self, file_path: str) -> List[Dict]:
        """
        Discover all test expressions in a file with their metadata.
        This provides comprehensive test discovery for IDE integration.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            List of test metadata dictionaries with keys:
            - line_number: 0-based line number
            - expression: The test expression
            - message: The test description
            - context: The context (function, class, global)
            - parent_name: Name of parent function/class if applicable
        """
        try:
            parsed_program = self.parse_file(file_path)
            tests = []

            # Collect tests from functions
            for func in parsed_program.functions:
                for test_block in func.test_blocks:
                    for test_case in test_block.test_cases:
                        tests.append({
                            'line_number': test_case.line_number - 1,  # Convert to 0-based
                            'expression': test_case.assertion,
                            'message': test_case.message,
                            'context': 'function',
                            'parent_name': func.name,
                            'statements': test_case.statements
                        })

            # Collect tests from class methods
            for cls in parsed_program.classes:
                for method in cls.methods:
                    for test_block in method.test_blocks:
                        for test_case in test_block.test_cases:
                            tests.append({
                                'line_number': test_case.line_number - 1,  # Convert to 0-based
                                'expression': test_case.assertion,
                                'message': test_case.message,
                                'context': 'method',
                                'parent_name': f"{cls.name}.{method.name}",
                                'class_name': cls.name,
                                'method_name': method.name,
                                'statements': test_case.statements
                            })

                # Collect class-level tests
                for test_block in cls.test_blocks:
                    for test_case in test_block.test_cases:
                        tests.append({
                            'line_number': test_case.line_number - 1,  # Convert to 0-based
                            'expression': test_case.assertion,
                            'message': test_case.message,
                            'context': 'class',
                            'parent_name': cls.name,
                            'class_name': cls.name,
                            'statements': test_case.statements
                        })

            # Collect global tests
            for test_block in parsed_program.global_test_blocks:
                for test_case in test_block.test_cases:
                    tests.append({
                        'line_number': test_case.line_number - 1,  # Convert to 0-based
                        'expression': test_case.assertion,
                        'message': test_case.message,
                        'context': 'global',
                        'parent_name': None,
                        'statements': test_case.statements
                    })

            return tests

        except Exception as e:
            print(f"Error discovering tests in {file_path}: {e}")
            return []

    def find_test_at_line(self, file_path: str, line_number: int) -> Optional[Dict]:
        """
        Find the test expression at a specific line number.

        Args:
            file_path: Path to the Python file
            line_number: 0-based line number

        Returns:
            Test metadata dictionary if found, None otherwise
        """
        all_tests = self.discover_all_tests_in_file(file_path)

        for test in all_tests:
            if test['line_number'] == line_number:
                return test

        return None

    def extract_test_context(self, file_path: str, line_number: int) -> str:
        """
        Extract context code needed to run a test (variables defined before).
        This replaces the VSCode extension's extractTestContext function.

        Args:
            file_path: Path to the Python file
            line_number: 0-based line number of the test

        Returns:
            Context code as a string
        """
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            if line_number >= len(lines):
                return ""

            # Find the start of the test block
            block_start_line = line_number
            for i in range(line_number, -1, -1):
                if i < len(lines) and lines[i].strip() == 'test:':
                    block_start_line = i
                    break

            # Collect all lines between test: and the current test line
            context_lines = []
            for i in range(block_start_line + 1, line_number):
                if i < len(lines):
                    line_text = lines[i]
                    trimmed_text = line_text.strip()

                    # Skip empty lines and test expressions (lines that look like assertions)
                    # Test expressions match pattern: expression: "description"
                    if trimmed_text and not self._is_test_assertion_line(trimmed_text):
                        context_lines.append(line_text.rstrip())

            return '\n'.join(context_lines)

        except Exception as e:
            print(f"Error extracting test context from {file_path}:{line_number}: {e}")
            return ""

    def _is_test_assertion_line(self, line: str) -> bool:
        """Check if a line is a test assertion (expression: "description")."""
        # Look for pattern: something: "description" with optional comma
        import re
        pattern = r'^.+:\s*["\'].*["\'][,]?$'
        return bool(re.match(pattern, line.strip()))
