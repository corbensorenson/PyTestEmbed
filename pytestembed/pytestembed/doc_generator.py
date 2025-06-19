"""Documentation generator for PyTestEmbed."""

import re
from typing import List, Dict, Any, Optional
from .parser import ParsedProgram, DocBlock, ClassDef, MethodDef, FunctionDef


class DocGenerator:
    """Generates documentation from parsed PyTestEmbed structures."""

    def __init__(self, use_ai: bool = False):
        """Initialize the documentation generator.

        Args:
            use_ai: Whether to use AI enhancement (not implemented in MVP)
        """
        self.use_ai = use_ai

    def generate_docs(self, parsed_program: ParsedProgram, title: str = "Documentation") -> str:
        """Generate documentation from parsed program."""
        lines = []

        # Add title
        lines.append(f"# {title}")
        lines.append("")

        # Add global documentation if present
        if parsed_program.global_doc_blocks:
            global_content = self._extract_doc_content(parsed_program.global_doc_blocks)
            if global_content:
                lines.append(global_content)
                lines.append("")

        # Generate documentation for classes
        for class_def in parsed_program.classes:
            class_docs = self._generate_class_docs(class_def)
            if class_docs:
                lines.extend(class_docs)
                lines.append("")

        # Generate documentation for standalone functions
        for func_def in parsed_program.functions:
            func_docs = self._generate_function_docs(func_def)
            if func_docs:
                lines.extend(func_docs)
                lines.append("")

        return "\n".join(lines).strip()

    def _generate_class_docs(self, class_def: ClassDef) -> List[str]:
        """Generate documentation for a class."""
        lines = []

        # Class header
        lines.append(f"## Class: {class_def.name}")
        lines.append("")

        # Class description from doc blocks
        if class_def.doc_blocks:
            class_content = self._extract_doc_content(class_def.doc_blocks)
            if class_content:
                lines.append(class_content)
                lines.append("")

        # Document methods
        for method_def in class_def.methods:
            method_docs = self._generate_method_docs(method_def)
            if method_docs:
                lines.extend(method_docs)
                lines.append("")

        return lines

    def _generate_method_docs(self, method_def: MethodDef) -> List[str]:
        """Generate documentation for a method."""
        lines = []

        # Method header
        params_str = ", ".join(method_def.parameters)
        lines.append(f"### Method: {method_def.name}({params_str})")
        lines.append("")

        # Method description from doc blocks
        if method_def.doc_blocks:
            method_content = self._extract_doc_content(method_def.doc_blocks)
            if method_content:
                lines.append(f"**Description**: {method_content}")
                lines.append("")

        # Add parameter information if available
        if len(method_def.parameters) > 1:  # More than just 'self'
            lines.append("**Parameters**:")
            for param in method_def.parameters:
                if param != 'self':
                    lines.append(f"- `{param}`: Parameter description")
            lines.append("")

        return lines

    def _generate_function_docs(self, func_def: FunctionDef) -> List[str]:
        """Generate documentation for a standalone function."""
        lines = []

        # Function header
        params_str = ", ".join(func_def.parameters)
        lines.append(f"## Function: {func_def.name}({params_str})")
        lines.append("")

        # Function description from doc blocks
        if func_def.doc_blocks:
            func_content = self._extract_doc_content(func_def.doc_blocks)
            if func_content:
                lines.append(f"**Description**: {func_content}")
                lines.append("")

        # Add parameter information if available
        if func_def.parameters:
            lines.append("**Parameters**:")
            for param in func_def.parameters:
                lines.append(f"- `{param}`: Parameter description")
            lines.append("")

        return lines

    def _extract_doc_content(self, doc_blocks: List[DocBlock]) -> str:
        """Extract and clean content from doc blocks."""
        content_lines = []

        for doc_block in doc_blocks:
            content_lines.extend(doc_block.content)

        if not content_lines:
            return ""

        # Join lines and clean up
        content = " ".join(content_lines).strip()

        # Basic text enhancement (simple version without AI)
        content = self._enhance_text(content)

        return content

    def _enhance_text(self, text: str) -> str:
        """Enhance text formatting (simple version without AI)."""
        if not text:
            return text

        # Capitalize first letter
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()

        # Ensure it ends with a period
        if not text.endswith('.'):
            text += '.'

        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)

        return text
