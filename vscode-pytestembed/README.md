# PyTestEmbed VSCode Extension

This VSCode extension provides comprehensive support for PyTestEmbed embedded test and documentation blocks, including syntax highlighting, code folding, and linting integration.

## Features

### 🎨 Syntax Highlighting
- **Keywords**: `test:` and `doc:` blocks are prominently highlighted
- **Test Assertions**: Expressions like `add(2, 3) == 5: "message"` get special coloring
- **Error Messages**: Test failure messages are highlighted as strings
- **Method Calls**: Function and method calls within test blocks are highlighted
- **Operators**: Comparison operators (`==`, `!=`, etc.) are emphasized

### 📁 Code Folding
- **Automatic Folding**: Test and doc blocks can be collapsed for cleaner code view
- **Smart Detection**: Folding ranges are detected based on indentation
- **Manual Commands**: Fold all test or doc blocks with dedicated commands
- **Visual Indicators**: Folded blocks show clear indicators of their content type

### 🔧 Linting Integration
- **Pre-configured Settings**: Ready-to-use configurations for popular Python linters
- **Error Suppression**: Helps prevent false positive errors in test blocks
- **Multiple Tools**: Support for pylint, flake8, mypy, black, and isort
- **Project Templates**: Complete configuration files for different project setups

## Installation

### From VSCode Marketplace
1. Open VSCode
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "PyTestEmbed"
4. Click Install

### From VSIX File
```bash
code --install-extension pytestembed-0.1.0.vsix
```

### Manual Installation
1. Download the `.vsix` file from releases
2. Open VSCode
3. Press Ctrl+Shift+P
4. Type "Extensions: Install from VSIX"
5. Select the downloaded file

### Important: Extension Compatibility

For best results with PyTestEmbed syntax highlighting, you may need to disable conflicting Python extensions:

- **Pylance** (ms-python.vscode-pylance) - Can cause red squiggles in test/doc blocks
- **Python** (ms-python.python) - May interfere with PyTestEmbed syntax highlighting

To disable these extensions:
1. Go to Extensions view (Ctrl+Shift+X)
2. Search for "Pylance" or "Python"
3. Click the gear icon and select "Disable"
4. Reload VSCode

**Note**: Disabling these extensions will remove Python IntelliSense and debugging features, but PyTestEmbed syntax highlighting will work properly.

## Usage

The extension automatically activates when you open Python files containing PyTestEmbed syntax.

### Syntax Example

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
3. **Commands**: Use Ctrl+Shift+P and search for "PyTestEmbed" commands

## Commands

| Command | Description | Keybinding |
|---------|-------------|------------|
| `PyTestEmbed: Fold Test Blocks` | Fold all test blocks in the current file | None |
| `PyTestEmbed: Fold Doc Blocks` | Fold all documentation blocks in the current file | None |

## Linting Configuration

The extension includes pre-configured settings for popular Python linters. Copy the appropriate configuration to your project:

### Pylint (`.pylintrc`)
```ini
[MESSAGES CONTROL]
disable=syntax-error,
        invalid-syntax,
        unexpected-indent,
        unindented-block

[FORMAT]
max-line-length=120

[BASIC]
good-names=test,doc
```

### Flake8 (`.flake8`)
```ini
[flake8]
extend-ignore = E999, E901, E902, E903
max-line-length = 120
exclude = .pytestembed_temp
```

### MyPy (`mypy.ini`)
```ini
[mypy]
ignore_errors = True
allow_untyped_defs = True
allow_any_expr = True
exclude = \.pytestembed_temp/
```

### PyProject.toml (Modern Python Projects)
```toml
[tool.pylint.messages_control]
disable = ["syntax-error", "invalid-syntax"]

[tool.mypy]
ignore_errors = true
allow_untyped_defs = true

[tool.black]
line-length = 120
extend-exclude = '''/(\.pytestembed_temp)/'''
```

## Configuration Files

The extension includes complete configuration templates in the `linting-configs/` directory:

- `.pylintrc` - Pylint configuration
- `.flake8` - Flake8 configuration
- `mypy.ini` - MyPy configuration
- `pyproject.toml` - Modern Python project configuration

Copy these files to your project root and customize as needed.

## Requirements

- **VSCode**: Version 1.74.0 or higher
- **Python**: Files with `.py` extension
- **PyTestEmbed**: The PyTestEmbed library for running tests and generating documentation

## Troubleshooting

### Syntax Highlighting Not Working
1. Ensure the file has a `.py` extension
2. Check that the file contains `test:` or `doc:` blocks
3. Reload VSCode window (Ctrl+Shift+P → "Developer: Reload Window")

### Folding Not Working
1. Verify that test/doc blocks are properly indented
2. Check that blocks have content (empty blocks won't fold)
3. Try the manual fold commands from the command palette

### Linting Errors
1. Copy the appropriate configuration file to your project
2. Restart your linter/language server
3. Check that the configuration file is in the correct location

## Known Issues

- **Complex Expressions**: Very complex nested expressions in test blocks may not highlight perfectly
- **Indentation Edge Cases**: Folding relies on consistent indentation and may not handle all edge cases
- **Performance**: Large files with many test blocks may experience slight performance impact

## Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Issues**: Report bugs and request features on GitHub
2. **Pull Requests**: Submit improvements and fixes
3. **Documentation**: Help improve documentation and examples

### Development Setup
```bash
git clone https://github.com/pytestembed/vscode-pytestembed.git
cd vscode-pytestembed
npm install
npm run compile
```

### Testing
```bash
npm run test
```

## Changelog

### 0.1.0
- Initial release
- Syntax highlighting for test: and doc: blocks
- Code folding support
- Linting configuration templates
- Manual fold commands

## License

MIT License - see LICENSE file for details.

## Links

- **GitHub**: https://github.com/pytestembed/vscode-pytestembed
- **Issues**: https://github.com/pytestembed/vscode-pytestembed/issues
- **PyTestEmbed Library**: https://github.com/pytestembed/pytestembed
- **Documentation**: https://pytestembed.readthedocs.io
