"""
Smart AI Code Generation for PyTestEmbed

Provides intelligent test and documentation generation with context-aware AI analysis.
Supports right-click context menu integration and real-time code analysis.
"""

import pytestembed  # Enable import hooks for proper test:/doc: block handling
import ast
import inspect
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from .ai_integration import get_ai_manager


@dataclass
class CodeContext:
    """Represents the context around a piece of code for AI analysis."""
    function_name: str
    class_name: Optional[str]
    parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    source_code: str
    imports: List[str]
    surrounding_functions: List[str]
    complexity_score: int
    line_number: int
    file_path: str


@dataclass
class GenerationRequest:
    """Request for AI code generation."""
    context: CodeContext
    generation_type: str  # 'test', 'doc', 'both'
    style_preferences: Dict[str, Any]
    existing_tests: List[str]
    existing_docs: List[str]


class SmartCodeAnalyzer:
    """Analyzes code to provide rich context for AI generation."""
    
    def __init__(self):
        self.complexity_weights = {
            'loops': 2,
            'conditionals': 1,
            'function_calls': 1,
            'nested_functions': 3,
            'exception_handling': 2,
            'recursion': 4
        }
    
    def analyze_function(self, source_code: str, line_number: int, file_path: str) -> Optional[CodeContext]:
        """Analyze a function and return rich context."""
        try:
            # Preprocess the source code to remove PyTestEmbed blocks for AST parsing
            clean_source = self._remove_pytestembed_blocks(source_code)

            # Try to parse the cleaned file first
            try:
                tree = ast.parse(clean_source)
            except SyntaxError:
                # If full file parsing fails, try to extract just the function
                function_source = self._extract_function_source(source_code, line_number)
                if function_source:
                    clean_function = self._remove_pytestembed_blocks(function_source)
                    tree = ast.parse(clean_function)
                else:
                    return None

            # Find the function at the specified line
            target_function = self._find_function_at_line(tree, line_number)
            if not target_function:
                # Try to find any function in the parsed code
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        target_function = node
                        break

                if not target_function:
                    return None

            # Extract context
            context = self._extract_function_context(target_function, tree, source_code, file_path)
            context.line_number = line_number

            return context

        except Exception as e:
            print(f"Error analyzing function: {e}")
            return None

    def _remove_pytestembed_blocks(self, source_code: str) -> str:
        """Remove PyTestEmbed test: and doc: blocks to make code parseable by AST."""
        lines = source_code.split('\n')
        clean_lines = []
        in_block = False
        block_indent = 0

        for line in lines:
            stripped = line.strip()

            # Check if this is a test: or doc: block start
            if stripped == 'test:' or stripped == 'doc:':
                in_block = True
                block_indent = len(line) - len(line.lstrip())
                # Replace with a comment to maintain line numbers
                clean_lines.append(line.replace(stripped, f'# {stripped}'))
                continue

            if in_block:
                current_indent = len(line) - len(line.lstrip()) if line.strip() else block_indent + 1

                # If we're still in the block (indented more than block start)
                if line.strip() == '' or current_indent > block_indent:
                    # Comment out the line to maintain line numbers
                    if line.strip():
                        clean_lines.append('    # ' + line.strip())
                    else:
                        clean_lines.append('')
                else:
                    # We've exited the block
                    in_block = False
                    clean_lines.append(line)
            else:
                clean_lines.append(line)

        return '\n'.join(clean_lines)

    def _extract_function_source(self, source_code: str, line_number: int) -> Optional[str]:
        """Extract just the function source code around the specified line."""
        lines = source_code.split('\n')
        if line_number > len(lines):
            return None

        # Find the start of the function - look backwards from the line
        start_line = line_number - 1
        while start_line >= 0:
            line = lines[start_line].strip()
            if line.startswith('def '):
                break
            start_line -= 1

        if start_line < 0:
            return None

        # Find the end of the function by looking for next function/class or dedent
        end_line = start_line + 1
        base_indent = len(lines[start_line]) - len(lines[start_line].lstrip())

        while end_line < len(lines):
            line = lines[end_line]
            if line.strip():  # Non-empty line
                current_indent = len(line) - len(line.lstrip())
                # Stop if we hit something at same or lower indentation that's not a comment
                if (current_indent <= base_indent and
                    not line.strip().startswith('#') and
                    not line.strip().startswith('test:') and
                    not line.strip().startswith('doc:')):
                    break
            end_line += 1

        # Extract the function and normalize indentation for AST parsing
        function_lines = lines[start_line:end_line]
        if not function_lines:
            return None

        # Calculate the minimum indentation to remove
        min_indent = float('inf')
        for line in function_lines:
            if line.strip():  # Non-empty line
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)

        # Remove the minimum indentation from all lines
        if min_indent != float('inf') and min_indent > 0:
            normalized_lines = []
            for line in function_lines:
                if line.strip():  # Non-empty line
                    normalized_lines.append(line[min_indent:])
                else:
                    normalized_lines.append('')  # Keep empty lines
            return '\n'.join(normalized_lines)

        return '\n'.join(function_lines)
    
    def _find_function_at_line(self, tree: ast.AST, line_number: int) -> Optional[ast.FunctionDef]:
        """Find the function definition at the specified line."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'lineno') and node.lineno <= line_number:
                    # Check if line is within function bounds
                    end_line = getattr(node, 'end_lineno', node.lineno + 10)
                    if line_number <= end_line:
                        return node
        return None
    
    def _extract_function_context(self, func_node: ast.FunctionDef, tree: ast.AST, 
                                source_code: str, file_path: str) -> CodeContext:
        """Extract comprehensive context from a function."""
        
        # Basic function info
        function_name = func_node.name
        parameters = [arg.arg for arg in func_node.args.args]
        docstring = ast.get_docstring(func_node)
        
        # Return type annotation
        return_type = None
        if func_node.returns:
            return_type = ast.unparse(func_node.returns) if hasattr(ast, 'unparse') else str(func_node.returns)
        
        # Class context
        class_name = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if func_node in ast.walk(node):
                    class_name = node.name
                    break
        
        # Extract imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                imports.extend([f"{module}.{alias.name}" for alias in node.names])
        
        # Find surrounding functions
        surrounding_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node != func_node:
                surrounding_functions.append(node.name)
        
        # Calculate complexity
        complexity_score = self._calculate_complexity(func_node)
        
        # Get source code for the function
        source_lines = source_code.split('\n')
        start_line = func_node.lineno - 1
        end_line = getattr(func_node, 'end_lineno', start_line + 10)
        function_source = '\n'.join(source_lines[start_line:end_line])
        
        return CodeContext(
            function_name=function_name,
            class_name=class_name,
            parameters=parameters,
            return_type=return_type,
            docstring=docstring,
            source_code=function_source,
            imports=imports,
            surrounding_functions=surrounding_functions,
            complexity_score=complexity_score,
            line_number=func_node.lineno,
            file_path=file_path
        )
    
    def _calculate_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate complexity score for a function."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While)):
                complexity += self.complexity_weights['loops']
            elif isinstance(node, (ast.If, ast.IfExp)):
                complexity += self.complexity_weights['conditionals']
            elif isinstance(node, ast.Call):
                complexity += self.complexity_weights['function_calls']
            elif isinstance(node, ast.FunctionDef) and node != func_node:
                complexity += self.complexity_weights['nested_functions']
            elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                complexity += self.complexity_weights['exception_handling']
            elif isinstance(node, ast.Call) and hasattr(node.func, 'id'):
                if node.func.id == func_node.name:  # Recursion
                    complexity += self.complexity_weights['recursion']
        
        return complexity


class SmartCodeGenerator:
    """Generates intelligent test and documentation code using AI."""
    
    def __init__(self, ai_provider: Optional[str] = None):
        self.ai_manager = get_ai_manager()
        self.ai_provider = ai_provider
        if ai_provider:
            self.ai_manager.set_active_provider(ai_provider)
        self.analyzer = SmartCodeAnalyzer()
        from .config_manager import get_config_manager
        self.config_manager = get_config_manager()
    
    def generate_for_function(self, source_code: str, line_number: int, 
                            file_path: str, generation_type: str = 'both') -> Dict[str, str]:
        """Generate tests and/or documentation for a function."""
        
        # Analyze the function
        context = self.analyzer.analyze_function(source_code, line_number, file_path)
        if not context:
            return {'error': 'Could not analyze function at specified line'}
        
        # Create generation request
        request = GenerationRequest(
            context=context,
            generation_type=generation_type,
            style_preferences=self._get_style_preferences(),
            existing_tests=[],
            existing_docs=[]
        )
        
        # Generate content
        result = {}

        if generation_type == 'both':
            # Use single AI call for both test and doc
            combined_result = self._generate_both(request)
            result.update(combined_result)
        else:
            # Use separate calls for individual generation
            if generation_type == 'test':
                test_content = self._generate_tests(request)
                result['test'] = test_content

            if generation_type == 'doc':
                doc_content = self._generate_documentation(request)
                result['doc'] = doc_content

        return result

    def _generate_both(self, request: GenerationRequest) -> Dict[str, str]:
        """Generate both test and documentation using a single AI call."""
        context = request.context

        # Create AI prompt for combined generation
        prompt = self._create_combined_prompt(context)

        if self.ai_manager.is_ai_available():
            try:
                # Use structured output for LMStudio
                ai_response = self.ai_manager.generate_completion(
                    prompt,
                    provider=self.ai_provider,
                    response_format=self._get_combined_schema(),
                    max_tokens=500
                )
                return self._format_combined_response(ai_response, context)
            except Exception as e:
                print(f"AI combined generation failed: {e}")

        # Fallback to template-based generation
        return {
            'test': self._generate_template_tests(context),
            'doc': self._generate_template_documentation(context)
        }

    def _generate_tests(self, request: GenerationRequest) -> str:
        """Generate test cases using AI."""
        context = request.context
        
        # Create AI prompt for test generation
        prompt = self._create_test_prompt(context)
        
        if self.ai_manager.is_ai_available():
            try:
                # Use structured output for LMStudio
                ai_response = self.ai_manager.generate_completion(
                    prompt,
                    provider=self.ai_provider,
                    response_format=self._get_test_schema(),
                    max_tokens=300
                )
                return self._format_structured_test_response(ai_response, context)
            except Exception as e:
                print(f"AI test generation failed: {e}")
        
        # Fallback to template-based generation
        return self._generate_template_tests(context)
    
    def _generate_documentation(self, request: GenerationRequest) -> str:
        """Generate documentation using AI."""
        context = request.context
        
        # Create AI prompt for documentation
        prompt = self._create_doc_prompt(context)
        
        if self.ai_manager.is_ai_available():
            try:
                # Use structured output for LMStudio
                ai_response = self.ai_manager.generate_completion(
                    prompt,
                    provider=self.ai_provider,
                    response_format=self._get_doc_schema(),
                    max_tokens=200
                )
                return self._format_structured_doc_response(ai_response, context)
            except Exception as e:
                print(f"AI documentation generation failed: {e}")
        
        # Fallback to template-based generation
        return self._generate_template_documentation(context)
    
    def _create_test_prompt(self, context: CodeContext) -> str:
        """Create AI prompt for test generation."""
        prompt = f"""You are an expert at writing PyTestEmbed test cases. PyTestEmbed requires a VERY SPECIFIC syntax format.

# CRITICAL: PyTestEmbed Syntax Requirements

## WRONG FORMAT (DO NOT USE):
```
test:
    function_call: "description"  ❌ MISSING COMPARISON AND EXPECTED RESULT
    assert function_call == value: "description"  ❌ NO ASSERT STATEMENTS
```

## CORRECT FORMAT (ALWAYS USE):
```
test:
    function_call == expected_result: "description",  ✅ INCLUDES COMPARISON AND EXPECTED RESULT
    function_call != unwanted_value: "description"   ✅ INCLUDES COMPARISON AND EXPECTED RESULT
```

## MANDATORY RULES:
1. **ALWAYS include comparison operator**: ==, !=, >, <, >=, <=
2. **ALWAYS include expected result**: Calculate what the function should return
3. **NEVER use just function_call**: Must be function_call OPERATOR expected_result
4. **NO assert statements**: PyTestEmbed uses direct comparisons only

## REQUIRED FORMAT EXAMPLES:

### Multiplication Function:
```python
def multiply_by_three(x):
    return x * 3
test:
    multiply_by_three(2) == 6: "2 times 3 equals 6",
    multiply_by_three(0) == 0: "0 times 3 equals 0",
    multiply_by_three(-1) == -3: "-1 times 3 equals -3"
```

### Addition Function:
```python
def add_numbers(a, b):
    return a + b
test:
    add_numbers(2, 3) == 5: "2 plus 3 equals 5",
    add_numbers(0, 0) == 0: "0 plus 0 equals 0",
    add_numbers(-1, 1) == 0: "-1 plus 1 equals 0"
```

### Boolean Function:
```python
def is_even(x):
    return x % 2 == 0
test:
    is_even(4) == True: "4 is even",
    is_even(3) == False: "3 is odd",
    is_even(0) == True: "0 is even"
```

### String Function:
```python
def get_greeting(name):
    return f"Hello, {{name}}!"
test:
    get_greeting("Alice") == "Hello, Alice!": "Greeting for Alice",
    get_greeting("") == "Hello, !": "Greeting for empty name",
    len(get_greeting("Bob")) == 11: "Greeting length check"
```

# YOUR TASK:
Generate PyTestEmbed test cases for this function:

```python
{context.source_code}
```

REQUIREMENTS:
1. **CALCULATE expected results**: Look at the function and determine what it should return
2. **USE comparison operators**: Every test must have == or !=, etc.
3. **INCLUDE expected values**: Never just function_call, always function_call == expected_result
4. **FOLLOW exact format**: Like the examples above
5. **Generate 2-4 test cases**: Cover normal and edge cases

REMEMBER: function_call == expected_result: "description" (NOT just function_call: "description")"""

        # Add /no_think if enabled in config
        config = self.config_manager.get_ai_provider_config()
        if config.no_think:
            prompt += " /no_think"

        return prompt

    def _create_combined_prompt(self, context: CodeContext) -> str:
        """Create AI prompt for generating both test and doc blocks together."""
        prompt = f"""You are an expert at writing PyTestEmbed test cases and documentation. Generate BOTH test and doc blocks for this function.

# CRITICAL: PyTestEmbed Syntax Requirements

## Test Block Format (MANDATORY):
```
test:
    function_call == expected_result: "description",
    function_call != unwanted_value: "description"
```

## Doc Block Format (MANDATORY):
```
doc:
    Brief description of what the function does

    Parameters: parameter descriptions with types
    Returns: return value description
```

## WRONG TEST FORMAT (DO NOT USE):
```
test:
    function_call: "description"  ❌ MISSING COMPARISON AND EXPECTED RESULT
```

## CORRECT TEST FORMAT (ALWAYS USE):
```
test:
    function_call == expected_result: "description",  ✅ INCLUDES COMPARISON AND EXPECTED RESULT
```

## EXAMPLES:

### Multiplication Function:
```python
def multiply_by_three(x):
    return x * 3
test:
    multiply_by_three(2) == 6: "2 times 3 equals 6",
    multiply_by_three(0) == 0: "0 times 3 equals 0",
    multiply_by_three(-1) == -3: "-1 times 3 equals -3"
doc:
    Multiplies the input value by 3

    Parameters: x (int/float) - number to multiply
    Returns: x multiplied by 3 (int/float)
```

### Boolean Function:
```python
def is_even(x):
    return x % 2 == 0
test:
    is_even(4) == True: "4 is even",
    is_even(3) == False: "3 is odd",
    is_even(0) == True: "0 is even"
doc:
    Checks if a number is even

    Parameters: x (int) - number to check
    Returns: True if even, False if odd (bool)
```

# YOUR TASK:
Generate BOTH test and doc blocks for this function:

```python
{context.source_code}
```

REQUIREMENTS:
1. **TEST BLOCK**: Calculate expected results, use comparison operators (==, !=, etc.)
2. **DOC BLOCK**: Clear description, parameter types, return value
3. **BOTH BLOCKS**: Generate complete test and doc blocks in one response
4. **PROPER FORMAT**: Follow exact syntax shown in examples"""

        # Add /no_think if enabled in config
        config = self.config_manager.get_ai_provider_config()
        if config.no_think:
            prompt += " /no_think"

        return prompt

    def _get_test_schema(self) -> dict:
        """Get JSON schema for structured test output."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "pytestembed_test",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "test_cases": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "expression": {
                                        "type": "string",
                                        "description": "MUST be complete PyTestEmbed expression: function_call OPERATOR expected_result. Examples: 'multiply(3, 4) == 12', 'is_even(3) == False', 'get_name() != None'. NEVER just 'function_call' without comparison."
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Brief description of what this test case verifies"
                                    }
                                },
                                "required": ["expression", "description"]
                            },
                            "minItems": 2,
                            "maxItems": 4
                        }
                    },
                    "required": ["test_cases"],
                    "additionalProperties": False
                }
            }
        }

    def _get_combined_schema(self) -> dict:
        """Get JSON schema for structured combined test and doc output."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "pytestembed_combined",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "test_cases": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "expression": {
                                        "type": "string",
                                        "description": "MUST be complete PyTestEmbed expression: function_call OPERATOR expected_result. Examples: 'multiply(3, 4) == 12', 'is_even(3) == False'"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Brief description of what this test case verifies"
                                    }
                                },
                                "required": ["expression", "description"]
                            },
                            "minItems": 2,
                            "maxItems": 4
                        },
                        "documentation": {
                            "type": "object",
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "description": "Brief, clear description of what the function does"
                                },
                                "parameters": {
                                    "type": "string",
                                    "description": "Description of parameters with types, e.g., 'x (int) - first number, y (int) - second number'"
                                },
                                "returns": {
                                    "type": "string",
                                    "description": "Description of return value with type, e.g., 'sum as int'"
                                }
                            },
                            "required": ["description", "parameters", "returns"],
                            "additionalProperties": False
                        }
                    },
                    "required": ["test_cases", "documentation"],
                    "additionalProperties": False
                }
            }
        }

    def _create_doc_prompt(self, context: CodeContext) -> str:
        """Create AI prompt for documentation generation."""
        prompt = f"""You are an expert at writing PyTestEmbed documentation. PyTestEmbed uses embedded doc blocks with a specific format.

# PyTestEmbed Documentation Syntax Guide

## Doc Block Format:
```
doc:
    Brief description of what the function does

    Parameters: parameter descriptions
    Returns: return value description
    Raises: exception descriptions (if applicable)
```

## Key Rules:
1. **Start with brief description**: One clear sentence about function purpose
2. **Parameters section**: Describe each parameter with type and purpose
3. **Returns section**: Describe return value type and meaning
4. **Proper indentation**: 4 spaces for doc content
5. **Clear and concise**: Focus on essential information

## Documentation Examples:

### Simple Function:
```python
def add(x, y):
    return x + y
doc:
    Adds two numbers together

    Parameters: x (int/float), y (int/float) - numbers to add
    Returns: sum of x and y (int/float)
```

### Function with Edge Cases:
```python
def divide(x, y):
    if y == 0:
        return None
    return x / y
doc:
    Divides x by y with zero-division protection

    Parameters: x (int/float) - dividend, y (int/float) - divisor
    Returns: x/y as float, or None if y is zero
```

### Function with Multiple Parameters:
```python
def calculate_discount(price, discount_percent):
    return price * (1 - discount_percent / 100)
doc:
    Calculates the discounted price

    Parameters: price (float) - original price, discount_percent (float) - discount percentage
    Returns: discounted price as float
```

### Class Method:
```python
def calculate_area(self):
    return self.width * self.height
doc:
    Calculates the area of the rectangle

    Returns: area as int/float (width × height)
```

# Your Task:
Generate PyTestEmbed documentation for this function:

```python
{context.source_code}
```

Requirements:
- Write clear, concise description
- Document all parameters with types
- Describe return value
- Follow the exact format shown in examples above
- Use proper PyTestEmbed doc syntax"""

        # Add /no_think if enabled in config
        config = self.config_manager.get_ai_provider_config()
        if config.no_think:
            prompt += " /no_think"

        return prompt

    def _get_doc_schema(self) -> dict:
        """Get JSON schema for structured doc output."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "pytestembed_doc",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Brief, clear description of what the function does"
                        },
                        "parameters": {
                            "type": "string",
                            "description": "Description of parameters with types, e.g., 'x (int) - first number, y (int) - second number'"
                        },
                        "returns": {
                            "type": "string",
                            "description": "Description of return value with type, e.g., 'sum as int'"
                        }
                    },
                    "required": ["description", "parameters", "returns"],
                    "additionalProperties": False
                }
            }
        }

    def _format_structured_test_response(self, ai_response: str, context: CodeContext) -> str:
        """Format structured JSON response into PyTestEmbed test syntax."""
        try:
            import json
            data = json.loads(ai_response)
            test_cases = data.get("test_cases", [])

            if not test_cases:
                return self._generate_template_tests(context)

            lines = ["test:"]
            for i, test_case in enumerate(test_cases):
                expression = test_case.get("expression", "").strip()
                description = test_case.get("description", "").strip()

                # Format as PyTestEmbed syntax
                if expression and description:
                    # Add comma except for last item
                    comma = "," if i < len(test_cases) - 1 else ""
                    lines.append(f'    {expression}: "{description}"{comma}')

            return '\n'.join(lines)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse structured test response: {e}")
            return self._generate_template_tests(context)

    def _format_structured_doc_response(self, ai_response: str, context: CodeContext) -> str:
        """Format structured JSON response into PyTestEmbed doc syntax."""
        try:
            import json
            data = json.loads(ai_response)

            description = data.get("description", "").strip()
            parameters = data.get("parameters", "").strip()
            returns = data.get("returns", "").strip()

            if not description:
                return self._generate_template_documentation(context)

            lines = ["doc:"]
            lines.append(f"    {description}")

            if parameters and parameters.lower() != "none":
                lines.append("")
                lines.append(f"    Parameters: {parameters}")

            if returns and returns.lower() != "none":
                lines.append(f"    Returns: {returns}")

            return '\n'.join(lines)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse structured doc response: {e}")
            return self._generate_template_documentation(context)

    def _format_combined_response(self, ai_response: str, context: CodeContext) -> Dict[str, str]:
        """Format structured JSON response into both PyTestEmbed test and doc syntax."""
        try:
            import json
            data = json.loads(ai_response)

            result = {}

            # Format test cases
            test_cases = data.get("test_cases", [])
            if test_cases:
                lines = ["test:"]
                for i, test_case in enumerate(test_cases):
                    expression = test_case.get("expression", "").strip()
                    description = test_case.get("description", "").strip()

                    if expression and description:
                        # Add comma except for last item
                        comma = "," if i < len(test_cases) - 1 else ""
                        lines.append(f'    {expression}: "{description}"{comma}')

                if len(lines) > 1:  # More than just "test:"
                    result['test'] = '\n'.join(lines)

            # Format documentation
            doc_data = data.get("documentation", {})
            if doc_data:
                description = doc_data.get("description", "").strip()
                parameters = doc_data.get("parameters", "").strip()
                returns = doc_data.get("returns", "").strip()

                if description:
                    lines = ["doc:"]
                    lines.append(f"    {description}")

                    if parameters and parameters.lower() != "none":
                        lines.append("")
                        lines.append(f"    Parameters: {parameters}")

                    if returns and returns.lower() != "none":
                        lines.append(f"    Returns: {returns}")

                    result['doc'] = '\n'.join(lines)

            # Fallback to individual generation if combined failed
            if not result:
                result['test'] = self._generate_template_tests(context)
                result['doc'] = self._generate_template_documentation(context)

            return result

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse combined response: {e}")
            # Fallback to individual generation
            return {
                'test': self._generate_template_tests(context),
                'doc': self._generate_template_documentation(context)
            }

    def _format_test_response(self, ai_response: str, context: CodeContext) -> str:
        """Format AI response into proper PyTestEmbed test syntax."""
        # Clean the response and extract test block
        lines = ai_response.split('\n')
        test_lines = []
        in_test_block = False

        for line in lines:
            # Look for test: block start
            if line.strip() == 'test:' or line.strip().endswith('test:'):
                in_test_block = True
                test_lines.append('test:')
                continue

            if in_test_block:
                # Stop at doc: or empty lines after content
                if line.strip().startswith('doc:') or (not line.strip() and test_lines):
                    break

                # Include test content lines
                if line.strip():
                    # Ensure proper indentation
                    if not line.startswith('    '):
                        line = '    ' + line.strip()
                    test_lines.append(line)

        # If we found a test block, return it; otherwise use template
        if len(test_lines) > 1:  # More than just "test:"
            return '\n'.join(test_lines)
        else:
            return self._generate_template_tests(context)
    
    def _format_doc_response(self, ai_response: str, context: CodeContext) -> str:
        """Format AI response into proper PyTestEmbed doc syntax."""
        # Clean the response and extract doc block
        lines = ai_response.split('\n')
        doc_lines = []
        in_doc_block = False

        for line in lines:
            # Look for doc: block start
            if line.strip() == 'doc:' or line.strip().endswith('doc:'):
                in_doc_block = True
                doc_lines.append('doc:')
                continue

            if in_doc_block:
                # Stop at test: or when we hit the end
                if line.strip().startswith('test:'):
                    break

                # Include doc content lines (including empty lines for formatting)
                if line.strip() or doc_lines:  # Include empty lines if we have content
                    # Ensure proper indentation for non-empty lines
                    if line.strip() and not line.startswith('    '):
                        line = '    ' + line.strip()
                    elif not line.strip():
                        line = ''  # Keep empty lines as-is
                    doc_lines.append(line)

        # If we found a doc block, return it; otherwise use template
        if len(doc_lines) > 1:  # More than just "doc:"
            return '\n'.join(doc_lines)
        else:
            return self._generate_template_documentation(context)
    
    def _generate_template_tests(self, context: CodeContext) -> str:
        """Generate template-based tests as fallback."""
        function_name = context.function_name
        params = ', '.join(['arg'] * len(context.parameters))
        
        if context.class_name:
            call = f"{function_name}({params})"
        else:
            call = f"{function_name}({params})"
        
        return f"""test:
    {call} == expected_result: "Basic functionality test",
    {call} != None: "Should return a value"
"""
    
    def _generate_template_documentation(self, context: CodeContext) -> str:
        """Generate template-based documentation as fallback."""
        function_name = context.function_name
        
        if context.docstring:
            description = context.docstring.split('\n')[0]
        else:
            description = f"Performs {function_name} operation."
        
        return f"""doc:
    {description}
    
    Parameters: {', '.join(context.parameters) if context.parameters else 'None'}
    Returns: {context.return_type or 'Result of the operation'}
"""
    
    def _get_style_preferences(self) -> Dict[str, Any]:
        """Get user style preferences for code generation."""
        return {
            'test_style': 'comprehensive',
            'doc_style': 'detailed',
            'include_examples': True,
            'include_edge_cases': True
        }


# CLI integration for smart generation
def generate_smart_blocks(file_path: str, line_number: int, 
                         generation_type: str = 'both', 
                         ai_provider: Optional[str] = None) -> Dict[str, str]:
    """Generate smart test and doc blocks for a function at a specific line."""
    
    try:
        with open(file_path, 'r') as f:
            source_code = f.read()
        
        generator = SmartCodeGenerator(ai_provider)
        result = generator.generate_for_function(source_code, line_number, file_path, generation_type)
        
        return result
        
    except Exception as e:
        return {'error': f"Failed to generate blocks: {e}"}


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python smart_generator.py <file_path> <line_number> [generation_type] [ai_provider]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    line_number = int(sys.argv[2])
    generation_type = sys.argv[3] if len(sys.argv) > 3 else 'both'
    ai_provider = sys.argv[4] if len(sys.argv) > 4 else None
    
    result = generate_smart_blocks(file_path, line_number, generation_type, ai_provider)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        if 'test' in result:
            print("Generated Test Block:")
            print(result['test'])
            print()
        
        if 'doc' in result:
            print("Generated Documentation Block:")
            print(result['doc'])
