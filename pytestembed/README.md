# PyTestEmbed

PyTestEmbed is a revolutionary Python development tool that enables developers to embed tests and documentation directly within Python class and method definitions using an intuitive custom syntax. Write tests and docs where they belong - right next to your code!

## 🚀 Features

### 🧪 Embedded Testing
- **Inline Tests**: Write tests directly within class and method definitions
- **Multiple Test Cases**: Support for multiple test cases per method/class
- **Multi-line Tests**: Complex test scenarios with setup statements
- **Automatic Test Generation**: Converts to standard unittest format
- **Instance Management**: Automatic instance creation for class method tests

### 📚 Inline Documentation
- **Embedded Docs**: Add documentation blocks right next to your code
- **Unified Generation**: Compile all docs into structured Markdown
- **Smart Formatting**: Automatic text enhancement and formatting
- **Hierarchical Structure**: Organized by classes, methods, and functions

### ⚡ Powerful CLI
- **Test Execution**: Run embedded tests with `--test`
- **Doc Generation**: Create documentation with `--doc`
- **Flexible Output**: Save to files or display in terminal
- **Verbose Mode**: Detailed output for debugging
- **Project-local Temp Files**: All temporary files stay within your project

### 🔧 Developer Experience
- **VSCode Extension**: Syntax highlighting and code folding
- **Linting Integration**: Pre-configured settings for popular linters
- **Caching System**: Avoid reparsing unchanged files
- **Error Handling**: Clear error messages and validation

## 📦 Installation

### From PyPI
```bash
pip install pytestembed
```

### From Source
```bash
git clone https://github.com/pytestembed/pytestembed.git
cd pytestembed
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/pytestembed/pytestembed.git
cd pytestembed
pip install -e ".[dev]"
```

## 🏃 Quick Start

### 1. Create a PyTestEmbed File

Create `calculator.py`:

```python
class Calculator:
    def add(self, x, y):
        return x + y
    test:
        add(2, 3) == 5: "Addition failed",
        add(-1, 1) == 0: "Addition with negative failed",
        add(0, 0) == 0: "Addition with zeros failed",
    doc:
        Adds two numbers together and returns the result.
        Supports both positive and negative numbers.

    def multiply(self, x, y):
        return x * y
    test:
        multiply(3, 4) == 12: "Multiplication failed",
        multiply(0, 5) == 0: "Multiplication by zero failed",
        multiply(-2, 3) == -6: "Multiplication with negative failed",
    doc:
        Multiplies two numbers and returns the result.
        Handles positive, negative, and zero values.

test:
    calc = Calculator()
    calc.add(2, 3) * calc.multiply(2, 2) == 20: "Combined operation failed",
    result = calc.add(10, 5)
    result == 15: "Variable assignment test failed",
doc:
    A comprehensive calculator class for basic arithmetic operations.
    Supports addition and multiplication with full test coverage.

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
test:
    factorial(5) == 120: "Factorial calculation failed",
    factorial(0) == 1: "Factorial of 0 failed",
    factorial(1) == 1: "Factorial of 1 failed",
doc:
    Calculates the factorial of a number using recursion.
    Returns 1 for inputs of 0 and 1.
```

### 2. Run Tests

```bash
python -m pytestembed --test calculator.py
```

Output:
```
Parsing calculator.py...
Generating test code...
Running tests...
........
----------------------------------------------------------------------
Ran 8 tests in 0.001s

OK
All tests passed!
```

### 3. Generate Documentation

```bash
python -m pytestembed --doc calculator.py
```

Output:
```markdown
# Calculator Documentation

A comprehensive calculator class for basic arithmetic operations.
Supports addition and multiplication with full test coverage.

## Class: Calculator

### Method: add(self, x, y)

**Description**: Adds two numbers together and returns the result. Supports both positive and negative numbers.

**Parameters**:
- `x`: Parameter description
- `y`: Parameter description

### Method: multiply(self, x, y)

**Description**: Multiplies two numbers and returns the result. Handles positive, negative, and zero values.

**Parameters**:
- `x`: Parameter description
- `y`: Parameter description

## Function: factorial(n)

**Description**: Calculates the factorial of a number using recursion. Returns 1 for inputs of 0 and 1.

**Parameters**:
- `n`: Parameter description
```

### 4. Normal Execution

```bash
python calculator.py  # test: and doc: blocks are ignored
```

## 📖 Syntax Guide

### Test Blocks

Test blocks are defined with `test:` and contain comma-separated test cases:

```python
test:
    expression == expected: "error message",
    another_test() == result: "another error message",
```

#### Test Case Format
- **Simple Assertion**: `method(args) == expected: "message",`
- **Multi-line Test**:
  ```python
  test:
      a = method1(args)
      b = method2(args)
      a + b == expected: "message",
  ```

#### Supported Locations
- **Method Level**: Tests for individual methods
- **Class Level**: Tests for the entire class
- **Global Level**: Tests for standalone functions or integration tests

### Documentation Blocks

Documentation blocks are defined with `doc:` and contain plain text:

```python
doc:
    This method performs a specific operation
    and returns the computed result
```

#### Documentation Features
- **Plain Text**: No need for triple quotes
- **Multi-line**: Automatic text joining and formatting
- **Hierarchical**: Organized by scope (method, class, global)

### Advanced Examples

#### Complex Test Scenarios
```python
class DataProcessor:
    def process_data(self, data):
        return [x * 2 for x in data if x > 0]
    test:
        process_data([1, 2, 3]) == [2, 4, 6]: "Basic processing failed",
        process_data([0, -1, 2]) == [4]: "Filtering failed",
        process_data([]) == []: "Empty list failed",
    doc:
        Processes a list of numbers by doubling positive values.
        Filters out zero and negative numbers.

    def aggregate(self, data):
        return sum(self.process_data(data))
    test:
        aggregate([1, 2, 3]) == 12: "Aggregation failed",
        result = aggregate([1, -1, 2, 0, 3])
        result == 10: "Complex aggregation failed",
    doc:
        Aggregates processed data by summing all values.
        Combines processing and summation in one operation.
```

## 🖥️ CLI Reference

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `--test` | Run embedded tests | `python -m pytestembed --test file.py` |
| `--doc` | Generate documentation | `python -m pytestembed --doc file.py` |
| `--verbose` | Show detailed output | `python -m pytestembed --test --verbose file.py` |
| `--output <file>` | Save output to file | `python -m pytestembed --test --output tests.py file.py` |

### Examples

#### Run Tests with Verbose Output
```bash
python -m pytestembed --test --verbose calculator.py
```

#### Generate Documentation to File
```bash
python -m pytestembed --doc calculator.py --output docs.md
```

#### Save Generated Test Code
```bash
python -m pytestembed --test calculator.py --output test_calculator.py
```

#### Process Multiple Files
```bash
python -m pytestembed --test module1.py
python -m pytestembed --test module2.py
python -m pytestembed --doc module1.py --output module1_docs.md
```

## 🔧 Configuration

### Caching

PyTestEmbed automatically caches parsed files to improve performance:

- **Cache Location**: `.pytestembed_cache/` in your project directory
- **Cache Invalidation**: Automatic when files change
- **Manual Cache Clear**: Delete the `.pytestembed_cache/` directory

### Temporary Files

All temporary files are created within your project:

- **Location**: `.pytestembed_temp/` directory
- **Cleanup**: Automatic cleanup after test execution
- **Persistence**: Files are removed unless execution fails

## 🧪 Testing PyTestEmbed

### Run the Test Suite
```bash
cd pytestembed
python -m pytest tests/ -v
```

### Test with Examples
```bash
python -m pytestembed --test tests/examples/derp.py
python -m pytestembed --doc tests/examples/derp.py
```

## 🛠️ Development

### Project Structure
```
pytestembed/
├── pytestembed/
│   ├── __init__.py
│   ├── parser.py       # textX-based parser
│   ├── generator.py    # Test code generation
│   ├── doc_generator.py # Documentation generation
│   ├── runner.py       # Test execution
│   ├── cli.py          # Command-line interface
│   └── utils.py        # Helper functions
├── tests/              # Comprehensive test suite
├── setup.py           # Package configuration
└── README.md          # This file
```

### Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Add** tests for new functionality
4. **Ensure** all tests pass
5. **Submit** a pull request

### Development Setup
```bash
git clone https://github.com/pytestembed/pytestembed.git
cd pytestembed
pip install -e ".[dev]"
python -m pytest tests/
```

## 📋 Requirements

### Runtime Requirements
- **Python**: 3.8 or higher
- **textX**: 3.0.0 or higher (for parsing)
- **click**: 8.0.0 or higher (for CLI)

### Optional Requirements
- **transformers**: 4.20.0 or higher (for enhanced documentation)
- **torch**: 1.12.0 or higher (for AI model support)

### Development Requirements
- **pytest**: 7.0.0 or higher
- **pytest-cov**: 4.0.0 or higher
- **black**: 22.0.0 or higher
- **flake8**: 5.0.0 or higher
- **mypy**: 0.991 or higher

## 🎯 Use Cases

### Test-Driven Development
```python
class APIClient:
    def get_user(self, user_id):
        # Implementation here
        pass
    test:
        get_user(123) != None: "Should return user object",
        get_user(999) == None: "Should return None for invalid ID",
    doc:
        Retrieves user information by ID.
        Returns None if user doesn't exist.
```

### Documentation-First Development
```python
class DataAnalyzer:
    def analyze_trends(self, data):
        # Implementation here
        pass
    doc:
        Analyzes data trends using statistical methods.
        Returns trend analysis with confidence intervals.
        Supports time series and cross-sectional data.
    test:
        # Tests added after implementation
        analyze_trends([1,2,3,4,5]) != None: "Should return analysis",
```

### Integration Testing
```python
test:
    # Global integration tests
    client = APIClient()
    analyzer = DataAnalyzer()
    data = client.get_data()
    results = analyzer.analyze_trends(data)
    len(results) > 0: "Integration test failed",
doc:
    Complete data processing pipeline.
    Integrates API client with data analysis.
```

## 🚨 Known Issues

### Current Limitations
- **AI Documentation**: Simplified version without full AI model integration
- **Complex Expressions**: Very complex nested expressions may not parse perfectly
- **Error Recovery**: Limited error recovery for malformed syntax

### Planned Improvements
- **Full AI Integration**: Enhanced documentation generation with local AI models
- **IDE Support**: Additional IDE extensions beyond VSCode
- **Advanced Testing**: Support for parameterized tests and fixtures

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **GitHub**: https://github.com/pytestembed/pytestembed
- **PyPI**: https://pypi.org/project/pytestembed/
- **Documentation**: https://pytestembed.readthedocs.io
- **Issues**: https://github.com/pytestembed/pytestembed/issues
- **VSCode Extension**: https://marketplace.visualstudio.com/items?itemName=pytestembed.pytestembed

## 🙏 Acknowledgments

- **textX**: For the excellent parsing framework
- **Click**: For the intuitive CLI framework
- **VSCode**: For the extensible editor platform
- **Python Community**: For inspiration and feedback
