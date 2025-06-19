#!/usr/bin/env python3
"""
Smart Test Selection Engine for PyTestEmbed

Intelligently selects which tests to run based on code changes,
reducing test execution time while maintaining confidence.
"""

import ast
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import time

from .parser import PyTestEmbedParser


@dataclass
class CodeChange:
    """Represents a change in the codebase."""
    file_path: str
    function_name: Optional[str]
    class_name: Optional[str]
    change_type: str  # 'added', 'modified', 'deleted'
    line_numbers: List[int]
    complexity_delta: int = 0


@dataclass
class TestImpact:
    """Represents the impact of a test."""
    test_file: str
    test_line: int
    test_expression: str
    target_function: str
    impact_score: float
    last_failure: Optional[float] = None
    execution_time: float = 0.0
    failure_rate: float = 0.0


@dataclass
class TestSelection:
    """Result of smart test selection."""
    selected_tests: List[TestImpact]
    skipped_tests: List[TestImpact]
    selection_reason: Dict[str, str]
    estimated_time_saved: float
    confidence_score: float


class DependencyAnalyzer:
    """Analyzes code dependencies to determine test impact."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = {}
        self.function_signatures: Dict[str, str] = {}
        
    def build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build a dependency graph of the codebase."""
        print("🔍 Building dependency graph...")
        
        for py_file in self.workspace_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                file_key = str(py_file.relative_to(self.workspace_path))
                
                # Extract imports and function calls
                imports = self._extract_imports(tree)
                function_calls = self._extract_function_calls(tree)
                function_defs = self._extract_function_definitions(tree)
                
                # Store function signatures
                for func_name, signature in function_defs.items():
                    self.function_signatures[f"{file_key}::{func_name}"] = signature
                
                # Build dependencies
                dependencies = set()
                dependencies.update(imports)
                dependencies.update(function_calls)
                
                self.dependency_graph[file_key] = dependencies
                
                # Build reverse dependencies
                for dep in dependencies:
                    if dep not in self.reverse_dependencies:
                        self.reverse_dependencies[dep] = set()
                    self.reverse_dependencies[dep].add(file_key)
                    
            except Exception as e:
                print(f"⚠️ Error analyzing {py_file}: {e}")
                
        print(f"✅ Dependency graph built: {len(self.dependency_graph)} files analyzed")
        return self.dependency_graph
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis."""
        skip_patterns = [
            '__pycache__',
            '.git',
            '.pytest_cache',
            'venv',
            'env',
            '.venv',
            'node_modules'
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract import statements from AST."""
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")
                        
        return imports
    
    def _extract_function_calls(self, tree: ast.AST) -> Set[str]:
        """Extract function calls from AST."""
        calls = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
                    
        return calls
    
    def _extract_function_definitions(self, tree: ast.AST) -> Dict[str, str]:
        """Extract function definitions and their signatures."""
        functions = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Create function signature
                args = [arg.arg for arg in node.args.args]
                signature = f"{node.name}({', '.join(args)})"
                functions[node.name] = signature
                
        return functions
    
    def find_impacted_files(self, changed_files: List[str]) -> Set[str]:
        """Find all files that could be impacted by changes."""
        impacted = set(changed_files)
        
        # Use BFS to find all dependent files
        queue = list(changed_files)
        visited = set()
        
        while queue:
            current_file = queue.pop(0)
            if current_file in visited:
                continue
                
            visited.add(current_file)
            
            # Find files that depend on this file
            dependents = self.reverse_dependencies.get(current_file, set())
            for dependent in dependents:
                if dependent not in impacted:
                    impacted.add(dependent)
                    queue.append(dependent)
                    
        return impacted


class GitChangeAnalyzer:
    """Analyzes Git changes to identify modified code."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
    
    def get_changes_since_commit(self, commit_hash: str = "HEAD~1") -> List[CodeChange]:
        """Get code changes since a specific commit."""
        try:
            # Get changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", commit_hash],
                cwd=self.workspace_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"⚠️ Git diff failed: {result.stderr}")
                return []
            
            changed_files = [f for f in result.stdout.strip().split('\n') if f.endswith('.py')]
            changes = []
            
            for file_path in changed_files:
                file_changes = self._analyze_file_changes(file_path, commit_hash)
                changes.extend(file_changes)
                
            return changes
            
        except Exception as e:
            print(f"⚠️ Error analyzing Git changes: {e}")
            return []
    
    def _analyze_file_changes(self, file_path: str, commit_hash: str) -> List[CodeChange]:
        """Analyze changes in a specific file."""
        try:
            # Get detailed diff for the file
            result = subprocess.run(
                ["git", "diff", "-U0", commit_hash, "--", file_path],
                cwd=self.workspace_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return []
            
            diff_lines = result.stdout.split('\n')
            changes = []
            
            # Parse diff to identify changed functions
            current_function = None
            changed_lines = []
            
            for line in diff_lines:
                if line.startswith('@@'):
                    # Extract line numbers from diff header
                    parts = line.split()
                    if len(parts) >= 3:
                        line_info = parts[2].replace('+', '').split(',')
                        start_line = int(line_info[0])
                        changed_lines.append(start_line)
                        
                elif line.startswith('+') and not line.startswith('+++'):
                    # Added line - try to identify function
                    function_name = self._extract_function_from_line(line[1:])
                    if function_name:
                        current_function = function_name
            
            # Create change objects
            if changed_lines:
                change = CodeChange(
                    file_path=file_path,
                    function_name=current_function,
                    class_name=None,  # TODO: Extract class name
                    change_type='modified',
                    line_numbers=changed_lines
                )
                changes.append(change)
                
            return changes
            
        except Exception as e:
            print(f"⚠️ Error analyzing file {file_path}: {e}")
            return []
    
    def _extract_function_from_line(self, line: str) -> Optional[str]:
        """Extract function name from a line of code."""
        line = line.strip()
        if line.startswith('def '):
            # Extract function name
            parts = line.split('(')[0].split()
            if len(parts) >= 2:
                return parts[1]
        return None


class SmartTestSelector:
    """Main class for intelligent test selection."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.parser = PyTestEmbedParser()
        self.dependency_analyzer = DependencyAnalyzer(workspace_path)
        self.git_analyzer = GitChangeAnalyzer(workspace_path)
        self.test_history_file = self.workspace_path / ".pytestembed" / "test_history.json"
        self.test_history: Dict[str, Dict] = self._load_test_history()
        
    def select_tests(self, 
                    commit_hash: str = "HEAD~1",
                    max_execution_time: Optional[float] = None,
                    confidence_threshold: float = 0.8) -> TestSelection:
        """Select tests to run based on code changes."""
        
        print("🧠 Starting smart test selection...")
        
        # Step 1: Analyze code changes
        changes = self.git_analyzer.get_changes_since_commit(commit_hash)
        print(f"📝 Found {len(changes)} code changes")
        
        # Step 2: Build dependency graph
        self.dependency_analyzer.build_dependency_graph()
        
        # Step 3: Find impacted files
        changed_files = list(set(change.file_path for change in changes))
        impacted_files = self.dependency_analyzer.find_impacted_files(changed_files)
        print(f"🎯 {len(impacted_files)} files potentially impacted")
        
        # Step 4: Find all tests
        all_tests = self._find_all_tests()
        print(f"🧪 Found {len(all_tests)} total tests")
        
        # Step 5: Calculate impact scores
        test_impacts = self._calculate_test_impacts(all_tests, changes, impacted_files)
        
        # Step 6: Select tests based on criteria
        selected_tests, skipped_tests = self._select_tests_by_criteria(
            test_impacts, max_execution_time, confidence_threshold
        )
        
        # Step 7: Calculate metrics
        total_time = sum(t.execution_time for t in all_tests)
        selected_time = sum(t.execution_time for t in selected_tests)
        time_saved = total_time - selected_time
        confidence = self._calculate_confidence_score(selected_tests, all_tests)
        
        selection = TestSelection(
            selected_tests=selected_tests,
            skipped_tests=skipped_tests,
            selection_reason=self._generate_selection_reasons(selected_tests),
            estimated_time_saved=time_saved,
            confidence_score=confidence
        )
        
        print(f"✅ Selected {len(selected_tests)}/{len(all_tests)} tests")
        print(f"⏱️ Estimated time saved: {time_saved:.1f}s ({time_saved/total_time*100:.1f}%)")
        print(f"🎯 Confidence score: {confidence:.2f}")
        
        return selection

    def _find_all_tests(self) -> List[TestImpact]:
        """Find all PyTestEmbed tests in the workspace."""
        tests = []

        for py_file in self.workspace_path.rglob("*.py"):
            if self.dependency_analyzer._should_skip_file(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse PyTestEmbed tests
                parsed = self.parser.parse_file(content)
                file_path = str(py_file.relative_to(self.workspace_path))

                # Extract tests from functions
                for func in parsed.functions:
                    for test_block in func.test_blocks:
                        for i, test_case in enumerate(test_block.test_cases):
                            test_key = f"{file_path}::{func.name}::{i}"
                            history = self.test_history.get(test_key, {})

                            test_impact = TestImpact(
                                test_file=file_path,
                                test_line=test_case.line_number,
                                test_expression=test_case.assertion,
                                target_function=func.name,
                                impact_score=0.0,
                                last_failure=history.get('last_failure'),
                                execution_time=history.get('execution_time', 0.1),
                                failure_rate=history.get('failure_rate', 0.0)
                            )
                            tests.append(test_impact)

            except Exception as e:
                print(f"⚠️ Error parsing {py_file}: {e}")

        return tests

    def _calculate_test_impacts(self, tests: List[TestImpact],
                              changes: List[CodeChange],
                              impacted_files: Set[str]) -> List[TestImpact]:
        """Calculate impact scores for tests based on changes."""

        for test in tests:
            score = 0.0

            # Direct impact: test file was changed
            if test.test_file in impacted_files:
                score += 1.0

            # Function impact: target function was changed
            for change in changes:
                if (change.file_path == test.test_file and
                    change.function_name == test.target_function):
                    score += 2.0

            # Dependency impact: dependencies were changed
            dependencies = self.dependency_analyzer.dependency_graph.get(test.test_file, set())
            for dep in dependencies:
                if dep in impacted_files:
                    score += 0.5

            # Historical impact: recently failed tests get higher priority
            if test.last_failure and time.time() - test.last_failure < 86400:  # 24 hours
                score += 1.0

            # Failure rate impact: flaky tests get higher priority
            score += test.failure_rate * 0.5

            test.impact_score = score

        return sorted(tests, key=lambda t: t.impact_score, reverse=True)

    def _select_tests_by_criteria(self, test_impacts: List[TestImpact],
                                max_execution_time: Optional[float],
                                confidence_threshold: float) -> Tuple[List[TestImpact], List[TestImpact]]:
        """Select tests based on impact scores and constraints."""

        selected = []
        skipped = []
        total_time = 0.0

        # Always include high-impact tests (score > 1.0)
        high_impact_tests = [t for t in test_impacts if t.impact_score > 1.0]
        selected.extend(high_impact_tests)
        total_time += sum(t.execution_time for t in high_impact_tests)

        # Add medium-impact tests if time allows
        medium_impact_tests = [t for t in test_impacts if 0.5 <= t.impact_score <= 1.0]

        if max_execution_time:
            for test in medium_impact_tests:
                if total_time + test.execution_time <= max_execution_time:
                    selected.append(test)
                    total_time += test.execution_time
                else:
                    skipped.append(test)
        else:
            selected.extend(medium_impact_tests)

        # Skip low-impact tests unless confidence is too low
        low_impact_tests = [t for t in test_impacts if t.impact_score < 0.5]

        current_confidence = self._calculate_confidence_score(selected, test_impacts)
        if current_confidence < confidence_threshold:
            # Add some low-impact tests to increase confidence
            needed_tests = int(len(low_impact_tests) * (confidence_threshold - current_confidence))
            selected.extend(low_impact_tests[:needed_tests])
            skipped.extend(low_impact_tests[needed_tests:])
        else:
            skipped.extend(low_impact_tests)

        return selected, skipped

    def _calculate_confidence_score(self, selected_tests: List[TestImpact],
                                  all_tests: List[TestImpact]) -> float:
        """Calculate confidence score for test selection."""
        if not all_tests:
            return 1.0

        # Base confidence from test coverage
        coverage_confidence = len(selected_tests) / len(all_tests)

        # Impact-weighted confidence
        total_impact = sum(t.impact_score for t in all_tests)
        selected_impact = sum(t.impact_score for t in selected_tests)

        if total_impact > 0:
            impact_confidence = selected_impact / total_impact
        else:
            impact_confidence = coverage_confidence

        # Combine confidences
        return min(1.0, (coverage_confidence + impact_confidence) / 2)

    def _generate_selection_reasons(self, selected_tests: List[TestImpact]) -> Dict[str, str]:
        """Generate human-readable reasons for test selection."""
        reasons = {}

        for test in selected_tests:
            test_key = f"{test.test_file}::{test.target_function}::{test.test_line}"

            if test.impact_score > 2.0:
                reasons[test_key] = "High impact: Target function was modified"
            elif test.impact_score > 1.0:
                reasons[test_key] = "Medium impact: Related code was changed"
            elif test.last_failure:
                reasons[test_key] = "Recently failed test"
            elif test.failure_rate > 0.1:
                reasons[test_key] = "Historically flaky test"
            else:
                reasons[test_key] = "Confidence threshold requirement"

        return reasons

    def _load_test_history(self) -> Dict[str, Dict]:
        """Load test execution history."""
        if self.test_history_file.exists():
            try:
                with open(self.test_history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading test history: {e}")
        return {}

    def update_test_history(self, test_results: List[Dict]):
        """Update test execution history with new results."""
        for result in test_results:
            test_key = f"{result['file']}::{result['function']}::{result['line']}"

            if test_key not in self.test_history:
                self.test_history[test_key] = {
                    'execution_count': 0,
                    'failure_count': 0,
                    'total_execution_time': 0.0
                }

            history = self.test_history[test_key]
            history['execution_count'] += 1
            history['total_execution_time'] += result.get('execution_time', 0.1)

            if result['status'] in ['fail', 'error']:
                history['failure_count'] += 1
                history['last_failure'] = time.time()

            # Calculate derived metrics
            history['failure_rate'] = history['failure_count'] / history['execution_count']
            history['execution_time'] = history['total_execution_time'] / history['execution_count']

        # Save updated history
        self._save_test_history()

    def _save_test_history(self):
        """Save test execution history to file."""
        try:
            self.test_history_file.parent.mkdir(exist_ok=True)
            with open(self.test_history_file, 'w') as f:
                json.dump(self.test_history, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving test history: {e}")


# CLI interface for smart test selection
def run_smart_test_selection(workspace_path: str = ".",
                           commit_hash: str = "HEAD~1",
                           max_time: Optional[float] = None,
                           confidence: float = 0.8) -> TestSelection:
    """Run smart test selection from command line."""

    selector = SmartTestSelector(workspace_path)
    selection = selector.select_tests(commit_hash, max_time, confidence)

    print("\n📊 Smart Test Selection Results:")
    print(f"Selected: {len(selection.selected_tests)} tests")
    print(f"Skipped: {len(selection.skipped_tests)} tests")
    print(f"Time saved: {selection.estimated_time_saved:.1f}s")
    print(f"Confidence: {selection.confidence_score:.2f}")

    return selection


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PyTestEmbed Smart Test Selection")
    parser.add_argument("--workspace", default=".", help="Workspace directory")
    parser.add_argument("--commit", default="HEAD~1", help="Compare against commit")
    parser.add_argument("--max-time", type=float, help="Maximum execution time")
    parser.add_argument("--confidence", type=float, default=0.8, help="Confidence threshold")

    args = parser.parse_args()

    run_smart_test_selection(args.workspace, args.commit, args.max_time, args.confidence)
