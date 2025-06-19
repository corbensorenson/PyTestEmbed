# PyTestEmbed

**The Future of Python Testing and Documentation**

PyTestEmbed is a revolutionary Python framework that embeds tests and documentation directly in your source code, making them impossible to ignore and easy to maintain. Perfect for agentic coding workflows and AI-assisted development.

## 🚀 Quick Start

### Installation

```bash
pip install pytestembed
```

### Your First PyTestEmbed File

```python
def add_numbers(a, b):
    return a + b
test:
    add_numbers(2, 3) == 5: "Basic addition",
    add_numbers(0, 0) == 0: "Zero case",
    add_numbers(-1, 1) == 0: "Negative numbers"
doc:
    Adds two numbers together and returns the result.
    
    Args:
        a (int): First number
        b (int): Second number
    
    Returns:
        int: Sum of a and b
```

### Run Tests

```bash
pytestembed run myfile.py
```

### Generate AI-Powered Tests and Docs

```bash
pytestembed generate myfile.py 10 --type both --ai-provider lmstudio
```

## ✨ Key Features

### 🎯 **Embedded Testing**
- Tests live right next to your code
- No separate test files to maintain
- Impossible to forget or ignore

### 📚 **Integrated Documentation**
- Documentation blocks alongside functions
- Always up-to-date with code changes
- Clear, structured format

### 🤖 **AI-Powered Generation**
- Intelligent test case generation
- Comprehensive documentation creation
- Support for Ollama and LMStudio

### ⚡ **Live Testing**
- Real-time test execution
- WebSocket-based live updates
- Perfect for IDE integration

### 🔧 **Easy Configuration**
- Beautiful GUI configuration tool
- Custom AI prompts
- Team-shareable settings

### 🏗️ **IDE Integration**
- VSCode extension
- PyCharm plugin
- Syntax highlighting and auto-completion

## 🎯 Perfect for Agentic Coding

PyTestEmbed is designed as a **formatting standard** for AI-assisted development:

- **AI models learn the pattern** and write better, more testable code
- **Consistent structure** across all Python projects
- **Self-documenting code** that AI can understand and extend
- **Immediate feedback** on code quality and correctness

## 📖 Documentation

- [Installation Guide](installation.md)
- [Tutorial](tutorial.md)
- [API Reference](api-reference.md)
- [Configuration Guide](configuration.md)
- [IDE Integration](ide-integration.md)
- [AI Integration](ai-integration.md)
- [Examples](examples/)

## 🤝 Community

- [GitHub Discussions](https://github.com/pytestembed/pytestembed/discussions)
- [Contributing Guide](contributing.md)
- [Code of Conduct](code-of-conduct.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🌟 Why PyTestEmbed?

Traditional testing separates tests from code, making them easy to ignore and hard to maintain. PyTestEmbed solves this by embedding tests directly in your source files, creating a new standard for Python development that's perfect for the age of AI-assisted coding.

**Join the revolution. Make your code self-testing and self-documenting.**
