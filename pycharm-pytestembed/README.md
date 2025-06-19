# PyTestEmbed PyCharm Plugin

This PyCharm plugin provides comprehensive support for PyTestEmbed embedded test and documentation blocks, including syntax highlighting, code folding, and inspection suppression.

## Features

### 🎨 Syntax Highlighting
- **Keywords**: `test:` and `doc:` blocks are prominently highlighted
- **Test Assertions**: Expressions like `add(2, 3) == 5: "message"` get special coloring
- **Error Messages**: Test failure messages are highlighted as strings
- **Integration**: Seamlessly integrates with PyCharm's Python syntax highlighting

### 📁 Code Folding
- **Smart Folding**: Test and doc blocks can be collapsed for cleaner code view
- **Automatic Detection**: Folding ranges are detected based on indentation
- **Custom Placeholders**: Folded blocks show clear indicators (`test: ...`, `doc: ...`)
- **Manual Control**: Keyboard shortcuts for folding specific block types

### 🔧 Inspection Suppression
- **Error Prevention**: Suppresses false positive errors in test blocks
- **Smart Detection**: Automatically identifies PyTestEmbed files
- **Seamless Integration**: Works with PyCharm's existing inspection system

### ⌨️ Keyboard Shortcuts
- **Ctrl+Shift+T**: Fold all test blocks
- **Ctrl+Shift+D**: Fold all doc blocks  
- **Ctrl+Shift+R**: Run PyTestEmbed tests for current file

## Installation

### From JetBrains Marketplace
1. Open PyCharm
2. Go to File → Settings → Plugins
3. Search for "PyTestEmbed"
4. Click Install and restart PyCharm

### Manual Installation
1. Download the plugin JAR file from releases
2. Go to File → Settings → Plugins
3. Click the gear icon → Install Plugin from Disk
4. Select the downloaded JAR file
5. Restart PyCharm

## Usage

The plugin automatically activates when you open Python files containing PyTestEmbed syntax.

### Example File

```python
class Calculator:
    def add(self, x, y):
        return x + y
    test:  # Highlighted as keyword
        add(2, 3) == 5: "Addition failed",  # Full assertion highlighting
        add(-1, 1) == 0: "Negative addition failed",
    doc:  # Highlighted as keyword
        Adds two numbers and returns the result

    def multiply(self, x, y):
        return x * y
    test:
        multiply(3, 4) == 12: "Multiplication failed",
        multiply(0, 5) == 0: "Multiplication by zero failed",
    doc:
        Multiplies two numbers and returns the result

test:  # Global test block
    calc = Calculator()
    calc.add(2, 3) * calc.multiply(2, 2) == 20: "Combined operation failed",
doc:  # Global documentation
    A simple calculator class for basic arithmetic operations
```

### Features in Action

1. **Syntax Highlighting**: Keywords, assertions, and messages are color-coded
2. **Code Folding**: Click the fold indicators next to `test:` or `doc:` lines
3. **Menu Actions**: Access PyTestEmbed commands from the Code menu
4. **Keyboard Shortcuts**: Use shortcuts for quick folding operations

## Menu Actions

Access PyTestEmbed actions from **Code → PyTestEmbed**:

| Action | Description | Shortcut |
|--------|-------------|----------|
| Fold Test Blocks | Fold all test: blocks in current file | Ctrl+Shift+T |
| Fold Doc Blocks | Fold all doc: blocks in current file | Ctrl+Shift+D |
| Run PyTestEmbed Tests | Execute tests for current file | Ctrl+Shift+R |

## Configuration

### PyTestEmbed Library Setup

The plugin works with the PyTestEmbed Python library. Install it first:

```bash
pip install pytestembed
```

### Project Configuration

For optimal experience, configure your PyCharm project:

1. **Python Interpreter**: Ensure PyTestEmbed is installed in your project's Python environment
2. **File Associations**: Python files with PyTestEmbed syntax are automatically detected
3. **Code Style**: The plugin respects your existing Python code style settings

### Python Interpreter Configuration

Configure the Python interpreter for PyTestEmbed live testing:

1. **Go to Settings**: File → Settings → Tools → PyTestEmbed
2. **Set Python Interpreter**: Browse to your desired Python executable
3. **Configure Live Testing**: Set live server port and auto-start options
4. **Apply Settings**: Click Apply to save changes

#### Available Settings:

- **Python Interpreter Path**: Path to Python executable for live testing
- **Live Server Port**: Port for live test server (default: 8765)
- **Auto-start Live Testing**: Automatically start live testing when opening Python files
- **AI Provider**: Choose between Ollama and LMStudio for AI generation

#### Environment Detection:

The plugin automatically detects and suggests:
- **Project Virtual Environment**: `.venv`, `venv`, `env` directories
- **Conda Environments**: Active conda environment
- **PyCharm Project Interpreter**: Currently configured project interpreter
- **System Python**: Fallback to system Python

#### Configuration Priority:

1. User-specified interpreter path in PyTestEmbed settings
2. PyCharm project interpreter
3. Detected virtual environment in project root
4. System Python installation

## Compatibility

### PyCharm Versions
- **PyCharm Professional**: 2023.3 and later
- **PyCharm Community**: 2023.3 and later
- **IntelliJ IDEA Ultimate**: 2023.3 and later (with Python plugin)

### Python Versions
- **Python**: 3.8 and later
- **PyTestEmbed Library**: 0.1.0 and later

## Troubleshooting

### Plugin Not Working
1. **Check PyCharm Version**: Ensure you're using 2023.3 or later
2. **Restart PyCharm**: After installation, restart the IDE
3. **Check File Extension**: Ensure your files have `.py` extension
4. **Verify Syntax**: Check that your files contain `test:` or `doc:` blocks

### Syntax Highlighting Issues
1. **File Detection**: The plugin automatically detects PyTestEmbed files
2. **Cache Refresh**: Try File → Invalidate Caches and Restart
3. **Plugin Conflicts**: Disable other Python syntax plugins temporarily

### Folding Not Working
1. **Indentation**: Ensure test/doc blocks are properly indented
2. **Block Content**: Empty blocks won't fold
3. **Manual Folding**: Use keyboard shortcuts if automatic folding fails

### Running Tests
1. **PyTestEmbed Installation**: Ensure `python -m pytestembed` works in terminal
2. **Project Path**: Check that PyCharm can access your project files
3. **Python Environment**: Verify the correct Python interpreter is selected

## Development

### Building the Plugin

```bash
# Clone the repository
git clone https://github.com/pytestembed/pycharm-pytestembed.git
cd pycharm-pytestembed

# Build the plugin
./gradlew buildPlugin

# The plugin JAR will be in build/distributions/
```

### Testing

```bash
# Run in development environment
./gradlew runIde

# Run tests
./gradlew test
```

### Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

## Known Issues

### Current Limitations
- **Complex Expressions**: Very complex nested expressions in test blocks may not highlight perfectly
- **Performance**: Large files with many test blocks may experience slight performance impact
- **Error Recovery**: Limited error recovery for malformed PyTestEmbed syntax

### Planned Improvements
- **Enhanced Syntax Highlighting**: More sophisticated expression parsing
- **Code Completion**: Auto-completion for test assertions
- **Refactoring Support**: Safe refactoring of code with embedded tests
- **Test Navigation**: Jump between tests and implementation

## Support

### Getting Help
- **Documentation**: https://pytestembed.dev/docs
- **Issues**: https://github.com/pytestembed/pycharm-pytestembed/issues
- **Discussions**: https://github.com/pytestembed/pytestembed/discussions

### Reporting Bugs
When reporting issues, please include:
1. PyCharm version
2. Plugin version
3. Python version
4. Sample code that reproduces the issue
5. Error messages or screenshots

## Changelog

### Version 0.1.0
- Initial release
- Syntax highlighting for test: and doc: blocks
- Code folding support
- Inspection suppression for test blocks
- Menu actions and keyboard shortcuts
- Integration with PyTestEmbed CLI

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **PyTestEmbed Library**: https://github.com/pytestembed/pytestembed
- **VSCode Extension**: https://marketplace.visualstudio.com/items?itemName=pytestembed.pytestembed
- **Documentation**: https://pytestembed.dev
- **JetBrains Marketplace**: https://plugins.jetbrains.com/plugin/pytestembed
