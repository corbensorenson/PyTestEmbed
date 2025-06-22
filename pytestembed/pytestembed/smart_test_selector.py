"""
Smart Test Selector for PyTestEmbed

This module provides intelligent test selection based on:
1. Code changes detected via content hashing
2. Dependency analysis from the dependency service
3. Cross-file impact analysis

When class Derp changes, it automatically finds and runs tests in other files
that depend on it (like fullTest).
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from .change_detector import ChangeDetector
from .parser import PyTestEmbedParser


@dataclass
class TestToRun:
    """Represents a test that should be run."""
    file_path: str
    test_name: str
    line_number: int
    reason: str  # Why this test needs to run
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class SmartTestSelection:
    """Result of smart test selection."""
    tests_to_run: List[TestToRun]
    total_tests_found: int
    selection_reason: str
    estimated_time_saved: float


class SmartTestSelector:
    """Selects tests intelligently based on changes and dependencies."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.change_detector = ChangeDetector(workspace_path)
        self.parser = PyTestEmbedParser()
        
        # Cache for dependency information
        self.dependency_cache: Dict[str, Set[str]] = {}
        self.reverse_dependency_cache: Dict[str, Set[str]] = {}
        
    async def select_tests_for_changes(self, changed_files: List[str], 
                                     dependency_service_ws=None) -> SmartTestSelection:
        """
        Select tests to run based on file changes and dependencies.
        
        Args:
            changed_files: List of file paths that changed
            dependency_service_ws: WebSocket connection to dependency service
            
        Returns:
            SmartTestSelection with tests to run
        """
        tests_to_run = []
        all_affected_elements = set()
        
        # Analyze each changed file
        for file_path in changed_files:
            if not file_path.endswith('.py'):
                continue
                
            # Detect precise changes in this file
            added, modified, deleted = self.change_detector.detect_changes(file_path)
            
            print(f"📊 Changes in {file_path}:")
            print(f"   Added: {added}")
            print(f"   Modified: {modified}")
            print(f"   Deleted: {deleted}")
            
            # Collect all affected elements
            affected_elements = set(added + modified + deleted)
            all_affected_elements.update(affected_elements)
            
            # Add tests for directly changed elements
            direct_tests = await self._get_tests_for_elements(file_path, affected_elements)
            tests_to_run.extend(direct_tests)
            
            # Get dependency impact if dependency service is available
            if dependency_service_ws:
                dependent_tests = await self._get_dependent_tests(
                    file_path, affected_elements, dependency_service_ws
                )
                tests_to_run.extend(dependent_tests)
        
        # Remove duplicates and sort by priority
        unique_tests = self._deduplicate_tests(tests_to_run)
        unique_tests.sort(key=lambda t: (t.priority, t.file_path, t.line_number))
        
        # Calculate estimated time saved
        total_tests = await self._count_total_tests()
        time_saved = max(0, (total_tests - len(unique_tests)) * 0.1)  # Assume 0.1s per test
        
        selection_reason = f"Smart selection based on {len(all_affected_elements)} changed elements"
        
        return SmartTestSelection(
            tests_to_run=unique_tests,
            total_tests_found=total_tests,
            selection_reason=selection_reason,
            estimated_time_saved=time_saved
        )
    
    async def _get_tests_for_elements(self, file_path: str, elements: Set[str]) -> List[TestToRun]:
        """Get tests that should run for specific changed elements."""
        tests = []
        
        try:
            # Parse the file to find tests
            parsed = self.parser.parse_file(file_path)
            rel_path = str(Path(file_path).relative_to(self.workspace_path))
            
            # Check if any test elements themselves changed
            for element in elements:
                if '_test_' in element or element.startswith('global_test_'):
                    # This is a test that changed - definitely run it
                    line_num = self._extract_line_number_from_test_name(element)
                    if line_num:
                        tests.append(TestToRun(
                            file_path=rel_path,
                            test_name=element,
                            line_number=line_num,
                            reason=f"Test {element} was modified",
                            priority=1
                        ))
            
            # For changed functions/classes, run their associated tests
            for element in elements:
                if not ('_test_' in element or element.startswith('global_test_')):
                    # This is a function or class that changed
                    element_tests = self._find_tests_for_element(parsed, element)
                    for test_info in element_tests:
                        tests.append(TestToRun(
                            file_path=rel_path,
                            test_name=test_info['name'],
                            line_number=test_info['line'],
                            reason=f"Tests for changed {element}",
                            priority=1
                        ))
            
            # If a class changed, run all its method tests too
            for element in elements:
                if '.' not in element and not element.startswith('global_test_'):
                    # This might be a class
                    class_tests = self._find_tests_for_class(parsed, element)
                    for test_info in class_tests:
                        tests.append(TestToRun(
                            file_path=rel_path,
                            test_name=test_info['name'],
                            line_number=test_info['line'],
                            reason=f"Tests for class {element} methods",
                            priority=2
                        ))
                        
        except Exception as e:
            print(f"Error getting tests for elements in {file_path}: {e}")
        
        return tests
    
    async def _get_dependent_tests(self, file_path: str, elements: Set[str], 
                                 dependency_service_ws) -> List[TestToRun]:
        """Get tests in other files that depend on the changed elements."""
        tests = []
        
        try:
            # For each changed element, find what depends on it
            for element in elements:
                if '_test_' in element or element.startswith('global_test_'):
                    continue  # Skip test elements for dependency analysis
                
                # Request dependency analysis from dependency service
                request = {
                    'command': 'get_dependents',
                    'file_path': str(Path(file_path).relative_to(self.workspace_path)),
                    'element_name': element
                }
                
                await dependency_service_ws.send(json.dumps(request))
                
                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(dependency_service_ws.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if data.get('type') == 'dependents':
                        dependents = data.get('dependents', [])
                        
                        for dependent in dependents:
                            dep_file = dependent.get('file_path')
                            dep_element = dependent.get('element_name')
                            
                            if dep_file and dep_element:
                                # Find tests for this dependent element
                                dep_tests = await self._find_tests_in_file(dep_file, dep_element)
                                for test_info in dep_tests:
                                    tests.append(TestToRun(
                                        file_path=dep_file,
                                        test_name=test_info['name'],
                                        line_number=test_info['line'],
                                        reason=f"Depends on changed {element}",
                                        priority=2
                                    ))
                                    
                except asyncio.TimeoutError:
                    print(f"Timeout waiting for dependency analysis of {element}")
                    
        except Exception as e:
            print(f"Error getting dependent tests: {e}")
        
        return tests
    
    async def _find_tests_in_file(self, file_path: str, element_name: str) -> List[Dict]:
        """Find tests related to a specific element in a file."""
        tests = []
        
        try:
            full_path = self.workspace_path / file_path
            parsed = self.parser.parse_file(str(full_path))
            
            # Look for tests that might be testing this element
            # This is a heuristic - look for tests that mention the element name
            
            # Check function tests
            for func in parsed.functions:
                if element_name in func.name or func.name in element_name:
                    for test_block in func.test_blocks:
                        for test_case in test_block.test_cases:
                            tests.append({
                                'name': f"{func.name}_test_{test_case.line_number}",
                                'line': test_case.line_number - 1
                            })
            
            # Check class tests
            for cls in parsed.classes:
                if element_name in cls.name or cls.name in element_name:
                    # Class-level tests
                    for test_block in cls.test_blocks:
                        for test_case in test_block.test_cases:
                            tests.append({
                                'name': f"{cls.name}_test_{test_case.line_number}",
                                'line': test_case.line_number - 1
                            })
                    
                    # Method tests
                    for method in cls.methods:
                        if element_name in method.name or method.name in element_name:
                            for test_block in method.test_blocks:
                                for test_case in test_block.test_cases:
                                    tests.append({
                                        'name': f"{cls.name}.{method.name}_test_{test_case.line_number}",
                                        'line': test_case.line_number - 1
                                    })
            
            # Check global tests that might reference the element
            for test_block in parsed.global_test_blocks:
                for test_case in test_block.test_cases:
                    if element_name in test_case.assertion:
                        tests.append({
                            'name': f"global_test_{test_case.line_number}",
                            'line': test_case.line_number - 1
                        })
                        
        except Exception as e:
            print(f"Error finding tests in {file_path} for {element_name}: {e}")
        
        return tests
    
    def _find_tests_for_element(self, parsed, element_name: str) -> List[Dict]:
        """Find tests for a specific element in parsed code."""
        tests = []
        
        # Find function tests
        for func in parsed.functions:
            if func.name == element_name:
                for test_block in func.test_blocks:
                    for test_case in test_block.test_cases:
                        tests.append({
                            'name': f"{func.name}_test_{test_case.line_number}",
                            'line': test_case.line_number - 1
                        })
        
        # Find class tests
        for cls in parsed.classes:
            if cls.name == element_name:
                for test_block in cls.test_blocks:
                    for test_case in test_block.test_cases:
                        tests.append({
                            'name': f"{cls.name}_test_{test_case.line_number}",
                            'line': test_case.line_number - 1
                        })
        
        return tests
    
    def _find_tests_for_class(self, parsed, class_name: str) -> List[Dict]:
        """Find all tests for methods of a class."""
        tests = []
        
        for cls in parsed.classes:
            if cls.name == class_name:
                for method in cls.methods:
                    for test_block in method.test_blocks:
                        for test_case in test_block.test_cases:
                            tests.append({
                                'name': f"{cls.name}.{method.name}_test_{test_case.line_number}",
                                'line': test_case.line_number - 1
                            })
        
        return tests
    
    def _extract_line_number_from_test_name(self, test_name: str) -> Optional[int]:
        """Extract line number from test name."""
        try:
            if '_test_' in test_name:
                parts = test_name.split('_test_')
                if len(parts) > 1:
                    return int(parts[-1]) - 1  # Convert to 0-based
        except ValueError:
            pass
        return None
    
    def _deduplicate_tests(self, tests: List[TestToRun]) -> List[TestToRun]:
        """Remove duplicate tests, keeping the highest priority."""
        seen = {}
        
        for test in tests:
            key = (test.file_path, test.line_number)
            if key not in seen or test.priority < seen[key].priority:
                seen[key] = test
        
        return list(seen.values())
    
    async def _count_total_tests(self) -> int:
        """Count total number of tests in the workspace."""
        total = 0
        
        try:
            for py_file in self.workspace_path.rglob('*.py'):
                if '.pytestembed_temp' in str(py_file):
                    continue
                    
                try:
                    parsed = self.parser.parse_file(str(py_file))
                    
                    # Count function tests
                    for func in parsed.functions:
                        for test_block in func.test_blocks:
                            total += len(test_block.test_cases)
                    
                    # Count class tests
                    for cls in parsed.classes:
                        for test_block in cls.test_blocks:
                            total += len(test_block.test_cases)
                        for method in cls.methods:
                            for test_block in method.test_blocks:
                                total += len(test_block.test_cases)
                    
                    # Count global tests
                    for test_block in parsed.global_test_blocks:
                        total += len(test_block.test_cases)
                        
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error counting total tests: {e}")
        
        return total
