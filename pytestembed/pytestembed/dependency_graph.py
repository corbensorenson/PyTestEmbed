"""
Code Dependency Graph System for PyTestEmbed

This module provides functionality to:
1. Build a dependency graph of functions, classes, and methods
2. Track what uses what across the entire project
3. Identify dead code and unused functions
4. Provide intelligent test selection based on changes
5. Enable navigation between related code elements
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class CodeElement:
    """Represents a code element (function, class, method)."""
    name: str
    file_path: str
    line_number: int
    element_type: str  # 'function', 'class', 'method'
    parent_class: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    calls: Set[str] = field(default_factory=set)  # Functions/methods this element calls
    imports: Set[str] = field(default_factory=set)  # Modules this element imports
    docstring: Optional[str] = None
    has_tests: bool = False


@dataclass
class DependencyEdge:
    """Represents a dependency relationship between code elements."""
    from_element: str  # "file:class.method" or "file:function"
    to_element: str
    edge_type: str  # 'calls', 'inherits', 'imports', 'tests'
    line_number: int


class CodeDependencyGraph:
    """Builds and maintains a dependency graph of the entire codebase."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.elements: Dict[str, CodeElement] = {}  # element_id -> CodeElement
        self.edges: List[DependencyEdge] = []
        self.file_elements: Dict[str, List[str]] = defaultdict(list)  # file -> element_ids
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)  # what depends on this
        
    def build_graph(self) -> None:
        """Build the complete dependency graph for the workspace."""
        print("🕸️ Building code dependency graph...")
        
        # First pass: collect all elements
        for py_file in self.workspace_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._analyze_file(py_file)
        
        # Second pass: resolve dependencies
        self._resolve_dependencies()
        
        # Third pass: identify dead code
        self._identify_dead_code()
        
        print(f"📊 Graph built: {len(self.elements)} elements, {len(self.edges)} dependencies")
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis."""
        skip_patterns = {
            '__pycache__', '.git', '.pytest_cache', 'venv', 'env',
            'node_modules', '.vscode', '__init__.py'
        }
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file and extract code elements."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            relative_path = str(file_path.relative_to(self.workspace_path))
            
            visitor = CodeElementVisitor(relative_path, self)
            visitor.visit(tree)
            
        except Exception as e:
            print(f"⚠️ Error analyzing {file_path}: {e}")
    
    def _resolve_dependencies(self) -> None:
        """Resolve function calls and create dependency edges."""
        for element_id, element in self.elements.items():
            for call in element.calls:
                # Try to resolve the call to an actual element
                target_element = self._resolve_call(call, element)
                if target_element:
                    edge = DependencyEdge(
                        from_element=element_id,
                        to_element=target_element,
                        edge_type='calls',
                        line_number=element.line_number
                    )
                    self.edges.append(edge)
                    self.reverse_dependencies[target_element].add(element_id)
    
    def _resolve_call(self, call: str, calling_element: CodeElement) -> Optional[str]:
        """Resolve a function call to an actual element ID."""
        # Try different resolution strategies
        
        # 1. Same file, same class (for method calls)
        if calling_element.parent_class:
            same_class_id = f"{calling_element.file_path}:{calling_element.parent_class}.{call}"
            if same_class_id in self.elements:
                return same_class_id
        
        # 2. Same file, global function
        same_file_id = f"{calling_element.file_path}:{call}"
        if same_file_id in self.elements:
            return same_file_id
        
        # 3. Imported function (would need import analysis)
        # TODO: Implement import resolution
        
        return None
    
    def _identify_dead_code(self) -> None:
        """Identify code elements that are never called (dead code)."""
        called_elements = set()
        for edge in self.edges:
            if edge.edge_type == 'calls':
                called_elements.add(edge.to_element)
        
        # Mark elements as dead if they're not called and not entry points
        for element_id, element in self.elements.items():
            if (element_id not in called_elements and 
                element.name not in ['main', '__init__'] and
                not element.has_tests):
                # This might be dead code
                pass
    
    def get_dependencies(self, element_id: str) -> List[str]:
        """Get all elements that this element depends on."""
        dependencies = []
        for edge in self.edges:
            if edge.from_element == element_id and edge.edge_type == 'calls':
                dependencies.append(edge.to_element)
        return dependencies
    
    def get_dependents(self, element_id: str) -> List[str]:
        """Get all elements that depend on this element."""
        return list(self.reverse_dependencies.get(element_id, set()))
    
    def get_test_impact(self, changed_file: str) -> List[str]:
        """Get all files that should be tested when the given file changes."""
        impact_files = set()
        
        # Get all elements in the changed file
        changed_elements = self.file_elements.get(changed_file, [])
        
        # For each changed element, find what depends on it
        for element_id in changed_elements:
            dependents = self.get_dependents(element_id)
            for dependent in dependents:
                dependent_file = dependent.split(':')[0]
                impact_files.add(dependent_file)
        
        # Always include the changed file itself
        impact_files.add(changed_file)
        
        return list(impact_files)
    
    def get_element_info(self, file_path: str, line_number: int) -> Optional[CodeElement]:
        """Get information about the code element at a specific location."""
        for element_id in self.file_elements.get(file_path, []):
            element = self.elements[element_id]
            # Simple line-based matching (could be improved)
            if abs(element.line_number - line_number) < 5:
                return element
        return None
    
    def export_graph(self, output_path: str) -> None:
        """Export the dependency graph to JSON for visualization."""
        graph_data = {
            'elements': {
                element_id: {
                    'name': element.name,
                    'file': element.file_path,
                    'line': element.line_number,
                    'type': element.element_type,
                    'parent_class': element.parent_class,
                    'has_tests': element.has_tests
                }
                for element_id, element in self.elements.items()
            },
            'edges': [
                {
                    'from': edge.from_element,
                    'to': edge.to_element,
                    'type': edge.edge_type,
                    'line': edge.line_number
                }
                for edge in self.edges
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(graph_data, f, indent=2)


class CodeElementVisitor(ast.NodeVisitor):
    """AST visitor to extract code elements and their relationships."""
    
    def __init__(self, file_path: str, graph: CodeDependencyGraph):
        self.file_path = file_path
        self.graph = graph
        self.current_class = None
        self.current_function = None
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition."""
        element_id = f"{self.file_path}:{node.name}"
        element = CodeElement(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            element_type='class',
            docstring=ast.get_docstring(node)
        )
        
        self.graph.elements[element_id] = element
        self.graph.file_elements[self.file_path].append(element_id)
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function or method definition."""
        if self.current_class:
            element_id = f"{self.file_path}:{self.current_class}.{node.name}"
            element_type = 'method'
            parent_class = self.current_class
        else:
            element_id = f"{self.file_path}:{node.name}"
            element_type = 'function'
            parent_class = None
        
        # Extract parameters
        parameters = [arg.arg for arg in node.args.args]
        
        element = CodeElement(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            element_type=element_type,
            parent_class=parent_class,
            parameters=parameters,
            docstring=ast.get_docstring(node)
        )
        
        self.graph.elements[element_id] = element
        self.graph.file_elements[self.file_path].append(element_id)
        
        # Extract function calls within this function
        old_function = self.current_function
        self.current_function = element_id
        
        call_visitor = FunctionCallVisitor()
        call_visitor.visit(node)
        element.calls = call_visitor.calls
        
        self.current_function = old_function


class FunctionCallVisitor(ast.NodeVisitor):
    """Visitor to extract function calls from within a function."""
    
    def __init__(self):
        self.calls = set()
    
    def visit_Call(self, node: ast.Call) -> None:
        """Visit a function call."""
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.add(node.func.attr)
        
        self.generic_visit(node)
