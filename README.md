# PyTestEmbed Project

🚀 **The Most Advanced Python Testing Framework** - Embed tests and documentation directly within your Python code with cutting-edge AI and predictive capabilities!

PyTestEmbed revolutionizes Python development by combining embedded testing, intelligent AI assistance, live test execution, and comprehensive code analysis. It's not just a testing framework - it's an intelligent development assistant that makes developers more productive and code more reliable.

## 🌟 Revolutionary Features

### ⚡ **Live Test Execution**
- **Real-time feedback**: Tests run automatically as you save files
- **Intelligent test selection**: Only runs tests affected by your changes
- **WebSocket integration**: Instant results in your IDE
- **Live coverage tracking**: See test coverage update in real-time

### 🧠 **Advanced AI Integration**
- **Smart test generation**: AI creates intelligent test cases based on code analysis
- **Predictive testing**: ML models predict which tests are likely to fail
- **Property-based testing**: Automatically generates edge cases and boundary tests
- **Context-aware suggestions**: AI understands your codebase patterns

### 🕸️ **Code Dependency Web**
- **Project-wide analysis**: Maps all function and class relationships
- **Dead code detection**: Identifies unused code across your entire project
- **Interactive visualization**: Explore code dependencies with D3.js graphs
- **Cross-file navigation**: Jump between related code elements instantly

### 🎯 **Smart Testing Features**
- **Failure prediction**: ML models predict test failures before they happen
- **Test impact analysis**: Shows which tests to run when code changes
- **Multi-statement tests**: Complex test setups with variable assignments
- **Class-level testing**: Tests that belong to entire classes, not just methods

### 📚 **PyTestEmbed Library (`pytestembed/`)**
A comprehensive Python library featuring:
- **🔍 Advanced Parser**: Recognizes embedded test and doc blocks using textX
- **🧪 Live Test Runner**: Real-time test execution with WebSocket communication
- **🤖 AI Test Generation**: Local AI support via Ollama and LMStudio
- **🔮 Failure Prediction**: ML-powered test failure prediction
- **🕸️ Dependency Analysis**: Complete codebase relationship mapping
- **📊 Smart Test Selection**: Intelligent test selection based on code changes
- **⚡ CLI Interface**: Comprehensive command-line tools
- **🛡️ Production Ready**: Handles real-world complexity and edge cases

### 🎨 **VSCode Extension (`vscode-pytestembed/`)**
A cutting-edge VSCode extension providing:
- **🌈 Advanced Syntax Highlighting**: Beautiful highlighting with TextMate grammars
- **💡 Lightbulb Quick Actions**: Generate tests/docs with AI assistance
- **📊 Live Test Status**: Real-time test results with pass/fail indicators
- **🔧 Integrated Controls**: Status bar buttons and toolbar integration
- **📁 Smart Code Folding**: Collapse test/doc blocks for cleaner views
- **🚨 Problems Integration**: Test results in VSCode's Problems panel

## ✨ Core Capabilities

### 🧪 **Advanced Embedded Testing**
Write sophisticated tests directly within your code:
```python
class Calculator:
    def divide(self, x, y):
        if y == 0: raise ValueError("Division by zero")
        return x / y
    test:
        # Multi-statement test with setup
        result = divide(10, 2)
        result == 5.0: "Basic division failed",

        # Exception testing
        try:
            divide(1, 0)
            False: "Should have raised ValueError"
        except ValueError:
            True: "Correctly raised ValueError",

        # Edge cases
        divide(-10, 2) == -5.0: "Negative division failed",
        divide(0, 5) == 0.0: "Zero dividend failed",
```

### 🕸️ **Class-Level Testing**
Tests that belong to entire classes:
```python
class UserManager:
    def create_user(self, name): return {"id": 1, "name": name}
    def delete_user(self, user_id): return True

test:
    # Class-level integration test
    user = create_user("Alice")
    user["name"] == "Alice": "User creation failed",
    delete_user(user["id"]) == True: "User deletion failed",
```

### 🤖 **AI-Powered Development**
- **Smart test generation**: AI analyzes your code and creates comprehensive tests
- **Intelligent documentation**: AI enhances and structures your documentation
- **Failure prediction**: ML models predict which tests might fail
- **Property-based testing**: AI generates edge cases you might miss

### ⚡ **Live Development Experience**
- **Auto-test on save**: Tests run automatically when you save files
- **Real-time feedback**: See test results instantly in your IDE
- **Smart test selection**: Only runs tests affected by your changes
- **Live coverage**: Watch test coverage update as you code

### 🔄 **Complete Workflow**
- **Development**: Write code with embedded tests and docs + AI assistance
- **Live Testing**: `python -m pytestembed live` (auto-runs tests on save)
- **Manual Testing**: `python -m pytestembed --test file.py`
- **Documentation**: `python -m pytestembed --doc file.py`
- **Dependency Analysis**: Interactive code relationship visualization
- **Production**: `python file.py` (test blocks ignored)

## 🚀 Quick Start

### 1. Installation

```bash
# Install the library
pip install pytestembed

# Install VSCode extension
# Search "PyTestEmbed" in VSCode Extensions marketplace

# Start live test server (optional but recommended)
python -m pytestembed live
```

### 2. Create Your First PyTestEmbed File

Create `example.py`:
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

    def divide(self, x, y):
        if y == 0: raise ValueError("Cannot divide by zero")
        return x / y
    test:
        # Multi-statement test with exception handling
        result = divide(10, 2)
        result == 5.0: "Basic division failed",

        try:
            divide(1, 0)
            False: "Should have raised ValueError"
        except ValueError:
            True: "Correctly handled division by zero",
    doc:
        Divides two numbers with proper error handling.
        Raises ValueError for division by zero.

test:
    # Class-level integration test
    calc = Calculator()
    sum_result = calc.add(2, 3)
    div_result = calc.divide(10, 2)
    sum_result + div_result == 10.0: "Integration test failed",
doc:
    A comprehensive calculator class with embedded testing.
    Demonstrates PyTestEmbed's advanced testing capabilities.
```

### 3. Live Testing (Recommended)

```bash
# Start live test server
python -m pytestembed live

# Now save your file - tests run automatically!
# See real-time results in your IDE
```

### 4. Manual Testing

```bash
python -m pytestembed --test example.py
```

Output:
```
✅ All tests passed!
📊 Test Results:
  - Calculator.add: 3 tests passed
  - Calculator.divide: 2 tests passed
  - Integration tests: 1 test passed
🕸️ Dependency analysis: 2 classes, 5 methods analyzed
```

### 5. AI-Enhanced Development

```bash
# Convert existing Python files with AI assistance
python -m pytestembed --convert old_file.py --ai-provider ollama

# Generate comprehensive documentation
python -m pytestembed --doc example.py --output docs.md
```

### 6. Explore Code Dependencies

```bash
# Export dependency graph for visualization
python -c "
import asyncio
import websockets
import json

async def export_graph():
    async with websockets.connect('ws://localhost:8765') as ws:
        await ws.send(json.dumps({'command': 'export_dependency_graph'}))
        response = await ws.recv()
        print('Graph exported to dependency_graph.json')

asyncio.run(export_graph())
"

# Open dependency_visualizer.html in browser to explore your code relationships
```

### 7. Normal Execution

```bash
python example.py  # Runs normally, test: and doc: blocks are ignored
```

## 🧠 Advanced Features

### 🔮 **Predictive Testing**
PyTestEmbed uses machine learning to predict which tests are likely to fail:

```bash
# Get failure predictions
python -c "
import asyncio
import websockets
import json

async def predict_failures():
    async with websockets.connect('ws://localhost:8765') as ws:
        await ws.send(json.dumps({'command': 'predict_failures'}))
        response = await ws.recv()
        data = json.loads(response)
        print(f'High-risk tests: {data[\"data\"][\"high_risk_count\"]}')

asyncio.run(predict_failures())
"
```

### 🧪 **Property-Based Testing**
Automatically generate edge cases and boundary tests:

```python
def sort_list(items):
    return sorted(items)
test:
    # PyTestEmbed can generate property-based tests
    property: "sorted list should be in ascending order"
    property: "sorted list should have same length as input"
    property: "sorting twice should give same result"
```

### 🕸️ **Code Dependency Analysis**
Understand your codebase relationships:

- **Dead code detection**: Find unused functions and classes
- **Impact analysis**: See what tests to run when code changes
- **Cross-file navigation**: Jump between related code elements
- **Interactive visualization**: Explore dependencies with D3.js graphs

### ⚡ **Smart Test Selection**
Only run tests that matter:

```bash
# Run smart test selection based on git changes
python -c "
import asyncio
import websockets
import json

async def smart_tests():
    async with websockets.connect('ws://localhost:8765') as ws:
        await ws.send(json.dumps({
            'command': 'smart_test_selection',
            'commit_hash': 'HEAD~1',
            'confidence': 0.8
        }))
        response = await ws.recv()
        data = json.loads(response)
        print(f'Selected {data[\"data\"][\"selected_count\"]} tests')
        print(f'Skipped {data[\"data\"][\"skipped_count\"]} tests')
        print(f'Time saved: {data[\"data\"][\"time_saved\"]}s')

asyncio.run(smart_tests())
"
```

## 🏗️ Project Structure

```
PyTestEmbed/
├── pytestembed/                 # 🐍 Main Python library
│   ├── pytestembed/
│   │   ├── __init__.py
│   │   ├── parser.py           # textX-based syntax parser
│   │   ├── generator.py        # Test code generation
│   │   ├── doc_generator.py    # Documentation generation
│   │   ├── runner.py           # Test execution engine
│   │   ├── cli.py              # Command-line interface
│   │   └── utils.py            # Utility functions
│   ├── tests/                  # Comprehensive test suite
│   │   ├── test_parser.py
│   │   ├── test_generator.py
│   │   ├── test_doc_generator.py
│   │   ├── test_runner.py
│   │   ├── test_integration.py
│   │   └── examples/
│   │       └── derp.py         # Example PyTestEmbed file
│   ├── setup.py               # Package configuration
│   ├── requirements.txt       # Dependencies
│   └── README.md              # Library documentation
├── vscode-pytestembed/         # 🎨 VSCode extension
│   ├── src/
│   │   ├── extension.ts       # Main extension logic
│   │   └── grammar/
│   │       └── pytestembed.tmLanguage.json
│   ├── linting-configs/       # Linter configuration templates
│   │   ├── .pylintrc
│   │   ├── .flake8
│   │   ├── mypy.ini
│   │   └── pyproject.toml
│   ├── package.json           # Extension manifest
│   ├── tsconfig.json          # TypeScript configuration
│   └── README.md              # Extension documentation
├── pycharm-pytestembed/        # 🧠 PyCharm plugin
│   ├── src/main/kotlin/com/pytestembed/plugin/
│   │   ├── PyTestEmbedFileType.kt
│   │   ├── highlighting/       # Syntax highlighting
│   │   ├── folding/           # Code folding
│   │   ├── inspections/       # Inspection suppression
│   │   └── actions/           # Menu actions
│   ├── src/main/resources/META-INF/
│   │   └── plugin.xml         # Plugin configuration
│   ├── build.gradle.kts       # Build configuration
│   └── README.md              # Plugin documentation
├── docs/                      # Additional documentation
└── README.md                  # This file
```

## 🛠️ Development Setup

### Library Development

```bash
# Clone the repository
git clone https://github.com/pytestembed/pytestembed.git
cd pytestembed

# Set up the library
cd pytestembed
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Test with examples
python -m pytestembed --test tests/examples/derp.py
```

### VSCode Extension Development

```bash
# Set up the extension
cd vscode-pytestembed
npm install

# Compile TypeScript
npm run compile

# Package extension
npm install -g vsce
vsce package
```

## 🧪 Testing

### Library Tests
```bash
cd pytestembed
python -m pytest tests/ -v --cov=pytestembed
```

### Integration Tests
```bash
# Test complete workflow
python -m pytestembed --test tests/examples/derp.py
python -m pytestembed --doc tests/examples/derp.py --output test_docs.md
```

### Extension Testing
```bash
cd vscode-pytestembed
npm test
```

## 📊 Current Status

### ✅ Completed Features
- [x] **Core Parser**: textX-based syntax parsing
- [x] **Test Generation**: unittest code generation
- [x] **Documentation Generation**: Markdown output
- [x] **Python File Converter**: Converts existing Python files to PyTestEmbed syntax
- [x] **AI Integration**: Local AI support via Ollama and LMStudio
- [x] **AI Test Generation**: Intelligent test case creation using code analysis
- [x] **AI Documentation Enhancement**: Smart documentation improvement and generation
- [x] **CLI Interface**: Complete command-line tools with --convert option
- [x] **Test Runner**: Isolated test execution
- [x] **Caching System**: File-based caching
- [x] **VSCode Extension**: Syntax highlighting and folding with enhanced UI controls
- [x] **PyCharm Plugin**: Full IDE integration with syntax highlighting, folding, and inspection suppression
- [x] **Enhanced IDE Controls**: Status bar buttons, toolbar integration, keyboard shortcuts
- [x] **Linting Integration**: Configuration templates for both IDEs
- [x] **Comprehensive Testing**: 30+ test cases including converter tests
- [x] **Project-local Temp Files**: No system temp directory usage

### 🔄 In Progress
- [ ] **Enhanced AI Documentation**: Full local AI model integration
- [ ] **Advanced Error Recovery**: Better syntax error handling
- [ ] **Performance Optimization**: Large file handling

### 🎯 Planned Features
- [ ] **Pytest Integration**: Plugin for pytest framework
- [ ] **Parameterized Tests**: Advanced testing features
- [ ] **Setup/Teardown Blocks**: Test fixture support
- [ ] **Type Annotations**: Enhanced type checking support
- [ ] **Code Completion**: Auto-completion for test assertions in IDEs

## 🎨 Syntax Examples

### Basic Method Testing
```python
class StringUtils:
    def reverse(self, text):
        return text[::-1]
    test:
        reverse("hello") == "olleh": "Basic reverse failed",
        reverse("") == "": "Empty string failed",
        reverse("a") == "a": "Single character failed",
    doc:
        Reverses a string and returns the result.
        Handles empty strings and single characters.
```

### Complex Integration Testing
```python
class DatabaseManager:
    def connect(self):
        # Implementation here
        pass

    def query(self, sql):
        # Implementation here
        pass

    def close(self):
        # Implementation here
        pass

test:
    # Integration test
    db = DatabaseManager()
    db.connect()
    result = db.query("SELECT 1")
    db.close()
    result is not None: "Database integration failed",
doc:
    Complete database management system.
    Provides connection, querying, and cleanup functionality.
```

### Multi-line Test Scenarios
```python
class DataAnalyzer:
    def process_batch(self, data):
        return {"processed": len(data), "valid": sum(1 for x in data if x > 0)}
    test:
        result = process_batch([1, 2, 3, -1, 0])
        result["processed"] == 5: "Batch size calculation failed",
        result["valid"] == 3: "Valid count calculation failed",

        empty_result = process_batch([])
        empty_result["processed"] == 0: "Empty batch failed",
    doc:
        Processes a batch of data and returns statistics.
        Counts total items and valid (positive) items.
```

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Set custom cache directory
export PYTESTEMBED_CACHE_DIR=".custom_cache"

# Optional: Disable caching
export PYTESTEMBED_NO_CACHE=1

# AI Provider Configuration
export PYTESTEMBED_OLLAMA_URL="http://localhost:11434"
export PYTESTEMBED_OLLAMA_MODEL="codellama"
export PYTESTEMBED_LMSTUDIO_URL="http://localhost:1234"
export PYTESTEMBED_LMSTUDIO_MODEL="local-model"
```

### Project Configuration
Create `.pytestembed.json` in your project root:
```json
{
    "cache_enabled": true,
    "cache_dir": ".pytestembed_cache",
    "temp_dir": ".pytestembed_temp",
    "verbose": false,
    "test_timeout": 30,
    "ai_provider": "ollama",
    "ai_enabled": true
}
```

### AI Provider Setup

#### Ollama (Recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a code model
ollama pull codellama
# or
ollama pull deepseek-coder

# Start Ollama (usually runs automatically)
ollama serve
```

#### LMStudio
1. Download and install LMStudio from https://lmstudio.ai/
2. Download a code-focused model (e.g., CodeLlama, DeepSeek Coder)
3. Start the local server in LMStudio
4. Configure PyTestEmbed to use LMStudio endpoint

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 1. Fork and Clone
```bash
git clone https://github.com/yourusername/pytestembed.git
cd pytestembed
```

### 2. Set Up Development Environment
```bash
# Library setup
cd pytestembed
pip install -e ".[dev]"

# VSCode extension setup
cd ../vscode-pytestembed
npm install

# PyCharm plugin setup
cd ../pycharm-pytestembed
./gradlew build
```

### 3. Make Changes
- **Library**: Add features to `pytestembed/pytestembed/`
- **Extension**: Modify `vscode-pytestembed/src/`
- **Tests**: Add tests to appropriate test files
- **Documentation**: Update README files

### 4. Test Your Changes
```bash
# Run library tests
cd pytestembed
python -m pytest tests/ -v

# Test VSCode extension
cd ../vscode-pytestembed
npm run compile

# Test PyCharm plugin
cd ../pycharm-pytestembed
./gradlew runIde
```

### 5. Submit Pull Request
- Create a feature branch
- Commit your changes
- Push to your fork
- Open a pull request

### Contribution Guidelines
- **Code Style**: Follow PEP 8 for Python, use Prettier for TypeScript
- **Testing**: Add tests for new features
- **Documentation**: Update relevant README files
- **Commit Messages**: Use clear, descriptive commit messages

## 📋 Requirements

### Runtime Requirements
- **Python**: 3.8 or higher
- **Node.js**: 16.0 or higher (for extension development)
- **VSCode**: 1.74.0 or higher (for extension usage)

### Python Dependencies
- **textX**: 3.0.0+ (parsing framework)
- **click**: 8.0.0+ (CLI framework)
- **transformers**: 4.20.0+ (optional, for AI documentation)

### Development Dependencies
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking
- **TypeScript**: Extension development

## 🐛 Known Issues

### Current Limitations
1. **Complex Expressions**: Very complex nested expressions may not parse perfectly
2. **Error Recovery**: Limited recovery from syntax errors
3. **Performance**: Large files (>1000 lines) may experience slower parsing

### Workarounds
1. **Complex Expressions**: Break into simpler test cases
2. **Syntax Errors**: Use `--verbose` flag for detailed error information
3. **Performance**: Use caching and process files individually

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **🏠 Homepage**: https://pytestembed.dev
- **📦 PyPI**: https://pypi.org/project/pytestembed/
- **🛍️ VSCode Marketplace**: https://marketplace.visualstudio.com/items?itemName=pytestembed.pytestembed
- **🧠 JetBrains Marketplace**: https://plugins.jetbrains.com/plugin/pytestembed
- **📚 Documentation**: https://docs.pytestembed.dev
- **🐛 Issues**: https://github.com/pytestembed/pytestembed/issues
- **💬 Discussions**: https://github.com/pytestembed/pytestembed/discussions

## 🙏 Acknowledgments

Special thanks to:
- **textX Team**: For the excellent parsing framework
- **Click Team**: For the intuitive CLI framework
- **VSCode Team**: For the extensible editor platform
- **Python Community**: For inspiration and feedback
- **Early Adopters**: For testing and feature requests

---

**Ready to revolutionize your Python development workflow?**

🚀 **[Get Started Now](https://pytestembed.dev/quickstart)** | 📖 **[Read the Docs](https://docs.pytestembed.dev)** | 💬 **[Join the Discussion](https://github.com/pytestembed/pytestembed/discussions)**
