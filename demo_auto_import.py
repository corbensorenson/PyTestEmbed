#!/usr/bin/env python3
"""
Demo: PyTestEmbed Auto-Import

This demonstrates how PyTestEmbed can automatically handle imports,
allowing you to use normal Python import syntax even with PyTestEmbed files.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytestembed as ptb

def main():
    print("🚀 PyTestEmbed Auto-Import Demo")
    print("=" * 40)
    
    # Enable auto-import
    print("\n1. Enabling auto-import...")
    ptb.enable_auto_import()
    
    print("\n2. Now you can use normal Python imports!")
    print("   Code: from derp import Derp")
    
    # This is just normal Python import syntax!
    from derp import Derp
    
    print("   ✓ Import successful!")
    
    print("\n3. Using the imported class:")
    d = Derp()
    print(f"   d.foo(4) = {d.foo(4)}")
    print(f"   d.bar(3) = {d.bar(3)}")  
    print(f"   d.baz(2) = {d.baz(2)}")
    
    print("\n4. The test: and doc: blocks were automatically stripped!")
    print("   (The class works normally without any PyTestEmbed syntax)")
    
    print("\n5. Regular Python modules still work:")
    import math
    print(f"   math.sqrt(16) = {math.sqrt(16)}")
    
    print("\n6. You can also import multiple things:")
    from derp import Derp as MyDerp
    import json
    
    d2 = MyDerp()
    print(f"   MyDerp().foo(8) = {d2.foo(8)}")
    test_data = {'test': 'works'}
    print(f"   json.dumps(test_data) = {json.dumps(test_data)}")
    
    # Clean up
    ptb.disable_auto_import()
    
    print("\n🎉 Demo complete!")
    print("\nWith auto-import enabled, you can:")
    print("  • Use normal Python import syntax")
    print("  • Import PyTestEmbed files seamlessly") 
    print("  • test: and doc: blocks are automatically stripped")
    print("  • Source tracking maintained for IDE navigation")
    print("  • Regular Python modules work unchanged")

if __name__ == "__main__":
    main()
