"""Utility functions for PyTestEmbed."""

import hashlib
import os
import sys
import tempfile
import importlib.util
import types
import re
from pathlib import Path
from typing import Optional, Any


def get_file_hash(file_path: str) -> str:
    """Get SHA256 hash of a file."""
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def get_cache_dir() -> Path:
    """Get the cache directory for PyTestEmbed."""
    cache_dir = Path.cwd() / '.pytestembed_cache'
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def is_file_cached(file_path: str) -> bool:
    """Check if a file is cached and up to date."""
    cache_dir = get_cache_dir()
    cache_file = cache_dir / f"{Path(file_path).name}.hash"
    
    if not cache_file.exists():
        return False
    
    with open(cache_file, 'r') as f:
        cached_hash = f.read().strip()
    
    current_hash = get_file_hash(file_path)
    return cached_hash == current_hash


def cache_file_hash(file_path: str) -> None:
    """Cache the hash of a file."""
    cache_dir = get_cache_dir()
    cache_file = cache_dir / f"{Path(file_path).name}.hash"

    file_hash = get_file_hash(file_path)
    with open(cache_file, 'w') as f:
        f.write(file_hash)


def import_from(import_statement: str) -> Any:
    """
    Execute a Python import statement with PyTestEmbed support.

    Args:
        import_statement: A standard Python import statement as a string
                         Examples: "from derp import Derp"
                                  "import math"
                                  "from .module import Class as Alias"

    Returns:
        The imported object(s) exactly as the import statement would return
    """
    import ast
    import re

    # Parse the import statement
    try:
        # Add a dummy assignment to make it a valid statement for parsing
        if import_statement.strip().startswith('from '):
            # Handle "from module import item" statements
            parsed = ast.parse(import_statement)
            import_node = parsed.body[0]

            if isinstance(import_node, ast.ImportFrom):
                module_name = import_node.module
                level = import_node.level

                # Handle relative imports
                if level > 0:
                    # For now, fall back to standard import for relative imports
                    # TODO: Implement relative import support
                    exec(import_statement, globals())

                    # Extract what was imported
                    if len(import_node.names) == 1:
                        alias = import_node.names[0]
                        imported_name = alias.asname if alias.asname else alias.name
                        return globals()[imported_name]
                    else:
                        # Multiple imports
                        result = {}
                        for alias in import_node.names:
                            imported_name = alias.asname if alias.asname else alias.name
                            result[imported_name] = globals()[imported_name]
                        return result

                # Handle absolute imports with PyTestEmbed support
                module = _import_pytestembed_module(module_name)

                # Extract the requested items
                if len(import_node.names) == 1 and import_node.names[0].name != '*':
                    # Single import: from module import item [as alias]
                    alias = import_node.names[0]
                    item_name = alias.name

                    if hasattr(module, item_name):
                        return getattr(module, item_name)
                    else:
                        raise ImportError(f"cannot import name '{item_name}' from '{module_name}'")

                elif len(import_node.names) == 1 and import_node.names[0].name == '*':
                    # from module import *
                    result = {}
                    for attr_name in dir(module):
                        if not attr_name.startswith('_'):
                            result[attr_name] = getattr(module, attr_name)
                    return result

                else:
                    # Multiple imports: from module import item1, item2, item3
                    result = {}
                    for alias in import_node.names:
                        item_name = alias.name
                        result_name = alias.asname if alias.asname else alias.name

                        if hasattr(module, item_name):
                            result[result_name] = getattr(module, item_name)
                        else:
                            raise ImportError(f"cannot import name '{item_name}' from '{module_name}'")
                    return result

        elif import_statement.strip().startswith('import '):
            # Handle "import module" statements
            parsed = ast.parse(import_statement)
            import_node = parsed.body[0]

            if isinstance(import_node, ast.Import):
                if len(import_node.names) == 1:
                    # Single import: import module [as alias]
                    alias = import_node.names[0]
                    module_name = alias.name

                    # Check if this might be a PyTestEmbed module
                    if _is_pytestembed_module(module_name):
                        return _import_pytestembed_module(module_name)
                    else:
                        # Fall back to standard import
                        exec(import_statement, globals())
                        imported_name = alias.asname if alias.asname else alias.name
                        return globals()[imported_name]
                else:
                    # Multiple imports: import module1, module2, module3
                    result = {}
                    for alias in import_node.names:
                        module_name = alias.name
                        result_name = alias.asname if alias.asname else alias.name

                        if _is_pytestembed_module(module_name):
                            result[result_name] = _import_pytestembed_module(module_name)
                        else:
                            exec(f"import {module_name}", globals())
                            result[result_name] = globals()[module_name]
                    return result
        else:
            raise ValueError(f"Invalid import statement: {import_statement}")

    except SyntaxError as e:
        raise ValueError(f"Invalid import statement syntax: {import_statement}") from e


def _import_pytestembed_module(module_name: str) -> Any:
    """Internal function to import a PyTestEmbed module."""
    from .parser import PyTestEmbedParser

    # Try to find the module file
    file_path = Path(f"{module_name}.py")
    if not file_path.exists():
        # Try current directory
        file_path = Path.cwd() / f"{module_name}.py"
        if not file_path.exists():
            # Fall back to standard import
            return importlib.import_module(module_name)

    # Read the original file
    with open(file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # Check if it has PyTestEmbed syntax
    if not _has_pytestembed_syntax(original_content):
        # No PyTestEmbed syntax, use standard import
        return importlib.import_module(module_name)

    # Parse and strip test/doc blocks
    parser = PyTestEmbedParser()
    parsed = parser.parse_content(original_content)

    # Generate clean Python code without test/doc blocks
    clean_code = _generate_clean_code(parsed)

    # Create a temporary file with clean code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(clean_code)
        temp_file_path = temp_file.name

    try:
        # Import the clean module
        spec = importlib.util.spec_from_file_location(module_name, temp_file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for {module_name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Add source file tracking for navigation
        module.__pytestembed_source__ = str(file_path.absolute())

        return module

    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass


def _is_pytestembed_module(module_name: str) -> bool:
    """Check if a module is likely a PyTestEmbed module."""
    file_path = Path(f"{module_name}.py")
    if not file_path.exists():
        file_path = Path.cwd() / f"{module_name}.py"
        if not file_path.exists():
            return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return _has_pytestembed_syntax(content)
    except:
        return False


def _has_pytestembed_syntax(content: str) -> bool:
    """Check if content contains PyTestEmbed syntax (excluding docstrings)."""
    lines = content.split('\n')
    in_docstring = False
    docstring_delimiter = None

    for line in lines:
        stripped = line.strip()

        # Check for docstring start/end
        if '"""' in stripped or "'''" in stripped:
            if not in_docstring:
                # Starting a docstring
                if stripped.count('"""') == 1:
                    in_docstring = True
                    docstring_delimiter = '"""'
                elif stripped.count("'''") == 1:
                    in_docstring = True
                    docstring_delimiter = "'''"
                # If count is 2, it's a single-line docstring, don't change state
            else:
                # Potentially ending a docstring
                if docstring_delimiter in stripped:
                    in_docstring = False
                    docstring_delimiter = None

        # Only check for test:/doc: if we're not in a docstring
        if not in_docstring:
            if re.match(r'^\s*test:\s*$', line) or re.match(r'^\s*doc:\s*$', line):
                return True

    return False


# Legacy function for backward compatibility
def import_pytestembed_module(module_path: str) -> Any:
    """Legacy function - use import_from() instead."""
    return _import_pytestembed_module(module_path)


def _generate_clean_code(parsed_data) -> str:
    """Generate clean Python code without test: and doc: blocks."""
    lines = []

    # Add classes
    for class_def in parsed_data.classes:
        lines.append(f"class {class_def.name}:")

        # Add methods
        if class_def.methods:
            for method in class_def.methods:
                params_str = ', '.join(method.parameters)
                lines.append(f"    def {method.name}({params_str}):")
                if method.body:
                    for line in method.body:
                        lines.append(f"        {line}")
                else:
                    lines.append("        pass")
        else:
            lines.append("    pass")

        lines.append("")  # Empty line after class

    # Add functions
    for func_def in parsed_data.functions:
        params_str = ', '.join(func_def.parameters)
        lines.append(f"def {func_def.name}({params_str}):")
        if func_def.body:
            for line in func_def.body:
                lines.append(f"    {line}")
        else:
            lines.append("    pass")
        lines.append("")  # Empty line after function

    return '\n'.join(lines)
