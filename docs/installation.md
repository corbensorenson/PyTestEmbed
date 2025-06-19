# Installation Guide

This guide will help you install and set up PyTestEmbed on your system.

## Requirements

- Python 3.8 or higher
- pip (Python package installer)
- Optional: Ollama or LMStudio for AI features

## Installation Methods

### 1. Install from PyPI (Recommended)

```bash
pip install pytestembed
```

### 2. Install from Source

```bash
git clone https://github.com/pytestembed/pytestembed.git
cd pytestembed
pip install -e .
```

### 3. Development Installation

```bash
git clone https://github.com/pytestembed/pytestembed.git
cd pytestembed
pip install -e ".[dev]"
```

## Verify Installation

```bash
pytestembed --version
```

You should see the PyTestEmbed version number.

## Quick Configuration

### 1. Open Configuration GUI

```bash
pytestembed config
```

This opens a user-friendly GUI where you can configure:
- AI providers (Ollama/LMStudio)
- Model selection
- Custom prompts
- General settings

### 2. Test Basic Functionality

Create a test file `hello.py`:

```python
def greet(name):
    return f"Hello, {name}!"
test:
    greet("World") == "Hello, World!": "Basic greeting",
    greet("") == "Hello, !": "Empty name"
doc:
    Greets a person by name.
    
    Args:
        name (str): Name to greet
    
    Returns:
        str: Greeting message
```

Run the tests:

```bash
pytestembed run hello.py
```

## AI Setup (Optional)

### Option 1: Ollama

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Pull a model:
   ```bash
   ollama pull codellama
   ```
3. Configure PyTestEmbed:
   ```bash
   pytestembed config
   ```
   - Set AI Provider to "Ollama"
   - Set Model to "codellama"
   - Test connection

### Option 2: LMStudio

1. Install LMStudio from [lmstudio.ai](https://lmstudio.ai)
2. Download a model (e.g., Qwen 14B)
3. Start the local server
4. Configure PyTestEmbed:
   ```bash
   pytestembed config
   ```
   - Set AI Provider to "LMStudio"
   - Set URL to "http://localhost:1234"
   - Test connection

## IDE Integration

### VSCode

1. Install the PyTestEmbed extension from the marketplace
2. Open a Python file with PyTestEmbed syntax
3. Enjoy syntax highlighting and live testing

### PyCharm

1. Install the PyTestEmbed plugin
2. Configure the plugin in settings
3. Use the PyTestEmbed tools in the context menu

## Troubleshooting

### Common Issues

#### "pytestembed command not found"

**Solution:** Make sure pip installed to the correct Python environment:

```bash
python -m pip install pytestembed
python -m pytestembed --version
```

#### "AI provider not available"

**Solution:** 
1. Check if Ollama/LMStudio is running
2. Verify the URL in configuration
3. Test connection in the config GUI

#### "Permission denied" errors

**Solution:** Install with user flag:

```bash
pip install --user pytestembed
```

#### Import errors

**Solution:** Reinstall with dependencies:

```bash
pip uninstall pytestembed
pip install pytestembed[all]
```

### Getting Help

If you encounter issues:

1. Check the [troubleshooting guide](troubleshooting.md)
2. Search [GitHub Issues](https://github.com/pytestembed/pytestembed/issues)
3. Ask in [GitHub Discussions](https://github.com/pytestembed/pytestembed/discussions)
4. Join our community chat

## Next Steps

- Read the [Tutorial](tutorial.md) to learn PyTestEmbed syntax
- Explore [Examples](examples/) for real-world usage
- Configure [AI Integration](ai-integration.md) for smart generation
- Set up [IDE Integration](ide-integration.md) for the best experience

## System Requirements

### Minimum Requirements
- Python 3.8+
- 100MB disk space
- 512MB RAM

### Recommended Requirements
- Python 3.10+
- 1GB disk space (for AI models)
- 4GB RAM
- SSD storage
- Internet connection (for AI features)

### Supported Platforms
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 18.04+, CentOS 7+)

## Environment Variables

PyTestEmbed respects these environment variables:

```bash
# AI Provider URLs
export PYTESTEMBED_OLLAMA_URL="http://localhost:11434"
export PYTESTEMBED_LMSTUDIO_URL="http://localhost:1234"

# Default models
export PYTESTEMBED_OLLAMA_MODEL="codellama"
export PYTESTEMBED_LMSTUDIO_MODEL="qwen-14b"

# Cache directory
export PYTESTEMBED_CACHE_DIR="~/.pytestembed/cache"

# Enable verbose logging
export PYTESTEMBED_VERBOSE=1
```

## Docker Installation

```dockerfile
FROM python:3.10-slim

RUN pip install pytestembed

# Optional: Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

WORKDIR /app
COPY . .

CMD ["pytestembed", "run", "*.py"]
```

## Uninstallation

```bash
pip uninstall pytestembed

# Remove configuration (optional)
rm -rf ~/.pytestembed
```
