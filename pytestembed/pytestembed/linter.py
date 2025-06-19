"""
PyTestEmbed Linter

Provides syntax checking and style validation for PyTestEmbed files.
Ensures code follows best practices and catches common errors.
"""

import ast
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .parser import PyTestEmbedParser
from .error_handler import get_error_handler, with_error_recovery


@dataclass
class LintIssue:
    """Represents a linting issue."""
    line: int
    column: int
    severity: str  # 'error', 'warning', 'info'
    code: str
    message: str
    suggestion: Optional[str] = None


class PyTestEmbedLinter:
    """Linter for PyTestEmbed syntax and style."""
    
    def __init__(self):
        self.parser = PyTestEmbedParser()
        self.error_handler = get_error_handler()
        self.issues: List[LintIssue] = []
        
        # Linting rules configuration
        self.rules = {
            'test_block_required': True,
            'doc_block_required': True,
            'min_test_cases': 2,
            'max_test_cases': 10,
            'test_description_required': True,
            'test_description_min_length': 5,
            'doc_args_required': True,
            'doc_returns_required': True,
            'trailing_comma_forbidden': True,
            'empty_blocks_forbidden': True,
            'duplicate_test_descriptions': True
        }
    
    @with_error_recovery(context="lint_file", default_return=[])
    def lint_file(self, file_path: str) -> List[LintIssue]:
        """Lint a PyTestEmbed file and return issues."""
        self.issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.lint_content(content, file_path)
            
        except FileNotFoundError:
            self.issues.append(LintIssue(
                line=0, column=0, severity='error', code='E001',
                message=f"File not found: {file_path}"
            ))
            return self.issues
    
    def lint_content(self, content: str, file_path: str = "<string>") -> List[LintIssue]:
        """Lint PyTestEmbed content and return issues."""
        self.issues = []
        lines = content.split('\n')
        
        # Parse the content
        try:
            parsed = self.parser.parse_content(content)
        except Exception as e:
            self.issues.append(LintIssue(
                line=1, column=0, severity='error', code='E002',
                message=f"Parse error: {str(e)}"
            ))
            return self.issues
        
        # Check Python syntax
        self._check_python_syntax(content)
        
        # Check PyTestEmbed syntax
        self._check_pytestembed_syntax(lines)
        
        # Check functions and methods
        for func in parsed.functions:
            self._check_function(func, lines)
        
        for cls in parsed.classes:
            for method in cls.methods:
                self._check_function(method, lines)
        
        return sorted(self.issues, key=lambda x: (x.line, x.column))
    
    def _check_python_syntax(self, content: str):
        """Check basic Python syntax."""
        try:
            ast.parse(content)
        except SyntaxError as e:
            self.issues.append(LintIssue(
                line=e.lineno or 1, column=e.offset or 0,
                severity='error', code='E003',
                message=f"Python syntax error: {e.msg}"
            ))
    
    def _check_pytestembed_syntax(self, lines: List[str]):
        """Check PyTestEmbed-specific syntax."""
        in_test_block = False
        in_doc_block = False
        test_start_line = 0
        doc_start_line = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for test block start
            if stripped == "test:":
                if in_test_block:
                    self.issues.append(LintIssue(
                        line=i, column=0, severity='error', code='E004',
                        message="Nested test blocks are not allowed"
                    ))
                in_test_block = True
                test_start_line = i
                continue
            
            # Check for doc block start
            if stripped == "doc:":
                if in_doc_block:
                    self.issues.append(LintIssue(
                        line=i, column=0, severity='error', code='E005',
                        message="Nested doc blocks are not allowed"
                    ))
                in_doc_block = True
                doc_start_line = i
                continue
            
            # Check for block end (function definition or class definition)
            if stripped.startswith(('def ', 'class ', '@')) and not line.startswith(' '):
                in_test_block = False
                in_doc_block = False
            
            # Check test block content
            if in_test_block and stripped:
                self._check_test_line(line, i)
            
            # Check doc block content
            if in_doc_block and stripped:
                self._check_doc_line(line, i)
    
    def _check_test_line(self, line: str, line_num: int):
        """Check individual test line syntax."""
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            return
        
        # Check for test case format
        if '==' in stripped or '!=' in stripped or ' is ' in stripped:
            # Check for description
            if ':' not in stripped:
                self.issues.append(LintIssue(
                    line=line_num, column=0, severity='warning', code='W001',
                    message="Test case should have a description",
                    suggestion="Add description after colon: expression == expected: \"description\""
                ))
            else:
                # Check description format
                parts = stripped.split(':', 1)
                if len(parts) > 1:
                    description = parts[1].strip()
                    if not description:
                        self.issues.append(LintIssue(
                            line=line_num, column=len(parts[0]) + 1, severity='warning', code='W002',
                            message="Empty test description"
                        ))
                    elif len(description) < self.rules['test_description_min_length']:
                        self.issues.append(LintIssue(
                            line=line_num, column=len(parts[0]) + 1, severity='info', code='I001',
                            message=f"Test description is very short (minimum {self.rules['test_description_min_length']} characters recommended)"
                        ))
            
            # Check for trailing comma
            if self.rules['trailing_comma_forbidden'] and stripped.endswith(','):
                # This might be the last test case
                self.issues.append(LintIssue(
                    line=line_num, column=len(stripped) - 1, severity='info', code='I002',
                    message="Consider removing trailing comma if this is the last test case"
                ))
    
    def _check_doc_line(self, line: str, line_num: int):
        """Check individual doc line syntax."""
        stripped = line.strip()
        
        # Check for common documentation patterns
        if stripped.startswith('Args:'):
            # Good practice
            pass
        elif stripped.startswith('Returns:'):
            # Good practice
            pass
        elif stripped.startswith('Raises:'):
            # Good practice
            pass
        elif stripped.startswith('Examples:'):
            # Good practice
            pass
    
    def _check_function(self, func, lines: List[str]):
        """Check function-specific linting rules."""
        func_name = func.name if hasattr(func, 'name') else str(func)
        func_line = getattr(func, 'line_number', 0)
        
        # Check if function has test block
        has_test_block = hasattr(func, 'test_blocks') and len(func.test_blocks) > 0
        if self.rules['test_block_required'] and not has_test_block:
            self.issues.append(LintIssue(
                line=func_line, column=0, severity='warning', code='W003',
                message=f"Function '{func_name}' should have a test block",
                suggestion="Add test: block after function definition"
            ))
        
        # Check if function has doc block
        has_doc_block = hasattr(func, 'doc_blocks') and len(func.doc_blocks) > 0
        if self.rules['doc_block_required'] and not has_doc_block:
            self.issues.append(LintIssue(
                line=func_line, column=0, severity='warning', code='W004',
                message=f"Function '{func_name}' should have a doc block",
                suggestion="Add doc: block after function definition"
            ))
        
        # Check test block quality
        if has_test_block:
            self._check_test_block_quality(func, func_name, func_line)
        
        # Check doc block quality
        if has_doc_block:
            self._check_doc_block_quality(func, func_name, func_line)
    
    def _check_test_block_quality(self, func, func_name: str, func_line: int):
        """Check quality of test blocks."""
        test_blocks = getattr(func, 'test_blocks', [])
        
        for test_block in test_blocks:
            test_cases = getattr(test_block, 'test_cases', [])
            
            # Check number of test cases
            if len(test_cases) < self.rules['min_test_cases']:
                self.issues.append(LintIssue(
                    line=func_line, column=0, severity='info', code='I003',
                    message=f"Function '{func_name}' has only {len(test_cases)} test case(s), consider adding more (minimum {self.rules['min_test_cases']} recommended)"
                ))
            elif len(test_cases) > self.rules['max_test_cases']:
                self.issues.append(LintIssue(
                    line=func_line, column=0, severity='info', code='I004',
                    message=f"Function '{func_name}' has {len(test_cases)} test cases, consider splitting into multiple test blocks"
                ))
            
            # Check for duplicate descriptions
            if self.rules['duplicate_test_descriptions']:
                descriptions = [tc.description for tc in test_cases if hasattr(tc, 'description')]
                if len(descriptions) != len(set(descriptions)):
                    self.issues.append(LintIssue(
                        line=func_line, column=0, severity='warning', code='W005',
                        message=f"Function '{func_name}' has duplicate test descriptions"
                    ))
    
    def _check_doc_block_quality(self, func, func_name: str, func_line: int):
        """Check quality of doc blocks."""
        doc_blocks = getattr(func, 'doc_blocks', [])
        
        for doc_block in doc_blocks:
            content = getattr(doc_block, 'content', '')
            
            # Check for Args section if function has parameters
            if hasattr(func, 'parameters') and func.parameters:
                if self.rules['doc_args_required'] and 'Args:' not in content:
                    self.issues.append(LintIssue(
                        line=func_line, column=0, severity='info', code='I005',
                        message=f"Function '{func_name}' with parameters should document Args"
                    ))
            
            # Check for Returns section
            if self.rules['doc_returns_required'] and 'Returns:' not in content:
                self.issues.append(LintIssue(
                    line=func_line, column=0, severity='info', code='I006',
                    message=f"Function '{func_name}' should document return value"
                ))
    
    def get_issue_summary(self) -> Dict[str, int]:
        """Get summary of issues by severity."""
        summary = {'error': 0, 'warning': 0, 'info': 0}
        for issue in self.issues:
            summary[issue.severity] += 1
        return summary
    
    def format_issues(self, format_type: str = 'text') -> str:
        """Format issues for display."""
        if format_type == 'json':
            import json
            return json.dumps([
                {
                    'line': issue.line,
                    'column': issue.column,
                    'severity': issue.severity,
                    'code': issue.code,
                    'message': issue.message,
                    'suggestion': issue.suggestion
                }
                for issue in self.issues
            ], indent=2)
        
        elif format_type == 'text':
            output = []
            for issue in self.issues:
                line = f"{issue.line}:{issue.column} {issue.severity.upper()} {issue.code}: {issue.message}"
                if issue.suggestion:
                    line += f"\n    Suggestion: {issue.suggestion}"
                output.append(line)
            return '\n'.join(output)
        
        else:
            return str(self.issues)
    
    def configure_rules(self, rules: Dict[str, Any]):
        """Configure linting rules."""
        self.rules.update(rules)


def lint_file(file_path: str, rules: Optional[Dict[str, Any]] = None) -> List[LintIssue]:
    """Convenience function to lint a single file."""
    linter = PyTestEmbedLinter()
    if rules:
        linter.configure_rules(rules)
    return linter.lint_file(file_path)


def lint_directory(directory: str, pattern: str = "*.py", 
                  rules: Optional[Dict[str, Any]] = None) -> Dict[str, List[LintIssue]]:
    """Lint all PyTestEmbed files in a directory."""
    from pathlib import Path
    
    results = {}
    directory_path = Path(directory)
    
    for file_path in directory_path.rglob(pattern):
        if file_path.is_file():
            issues = lint_file(str(file_path), rules)
            if issues:  # Only include files with issues
                results[str(file_path)] = issues
    
    return results
