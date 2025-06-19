"""
AI-powered documentation enhancer for PyTestEmbed.

Enhances existing docstrings and generates comprehensive documentation
using local AI models.
"""

import ast
import re
from typing import List, Dict, Optional, Any
from .ai_integration import get_ai_manager, AIProviderError


class AIDocumentationEnhancer:
    """Enhances documentation using AI for Python functions, methods, and classes."""
    
    def __init__(self, ai_provider: Optional[str] = None):
        self.ai_manager = get_ai_manager()
        self.ai_provider = ai_provider
    
    def enhance_documentation(self, item_info: Dict, item_type: str, class_info: Optional[Dict] = None, indent: str = "    ") -> List[str]:
        """Enhance documentation for a function, method, or class."""
        if not self.ai_manager.is_ai_available():
            return self._generate_fallback_documentation(item_info, item_type, indent)
        
        try:
            # Create prompt for AI
            prompt = self._create_documentation_prompt(item_info, item_type, class_info)
            
            # Generate documentation using AI with PyTestEmbed context
            ai_response = self.ai_manager.generate_contextualized_completion(
                prompt,
                task_type="doc_generation",
                provider=self.ai_provider,
                temperature=0.4,  # Moderate temperature for creative but accurate docs
                max_tokens=600
            )
            
            # Parse and format the AI response
            return self._parse_ai_documentation(ai_response, indent)
            
        except AIProviderError as e:
            print(f"AI documentation generation failed: {e}")
            return self._generate_fallback_documentation(item_info, item_type, indent)
    
    def _create_documentation_prompt(self, item_info: Dict, item_type: str, class_info: Optional[Dict] = None) -> str:
        """Create a prompt for AI documentation generation."""
        name = item_info['name']
        args = item_info.get('args', [])
        existing_docstring = item_info.get('docstring', '')
        
        # Get function/method source if available
        source_context = self._extract_source_context(item_info)
        
        prompt = f"""Generate comprehensive documentation for this Python {item_type}:

Name: {name}
Arguments: {', '.join(args)}
"""
        
        if existing_docstring:
            prompt += f"Existing documentation: {existing_docstring}\n"
        
        if class_info:
            prompt += f"Class: {class_info['name']}\n"
            if class_info.get('docstring'):
                prompt += f"Class documentation: {class_info['docstring']}\n"
        
        if source_context:
            prompt += f"Code context:\n{source_context}\n"
        
        prompt += f"""
Generate clear, comprehensive documentation for {name}. The documentation should:

1. Provide a clear, concise description of what the {item_type} does
2. Explain the purpose and behavior
3. Describe parameters and their types (if applicable)
4. Mention return value and type (if applicable)
5. Note any important side effects or exceptions
6. Be written in a professional, clear style
7. Be 1-3 sentences for simple functions, longer for complex ones

Requirements:
- Write in plain text, no markdown formatting
- Start with a clear action verb when possible
- Be specific about what the function accomplishes
- Keep it concise but informative
- Only return the documentation text, no other content

Generate documentation for {name}:"""
        
        return prompt
    
    def _extract_source_context(self, item_info: Dict) -> Optional[str]:
        """Extract relevant source code context for better documentation."""
        try:
            node = item_info.get('node')
            if node and isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # Analyze the function/class body for context
                context_info = []
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and hasattr(child, 'value'):
                        context_info.append("Returns a value")
                    elif isinstance(child, ast.Raise):
                        context_info.append("May raise exceptions")
                    elif isinstance(child, ast.If):
                        context_info.append("Contains conditional logic")
                    elif isinstance(child, (ast.For, ast.While)):
                        context_info.append("Contains loops")
                
                if context_info:
                    return "Code analysis: " + ", ".join(context_info)
        except:
            pass
        
        return None
    
    def _parse_ai_documentation(self, response: str, indent: str) -> List[str]:
        """Parse AI response and format as PyTestEmbed doc block."""
        lines = [f"{indent}doc:"]
        
        # Clean up the response
        response = response.strip()
        
        # Remove any markdown formatting
        response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)  # Remove bold
        response = re.sub(r'\*(.*?)\*', r'\1', response)      # Remove italic
        response = re.sub(r'`(.*?)`', r'\1', response)        # Remove code blocks
        
        # Split into sentences and format
        sentences = self._split_into_sentences(response)
        
        current_line = ""
        max_line_length = 80
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would make the line too long, start a new line
            if current_line and len(current_line + " " + sentence) > max_line_length:
                lines.append(f"{indent}    {current_line}")
                current_line = sentence
            else:
                if current_line:
                    current_line += " " + sentence
                else:
                    current_line = sentence
        
        # Add the last line if there's content
        if current_line:
            lines.append(f"{indent}    {current_line}")
        
        # If no content was generated, add a placeholder
        if len(lines) == 1:
            lines.append(f"{indent}    {item_info['name']} - Add description here")
        
        return lines
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for better formatting."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _generate_fallback_documentation(self, item_info: Dict, item_type: str, indent: str) -> List[str]:
        """Generate fallback documentation when AI is not available."""
        name = item_info['name']
        existing_docstring = item_info.get('docstring', '')
        
        lines = [f"{indent}doc:"]
        
        if existing_docstring:
            # Use existing docstring, cleaned up
            for line in existing_docstring.split('\n'):
                line = line.strip()
                if line:
                    lines.append(f"{indent}    {line}")
        else:
            # Generate basic documentation
            if item_type == 'class':
                lines.append(f"{indent}    {name} class - Add description here")
            elif item_type == 'method':
                lines.append(f"{indent}    {name} method - Add description here")
            else:
                lines.append(f"{indent}    {name} function - Add description here")
        
        return lines


class SmartDocumentationEnhancer:
    """Enhanced documentation generator with code analysis."""
    
    def __init__(self, ai_provider: Optional[str] = None):
        self.ai_enhancer = AIDocumentationEnhancer(ai_provider)
    
    def generate_comprehensive_documentation(self, item_info: Dict, item_type: str, class_info: Optional[Dict] = None, indent: str = "    ") -> List[str]:
        """Generate comprehensive documentation with static analysis + AI."""
        
        # Analyze the code for better documentation context
        analysis = self._analyze_code_structure(item_info, item_type)
        
        # Generate enhanced documentation
        return self._generate_enhanced_documentation(item_info, analysis, item_type, class_info, indent)
    
    def _analyze_code_structure(self, item_info: Dict, item_type: str) -> Dict:
        """Analyze code structure for better documentation."""
        analysis = {
            'complexity': 'simple',
            'has_parameters': False,
            'has_return': False,
            'has_exceptions': False,
            'has_side_effects': False,
            'parameter_count': 0,
            'key_operations': []
        }
        
        try:
            args = item_info.get('args', [])
            analysis['parameter_count'] = len(args)
            analysis['has_parameters'] = len(args) > 0
            
            node = item_info.get('node')
            if node and isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # Analyze AST for patterns
                operations = []
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        analysis['has_return'] = True
                    elif isinstance(child, ast.Raise):
                        analysis['has_exceptions'] = True
                    elif isinstance(child, (ast.Assign, ast.AugAssign)):
                        analysis['has_side_effects'] = True
                    elif isinstance(child, ast.Call):
                        if hasattr(child.func, 'id'):
                            operations.append(child.func.id)
                        elif hasattr(child.func, 'attr'):
                            operations.append(child.func.attr)
                
                analysis['key_operations'] = list(set(operations))
                
                # Determine complexity
                node_count = len(list(ast.walk(node)))
                if node_count > 20:
                    analysis['complexity'] = 'complex'
                elif node_count > 10:
                    analysis['complexity'] = 'moderate'
        
        except Exception:
            pass
        
        return analysis
    
    def _generate_enhanced_documentation(self, item_info: Dict, analysis: Dict, item_type: str, class_info: Optional[Dict], indent: str) -> List[str]:
        """Generate enhanced documentation with analysis context."""
        
        # Create enhanced prompt
        prompt = self._create_enhanced_documentation_prompt(item_info, analysis, item_type, class_info)
        
        try:
            ai_response = self.ai_enhancer.ai_manager.generate_contextualized_completion(
                prompt,
                task_type="doc_generation",
                provider=self.ai_enhancer.ai_provider,
                temperature=0.3,  # Lower temperature for more consistent docs
                max_tokens=800
            )
            
            return self.ai_enhancer._parse_ai_documentation(ai_response, indent)
            
        except AIProviderError:
            return self.ai_enhancer._generate_fallback_documentation(item_info, item_type, indent)
    
    def _create_enhanced_documentation_prompt(self, item_info: Dict, analysis: Dict, item_type: str, class_info: Optional[Dict]) -> str:
        """Create enhanced documentation prompt with analysis context."""
        
        base_prompt = self.ai_enhancer._create_documentation_prompt(item_info, item_type, class_info)
        
        # Add analysis context
        enhancement = "\nCode Analysis:\n"
        
        if analysis['complexity'] == 'complex':
            enhancement += "- This is a complex function requiring detailed documentation\n"
        elif analysis['complexity'] == 'moderate':
            enhancement += "- This is a moderately complex function\n"
        
        if analysis['has_parameters']:
            enhancement += f"- Has {analysis['parameter_count']} parameter(s) - describe each one\n"
        
        if analysis['has_return']:
            enhancement += "- Returns a value - describe what it returns\n"
        
        if analysis['has_exceptions']:
            enhancement += "- May raise exceptions - mention potential error conditions\n"
        
        if analysis['has_side_effects']:
            enhancement += "- Has side effects - mention what it modifies\n"
        
        if analysis['key_operations']:
            enhancement += f"- Key operations: {', '.join(analysis['key_operations'][:3])}\n"
        
        enhancement += "\nGenerate documentation that addresses these aspects appropriately.\n"
        
        return base_prompt + enhancement
