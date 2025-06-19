"""
Legacy Python file for testing conversion functionality.

This file contains standard Python code without PyTestEmbed syntax
to test the conversion process.
"""

def simple_function(x):
    """A simple function for testing."""
    return x * 2

def function_with_docstring(a, b):
    """
    A function with a detailed docstring.
    
    Args:
        a (int): First parameter
        b (int): Second parameter
    
    Returns:
        int: The sum of a and b
    """
    return a + b

def function_without_docstring(value):
    return value.upper() if isinstance(value, str) else str(value)

class SimpleClass:
    """A simple class for testing."""
    
    def __init__(self, name):
        """Initialize with a name."""
        self.name = name
    
    def get_name(self):
        """Get the name."""
        return self.name
    
    def set_name(self, name):
        """Set the name."""
        self.name = name

def complex_function(data, filters=None, sort_key=None):
    """
    A more complex function for testing.
    
    Args:
        data (list): Input data
        filters (dict, optional): Filters to apply
        sort_key (callable, optional): Sort key function
    
    Returns:
        list: Processed data
    """
    if not data:
        return []
    
    result = data.copy()
    
    if filters:
        for key, value in filters.items():
            if key == "min_value":
                result = [x for x in result if x >= value]
            elif key == "max_value":
                result = [x for x in result if x <= value]
    
    if sort_key:
        result.sort(key=sort_key)
    
    return result

def error_prone_function(x, y):
    """Function that can raise errors."""
    if y == 0:
        raise ValueError("Division by zero")
    if x < 0:
        raise ValueError("Negative input not allowed")
    return x / y
