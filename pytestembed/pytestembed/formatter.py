"""
PyTestEmbed Code Formatter

Provides automatic formatting for PyTestEmbed files to ensure
consistent style and proper syntax structure.
"""

import re
import ast
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .parser import PyTestEmbedParser
from .error_handler import get_error_handler, with_error_recovery


class PyTestEmbedFormatter:
    """Formatter for PyTestEmbed syntax and style."""
    
    def __init__(self):
        self.parser = PyTestEmbedParser()
        self.error_handler = get_error_handler()
        
        # Formatting configuration
        self.config = {
            'indent_size': 4,
            'max_line_length': 88,
            'test_case_alignment': True,
            'doc_block_wrap': True,
            'remove_trailing_commas': True,
            'normalize_quotes': True,
            'preferred_quote': '"',
            'sort_test_cases': False,
            'add_blank_lines': True
        }
    
    @with_error_recovery(context="format_file", default_return="")
    def format_file(self, file_path: str, in_place: bool = False) -> str:
        """Format a PyTestEmbed file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            formatted_content = self.format_content(content)
            
            if in_place:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(formatted_content)
            
            return formatted_content
            
        except Exception as e:
            self.error_handler.handle_error(e, f"format_file_{file_path}")
            return content if 'content' in locals() else ""
    
    def format_content(self, content: str) -> str:
        """Format PyTestEmbed content."""
        lines = content.split('\n')
        formatted_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a test block
            if line.strip() == "test:":
                formatted_lines.append(line)
                i += 1
                i = self._format_test_block(lines, i, formatted_lines)
                continue
            
            # Check if this is a doc block
            elif line.strip() == "doc:":
                formatted_lines.append(line)
                i += 1
                i = self._format_doc_block(lines, i, formatted_lines)
                continue
            
            # Regular Python line
            else:
                formatted_lines.append(line)
                i += 1
        
        # Post-process for blank lines and final cleanup
        return self._post_process(formatted_lines)
    
    def _format_test_block(self, lines: List[str], start_idx: int,
                          formatted_lines: List[str]) -> int:
        """Format a test block and return next line index."""
        test_lines = []
        i = start_idx

        # Collect test block lines
        while i < len(lines):
            line = lines[i]

            # Check if we've reached the end of the test block
            if (line.strip() and
                line.strip() in ['doc:', 'test:'] and i > start_idx):
                # Hit another block
                break
            elif (line.strip() and
                  not line.startswith(' ') and
                  not line.strip().startswith('#') and
                  line.strip() not in ['test:', 'doc:'] and
                  not self._looks_like_test_case(line)):
                # Hit a function/class definition
                break

            if line.strip():  # Non-empty line
                test_lines.append(line)

            i += 1

        # Format the test cases
        formatted_test_lines = self._format_test_cases(test_lines)
        formatted_lines.extend(formatted_test_lines)

        return i

    def _looks_like_test_case(self, line: str) -> bool:
        """Check if line looks like a test case."""
        stripped = line.strip()
        # Look for comparison operators and colon (test case pattern)
        has_comparison = any(op in stripped for op in ['==', '!=', ' is ', ' in ', '>=', '<=', '>', '<'])
        has_colon = ':' in stripped
        return has_comparison and has_colon
    
    def _format_test_cases(self, test_lines: List[str]) -> List[str]:
        """Format individual test cases."""
        if not test_lines:
            return []
        
        formatted = []
        test_cases = []
        
        # Parse test cases
        current_case = ""
        for line in test_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            current_case += " " + stripped if current_case else stripped
            
            # Check if this completes a test case
            if self._is_complete_test_case(current_case):
                test_cases.append(current_case.strip())
                current_case = ""
        
        # Add any remaining incomplete case
        if current_case.strip():
            test_cases.append(current_case.strip())
        
        # Format each test case
        for i, test_case in enumerate(test_cases):
            formatted_case = self._format_single_test_case(test_case)
            
            # Remove trailing comma from last test case
            if (i == len(test_cases) - 1 and 
                self.config['remove_trailing_commas'] and 
                formatted_case.rstrip().endswith(',')):
                formatted_case = formatted_case.rstrip()[:-1]
            
            # Add comma to non-last test cases if missing
            elif (i < len(test_cases) - 1 and 
                  not formatted_case.rstrip().endswith(',')):
                formatted_case = formatted_case.rstrip() + ','
            
            formatted.append(f"    {formatted_case}")
        
        return formatted
    
    def _is_complete_test_case(self, case: str) -> bool:
        """Check if a test case is complete."""
        # Simple heuristic: contains comparison and description
        has_comparison = any(op in case for op in ['==', '!=', ' is ', ' in '])
        has_description = ':' in case and '"' in case.split(':', 1)[-1]
        return has_comparison and has_description
    
    def _format_single_test_case(self, test_case: str) -> str:
        """Format a single test case."""
        # Remove trailing comma for processing
        case = test_case.rstrip(',').strip()

        # Split into expression and description
        if ':' in case:
            parts = case.split(':', 1)
            expression = parts[0].strip()
            description = parts[1].strip()

            # Format expression with proper spacing around operators
            expression = self._format_expression(expression)

            # Normalize quotes in description
            if self.config['normalize_quotes']:
                description = self._normalize_quotes(description)

            # Format with proper spacing
            formatted = f"{expression}: {description}"

            # Restore trailing comma if it was there
            if test_case.rstrip().endswith(','):
                formatted += ','

            return formatted

        return test_case

    def _format_expression(self, expression: str) -> str:
        """Format expression with proper spacing around operators."""
        import re

        # Add spaces around comparison operators
        operators = ['==', '!=', '<=', '>=', '<', '>', ' is ', ' in ']

        for op in operators:
            if op.strip() in expression:
                # Handle operators with existing spaces
                if op.startswith(' ') and op.endswith(' '):
                    # Already has spaces, ensure proper spacing
                    expression = re.sub(f'\\s*{re.escape(op.strip())}\\s*', op, expression)
                else:
                    # Add spaces around operator
                    expression = re.sub(f'\\s*{re.escape(op)}\\s*', f' {op} ', expression)

        # Add spaces around parentheses and commas
        expression = re.sub(r'\s*,\s*', ', ', expression)
        expression = re.sub(r'\(\s*', '(', expression)
        expression = re.sub(r'\s*\)', ')', expression)

        return expression.strip()
    
    def _normalize_quotes(self, text: str) -> str:
        """Normalize quotes in text."""
        preferred = self.config['preferred_quote']
        other = "'" if preferred == '"' else '"'
        
        # Simple quote normalization (doesn't handle nested quotes perfectly)
        if text.startswith(other) and text.endswith(other):
            # Only change if no internal quotes of preferred type
            if preferred not in text[1:-1]:
                return preferred + text[1:-1] + preferred
        
        return text
    
    def _format_doc_block(self, lines: List[str], start_idx: int, 
                         formatted_lines: List[str]) -> int:
        """Format a doc block and return next line index."""
        doc_lines = []
        i = start_idx
        
        # Collect doc block lines
        while i < len(lines):
            line = lines[i]
            
            # Check if we've reached the end of the doc block
            if (line.strip() and not line.startswith(' ') and 
                not line.strip().startswith('#') and
                line.strip() not in ['test:', 'doc:']):
                break
            
            doc_lines.append(line)
            i += 1
        
        # Format the documentation
        formatted_doc_lines = self._format_documentation(doc_lines)
        formatted_lines.extend(formatted_doc_lines)
        
        return i
    
    def _format_documentation(self, doc_lines: List[str]) -> List[str]:
        """Format documentation content."""
        if not doc_lines:
            return []
        
        formatted = []
        current_section = None
        
        for line in doc_lines:
            stripped = line.strip()
            
            if not stripped:
                formatted.append("")
                continue
            
            # Detect sections
            if stripped.endswith(':') and stripped.split(':')[0] in ['Args', 'Returns', 'Raises', 'Examples']:
                current_section = stripped.split(':')[0]
                formatted.append(f"    {stripped}")
                continue
            
            # Format based on section
            if current_section in ['Args', 'Returns', 'Raises']:
                # Parameter documentation
                if ':' in stripped and not stripped.startswith(' '):
                    formatted.append(f"        {stripped}")
                else:
                    formatted.append(f"    {stripped}")
            else:
                # Regular documentation
                formatted.append(f"    {stripped}")
        
        return formatted
    
    def _post_process(self, lines: List[str]) -> str:
        """Post-process formatted lines."""
        if not self.config['add_blank_lines']:
            return '\n'.join(lines)
        
        # Add blank lines around test and doc blocks
        processed = []
        prev_was_block = False
        
        for i, line in enumerate(lines):
            current_is_block = line.strip() in ['test:', 'doc:']
            
            # Add blank line before block if previous wasn't a block
            if current_is_block and not prev_was_block and processed and processed[-1].strip():
                processed.append("")
            
            processed.append(line)
            prev_was_block = current_is_block
        
        return '\n'.join(processed)
    
    def configure(self, config: Dict[str, Any]):
        """Configure formatter settings."""
        self.config.update(config)
    
    def check_formatting(self, content: str) -> bool:
        """Check if content is already properly formatted."""
        formatted = self.format_content(content)
        return content.strip() == formatted.strip()


class PyTestEmbedStyleGuide:
    """Style guide and best practices for PyTestEmbed."""
    
    @staticmethod
    def get_style_recommendations() -> Dict[str, str]:
        """Get style recommendations."""
        return {
            'test_descriptions': 'Use clear, descriptive test case descriptions',
            'test_coverage': 'Include at least 2-3 test cases per function',
            'edge_cases': 'Test edge cases like empty inputs, zero values, and boundary conditions',
            'doc_structure': 'Use Args, Returns, and Raises sections in documentation',
            'line_length': 'Keep lines under 88 characters when possible',
            'quotes': 'Use double quotes for test descriptions consistently',
            'trailing_commas': 'Remove trailing commas from the last test case',
            'blank_lines': 'Add blank lines around test and doc blocks for readability'
        }
    
    @staticmethod
    def get_example_formatting() -> str:
        """Get example of well-formatted PyTestEmbed code."""
        return '''
def calculate_area(length, width):
    """Calculate the area of a rectangle."""
    return length * width

test:
    calculate_area(5, 3) == 15: "Basic rectangle area",
    calculate_area(0, 5) == 0: "Zero length handling",
    calculate_area(2.5, 4) == 10.0: "Float dimensions"

doc:
    Calculates the area of a rectangle given length and width.
    
    Args:
        length (float): Length of the rectangle
        width (float): Width of the rectangle
    
    Returns:
        float: Area of the rectangle
    
    Examples:
        >>> calculate_area(5, 3)
        15
'''


def format_file(file_path: str, in_place: bool = False, 
               config: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to format a single file."""
    formatter = PyTestEmbedFormatter()
    if config:
        formatter.configure(config)
    return formatter.format_file(file_path, in_place)


def format_directory(directory: str, pattern: str = "*.py", 
                    in_place: bool = False,
                    config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Format all PyTestEmbed files in a directory."""
    from pathlib import Path
    
    results = {}
    directory_path = Path(directory)
    
    for file_path in directory_path.rglob(pattern):
        if file_path.is_file():
            formatted = format_file(str(file_path), in_place, config)
            results[str(file_path)] = formatted
    
    return results
