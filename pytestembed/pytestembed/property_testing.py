#!/usr/bin/env python3
"""
Property-Based Testing for PyTestEmbed

Extends PyTestEmbed with property-based testing capabilities,
automatically generating test cases to verify mathematical properties
and invariants of functions.
"""

import ast
import random
import sys
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import inspect
import traceback


@dataclass
class PropertyTestCase:
    """Represents a property-based test case."""
    property_description: str
    property_function: Callable
    generated_inputs: List[Tuple[Any, ...]]
    test_results: List[bool]
    counterexamples: List[Tuple[Any, ...]]
    execution_count: int


@dataclass
class PropertyTestResult:
    """Result of property-based testing."""
    property_name: str
    passed: bool
    tests_run: int
    counterexamples: List[Tuple[Any, ...]]
    error_message: Optional[str]
    coverage_achieved: float


class InputGenerator:
    """Generates test inputs for property-based testing."""
    
    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)
        self.generation_strategies = {
            int: self._generate_int,
            float: self._generate_float,
            str: self._generate_string,
            bool: self._generate_bool,
            list: self._generate_list,
            dict: self._generate_dict,
        }
    
    def generate_inputs(self, func: Callable, count: int = 100) -> List[Tuple[Any, ...]]:
        """Generate test inputs for a function based on its signature."""
        
        sig = inspect.signature(func)
        inputs = []
        
        for _ in range(count):
            args = []
            for param_name, param in sig.parameters.items():
                if param.annotation != inspect.Parameter.empty:
                    # Use type annotation
                    arg_type = param.annotation
                else:
                    # Infer type from default value or use int as fallback
                    if param.default != inspect.Parameter.empty:
                        arg_type = type(param.default)
                    else:
                        arg_type = int
                
                generated_value = self._generate_value(arg_type)
                args.append(generated_value)
            
            inputs.append(tuple(args))
        
        return inputs
    
    def _generate_value(self, value_type: type) -> Any:
        """Generate a single value of the specified type."""
        
        if value_type in self.generation_strategies:
            return self.generation_strategies[value_type]()
        elif hasattr(value_type, '__origin__'):
            # Handle generic types like List[int], Dict[str, int]
            return self._generate_generic_type(value_type)
        else:
            # Fallback to int for unknown types
            return self._generate_int()
    
    def _generate_int(self, min_val: int = -1000, max_val: int = 1000) -> int:
        """Generate random integer."""
        # Include edge cases
        edge_cases = [0, 1, -1, min_val, max_val]
        if self.random.random() < 0.2:  # 20% chance of edge case
            return self.random.choice(edge_cases)
        return self.random.randint(min_val, max_val)
    
    def _generate_float(self, min_val: float = -1000.0, max_val: float = 1000.0) -> float:
        """Generate random float."""
        # Include edge cases
        edge_cases = [0.0, 1.0, -1.0, float('inf'), float('-inf')]
        if self.random.random() < 0.1:  # 10% chance of edge case
            return self.random.choice(edge_cases)
        return self.random.uniform(min_val, max_val)
    
    def _generate_string(self, max_length: int = 50) -> str:
        """Generate random string."""
        # Include edge cases
        if self.random.random() < 0.1:
            return self.random.choice(['', ' ', '\n', '\t', 'a' * 1000])
        
        length = self.random.randint(0, max_length)
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 '
        return ''.join(self.random.choice(chars) for _ in range(length))
    
    def _generate_bool(self) -> bool:
        """Generate random boolean."""
        return self.random.choice([True, False])
    
    def _generate_list(self, max_length: int = 10) -> List[Any]:
        """Generate random list."""
        if self.random.random() < 0.1:
            return []  # Empty list edge case
        
        length = self.random.randint(1, max_length)
        element_type = self.random.choice([int, str, float])
        return [self._generate_value(element_type) for _ in range(length)]
    
    def _generate_dict(self, max_size: int = 5) -> Dict[str, Any]:
        """Generate random dictionary."""
        if self.random.random() < 0.1:
            return {}  # Empty dict edge case
        
        size = self.random.randint(1, max_size)
        result = {}
        for _ in range(size):
            key = self._generate_string(10)
            value_type = self.random.choice([int, str, float, bool])
            result[key] = self._generate_value(value_type)
        return result
    
    def _generate_generic_type(self, generic_type) -> Any:
        """Generate value for generic types like List[int]."""
        # Simplified handling of generic types
        origin = getattr(generic_type, '__origin__', None)
        
        if origin is list:
            return self._generate_list()
        elif origin is dict:
            return self._generate_dict()
        else:
            return self._generate_int()


class PropertyChecker:
    """Checks properties against generated test cases."""
    
    def __init__(self, max_tests: int = 100, max_counterexamples: int = 10):
        self.max_tests = max_tests
        self.max_counterexamples = max_counterexamples
        self.input_generator = InputGenerator()
    
    def check_property(self, target_function: Callable, 
                      property_function: Callable,
                      property_description: str) -> PropertyTestResult:
        """Check a property against a target function."""
        
        print(f"🔍 Checking property: {property_description}")
        
        # Generate test inputs
        inputs = self.input_generator.generate_inputs(target_function, self.max_tests)
        
        counterexamples = []
        tests_run = 0
        errors = []
        
        for test_input in inputs:
            tests_run += 1
            
            try:
                # Call the target function
                result = target_function(*test_input)
                
                # Check the property
                property_holds = property_function(*test_input, result)
                
                if not property_holds:
                    counterexamples.append(test_input)
                    if len(counterexamples) >= self.max_counterexamples:
                        break
                        
            except Exception as e:
                errors.append(f"Input {test_input}: {str(e)}")
                # Continue testing with other inputs
        
        # Determine if property passed
        passed = len(counterexamples) == 0 and len(errors) == 0
        
        # Calculate coverage (simplified)
        coverage = min(1.0, tests_run / self.max_tests)
        
        error_message = None
        if errors:
            error_message = f"Errors encountered: {'; '.join(errors[:3])}"
        elif counterexamples:
            error_message = f"Property violated with inputs: {counterexamples[:3]}"
        
        return PropertyTestResult(
            property_name=property_description,
            passed=passed,
            tests_run=tests_run,
            counterexamples=counterexamples,
            error_message=error_message,
            coverage_achieved=coverage
        )


class PropertyTestParser:
    """Parses property-based test syntax in PyTestEmbed."""
    
    def __init__(self):
        self.property_patterns = [
            'property(',
            'forall(',
            'invariant(',
            'postcondition(',
            'precondition('
        ]
    
    def extract_properties(self, test_block_content: str) -> List[Dict[str, str]]:
        """Extract property-based tests from test block content."""
        
        properties = []
        lines = test_block_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(pattern in line for pattern in self.property_patterns):
                property_info = self._parse_property_line(line)
                if property_info:
                    properties.append(property_info)
        
        return properties
    
    def _parse_property_line(self, line: str) -> Optional[Dict[str, str]]:
        """Parse a single property test line."""
        
        try:
            # Extract property function and description
            if ':' in line:
                property_part, description = line.split(':', 1)
                description = description.strip().strip('"\'')
            else:
                property_part = line
                description = "Property test"
            
            # Extract the property function
            property_code = property_part.strip().rstrip(',')
            
            return {
                'property_code': property_code,
                'description': description,
                'line': line
            }
            
        except Exception as e:
            print(f"⚠️ Error parsing property line '{line}': {e}")
            return None


class PropertyBasedTester:
    """Main class for property-based testing integration."""
    
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = workspace_path
        self.parser = PropertyTestParser()
        self.checker = PropertyChecker()
        self.property_cache: Dict[str, Callable] = {}
    
    def run_property_tests(self, target_function: Callable, 
                          test_block_content: str) -> List[PropertyTestResult]:
        """Run property-based tests for a function."""
        
        properties = self.parser.extract_properties(test_block_content)
        results = []
        
        for prop_info in properties:
            try:
                # Create property function
                property_func = self._create_property_function(
                    prop_info['property_code'], 
                    target_function
                )
                
                # Run property check
                result = self.checker.check_property(
                    target_function,
                    property_func,
                    prop_info['description']
                )
                
                results.append(result)
                
            except Exception as e:
                # Create error result
                error_result = PropertyTestResult(
                    property_name=prop_info['description'],
                    passed=False,
                    tests_run=0,
                    counterexamples=[],
                    error_message=f"Property creation failed: {str(e)}",
                    coverage_achieved=0.0
                )
                results.append(error_result)
        
        return results
    
    def _create_property_function(self, property_code: str, target_function: Callable) -> Callable:
        """Create a property function from property code."""
        
        # Cache compiled properties
        if property_code in self.property_cache:
            return self.property_cache[property_code]
        
        try:
            # Create a safe execution environment
            safe_globals = {
                '__builtins__': {
                    'abs': abs, 'all': all, 'any': any, 'bool': bool,
                    'float': float, 'int': int, 'len': len, 'max': max,
                    'min': min, 'round': round, 'str': str, 'sum': sum,
                    'type': type, 'isinstance': isinstance
                },
                'target_function': target_function
            }
            
            # Handle different property patterns
            if property_code.startswith('property('):
                # Extract lambda from property(lambda ...)
                lambda_code = property_code[9:-1]  # Remove 'property(' and ')'
                if lambda_code.startswith('lambda'):
                    # Compile the lambda
                    property_func = eval(lambda_code, safe_globals)
                else:
                    # Create lambda wrapper
                    property_func = eval(f"lambda *args, result: {lambda_code}", safe_globals)
            
            elif property_code.startswith('forall('):
                # Handle forall quantifier
                lambda_code = property_code[7:-1]  # Remove 'forall(' and ')'
                property_func = eval(f"lambda *args, result: {lambda_code}", safe_globals)
            
            else:
                # Default: treat as boolean expression
                property_func = eval(f"lambda *args, result: {property_code}", safe_globals)
            
            # Cache the compiled property
            self.property_cache[property_code] = property_func
            return property_func
            
        except Exception as e:
            raise ValueError(f"Failed to create property function from '{property_code}': {e}")
    
    def generate_property_suggestions(self, target_function: Callable) -> List[str]:
        """Generate suggested properties for a function based on its signature and behavior."""
        
        suggestions = []
        sig = inspect.signature(target_function)
        func_name = target_function.__name__
        
        # Basic properties based on function name patterns
        if 'add' in func_name.lower() or 'sum' in func_name.lower():
            suggestions.extend([
                "property(lambda a, b, result: result == b + a): \"Addition is commutative\"",
                "property(lambda a, b, result: result >= max(a, b)): \"Sum is at least as large as largest input\""
            ])
        
        elif 'multiply' in func_name.lower() or 'mul' in func_name.lower():
            suggestions.extend([
                "property(lambda a, b, result: result == b * a): \"Multiplication is commutative\"",
                "property(lambda a, b, result: a == 0 or b == 0 or abs(result) >= abs(a)): \"Product magnitude property\""
            ])
        
        elif 'sort' in func_name.lower():
            suggestions.extend([
                "property(lambda lst, result: len(result) == len(lst)): \"Sorted list has same length\"",
                "property(lambda lst, result: all(result[i] <= result[i+1] for i in range(len(result)-1))): \"Result is sorted\""
            ])
        
        elif 'reverse' in func_name.lower():
            suggestions.extend([
                "property(lambda lst, result: len(result) == len(lst)): \"Reversed list has same length\"",
                "property(lambda lst, result: result == lst[::-1]): \"Reverse property\""
            ])
        
        # Generic properties based on parameter count
        param_count = len(sig.parameters)
        
        if param_count == 1:
            suggestions.append("property(lambda x, result: type(result) is not type(None)): \"Function returns non-None value\"")
        
        elif param_count == 2:
            suggestions.append("property(lambda a, b, result: type(result) == type(a) or type(result) == type(b)): \"Result type consistency\"")
        
        # Type-based properties
        for param_name, param in sig.parameters.items():
            if param.annotation == int:
                suggestions.append(f"property(lambda {param_name}, result: isinstance(result, (int, float))): \"Numeric result for int input\"")
            elif param.annotation == str:
                suggestions.append(f"property(lambda {param_name}, result: isinstance(result, str)): \"String result for string input\"")
        
        return suggestions[:5]  # Return top 5 suggestions


# Integration with PyTestEmbed syntax
def extend_pytestembed_with_properties():
    """Extend PyTestEmbed parser to handle property-based tests."""
    
    # This would be integrated into the main PyTestEmbed parser
    # to recognize property() syntax in test blocks
    pass


# CLI interface for property-based testing
def run_property_testing(file_path: str, function_name: str):
    """Run property-based testing from command line."""
    
    print(f"🧪 Running property-based tests for {function_name} in {file_path}")
    
    # Load and execute the function
    # Generate properties
    # Run tests
    # Report results
    
    pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PyTestEmbed Property-Based Testing")
    parser.add_argument("file", help="Python file to test")
    parser.add_argument("function", help="Function name to test")
    
    args = parser.parse_args()
    
    run_property_testing(args.file, args.function)
