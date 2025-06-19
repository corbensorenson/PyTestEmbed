# PyTestEmbed Tutorial

Learn PyTestEmbed from the ground up with hands-on examples and best practices.

## Table of Contents

1. [Basic Syntax](#basic-syntax)
2. [Writing Tests](#writing-tests)
3. [Writing Documentation](#writing-documentation)
4. [Advanced Patterns](#advanced-patterns)
5. [AI-Powered Generation](#ai-powered-generation)
6. [Best Practices](#best-practices)

## Basic Syntax

PyTestEmbed uses two special blocks: `test:` and `doc:` that appear right after function definitions.

### Your First Function

```python
def add(a, b):
    return a + b
test:
    add(2, 3) == 5: "Basic addition",
    add(0, 0) == 0: "Zero case"
doc:
    Adds two numbers together.
```

### Key Syntax Rules

1. **Test blocks** start with `test:` (no indentation)
2. **Doc blocks** start with `doc:` (no indentation)
3. **Test cases** use format: `expression == expected: "description"`
4. **Multiple tests** are separated by commas
5. **Last test** should NOT have a trailing comma

## Writing Tests

### Basic Test Cases

```python
def multiply(x, y):
    return x * y
test:
    multiply(3, 4) == 12: "Basic multiplication",
    multiply(0, 5) == 0: "Zero multiplication",
    multiply(-2, 3) == -6: "Negative numbers",
    multiply(2.5, 4) == 10.0: "Float numbers"
```

### Testing Different Types

```python
def get_user_info(user_id):
    if user_id == 1:
        return {"name": "Alice", "age": 30}
    return None
test:
    get_user_info(1)["name"] == "Alice": "Valid user name",
    get_user_info(1)["age"] == 30: "Valid user age",
    get_user_info(999) is None: "Invalid user ID"
```

### Testing Exceptions

```python
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
test:
    divide(10, 2) == 5.0: "Normal division",
    divide(7, 2) == 3.5: "Float result"
    # Note: Exception testing requires try/catch in test
```

### Class Method Testing

```python
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    test:
        calc = Calculator()
        calc.add(2, 3) == 5: "Addition works",
        len(calc.history) == 1: "History recorded"
```

## Writing Documentation

### Basic Documentation

```python
def format_name(first, last):
    return f"{first} {last}".strip()
doc:
    Formats a person's full name.
    
    Args:
        first (str): First name
        last (str): Last name
    
    Returns:
        str: Formatted full name
```

### Comprehensive Documentation

```python
def process_data(data, filters=None, sort_key=None):
    if not data:
        return []
    
    result = data.copy()
    
    if filters:
        for key, value in filters.items():
            if key == "min_value":
                result = [x for x in result if x >= value]
    
    if sort_key:
        result.sort(key=sort_key)
    
    return result
doc:
    Processes a list of data with optional filtering and sorting.
    
    This function applies filters to remove unwanted items and then
    sorts the result using the provided key function.
    
    Args:
        data (list): Input data to process
        filters (dict, optional): Filter criteria. Supported keys:
            - min_value: Minimum value threshold
        sort_key (callable, optional): Function for sorting. Defaults to None.
    
    Returns:
        list: Processed and optionally sorted data
    
    Examples:
        >>> process_data([1, 2, 3], filters={'min_value': 2})
        [2, 3]
        
        >>> process_data([3, 1, 2], sort_key=lambda x: x)
        [1, 2, 3]
    
    Raises:
        TypeError: If data is not a list
```

## Advanced Patterns

### Multiple Test Blocks

```python
def complex_function(x, y, operation="add"):
    if operation == "add":
        return x + y
    elif operation == "multiply":
        return x * y
    else:
        raise ValueError("Unknown operation")
test:
    # Basic operations
    complex_function(2, 3) == 5: "Default addition",
    complex_function(2, 3, "add") == 5: "Explicit addition",
    complex_function(2, 3, "multiply") == 6: "Multiplication"
test:
    # Edge cases
    complex_function(0, 0) == 0: "Zero values",
    complex_function(-1, 1) == 0: "Negative values"
doc:
    Performs arithmetic operations on two numbers.
```

### Testing with Setup

```python
def analyze_text(text):
    words = text.lower().split()
    return {
        "word_count": len(words),
        "unique_words": len(set(words)),
        "avg_length": sum(len(w) for w in words) / len(words) if words else 0
    }
test:
    result = analyze_text("Hello world hello")
    result["word_count"] == 3: "Word count correct",
    result["unique_words"] == 2: "Unique words correct",
    result["avg_length"] == 5.0: "Average length correct"
test:
    empty_result = analyze_text("")
    empty_result["word_count"] == 0: "Empty text word count",
    empty_result["avg_length"] == 0: "Empty text average"
```

## AI-Powered Generation

### Generate Tests for Existing Functions

```bash
# Generate tests for function at line 10
pytestembed generate myfile.py 10 --type test --ai-provider lmstudio
```

### Generate Documentation

```bash
# Generate documentation for function at line 15
pytestembed generate myfile.py 15 --type doc --ai-provider ollama
```

### Generate Both Tests and Docs

```bash
# Generate both for function at line 20
pytestembed generate myfile.py 20 --type both --ai-provider lmstudio
```

### Convert Legacy Files

```bash
# Convert entire file to PyTestEmbed format
pytestembed run --convert legacy_file.py --output new_file.py --ai-provider ollama
```

## Best Practices

### 1. Test Coverage Guidelines

- **Minimum 3 test cases** per function
- **Cover normal operation** with typical inputs
- **Test edge cases** (empty, zero, max values)
- **Test error conditions** when applicable

### 2. Test Descriptions

```python
# Good: Specific and descriptive
add(2, 3) == 5: "Basic positive integer addition"
add(0, 0) == 0: "Zero value handling"
add(-1, 1) == 0: "Negative and positive cancellation"

# Bad: Vague or generic
add(2, 3) == 5: "test1"
add(0, 0) == 0: "works"
```

### 3. Documentation Structure

```python
doc:
    Brief one-line description of what the function does.
    
    Optional longer explanation with more details about
    the implementation or important behavior.
    
    Args:
        param1 (type): Description with constraints
        param2 (type, optional): Description. Defaults to value.
    
    Returns:
        type: Description of return value
    
    Raises:
        ExceptionType: When this exception occurs
    
    Examples:
        >>> function_call()
        expected_result
```

### 4. Organizing Complex Functions

```python
def complex_algorithm(data, config):
    # Implementation here
    pass
test:
    # Happy path tests
    simple_data = [1, 2, 3]
    simple_config = {"mode": "basic"}
    complex_algorithm(simple_data, simple_config) == [1, 4, 9]: "Basic mode squares"
test:
    # Edge case tests
    complex_algorithm([], {}) == []: "Empty data handling",
    complex_algorithm([1], {"mode": "invalid"}) == [1]: "Invalid mode fallback"
test:
    # Performance tests (for critical functions)
    large_data = list(range(1000))
    result = complex_algorithm(large_data, {"mode": "fast"})
    len(result) == 1000: "Large data processing"
doc:
    Comprehensive documentation here...
```

### 5. Team Conventions

- **Consistent test descriptions** across the team
- **Shared AI prompts** via configuration export/import
- **Code review** includes test and doc quality
- **Regular updates** when function behavior changes

## Common Patterns

### Data Processing Functions

```python
def filter_items(items, predicate):
    return [item for item in items if predicate(item)]
test:
    filter_items([1, 2, 3, 4], lambda x: x > 2) == [3, 4]: "Number filtering",
    filter_items([], lambda x: True) == []: "Empty list",
    filter_items([1, 2, 3], lambda x: False) == []: "No matches"
```

### API Response Handlers

```python
def parse_api_response(response_data):
    if not response_data or "data" not in response_data:
        return {"error": "Invalid response"}
    return {"success": True, "data": response_data["data"]}
test:
    valid_response = {"data": {"id": 1, "name": "test"}}
    parse_api_response(valid_response)["success"] == True: "Valid response",
    parse_api_response({})["error"] == "Invalid response": "Empty response",
    parse_api_response(None)["error"] == "Invalid response": "None response"
```

### Configuration Handlers

```python
def load_config(config_path, defaults=None):
    defaults = defaults or {}
    try:
        with open(config_path) as f:
            config = json.load(f)
        return {**defaults, **config}
    except FileNotFoundError:
        return defaults
test:
    # This would need actual file setup in practice
    load_config("nonexistent.json", {"key": "value"}) == {"key": "value"}: "Missing file uses defaults"
```

## Next Steps

- Explore [Examples](examples/) for real-world usage patterns
- Set up [IDE Integration](ide-integration.md) for the best experience
- Configure [AI Integration](ai-integration.md) for smart generation
- Read [API Reference](api-reference.md) for complete documentation
