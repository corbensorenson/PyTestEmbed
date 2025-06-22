"""
Change Detection System for PyTestEmbed

This module provides intelligent change detection using content hashing
to identify exactly what code changed, not just which files were modified.
This enables precise test selection based on actual code changes.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from .parser import PyTestEmbedParser


@dataclass
class CodeElement:
    """Represents a code element (function, class, method, test) with its hash."""
    name: str
    element_type: str  # 'function', 'class', 'method', 'test', 'global'
    content_hash: str
    line_start: int
    line_end: int
    parent: Optional[str] = None  # For methods, the class name


@dataclass
class FileSnapshot:
    """Snapshot of a file's code elements and their hashes."""
    file_path: str
    file_hash: str
    timestamp: float
    elements: List[CodeElement]


class ChangeDetector:
    """Detects precise changes in Python files using content hashing."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.parser = PyTestEmbedParser()
        self.snapshots: Dict[str, FileSnapshot] = {}
        self.cache_file = self.workspace_path / '.pytestembed_temp' / 'change_cache.json'
        
        # Load existing cache
        self.load_cache()
    
    def get_file_hash(self, file_path: str) -> str:
        """Get hash of entire file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        except Exception:
            return ""
    
    def get_element_hash(self, content: str) -> str:
        """Get hash of a code element's content."""
        # Normalize whitespace and remove comments for more stable hashing
        lines = content.split('\n')
        normalized_lines = []
        
        for line in lines:
            # Remove leading/trailing whitespace but preserve relative indentation
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                # Preserve relative indentation by counting leading spaces
                indent = len(line) - len(line.lstrip())
                normalized_lines.append(' ' * (indent // 4) + stripped)
        
        normalized_content = '\n'.join(normalized_lines)
        return hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()
    
    def extract_code_elements(self, file_path: str) -> List[CodeElement]:
        """Extract all code elements from a file with their hashes."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            elements = []
            
            # Parse the file
            parsed = self.parser.parse_file(file_path)
            
            # Extract functions
            for func in parsed.functions:
                func_content = self._extract_lines(lines, func.line_number - 1, func.line_number + 10)  # Approximate
                func_hash = self.get_element_hash(func_content)
                
                elements.append(CodeElement(
                    name=func.name,
                    element_type='function',
                    content_hash=func_hash,
                    line_start=func.line_number - 1,
                    line_end=func.line_number + 10  # Will be refined
                ))
                
                # Extract function tests
                for test_block in func.test_blocks:
                    for test_case in test_block.test_cases:
                        test_content = f"{test_case.assertion}: {test_case.message}"
                        test_hash = self.get_element_hash(test_content)
                        
                        elements.append(CodeElement(
                            name=f"{func.name}_test_{test_case.line_number}",
                            element_type='test',
                            content_hash=test_hash,
                            line_start=test_case.line_number - 1,
                            line_end=test_case.line_number - 1,
                            parent=func.name
                        ))
            
            # Extract classes
            for cls in parsed.classes:
                cls_content = self._extract_lines(lines, cls.line_number - 1, cls.line_number + 20)  # Approximate
                cls_hash = self.get_element_hash(cls_content)
                
                elements.append(CodeElement(
                    name=cls.name,
                    element_type='class',
                    content_hash=cls_hash,
                    line_start=cls.line_number - 1,
                    line_end=cls.line_number + 20  # Will be refined
                ))
                
                # Extract methods
                for method in cls.methods:
                    method_content = self._extract_lines(lines, method.line_number - 1, method.line_number + 10)
                    method_hash = self.get_element_hash(method_content)
                    
                    elements.append(CodeElement(
                        name=f"{cls.name}.{method.name}",
                        element_type='method',
                        content_hash=method_hash,
                        line_start=method.line_number - 1,
                        line_end=method.line_number + 10,
                        parent=cls.name
                    ))
                    
                    # Extract method tests
                    for test_block in method.test_blocks:
                        for test_case in test_block.test_cases:
                            test_content = f"{test_case.assertion}: {test_case.message}"
                            test_hash = self.get_element_hash(test_content)
                            
                            elements.append(CodeElement(
                                name=f"{cls.name}.{method.name}_test_{test_case.line_number}",
                                element_type='test',
                                content_hash=test_hash,
                                line_start=test_case.line_number - 1,
                                line_end=test_case.line_number - 1,
                                parent=f"{cls.name}.{method.name}"
                            ))
                
                # Extract class-level tests
                for test_block in cls.test_blocks:
                    for test_case in test_block.test_cases:
                        test_content = f"{test_case.assertion}: {test_case.message}"
                        test_hash = self.get_element_hash(test_content)
                        
                        elements.append(CodeElement(
                            name=f"{cls.name}_test_{test_case.line_number}",
                            element_type='test',
                            content_hash=test_hash,
                            line_start=test_case.line_number - 1,
                            line_end=test_case.line_number - 1,
                            parent=cls.name
                        ))
            
            # Extract global tests
            for test_block in parsed.global_test_blocks:
                for test_case in test_block.test_cases:
                    test_content = f"{test_case.assertion}: {test_case.message}"
                    test_hash = self.get_element_hash(test_content)
                    
                    elements.append(CodeElement(
                        name=f"global_test_{test_case.line_number}",
                        element_type='test',
                        content_hash=test_hash,
                        line_start=test_case.line_number - 1,
                        line_end=test_case.line_number - 1
                    ))
            
            return elements
            
        except Exception as e:
            print(f"Error extracting code elements from {file_path}: {e}")
            return []
    
    def _extract_lines(self, lines: List[str], start: int, end: int) -> str:
        """Extract lines from start to end (inclusive)."""
        if start < 0:
            start = 0
        if end >= len(lines):
            end = len(lines) - 1
        return '\n'.join(lines[start:end + 1])
    
    def create_snapshot(self, file_path: str) -> FileSnapshot:
        """Create a snapshot of a file's current state."""
        file_hash = self.get_file_hash(file_path)
        elements = self.extract_code_elements(file_path)
        
        snapshot = FileSnapshot(
            file_path=file_path,
            file_hash=file_hash,
            timestamp=time.time(),
            elements=elements
        )
        
        # Store relative path for portability
        rel_path = str(Path(file_path).relative_to(self.workspace_path))
        self.snapshots[rel_path] = snapshot
        
        return snapshot
    
    def detect_changes(self, file_path: str) -> Tuple[List[str], List[str], List[str]]:
        """
        Detect what changed in a file.
        
        Returns:
            Tuple of (added_elements, modified_elements, deleted_elements)
        """
        rel_path = str(Path(file_path).relative_to(self.workspace_path))
        
        # Get current state
        current_snapshot = self.create_snapshot(file_path)
        
        # Get previous state
        previous_snapshot = self.snapshots.get(rel_path)
        
        if not previous_snapshot:
            # First time seeing this file - everything is new
            return ([elem.name for elem in current_snapshot.elements], [], [])
        
        # Compare snapshots
        current_elements = {elem.name: elem for elem in current_snapshot.elements}
        previous_elements = {elem.name: elem for elem in previous_snapshot.elements}
        
        added = []
        modified = []
        deleted = []
        
        # Find added and modified elements
        for name, current_elem in current_elements.items():
            if name not in previous_elements:
                added.append(name)
            elif current_elem.content_hash != previous_elements[name].content_hash:
                modified.append(name)
        
        # Find deleted elements
        for name in previous_elements:
            if name not in current_elements:
                deleted.append(name)
        
        return (added, modified, deleted)
    
    def save_cache(self):
        """Save snapshots to cache file."""
        try:
            self.cache_file.parent.mkdir(exist_ok=True)
            
            # Convert snapshots to serializable format
            cache_data = {}
            for path, snapshot in self.snapshots.items():
                cache_data[path] = asdict(snapshot)
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving change cache: {e}")
    
    def load_cache(self):
        """Load snapshots from cache file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Convert back to snapshot objects
                for path, data in cache_data.items():
                    elements = [CodeElement(**elem) for elem in data['elements']]
                    self.snapshots[path] = FileSnapshot(
                        file_path=data['file_path'],
                        file_hash=data['file_hash'],
                        timestamp=data['timestamp'],
                        elements=elements
                    )
                    
        except Exception as e:
            print(f"Error loading change cache: {e}")
            self.snapshots = {}
