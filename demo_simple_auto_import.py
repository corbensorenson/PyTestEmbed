#!/usr/bin/env python3
"""
Simple Demo: PyTestEmbed Auto-Import

Shows how clean the import experience is now.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Just import pytestembed - that's it!
import pytestembed

# Now normal Python imports work with PyTestEmbed files
from derp import Derp

def main():
    print("✨ PyTestEmbed Auto-Import Demo")
    print("=" * 32)
    
    print("\nStep 1: Import pytestembed")
    print("   import pytestembed")
    print("   ✓ Auto-import enabled automatically!")
    
    print("\nStep 2: Use normal Python imports")  
    print("   from derp import Derp")
    print("   ✓ PyTestEmbed file imported seamlessly!")
    
    print("\nStep 3: Use the imported class")
    d = Derp()
    print(f"   d.foo(4) = {d.foo(4)}")
    print(f"   d.bar(3) = {d.bar(3)}")
    print(f"   d.baz(2) = {d.baz(2)}")
    print("   ✓ test: and doc: blocks automatically stripped!")
    
    print("\nStep 4: Regular Python modules work too")
    import math
    print(f"   math.sqrt(16) = {math.sqrt(16)}")
    print("   ✓ No interference with standard imports!")
    
    print("\n🎉 That's it! Just two lines:")
    print("   import pytestembed")
    print("   from your_pytestembed_file import YourClass")
    
    print("\n💡 Benefits:")
    print("   • Natural Python syntax")
    print("   • No manual setup required") 
    print("   • IDE navigation works")
    print("   • Zero interference with regular imports")

if __name__ == "__main__":
    main()
