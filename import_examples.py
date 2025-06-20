#!/usr/bin/env python3
"""
PyTestEmbed Import Examples
==========================

This file demonstrates all the supported import patterns for PyTestEmbed.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytestembed as ptb

def demonstrate_import_patterns():
    """Demonstrate all supported PyTestEmbed import patterns."""
    
    print("PyTestEmbed Import Pattern Examples")
    print("=" * 40)
    
    # Pattern 1: from module import Class
    print("\n1. from module import Class")
    print("   Code: Derp = ptb.import_from('from derp import Derp')")
    Derp = ptb.import_from("from derp import Derp")
    instance = Derp()
    print(f"   Result: Derp().foo(4) = {instance.foo(4)}")
    
    # Pattern 2: import module
    print("\n2. import module")
    print("   Code: derp = ptb.import_from('import derp')")
    derp = ptb.import_from("import derp")
    instance2 = derp.Derp()
    print(f"   Result: derp.Derp().bar(3) = {instance2.bar(3)}")
    
    # Pattern 3: Short alias
    print("\n3. Short alias ptb.imp()")
    print("   Code: Derp2 = ptb.imp('from derp import Derp')")
    Derp2 = ptb.imp("from derp import Derp")
    instance3 = Derp2()
    print(f"   Result: Derp2().baz(2) = {instance3.baz(2)}")
    
    # Pattern 4: Standard library (works normally)
    print("\n4. Standard library imports")
    print("   Code: math = ptb.import_from('import math')")
    math = ptb.import_from("import math")
    print(f"   Result: math.sqrt(16) = {math.sqrt(16)}")
    
    # Pattern 5: Multiple imports from same module
    print("\n5. Multiple imports (cached)")
    print("   Code: Multiple calls to same import")
    DerpA = ptb.import_from("from derp import Derp")
    DerpB = ptb.import_from("from derp import Derp")
    print(f"   Result: Both imports work independently")
    
    print("\n" + "=" * 40)
    print("All import patterns work correctly! ✅")
    
    print("\nSupported Import Patterns:")
    print("  • ptb.import_from('from module import Class')")
    print("  • ptb.import_from('import module')")
    print("  • ptb.imp('from module import Class')  # short alias")
    print("  • Works with standard library modules")
    print("  • Automatically detects PyTestEmbed syntax")
    print("  • Falls back to standard import when no test:/doc: blocks")

if __name__ == "__main__":
    demonstrate_import_patterns()
