"""PyTestEmbed - Embed tests and documentation within Python class and method definitions.

This package provides tools to parse custom syntax that embeds tests and documentation
directly within Python class and method definitions, generate standard Python test code,
and compile unified documentation.
"""

__version__ = "0.1.0"
__author__ = "PyTestEmbed Team"
__email__ = "team@pytestembed.dev"

from .parser import PyTestEmbedParser
from .generator import TestGenerator
from .doc_generator import DocGenerator
from .runner import TestRunner
from .utils import import_from, import_pytestembed_module

__all__ = [
    "PyTestEmbedParser",
    "TestGenerator",
    "DocGenerator",
    "TestRunner",
    "import_from",
    "imp",
    "import_pytestembed_module",
]

# Main import function - accepts standard Python import statements
def import_from(import_statement):
    """
    Execute Python import statement(s) with PyTestEmbed support.

    Args:
        import_statement: A string or list of import statements

    Examples:
        Derp = ptb.import_from("from derp import Derp")
        math = ptb.import_from("import math")
        [Derp, math] = ptb.import_from(["from derp import Derp", "import math"])
    """
    from .utils import import_from as _import_from

    if isinstance(import_statement, list):
        return [_import_from(stmt) for stmt in import_statement]
    else:
        return _import_from(import_statement)

# Short alias
def imp(import_statement):
    """Short alias for import_from() - supports single or list of imports"""
    return import_from(import_statement)

# Import hook functionality
from .import_hook import install_import_hook, uninstall_import_hook, is_import_hook_installed

def enable_auto_import():
    """
    Enable automatic PyTestEmbed import handling.

    After calling this, you can use normal Python imports:
        from derp import Derp  # Automatically strips test:/doc: blocks

    Instead of:
        Derp = ptb.import_from("from derp import Derp")
    """
    install_import_hook()
    print("✓ PyTestEmbed auto-import enabled - use normal Python imports!")

def disable_auto_import():
    """Disable automatic PyTestEmbed import handling."""
    uninstall_import_hook()
    print("✓ PyTestEmbed auto-import disabled")

def is_auto_import_enabled():
    """Check if auto-import is currently enabled."""
    return is_import_hook_installed()

# Auto-enable import hook when PyTestEmbed is imported
install_import_hook()

# Legacy function for backward compatibility
def import_module(module_path):
    """Legacy function - use import_from() instead"""
    return import_pytestembed_module(module_path)
