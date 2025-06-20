"""
PyTestEmbed Import Hook - Automatically handles PyTestEmbed files during import.

This module provides an import hook that intercepts Python imports and automatically
strips test: and doc: blocks from PyTestEmbed files before importing them.
"""

import sys
import os
import tempfile
import importlib.util
import importlib.machinery
from pathlib import Path
from typing import Optional, List
import re

from .utils import _has_pytestembed_syntax, _generate_clean_code


class PyTestEmbedFinder:
    """Meta path finder that detects PyTestEmbed files."""
    
    def find_spec(self, fullname: str, path: Optional[List[str]], target=None):
        """Find module spec for PyTestEmbed files."""
        
        # Try to find the module file
        module_file = self._find_module_file(fullname, path)
        if not module_file:
            return None
        
        # Check if it has PyTestEmbed syntax
        try:
            with open(module_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not _has_pytestembed_syntax(content):
                # Not a PyTestEmbed file, let standard import handle it
                return None
                
        except (OSError, UnicodeDecodeError):
            # Can't read file, let standard import handle it
            return None
        
        # Create a loader for PyTestEmbed files
        loader = PyTestEmbedLoader(fullname, module_file, content)
        
        # Create module spec
        spec = importlib.machinery.ModuleSpec(fullname, loader, origin=module_file)
        return spec
    
    def _find_module_file(self, fullname: str, path: Optional[List[str]]) -> Optional[str]:
        """Find the module file for the given module name."""
        
        # Handle relative imports and package structure
        parts = fullname.split('.')
        module_name = parts[-1]
        
        # Search paths
        search_paths = []
        
        if path:
            search_paths.extend(path)
        else:
            # Add current working directory
            search_paths.append(os.getcwd())
            # Add sys.path
            search_paths.extend(sys.path)
        
        # Look for .py file
        for search_path in search_paths:
            if not search_path:
                continue
                
            # Try direct file
            module_file = os.path.join(search_path, f"{module_name}.py")
            if os.path.isfile(module_file):
                return module_file
            
            # Try package structure
            if len(parts) > 1:
                package_path = os.path.join(search_path, *parts[:-1])
                module_file = os.path.join(package_path, f"{module_name}.py")
                if os.path.isfile(module_file):
                    return module_file
        
        return None


class PyTestEmbedLoader:
    """Loader that strips test: and doc: blocks before importing."""
    
    def __init__(self, fullname: str, filename: str, source_code: str):
        self.fullname = fullname
        self.filename = filename
        self.source_code = source_code
    
    def create_module(self, spec):
        """Create the module object."""
        return None  # Use default module creation
    
    def exec_module(self, module):
        """Execute the module with stripped test/doc blocks."""
        from .parser import PyTestEmbedParser
        
        # Parse and strip test/doc blocks
        parser = PyTestEmbedParser()
        parsed = parser.parse_content(self.source_code)
        
        # Generate clean Python code
        clean_code = _generate_clean_code(parsed)
        
        # Add source tracking for navigation
        module.__pytestembed_source__ = os.path.abspath(self.filename)
        module.__file__ = self.filename
        
        # Execute the clean code
        exec(compile(clean_code, self.filename, 'exec'), module.__dict__)


class PyTestEmbedImportHook:
    """Main import hook manager."""
    
    def __init__(self):
        self.finder = PyTestEmbedFinder()
        self.installed = False
    
    def install(self):
        """Install the import hook."""
        if not self.installed:
            # Insert at the beginning so we get first chance
            sys.meta_path.insert(0, self.finder)
            self.installed = True
    
    def uninstall(self):
        """Uninstall the import hook."""
        if self.installed:
            try:
                sys.meta_path.remove(self.finder)
                self.installed = False
            except ValueError:
                pass  # Already removed
    
    def __enter__(self):
        """Context manager entry."""
        self.install()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.uninstall()


# Global hook instance
_import_hook = PyTestEmbedImportHook()


def install_import_hook():
    """Install the PyTestEmbed import hook globally."""
    _import_hook.install()


def uninstall_import_hook():
    """Uninstall the PyTestEmbed import hook."""
    _import_hook.uninstall()


def is_import_hook_installed():
    """Check if the import hook is installed."""
    return _import_hook.installed
