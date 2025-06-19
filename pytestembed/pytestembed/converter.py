"""
Python to PyTestEmbed converter.

Converts existing Python files to PyTestEmbed syntax by:
- Moving docstrings to doc: blocks
- Generating test: blocks using AI
- Preserving original code structure
"""

import ast
from typing import List, Dict, Optional
from .ai_integration import get_ai_manager, AIProviderError
from .ai_test_generator import SmartTestGenerator
from .ai_doc_enhancer import SmartDocumentationEnhancer


class PythonToPyTestEmbedConverter:
    """Converts Python files to PyTestEmbed syntax."""
    
    def __init__(self, use_ai: bool = True, ai_provider: Optional[str] = None):
        self.use_ai = use_ai
        self.ai_provider = ai_provider
        self.ai_manager = get_ai_manager() if use_ai else None
    
    def convert_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """Convert a Python file to PyTestEmbed syntax."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        converted_content = self.convert_content(content)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
        
        return converted_content
    
    def convert_content(self, content: str) -> str:
        """Convert Python content to PyTestEmbed syntax."""
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")
        
        # Analyze the AST to find functions, classes, and methods
        analyzer = PythonCodeAnalyzer()
        analysis = analyzer.analyze(tree, content)
        
        # Convert the content
        converter = ContentConverter(self.ai_manager, self.ai_provider)
        return converter.convert(content, analysis)


class PythonCodeAnalyzer:
    """Analyzes Python AST to extract functions, classes, and methods."""

    def __init__(self):
        self.functions = []
        self.classes = []

    def analyze(self, tree: ast.AST, content: str) -> Dict:
        """Analyze the AST and return structured information."""
        content_lines = content.split('\n')

        # Process top-level nodes only
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                # Top-level function
                function_info = {
                    'name': node.name,
                    'lineno': node.lineno,
                    'end_lineno': getattr(node, 'end_lineno', node.lineno),
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node),
                    'is_method': False,
                    'node': node
                }
                self.functions.append(function_info)

            elif isinstance(node, ast.ClassDef):
                # Class with methods
                class_info = {
                    'name': node.name,
                    'lineno': node.lineno,
                    'end_lineno': getattr(node, 'end_lineno', node.lineno),
                    'docstring': ast.get_docstring(node),
                    'methods': [],
                    'node': node
                }

                # Find methods in this class
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        method_info = {
                            'name': child.name,
                            'lineno': child.lineno,
                            'end_lineno': getattr(child, 'end_lineno', child.lineno),
                            'args': [arg.arg for arg in child.args.args],
                            'docstring': ast.get_docstring(child),
                            'is_method': True,
                            'node': child
                        }
                        class_info['methods'].append(method_info)

                self.classes.append(class_info)

        return {
            'functions': self.functions,
            'classes': self.classes,
            'content_lines': content_lines
        }


class ContentConverter:
    """Converts content based on analysis."""

    def __init__(self, ai_manager, ai_provider: Optional[str] = None):
        self.ai_manager = ai_manager
        self.ai_provider = ai_provider
        self.test_generator = SmartTestGenerator(ai_provider) if ai_manager else None
        self.doc_enhancer = SmartDocumentationEnhancer(ai_provider) if ai_manager else None
    
    def convert(self, content: str, analysis: Dict) -> str:
        """Convert content to PyTestEmbed syntax."""
        lines = content.split('\n')

        # Create a list to track insertions
        insertions = []

        # Process functions (not methods)
        for func in analysis['functions']:
            if not func['is_method']:  # Only process standalone functions
                end_line = func.get('end_lineno', func['lineno'])
                test_block = self._generate_test_block(func, 'function', None, self._get_indentation(lines[func['lineno'] - 1]))
                doc_block = self._generate_doc_block(func, 'function', self._get_indentation(lines[func['lineno'] - 1]))

                insertions.append((end_line, test_block + doc_block))

        # Process classes and their methods
        for cls in analysis['classes']:
            # Process methods within the class first (in reverse order)
            for method in cls['methods']:
                method_end = method.get('end_lineno', method['lineno'])
                test_block = self._generate_test_block(method, 'method', cls, self._get_indentation(lines[method['lineno'] - 1]))
                doc_block = self._generate_doc_block(method, 'method', self._get_indentation(lines[method['lineno'] - 1]))

                insertions.append((method_end, test_block + doc_block))

            # Add class doc block at the end of the class (after all methods)
            class_end = cls.get('end_lineno', cls['lineno'])
            class_doc_block = self._generate_doc_block(cls, 'class', self._get_indentation(lines[cls['lineno'] - 1]))
            insertions.append((class_end, class_doc_block))

        # Sort all insertions by line number in reverse order
        insertions.sort(key=lambda x: x[0], reverse=True)

        # Apply insertions
        for line_num, blocks in insertions:
            for block_line in reversed(blocks):
                lines.insert(line_num, block_line)

        return '\n'.join(lines)
    

    

    
    def _get_indentation(self, line: str) -> str:
        """Get the indentation of a line."""
        return line[:len(line) - len(line.lstrip())]
    
    def _generate_test_block(self, item_info: Dict, item_type: str, class_info: Optional[Dict], indent: str) -> List[str]:
        """Generate test block for a function or method."""
        if not self.ai_manager or not self.ai_manager.is_ai_available():
            # Generate simple placeholder tests
            return self._generate_placeholder_tests(item_info, indent)
        
        try:
            # Generate AI-powered tests
            return self._generate_ai_tests(item_info, item_type, class_info, indent)
        except AIProviderError:
            # Fallback to placeholder tests
            return self._generate_placeholder_tests(item_info, indent)
    
    def _generate_doc_block(self, item_info: Dict, item_type: str, indent: str) -> List[str]:
        """Generate doc block from existing docstring or AI."""
        docstring = item_info.get('docstring')
        
        if docstring:
            # Convert existing docstring
            doc_lines = [f"{indent}doc:"]
            for line in docstring.split('\n'):
                if line.strip():
                    doc_lines.append(f"{indent}    {line.strip()}")
            return doc_lines
        
        if self.ai_manager and self.ai_manager.is_ai_available():
            try:
                return self._generate_ai_documentation(item_info, item_type, indent)
            except AIProviderError:
                pass
        
        # Generate placeholder documentation
        return [
            f"{indent}doc:",
            f"{indent}    {item_info['name']} - Add description here"
        ]
    
    def _generate_placeholder_tests(self, item_info: Dict, indent: str) -> List[str]:
        """Generate placeholder test block."""
        return [
            f"{indent}test:",
            f"{indent}    # Add tests for {item_info['name']} here",
            f"{indent}    True == True: \"Placeholder test\","
        ]
    
    def _generate_ai_tests(self, item_info: Dict, item_type: str, class_info: Optional[Dict], indent: str) -> List[str]:
        """Generate AI-powered test block."""
        if self.test_generator:
            try:
                return self.test_generator.generate_comprehensive_tests(item_info, item_type, class_info, indent)
            except Exception as e:
                print(f"AI test generation failed: {e}")

        return self._generate_placeholder_tests(item_info, indent)

    def _generate_ai_documentation(self, item_info: Dict, item_type: str, indent: str) -> List[str]:
        """Generate AI-powered documentation."""
        if self.doc_enhancer:
            try:
                return self.doc_enhancer.generate_comprehensive_documentation(item_info, item_type, None, indent)
            except Exception as e:
                print(f"AI documentation generation failed: {e}")

        return [
            f"{indent}doc:",
            f"{indent}    {item_info['name']} - Add description here"
        ]
