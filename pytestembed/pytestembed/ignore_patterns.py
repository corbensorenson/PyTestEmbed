"""
PyTestEmbed Ignore Patterns

This module provides support for .pytestembedignore files that control
which files and directories the file watcher monitors. It follows the
same pattern as .gitignore and .vscodeignore.
"""

import fnmatch
import os
import re
from pathlib import Path
from typing import List, Set, Optional


class PyTestEmbedIgnore:
    """Handles .pytestembedignore file parsing and pattern matching."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.ignore_file = self.workspace_path / '.pytestembedignore'
        self.patterns: List[str] = []
        self.negation_patterns: List[str] = []
        self.directory_patterns: Set[str] = set()
        
        # Load patterns from .pytestembedignore file
        self.load_patterns()
    
    def load_patterns(self):
        """Load ignore patterns from .pytestembedignore file."""
        self.patterns = []
        self.negation_patterns = []
        self.directory_patterns = set()
        
        if not self.ignore_file.exists():
            # Create default .pytestembedignore if it doesn't exist
            self.create_default_ignore_file()
        
        try:
            with open(self.ignore_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Handle negation patterns (lines starting with !)
                    if line.startswith('!'):
                        negation_pattern = line[1:].strip()
                        if negation_pattern:
                            self.negation_patterns.append(negation_pattern)
                        continue
                    
                    # Handle directory patterns (lines ending with /)
                    if line.endswith('/'):
                        dir_pattern = line[:-1]
                        if dir_pattern:
                            self.directory_patterns.add(dir_pattern)
                            self.patterns.append(dir_pattern)
                        continue
                    
                    # Regular file/pattern
                    self.patterns.append(line)
                    
        except Exception as e:
            print(f"Warning: Error reading .pytestembedignore: {e}")
            # Use default patterns if file is corrupted
            self.create_default_ignore_file()
    
    def create_default_ignore_file(self):
        """Create a default .pytestembedignore file with sensible defaults."""
        default_content = """# PyTestEmbed Ignore File
# This file controls which files and directories the file watcher monitors
# Patterns follow gitignore syntax

# Common directories to ignore
__pycache__/
.git/
.svn/
.hg/
.bzr/
node_modules/
.venv/
venv/
env/
.env/

# Build and distribution directories
build/
dist/
*.egg-info/
.tox/
.coverage/
htmlcov/
.pytest_cache/

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# PyTestEmbed temporary files
.pytestembed_temp/

# Log files
*.log
logs/

# Compiled Python files
*.pyc
*.pyo
*.pyd

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Only watch Python files in specific directories
# Uncomment and modify these patterns as needed:
# !testProject/
# !src/
# !tests/

# Example: Only watch testProject directory
# Comment out to watch all Python files
# *
# !testProject/
# !testProject/**
"""
        
        try:
            with open(self.ignore_file, 'w', encoding='utf-8') as f:
                f.write(default_content)
            print(f"✅ Created default .pytestembedignore file at {self.ignore_file}")
        except Exception as e:
            print(f"⚠️ Could not create .pytestembedignore file: {e}")
    
    def should_ignore(self, file_path: str) -> bool:
        """
        Check if a file should be ignored based on .pytestembedignore patterns.
        
        Args:
            file_path: Path to check (can be absolute or relative to workspace)
            
        Returns:
            True if the file should be ignored, False otherwise
        """
        # Convert to relative path from workspace root
        try:
            abs_path = Path(file_path)
            if abs_path.is_absolute():
                rel_path = abs_path.relative_to(self.workspace_path)
            else:
                rel_path = Path(file_path)
            
            rel_path_str = str(rel_path).replace('\\', '/')  # Normalize path separators
            
        except ValueError:
            # Path is not under workspace, ignore it
            return True
        
        # Check if explicitly not ignored (negation patterns)
        for negation_pattern in self.negation_patterns:
            if self._matches_pattern(rel_path_str, negation_pattern):
                return False
        
        # Check if ignored by any pattern
        for pattern in self.patterns:
            if self._matches_pattern(rel_path_str, pattern):
                return True
        
        # Check directory patterns for parent directories
        path_parts = rel_path.parts
        for i in range(len(path_parts)):
            parent_path = '/'.join(path_parts[:i+1])
            if parent_path in self.directory_patterns:
                return True
        
        return False
    
    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """
        Check if a file path matches a gitignore-style pattern.
        
        Args:
            file_path: File path to check
            pattern: Pattern to match against
            
        Returns:
            True if the pattern matches, False otherwise
        """
        # Handle absolute patterns (starting with /)
        if pattern.startswith('/'):
            pattern = pattern[1:]
            # Only match from root
            return fnmatch.fnmatch(file_path, pattern) or file_path.startswith(pattern + '/')
        
        # Handle directory patterns
        if pattern.endswith('/'):
            dir_pattern = pattern[:-1]
            # Match directory anywhere in path
            path_parts = file_path.split('/')
            for i, part in enumerate(path_parts):
                if fnmatch.fnmatch(part, dir_pattern):
                    return True
            return False
        
        # Handle wildcard patterns
        if '**' in pattern:
            # Convert ** to regex pattern
            regex_pattern = pattern.replace('**', '.*')
            regex_pattern = regex_pattern.replace('*', '[^/]*')
            regex_pattern = regex_pattern.replace('?', '[^/]')
            try:
                return bool(re.match(regex_pattern, file_path))
            except re.error:
                # Fallback to simple fnmatch
                return fnmatch.fnmatch(file_path, pattern)
        
        # Simple pattern matching
        if fnmatch.fnmatch(file_path, pattern):
            return True
        
        # Check if pattern matches any part of the path
        path_parts = file_path.split('/')
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern):
                return True
        
        # Check if file is in a directory that matches the pattern
        for i in range(len(path_parts)):
            parent_path = '/'.join(path_parts[:i+1])
            if fnmatch.fnmatch(parent_path, pattern):
                return True
        
        return False
    
    def get_watched_directories(self) -> List[str]:
        """
        Get list of directories that should be watched based on ignore patterns.
        
        Returns:
            List of directory paths relative to workspace root
        """
        watched_dirs = []
        
        # If no specific inclusion patterns, watch everything not explicitly ignored
        if not self.negation_patterns:
            # Find all Python directories not ignored
            for root, dirs, files in os.walk(self.workspace_path):
                # Remove ignored directories from dirs list to prevent walking them
                dirs[:] = [d for d in dirs if not self.should_ignore(os.path.join(root, d))]
                
                # Check if this directory contains Python files
                has_python_files = any(f.endswith('.py') for f in files)
                if has_python_files:
                    rel_root = os.path.relpath(root, self.workspace_path)
                    if rel_root != '.' and not self.should_ignore(rel_root):
                        watched_dirs.append(rel_root)
        else:
            # Use negation patterns to determine what to watch
            for pattern in self.negation_patterns:
                if pattern.endswith('/'):
                    # Directory pattern
                    dir_pattern = pattern[:-1]
                    watched_dirs.append(dir_pattern)
                else:
                    # File pattern - add its parent directory
                    parent_dir = os.path.dirname(pattern)
                    if parent_dir and parent_dir not in watched_dirs:
                        watched_dirs.append(parent_dir)
        
        return watched_dirs
    
    def reload(self):
        """Reload patterns from .pytestembedignore file."""
        self.load_patterns()
        print(f"🔄 Reloaded .pytestembedignore patterns: {len(self.patterns)} patterns, {len(self.negation_patterns)} negations")
    
    def get_stats(self) -> dict:
        """Get statistics about ignore patterns."""
        return {
            'total_patterns': len(self.patterns),
            'negation_patterns': len(self.negation_patterns),
            'directory_patterns': len(self.directory_patterns),
            'ignore_file_exists': self.ignore_file.exists(),
            'ignore_file_path': str(self.ignore_file)
        }
