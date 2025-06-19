
"""
PyTestEmbed Full Feature Demonstration
=====================================

This file demonstrates all PyTestEmbed capabilities:
- Simple and complex test syntax
- Cross-file dependencies and imports
- Class and function testing
- Documentation blocks
- Error handling and edge cases
- AI-generated content examples
"""

# Import from derp.py to show cross-file dependency tracking
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from derp import Derp
    IMPORTS_AVAILABLE = True
except ImportError:
    # Fallback if derp.py is not available - create mock implementations
    IMPORTS_AVAILABLE = False

    class Derp:
        """Mock Derp class for demonstration"""
        def foo(self, x):
            return x / 2

        def bar(self, x):
            return x * 2


class Calculator:
    """Advanced calculator with comprehensive testing"""
    
    def __init__(self, precision=2):
        self.precision = precision
        self.history = []
    
    def add(self, a, b):
        """Add two numbers with history tracking"""
        result = round(a + b, self.precision)
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers"""
        result = round(a * b, self.precision)
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a, b):
        """Divide with zero protection"""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = round(a / b, self.precision)
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def get_history(self):
        """Get calculation history"""
        return self.history.copy()
    
    def clear_history(self):
        """Clear calculation history"""
        self.history.clear()

test:
    add(2, 3) == 5: "basic addition works",
    multiply(4, 5) == 20: "basic multiplication works",
    divide(10, 2) == 5: "basic division works",
    add(1, 1)
    len(get_history()) == 1: "history tracking works",
    add(1, 1)
    clear_history()
    len(get_history()) == 0: "history clearing works"

doc:
    Calculator class provides mathematical operations with history tracking.
    
    Features:
    - Configurable precision
    - Operation history
    - Error handling for division by zero
    - Memory management with clear functionality

def fibonacci(n):
    """Generate fibonacci sequence up to n terms"""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    return sequence

test:
    fibonacci(0) == []: "empty sequence for zero",
    fibonacci(1) == [0]: "single element sequence",
    fibonacci(2) == [0, 1]: "two element sequence",
    fibonacci(5) == [0, 1, 1, 2, 3]: "five element fibonacci",
    fibonacci(8) == [0, 1, 1, 2, 3, 5, 8, 13]: "eight element fibonacci",
    len(fibonacci(10)) == 10: "correct length for 10 terms"

doc:
    Generates the Fibonacci sequence where each number is the sum of the two preceding ones.

    Args:
        n (int): Number of terms to generate
        
    Returns:
        list: Fibonacci sequence up to n terms
        
    Examples:
        fibonacci(5) returns [0, 1, 1, 2, 3]

def validate_email(email):
    """Simple email validation"""
    if not email or '@' not in email:
        return False
    
    parts = email.split('@')
    if len(parts) != 2:
        return False
    
    local, domain = parts
    if not local or not domain:
        return False
    
    if '.' not in domain:
        return False
    
    return True

test:
    validate_email("test@example.com") == True: "valid email passes",
    validate_email("invalid.email") == False: "email without @ fails",
    validate_email("@example.com") == False: "email without local part fails",
    validate_email("test@") == False: "email without domain fails",
    validate_email("test@nodot") == False: "domain without dot fails",
    validate_email("") == False: "empty string fails",
    validate_email(None) == False: "None input fails"

doc:
    Validates email addresses using basic rules:
    - Must contain exactly one @ symbol
    - Must have non-empty local and domain parts
    - Domain must contain at least one dot

class DataProcessor:
    """Process and analyze data with various operations"""
    
    def __init__(self):
        self.data = []
    
    def add_data(self, value):
        """Add a single data point"""
        if isinstance(value, (int, float)):
            self.data.append(value)
            return True
        return False
    
    def add_batch(self, values):
        """Add multiple data points"""
        added = 0
        for value in values:
            if self.add_data(value):
                added += 1
        return added
    
    def get_stats(self):
        """Calculate basic statistics"""
        if not self.data:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}
        
        return {
            "count": len(self.data),
            "sum": sum(self.data),
            "avg": sum(self.data) / len(self.data),
            "min": min(self.data),
            "max": max(self.data)
        }
    
    def filter_above(self, threshold):
        """Get values above threshold"""
        return [x for x in self.data if x > threshold]
    
    def reset(self):
        """Clear all data"""
        self.data.clear()

test:
    add_data(10) == True: "adding valid number works",
    add_data("invalid") == False: "adding invalid data fails",
    add_batch([1, 2, 3, 4, 5]) == 5: "batch adding works",
    add_data(10)
    add_batch([1, 2, 3, 4, 5])
    stats = get_stats()
    stats["count"] == 6: "correct count in stats",
    add_data(10)
    add_batch([1, 2, 3, 4, 5])
    stats = get_stats()
    stats["sum"] == 25: "correct sum in stats",
    add_data(10)
    add_batch([1, 2, 3, 4, 5])
    len(filter_above(3)) == 3: "filtering works correctly",
    add_data(10)
    reset()
    len(data) == 0: "reset clears data"

doc:
    DataProcessor handles numerical data with statistical analysis capabilities.
    
    Key features:
    - Type validation for data input
    - Batch processing support
    - Statistical calculations (count, sum, average, min, max)
    - Data filtering and manipulation
    - Memory management with reset functionality

def cross_file_integration_test():
    """Test integration with imported classes and functions"""
    # Test imported Derp class
    derp_instance = Derp()

    # Test imported methods
    foo_result = derp_instance.foo(5)
    bar_result = derp_instance.bar(2)

    # Test Calculator with imported function results
    calc = Calculator()
    combined_result = calc.add(foo_result, bar_result)

    return {
        "derp_created": derp_instance is not None,
        "foo_result": foo_result,
        "bar_result": bar_result,
        "combined": combined_result
    }

test:
    result = cross_file_integration_test()
    result["derp_created"] == True: "can create imported Derp instance",
    result = cross_file_integration_test()
    result["foo_result"] == 2.5: "imported foo method works (5/2)",
    result = cross_file_integration_test()
    result["bar_result"] == 4: "imported bar method works (2*2)",
    result = cross_file_integration_test()
    result["combined"] == 6.5: "can combine imported method results (2.5+4)",
    result = cross_file_integration_test()
    isinstance(result, dict) == True: "returns proper dictionary structure"

doc:
    Demonstrates cross-file dependency integration by importing and using
    classes and functions from test.py. This tests the dependency tracking
    and navigation features of PyTestEmbed.

def error_handling_demo():
    """Demonstrate error handling in tests"""
    calc = Calculator()
    
    try:
        calc.divide(10, 0)
        return "no_error"  # Should not reach here
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"unexpected_error: {e}"

test:
    error_handling_demo() == "Cannot divide by zero": "proper error handling",
    # This test should fail to demonstrate failure indicators
    1 + 1 == 3: "intentional failure for testing",
    len("test") == 4: "this should pass after the failure"

doc:
    Shows how PyTestEmbed handles exceptions and errors in test cases.
    Includes an intentional failure to demonstrate error indicators.

# Global level test and doc blocks
test:
    # Test module-level functionality
    len(__name__) > 0: "module has a name",
    "Calculator" in globals(): "Calculator class is defined",
    "fibonacci" in globals(): "fibonacci function is defined",
    callable(fibonacci): "fibonacci is callable"

doc:
    This module demonstrates the complete feature set of PyTestEmbed including:
    
    1. **Class Testing**: Comprehensive testing of Calculator and DataProcessor classes
    2. **Function Testing**: Individual function tests with various complexity levels
    3. **Cross-file Dependencies**: Integration with imported modules
    4. **Error Handling**: Proper exception handling and failure demonstration
    5. **Documentation**: Rich documentation blocks with examples
    6. **Complex Test Syntax**: Advanced test patterns and assertions
    
    The module serves as both a feature demonstration and a comprehensive test suite
    for validating PyTestEmbed functionality across different scenarios.
