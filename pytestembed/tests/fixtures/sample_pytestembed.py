"""
Sample PyTestEmbed file for testing.

Contains various PyTestEmbed patterns to test parsing and execution.
"""

def add_numbers(a, b):
    """Add two numbers together."""
    return a + b
test:
    add_numbers(2, 3) == 5: "Basic addition",
    add_numbers(0, 0) == 0: "Zero addition",
    add_numbers(-1, 1) == 0: "Negative addition"
doc:
    Adds two numbers and returns the result.
    
    Args:
        a (int): First number
        b (int): Second number
    
    Returns:
        int: Sum of a and b


def multiply_numbers(x, y):
    """Multiply two numbers."""
    return x * y
test:
    multiply_numbers(3, 4) == 12: "Basic multiplication",
    multiply_numbers(0, 5) == 0: "Zero multiplication",
    multiply_numbers(-2, 3) == -6: "Negative multiplication"
doc:
    Multiplies two numbers and returns the result.


def divide_safely(a, b):
    """Divide two numbers with error handling."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
test:
    divide_safely(10, 2) == 5.0: "Basic division",
    divide_safely(7, 2) == 3.5: "Float division"
doc:
    Safely divides two numbers with zero-check.
    
    Args:
        a (float): Dividend
        b (float): Divisor
    
    Returns:
        float: Result of division
    
    Raises:
        ValueError: If divisor is zero


class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers and record in history."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    test:
        calc = Calculator()
        calc.add(2, 3) == 5: "Calculator addition",
        len(calc.history) == 1: "History recorded"
    doc:
        Adds two numbers and stores the operation in history.
        
        Args:
            a (int): First number
            b (int): Second number
        
        Returns:
            int: Sum of the numbers
    
    def get_history(self):
        """Get calculation history."""
        return self.history.copy()
    test:
        calc = Calculator()
        calc.add(1, 2)
        calc.add(3, 4)
        len(calc.get_history()) == 2: "History length correct",
        "1 + 2 = 3" in calc.get_history(): "First operation recorded"
    doc:
        Returns a copy of the calculation history.
        
        Returns:
            list: List of calculation strings


def fibonacci(n):
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
test:
    fibonacci(0) == 0: "Fibonacci base case 0",
    fibonacci(1) == 1: "Fibonacci base case 1",
    fibonacci(5) == 5: "Fibonacci recursive case",
    fibonacci(7) == 13: "Fibonacci larger case"
doc:
    Calculates the nth Fibonacci number using recursion.
    
    Args:
        n (int): Position in Fibonacci sequence
    
    Returns:
        int: The nth Fibonacci number


def process_list(items, operation="sum"):
    """Process a list with different operations."""
    if not items:
        return None
    
    if operation == "sum":
        return sum(items)
    elif operation == "max":
        return max(items)
    elif operation == "min":
        return min(items)
    else:
        raise ValueError(f"Unknown operation: {operation}")
test:
    process_list([1, 2, 3]) == 6: "Sum operation",
    process_list([1, 2, 3], "max") == 3: "Max operation",
    process_list([1, 2, 3], "min") == 1: "Min operation",
    process_list([]) is None: "Empty list handling"
doc:
    Processes a list of numbers with the specified operation.
    
    Args:
        items (list): List of numbers to process
        operation (str): Operation to perform ('sum', 'max', 'min')
    
    Returns:
        int/float/None: Result of operation or None for empty list
    
    Raises:
        ValueError: If operation is not supported
