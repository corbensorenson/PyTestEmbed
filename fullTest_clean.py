#!/usr/bin/env python3
"""Clean version of fullTest.py that can be run directly."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Use PyTestEmbed import system for files with test: and doc: blocks
import pytestembed as ptb
Derp = ptb.import_from("from derp import Derp")

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

def test_integration():
    """Test the cross-file integration"""
    print("Testing cross-file integration...")
    
    result = cross_file_integration_test()
    
    # Test assertions
    assert result["derp_created"] == True, "can create imported Derp instance"
    print("✓ Can create imported Derp instance")
    
    assert result["foo_result"] == 2.5, f"imported foo method works (5/2), got {result['foo_result']}"
    print("✓ Imported foo method works (5/2)")
    
    assert result["bar_result"] == 4, f"imported bar method works (2*2), got {result['bar_result']}"
    print("✓ Imported bar method works (2*2)")
    
    assert result["combined"] == 6.5, f"can combine imported method results (2.5+4), got {result['combined']}"
    print("✓ Can combine imported method results (2.5+4)")
    
    assert isinstance(result, dict) == True, "returns proper dictionary structure"
    print("✓ Returns proper dictionary structure")
    
    print("🎉 All cross-file integration tests passed!")

if __name__ == "__main__":
    test_integration()
