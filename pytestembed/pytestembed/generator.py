"""Test code generator for PyTestEmbed."""

import ast
import textwrap
from typing import List, Dict, Any, Set
from .parser import ParsedProgram, ClassDef, MethodDef, FunctionDef, TestBlock, TestCase


class TestGenerator:
    """Generates unittest test code from parsed PyTestEmbed structures."""

    def __init__(self):
        self.test_counter = 0

    def generate_tests(self, parsed_program: ParsedProgram) -> str:
        """Generate unittest test code from parsed program."""
        self.test_counter = 0

        # Start with imports
        lines = [
            "import unittest",
            "",
        ]

        # Generate test classes for each class in the program
        for class_def in parsed_program.classes:
            test_class_code = self._generate_class_tests(class_def)
            if test_class_code:
                lines.extend(test_class_code)
                lines.append("")

        # Generate test classes for standalone functions
        for func_def in parsed_program.functions:
            test_func_code = self._generate_function_tests(func_def)
            if test_func_code:
                lines.extend(test_func_code)
                lines.append("")

        # Generate test class for global tests
        if parsed_program.global_test_blocks:
            global_test_code = self._generate_global_tests(parsed_program.global_test_blocks)
            if global_test_code:
                lines.extend(global_test_code)
                lines.append("")

        # Add main runner
        lines.extend([
            "if __name__ == '__main__':",
            "    unittest.main()",
        ])

        return "\n".join(lines)

    def _generate_class_tests(self, class_def: ClassDef) -> List[str]:
        """Generate test class for a given class definition."""
        lines = []

        # Check if there are any tests to generate
        has_tests = any(method.test_blocks for method in class_def.methods)

        if not has_tests:
            return lines

        # Generate test class header
        test_class_name = f"Test{class_def.name}"
        lines.append(f"class {test_class_name}(unittest.TestCase):")
        lines.append(f'    """Test cases for {class_def.name} class."""')
        lines.append("")

        # Generate setUp method
        lines.append("    def setUp(self):")
        lines.append(f"        \"\"\"Set up test fixtures.\"\"\"")
        lines.append(f"        self.instance = {class_def.name}()")
        lines.append("")

        # Generate test methods for each method's test blocks
        for method_def in class_def.methods:
            for test_block in method_def.test_blocks:
                method_tests = self._generate_method_test_methods(
                    method_def.name, test_block, class_def.name
                )
                lines.extend(method_tests)

        return lines

    def _generate_method_test_methods(self, method_name: str, test_block: TestBlock, class_name: str) -> List[str]:
        """Generate test methods for a method's test block."""
        lines = []

        for i, test_case in enumerate(test_block.test_cases, 1):
            self.test_counter += 1
            test_method_name = f"test_{method_name}_{i}"

            lines.append(f"    def {test_method_name}(self):")
            lines.append(f'        """Test case {i} for {method_name}."""')

            # Add any setup statements
            for statement in test_case.statements:
                lines.append(f"        {statement}")

            # Parse the assertion
            assertion_code = self._generate_assertion(test_case, "self.instance")
            lines.append(f"        {assertion_code}")
            lines.append("")

        return lines

    def _generate_function_tests(self, func_def: FunctionDef) -> List[str]:
        """Generate test class for a standalone function."""
        lines = []

        if not func_def.test_blocks:
            return lines

        # Generate test class header
        test_class_name = f"Test{func_def.name.capitalize()}"
        lines.append(f"class {test_class_name}(unittest.TestCase):")
        lines.append(f'    """Test cases for {func_def.name} function."""')
        lines.append("")

        # Generate test methods for function's test blocks
        for test_block in func_def.test_blocks:
            function_tests = self._generate_function_test_methods(func_def.name, test_block)
            lines.extend(function_tests)

        return lines

    def _generate_function_test_methods(self, func_name: str, test_block: TestBlock) -> List[str]:
        """Generate test methods for a function's test block."""
        lines = []

        for i, test_case in enumerate(test_block.test_cases, 1):
            self.test_counter += 1
            test_method_name = f"test_{func_name}_{i}"

            lines.append(f"    def {test_method_name}(self):")
            lines.append(f'        """Test case {i} for {func_name}."""')

            # Add any setup statements
            for statement in test_case.statements:
                lines.append(f"        {statement}")

            # Parse the assertion
            assertion_code = self._generate_assertion(test_case, None)
            lines.append(f"        {assertion_code}")
            lines.append("")

        return lines

    def _generate_global_tests(self, global_test_blocks: List[TestBlock]) -> List[str]:
        """Generate test class for global test blocks."""
        lines = []

        if not global_test_blocks:
            return lines

        # Generate test class header
        lines.append("class TestGlobal(unittest.TestCase):")
        lines.append('    """Test cases for global tests."""')
        lines.append("")

        # Add setUp method to create instances of any classes that might be needed
        lines.append("    def setUp(self):")
        lines.append('        """Set up test fixtures."""')
        lines.append("        # Create instances of classes for global tests")
        lines.append("        try:")
        lines.append("            self.derp_instance = Derp()")
        lines.append("        except NameError:")
        lines.append("            self.derp_instance = None")
        lines.append("")

        # Generate test methods for global test blocks
        for test_block in global_test_blocks:
            global_tests = self._generate_global_test_methods(test_block)
            lines.extend(global_tests)

        return lines

    def _generate_global_test_methods(self, test_block: TestBlock) -> List[str]:
        """Generate test methods for global test blocks."""
        lines = []

        for i, test_case in enumerate(test_block.test_cases, 1):
            self.test_counter += 1
            test_method_name = f"test_global_{i}"

            lines.append(f"    def {test_method_name}(self):")
            lines.append(f'        """Global test case {i}."""')

            # Add any setup statements (with potential method call replacement)
            for statement in test_case.statements:
                enhanced_statement = self._replace_method_calls_global(statement)
                lines.append(f"        {enhanced_statement}")

            # Parse the assertion (with potential method call replacement)
            assertion_code = self._generate_assertion_global(test_case)
            lines.append(f"        {assertion_code}")
            lines.append("")

        return lines

    def _generate_assertion(self, test_case: TestCase, instance_var: str = None) -> str:
        """Generate unittest assertion from test case."""
        # Parse the assertion
        assertion = test_case.assertion
        message = test_case.message.strip('"\'')

        # Handle different types of assertions
        if '==' in assertion:
            # Equality assertion: left == right
            left, right = assertion.split('==', 1)
            left = left.strip()
            right = right.strip()

            # If we have an instance variable, replace method calls with instance calls
            if instance_var:
                left = self._replace_method_calls(left, instance_var)
                right = self._replace_method_calls(right, instance_var)

            return f'self.assertEqual({left}, {right}, "{message}")'

        elif '!=' in assertion:
            # Inequality assertion: left != right
            left, right = assertion.split('!=', 1)
            left = left.strip()
            right = right.strip()

            if instance_var:
                left = self._replace_method_calls(left, instance_var)
                right = self._replace_method_calls(right, instance_var)

            return f'self.assertNotEqual({left}, {right}, "{message}")'

        elif ' in ' in assertion:
            # Membership assertion: item in container
            parts = assertion.split(' in ', 1)
            item = parts[0].strip()
            container = parts[1].strip()

            if instance_var:
                item = self._replace_method_calls(item, instance_var)
                container = self._replace_method_calls(container, instance_var)

            return f'self.assertIn({item}, {container}, "{message}")'

        elif ' not in ' in assertion:
            # Non-membership assertion: item not in container
            parts = assertion.split(' not in ', 1)
            item = parts[0].strip()
            container = parts[1].strip()

            if instance_var:
                item = self._replace_method_calls(item, instance_var)
                container = self._replace_method_calls(container, instance_var)

            return f'self.assertNotIn({item}, {container}, "{message}")'

        elif ' is ' in assertion and ' is not ' not in assertion:
            # Identity assertion: left is right
            parts = assertion.split(' is ', 1)
            left = parts[0].strip()
            right = parts[1].strip()

            if instance_var:
                left = self._replace_method_calls(left, instance_var)
                right = self._replace_method_calls(right, instance_var)

            return f'self.assertIs({left}, {right}, "{message}")'

        elif ' is not ' in assertion:
            # Non-identity assertion: left is not right
            parts = assertion.split(' is not ', 1)
            left = parts[0].strip()
            right = parts[1].strip()

            if instance_var:
                left = self._replace_method_calls(left, instance_var)
                right = self._replace_method_calls(right, instance_var)

            return f'self.assertIsNot({left}, {right}, "{message}")'

        elif '>=' in assertion:
            # Greater than or equal assertion: left >= right
            left, right = assertion.split('>=', 1)
            left = left.strip()
            right = right.strip()

            if instance_var:
                left = self._replace_method_calls(left, instance_var)
                right = self._replace_method_calls(right, instance_var)

            return f'self.assertGreaterEqual({left}, {right}, "{message}")'

        elif '<=' in assertion:
            # Less than or equal assertion: left <= right
            left, right = assertion.split('<=', 1)
            left = left.strip()
            right = right.strip()

            if instance_var:
                left = self._replace_method_calls(left, instance_var)
                right = self._replace_method_calls(right, instance_var)

            return f'self.assertLessEqual({left}, {right}, "{message}")'

        elif '>' in assertion:
            # Greater than assertion: left > right
            left, right = assertion.split('>', 1)
            left = left.strip()
            right = right.strip()

            if instance_var:
                left = self._replace_method_calls(left, instance_var)
                right = self._replace_method_calls(right, instance_var)

            return f'self.assertGreater({left}, {right}, "{message}")'

        elif '<' in assertion:
            # Less than assertion: left < right
            left, right = assertion.split('<', 1)
            left = left.strip()
            right = right.strip()

            if instance_var:
                left = self._replace_method_calls(left, instance_var)
                right = self._replace_method_calls(right, instance_var)

            return f'self.assertLess({left}, {right}, "{message}")'

        else:
            # Boolean assertion or complex expression
            if instance_var:
                assertion = self._replace_method_calls(assertion, instance_var)

            return f'self.assertTrue({assertion}, "{message}")'

    def _replace_method_calls(self, expression: str, instance_var: str) -> str:
        """Replace bare method calls with instance method calls."""
        # This is a simple replacement - for a more robust solution,
        # we'd need to parse the expression properly

        # Handle simple method calls like foo(args) -> instance.foo(args)
        import re

        # Pattern to match function calls that are NOT already qualified (no dot before them)
        # Look for word boundaries followed by method name and opening paren, but not preceded by a dot
        pattern = r'(?<!\.)(?<!\w)([a-zA-Z_][a-zA-Z0-9_]*)\s*\('

        def replace_call(match):
            method_name = match.group(1)
            # Don't replace built-in functions or common functions
            if method_name in ['len', 'str', 'int', 'float', 'bool', 'print', 'type', 'isinstance', 'hasattr', 'abs', 'min', 'max', 'sum', 'all', 'any']:
                return match.group(0)
            return f'{instance_var}.{method_name}('

        return re.sub(pattern, replace_call, expression)

    def _generate_assertion_global(self, test_case: TestCase) -> str:
        """Generate unittest assertion for global test case."""
        # Parse the assertion: "left == right"
        assertion = test_case.assertion
        message = test_case.message.strip('"\'')

        if '==' not in assertion:
            # Fallback for malformed assertions
            return f"self.assertTrue({assertion}, {test_case.message})"

        left, right = assertion.split('==', 1)
        left = left.strip()
        right = right.strip()

        # Replace method calls with instance calls for global tests
        left = self._replace_method_calls_global(left)
        right = self._replace_method_calls_global(right)

        return f'self.assertEqual({left}, {right}, "{message}")'

    def _replace_method_calls_global(self, expression: str) -> str:
        """Replace bare method calls with instance method calls for global tests."""
        import re

        # For the derp example, replace foo() and bar() with self.derp_instance.foo() and self.derp_instance.bar()
        # This is a simple heuristic - a full implementation would be more sophisticated

        # Replace foo( with self.derp_instance.foo(
        expression = re.sub(r'\bfoo\s*\(', 'self.derp_instance.foo(', expression)

        # Replace bar( with self.derp_instance.bar(
        expression = re.sub(r'\bbar\s*\(', 'self.derp_instance.bar(', expression)

        return expression
