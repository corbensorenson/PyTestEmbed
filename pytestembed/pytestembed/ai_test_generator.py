"""
AI-powered test generator for PyTestEmbed.

Generates test cases for Python functions and methods using local AI models.
"""

import ast
import inspect
from typing import List, Dict, Optional, Any
from .ai_integration import get_ai_manager, AIProviderError


class AITestGenerator:
    """Generates test cases using AI for Python functions and methods."""
    
    def __init__(self, ai_provider: Optional[str] = None):
        self.ai_manager = get_ai_manager()
        self.ai_provider = ai_provider
    
    def generate_tests(self, function_info: Dict, item_type: str, class_info: Optional[Dict] = None, indent: str = "    ") -> List[str]:
        """Generate test cases for a function or method."""
        if not self.ai_manager.is_ai_available():
            return self._generate_fallback_tests(function_info, indent)
        
        try:
            # Create prompt for AI
            prompt = self._create_test_prompt(function_info, item_type, class_info)
            
            # Generate tests using AI with PyTestEmbed context
            ai_response = self.ai_manager.generate_contextualized_completion(
                prompt,
                task_type="test_generation",
                provider=self.ai_provider,
                temperature=0.3,  # Lower temperature for more consistent code generation
                max_tokens=500
            )
            
            # Parse and format the AI response
            return self._parse_ai_response(ai_response, indent)
            
        except AIProviderError as e:
            print(f"AI test generation failed: {e}")
            return self._generate_fallback_tests(function_info, indent)
    
    def _create_test_prompt(self, function_info: Dict, item_type: str, class_info: Optional[Dict] = None) -> str:
        """Create a prompt for AI test generation."""
        function_name = function_info['name']
        args = function_info.get('args', [])
        docstring = function_info.get('docstring', '')
        
        # Get function source if available
        function_source = self._extract_function_source(function_info)
        
        prompt = f"""Generate test cases for this Python {item_type}:

Function: {function_name}
Arguments: {', '.join(args)}
"""
        
        if docstring:
            prompt += f"Documentation: {docstring}\n"
        
        if function_source:
            prompt += f"Source code:\n{function_source}\n"
        
        if class_info:
            prompt += f"Class: {class_info['name']}\n"
        
        prompt += f"""
Generate test cases in PyTestEmbed format. PyTestEmbed supports advanced testing patterns:

BASIC SYNTAX:
function_call == expected_result: "error_message",

MULTI-STATEMENT TESTS (for complex setup):
variable = function_call(args)
variable == expected: "test description",

EXCEPTION TESTING:
try:
    function_call(bad_args)
    False: "Should have raised exception"
except ExpectedError:
    True: "Correctly raised exception",

CLASS-LEVEL TESTS (when testing methods):
# Setup variables, then test
result1 = method1(args)
result2 = method2(args)
result1 + result2 == expected: "integration test",

Requirements:
1. Generate 3-7 meaningful test cases using appropriate syntax
2. Use multi-statement tests for complex scenarios
3. Include exception testing for error conditions
4. Test edge cases (empty inputs, None, zero, negative numbers)
5. Use realistic test data and descriptive error messages
6. Each test case should end with a comma
7. Only return the test content, no other text

Examples:
# Basic tests
add(2, 3) == 5: "Basic addition failed",
add(0, 0) == 0: "Addition with zeros failed",

# Multi-statement test
result = add(2, 3)
result * 2 == 10: "Addition and multiplication failed",

# Exception test
try:
    divide(1, 0)
    False: "Should have raised ZeroDivisionError"
except ZeroDivisionError:
    True: "Correctly handled division by zero",

Generate tests for {function_name}:"""
        
        return prompt
    
    def _extract_function_source(self, function_info: Dict) -> Optional[str]:
        """Extract source code for the function if available."""
        try:
            node = function_info.get('node')
            if node and isinstance(node, ast.FunctionDef):
                # This is a simplified source extraction
                # In a real implementation, you'd want to reconstruct the source
                return f"def {node.name}({', '.join(arg.arg for arg in node.args.args)}):"
        except:
            pass
        return None
    
    def _parse_ai_response(self, response: str, indent: str) -> List[str]:
        """Parse AI response and format as PyTestEmbed test block."""
        lines = [f"{indent}test:"]

        # Clean up the response
        response = response.strip()

        # Split into lines and process each one
        response_lines = response.split('\n')
        i = 0

        while i < len(response_lines):
            line = response_lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith('#') or line.startswith('//'):
                i += 1
                continue

            # Check if this is a multi-statement test (no == on this line, but next lines might have it)
            if ('==' not in line and ':' not in line and
                (line.endswith('=') or '=' in line or 'try:' in line or
                 any(keyword in line for keyword in ['result', 'value', 'output', 'temp']))):

                # This might be the start of a multi-statement test
                test_block = [line]
                i += 1

                # Collect related lines until we find the assertion
                while i < len(response_lines):
                    next_line = response_lines[i].strip()
                    if not next_line:
                        i += 1
                        continue

                    test_block.append(next_line)

                    # If we found an assertion line, we're done with this test
                    if '==' in next_line and ':' in next_line:
                        break

                    # If we hit another test or end, break
                    if (next_line.startswith('#') or
                        (len(test_block) > 1 and '==' not in next_line and ':' not in next_line and
                         any(keyword in next_line for keyword in ['result', 'value', 'output', 'temp']))):
                        i -= 1  # Back up one line
                        break

                    i += 1

                # Add the multi-statement test block
                for test_line in test_block:
                    if test_line.strip():
                        # Ensure assertion lines end with comma
                        if '==' in test_line and ':' in test_line and not test_line.endswith(','):
                            test_line += ','
                        lines.append(f"{indent}    {test_line}")

                # Add blank line after multi-statement test
                if len(test_block) > 1:
                    lines.append("")

            # Single-line test case
            elif '==' in line and ':' in line:
                # Ensure line ends with comma
                if not line.endswith(','):
                    line += ','

                # Add proper indentation
                lines.append(f"{indent}    {line}")

            # Other lines (like try/except blocks)
            elif any(keyword in line for keyword in ['try:', 'except', 'False:', 'True:']):
                # Ensure assertion lines end with comma
                if ('True:' in line or 'False:' in line) and not line.endswith(','):
                    line += ','
                lines.append(f"{indent}    {line}")

            i += 1

        # If no valid test lines were found, add a placeholder
        if len(lines) == 1:
            lines.append(f"{indent}    True == True: \"AI generation placeholder\",")

        return lines
    
    def _generate_fallback_tests(self, function_info: Dict, indent: str) -> List[str]:
        """Generate fallback tests when AI is not available."""
        function_name = function_info['name']
        args = function_info.get('args', [])
        
        lines = [f"{indent}test:"]
        
        if args:
            # Generate basic test based on argument count
            if len(args) == 1:
                lines.append(f"{indent}    {function_name}(None) is not None: \"Basic test failed\",")
            elif len(args) == 2:
                lines.append(f"{indent}    {function_name}(1, 2) is not None: \"Basic test failed\",")
            else:
                arg_list = ', '.join(['None'] * len(args))
                lines.append(f"{indent}    {function_name}({arg_list}) is not None: \"Basic test failed\",")
        else:
            lines.append(f"{indent}    {function_name}() is not None: \"Basic test failed\",")
        
        return lines


class SmartTestGenerator:
    """Enhanced test generator with code analysis."""
    
    def __init__(self, ai_provider: Optional[str] = None):
        self.ai_generator = AITestGenerator(ai_provider)
    
    def generate_comprehensive_tests(self, function_info: Dict, item_type: str, class_info: Optional[Dict] = None, indent: str = "    ") -> List[str]:
        """Generate comprehensive tests with static analysis + AI."""
        
        # Analyze function signature and body for better test generation
        analysis = self._analyze_function(function_info)
        
        # Generate AI tests with enhanced context
        return self._generate_enhanced_ai_tests(function_info, analysis, item_type, class_info, indent)
    
    def _analyze_function(self, function_info: Dict) -> Dict:
        """Analyze function for better test generation."""
        analysis = {
            'return_type_hints': [],
            'parameter_types': [],
            'has_conditionals': False,
            'has_loops': False,
            'raises_exceptions': False,
            'complexity_score': 1
        }
        
        try:
            node = function_info.get('node')
            if node and isinstance(node, ast.FunctionDef):
                # Analyze the AST for patterns
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.IfExp)):
                        analysis['has_conditionals'] = True
                    elif isinstance(child, (ast.For, ast.While)):
                        analysis['has_loops'] = True
                    elif isinstance(child, ast.Raise):
                        analysis['raises_exceptions'] = True
                
                # Calculate complexity score
                analysis['complexity_score'] = len(list(ast.walk(node))) // 10 + 1
        
        except Exception:
            pass
        
        return analysis
    
    def _generate_enhanced_ai_tests(self, function_info: Dict, analysis: Dict, item_type: str, class_info: Optional[Dict], indent: str) -> List[str]:
        """Generate enhanced AI tests with analysis context."""
        
        # Create enhanced prompt with analysis
        prompt = self._create_enhanced_prompt(function_info, analysis, item_type, class_info)
        
        try:
            ai_response = self.ai_generator.ai_manager.generate_contextualized_completion(
                prompt,
                task_type="test_generation",
                provider=self.ai_generator.ai_provider,
                temperature=0.2,  # Even lower temperature for better code
                max_tokens=800    # More tokens for comprehensive tests
            )
            
            return self.ai_generator._parse_ai_response(ai_response, indent)
            
        except AIProviderError:
            return self.ai_generator._generate_fallback_tests(function_info, indent)
    
    def _create_enhanced_prompt(self, function_info: Dict, analysis: Dict, item_type: str, class_info: Optional[Dict]) -> str:
        """Create enhanced prompt with static analysis context."""
        
        base_prompt = self.ai_generator._create_test_prompt(function_info, item_type, class_info)
        
        # Add analysis context
        enhancement = "\nCode Analysis:\n"
        
        if analysis['has_conditionals']:
            enhancement += "- Function contains conditional logic - test different branches\n"
        
        if analysis['has_loops']:
            enhancement += "- Function contains loops - test with different collection sizes\n"
        
        if analysis['raises_exceptions']:
            enhancement += "- Function may raise exceptions - test error conditions\n"
        
        if analysis['complexity_score'] > 3:
            enhancement += "- Function is complex - generate more comprehensive tests\n"
        
        enhancement += f"\nGenerate {min(analysis['complexity_score'] + 2, 7)} test cases covering:\n"
        enhancement += "1. Normal operation with typical inputs\n"
        enhancement += "2. Edge cases (empty, None, zero, negative)\n"
        enhancement += "3. Boundary conditions\n"
        
        if analysis['has_conditionals']:
            enhancement += "4. Different conditional branches\n"
        
        if analysis['raises_exceptions']:
            enhancement += "5. Exception scenarios\n"
        
        return base_prompt + enhancement
