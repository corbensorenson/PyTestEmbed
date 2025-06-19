"""
PyTestEmbed Project Initialization

Provides one-command setup for new PyTestEmbed projects with:
- Project structure creation
- IDE configuration
- Example files
- CI/CD templates
- Documentation setup
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json
import click


class ProjectInitializer:
    """Handles PyTestEmbed project initialization."""
    
    def __init__(self, project_name: str, project_path: Optional[str] = None):
        self.project_name = project_name
        self.project_path = Path(project_path or project_name)
        self.templates_dir = Path(__file__).parent / "templates"
    
    def init_project(self, 
                    framework: str = "basic",
                    ai_provider: Optional[str] = None,
                    ide: str = "vscode",
                    git: bool = True,
                    ci: bool = True) -> bool:
        """Initialize a complete PyTestEmbed project."""
        
        try:
            click.echo(f"🚀 Initializing PyTestEmbed project: {self.project_name}")
            
            # Create project structure
            self._create_project_structure()
            
            # Setup configuration
            self._create_config_files(ai_provider)
            
            # Create example files based on framework
            self._create_example_files(framework)
            
            # Setup IDE configuration
            self._setup_ide_config(ide)
            
            # Initialize git repository
            if git:
                self._setup_git()
            
            # Setup CI/CD
            if ci:
                self._setup_ci_cd()
            
            # Create documentation
            self._create_documentation()
            
            # Install dependencies
            self._setup_dependencies()
            
            # Final setup steps
            self._finalize_setup()
            
            click.echo(f"✅ Project '{self.project_name}' initialized successfully!")
            self._print_next_steps()
            
            return True
            
        except Exception as e:
            click.echo(f"❌ Error initializing project: {e}", err=True)
            return False
    
    def _create_project_structure(self):
        """Create the basic project directory structure."""
        click.echo("📁 Creating project structure...")
        
        # Create main directories
        directories = [
            "",  # Root directory
            "src",
            "tests",
            "docs",
            "examples",
            ".vscode",
            ".idea",
            ".github/workflows",
            "scripts"
        ]
        
        for dir_path in directories:
            full_path = self.project_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
    
    def _create_config_files(self, ai_provider: Optional[str]):
        """Create configuration files."""
        click.echo("⚙️  Creating configuration files...")
        
        # PyTestEmbed configuration
        config = {
            "cache_enabled": True,
            "cache_dir": ".pytestembed_cache",
            "temp_dir": ".pytestembed_temp",
            "verbose": False,
            "test_timeout": 30,
            "ai_enabled": ai_provider is not None,
            "ai_provider": ai_provider or "ollama",
            "auto_generate_tests": True,
            "auto_generate_docs": True,
            "live_testing": True
        }
        
        config_path = self.project_path / ".pytestembed.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Pixi configuration
        self._create_pixi_config()
        
        # Environment file
        self._create_env_file(ai_provider)
    
    def _create_pixi_config(self):
        """Create pixi.toml for the project."""
        pixi_content = f'''[project]
name = "{self.project_name}"
version = "0.1.0"
description = "PyTestEmbed project: {self.project_name}"
authors = ["Developer <dev@example.com>"]
channels = ["conda-forge"]
platforms = ["win-64", "linux-64", "osx-64", "osx-arm64"]

[dependencies]
python = ">=3.8,<4.0"
pytestembed = "*"

[tasks]
# Development tasks
test = "python -m pytestembed --test src/ --verbose"
test-watch = "python scripts/watch_tests.py"
doc = "python -m pytestembed --doc src/ --output docs/api.md"
doc-serve = "python -m http.server 8000 --directory docs"

# Example tasks
example = "python examples/demo.py"
convert = "python -m pytestembed --convert examples/legacy.py --ai-provider ollama"

# Quality tasks
lint = "python -m flake8 src/"
format = "python -m black src/"
type-check = "python -m mypy src/"

# Setup tasks
setup = "pip install -e ."
clean = "rm -rf .pytestembed_cache .pytestembed_temp __pycache__"

[feature.dev.dependencies]
pytest = ">=7.0.0"
black = ">=22.0.0"
flake8 = ">=5.0.0"
mypy = ">=1.0.0"
watchdog = ">=2.0.0"

[environments]
default = ["dev"]
'''
        
        pixi_path = self.project_path / "pixi.toml"
        with open(pixi_path, 'w') as f:
            f.write(pixi_content)
    
    def _create_env_file(self, ai_provider: Optional[str]):
        """Create environment configuration file."""
        env_content = f'''# PyTestEmbed Environment Configuration

# AI Provider Settings
PYTESTEMBED_AI_PROVIDER={ai_provider or "ollama"}
PYTESTEMBED_OLLAMA_URL=http://localhost:11434
PYTESTEMBED_OLLAMA_MODEL=codellama
PYTESTEMBED_LMSTUDIO_URL=http://localhost:1234

# Cache Settings
PYTESTEMBED_CACHE_DIR=.pytestembed_cache
PYTESTEMBED_TEMP_DIR=.pytestembed_temp

# Development Settings
PYTESTEMBED_LIVE_TESTING=true
PYTESTEMBED_AUTO_GENERATE=true
PYTESTEMBED_VERBOSE=false
'''
        
        env_path = self.project_path / ".env"
        with open(env_path, 'w') as f:
            f.write(env_content)
    
    def _create_example_files(self, framework: str):
        """Create example files based on the chosen framework."""
        click.echo(f"📝 Creating {framework} example files...")
        
        if framework == "basic":
            self._create_basic_examples()
        elif framework == "django":
            self._create_django_examples()
        elif framework == "fastapi":
            self._create_fastapi_examples()
        elif framework == "flask":
            self._create_flask_examples()
        else:
            self._create_basic_examples()
    
    def _create_basic_examples(self):
        """Create basic Python examples."""
        # Main module example
        main_example = '''"""
Example module demonstrating PyTestEmbed syntax.
"""

def calculate_area(length: float, width: float) -> float:
    """Calculate the area of a rectangle."""
    if length < 0 or width < 0:
        raise ValueError("Dimensions must be non-negative")
    return length * width
test:
    calculate_area(5, 3) == 15: "Basic area calculation",
    calculate_area(0, 10) == 0: "Zero dimension",
    calculate_area(2.5, 4) == 10.0: "Decimal calculation"
doc:
    Calculates the area of a rectangle given length and width.
    
    Both parameters must be non-negative numbers.
    Returns the product of length and width.


class Calculator:
    """A simple calculator with history tracking."""
    
    def __init__(self):
        """Initialize calculator with empty history."""
        self.history = []
    
    def add(self, x: float, y: float) -> float:
        """Add two numbers."""
        result = x + y
        self.history.append(f"{x} + {y} = {result}")
        return result
    test:
        add(2, 3) == 5: "Basic addition",
        add(-1, 1) == 0: "Negative addition",
        add(0.1, 0.2) == 0.3: "Decimal addition"
    doc:
        Adds two numbers and records the operation in history.
        
        Returns the sum of x and y.
        Automatically logs the operation for history tracking.
    
    def get_history(self) -> list:
        """Get calculation history."""
        return self.history.copy()
    test:
        calc = Calculator()
        calc.add(1, 2)
        history = calc.get_history()
        len(history) == 1: "History should contain one entry"
    doc:
        Returns a copy of the calculation history.
        
        Each entry shows the operation and result.
        Returns a new list to prevent external modification.

test:
    # Integration test
    calc = Calculator()
    result = calc.add(10, 20)
    result == 30: "Calculator integration test"
doc:
    Example module showcasing PyTestEmbed features.
    
    Demonstrates function-level and class-level testing
    with embedded documentation.


def main():
    """Demonstrate the calculator functionality."""
    print("PyTestEmbed Example")
    print("=" * 20)
    
    # Test area calculation
    area = calculate_area(5, 3)
    print(f"Area of 5x3 rectangle: {area}")
    
    # Test calculator
    calc = Calculator()
    result = calc.add(10, 15)
    print(f"10 + 15 = {result}")
    print(f"History: {calc.get_history()}")
    
    return 0
test:
    main() == 0: "Main function should complete successfully"
doc:
    Main demonstration function.
    
    Shows basic usage of the calculator and area functions.
    Returns 0 on successful completion.


if __name__ == "__main__":
    main()
'''
        
        src_path = self.project_path / "src" / "main.py"
        with open(src_path, 'w') as f:
            f.write(main_example)
        
        # Legacy example for conversion
        legacy_example = '''"""
Legacy Python file for conversion demonstration.
"""

def factorial(n):
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def fibonacci(n):
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

class StringProcessor:
    """Process strings in various ways."""
    
    def reverse(self, text):
        """Reverse a string."""
        return text[::-1]
    
    def count_words(self, text):
        """Count words in text."""
        return len(text.split())

def main():
    """Demonstrate legacy functions."""
    print(f"Factorial of 5: {factorial(5)}")
    print(f"Fibonacci of 8: {fibonacci(8)}")
    
    processor = StringProcessor()
    print(f"Reversed 'hello': {processor.reverse('hello')}")

if __name__ == "__main__":
    main()
'''
        
        legacy_path = self.project_path / "examples" / "legacy.py"
        with open(legacy_path, 'w') as f:
            f.write(legacy_example)
    
    def _setup_ide_config(self, ide: str):
        """Setup IDE-specific configuration."""
        click.echo(f"🔧 Configuring {ide} settings...")
        
        if ide == "vscode":
            self._setup_vscode()
        elif ide == "pycharm":
            self._setup_pycharm()
        elif ide == "both":
            self._setup_vscode()
            self._setup_pycharm()
    
    def _setup_vscode(self):
        """Setup VSCode configuration."""
        # Settings
        vscode_settings = {
            "python.defaultInterpreterPath": "./venv/bin/python",
            "python.testing.pytestEnabled": False,
            "python.testing.unittestEnabled": False,
            "pytestembed.enabled": True,
            "pytestembed.autoRun": True,
            "pytestembed.showInlineResults": True,
            "files.associations": {
                "*.py": "pytestembed"
            },
            "editor.rulers": [88],
            "editor.formatOnSave": True,
            "python.formatting.provider": "black"
        }
        
        settings_path = self.project_path / ".vscode" / "settings.json"
        with open(settings_path, 'w') as f:
            json.dump(vscode_settings, f, indent=2)
        
        # Extensions recommendations
        extensions = {
            "recommendations": [
                "pytestembed.pytestembed",
                "ms-python.python",
                "ms-python.black-formatter",
                "ms-python.flake8",
                "ms-python.mypy-type-checker"
            ]
        }
        
        extensions_path = self.project_path / ".vscode" / "extensions.json"
        with open(extensions_path, 'w') as f:
            json.dump(extensions, f, indent=2)
        
        # Tasks
        tasks = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "PyTestEmbed: Run Tests",
                    "type": "shell",
                    "command": "python",
                    "args": ["-m", "pytestembed", "--test", "${file}", "--verbose"],
                    "group": "test",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "shared"
                    }
                },
                {
                    "label": "PyTestEmbed: Generate Docs",
                    "type": "shell",
                    "command": "python",
                    "args": ["-m", "pytestembed", "--doc", "${file}"],
                    "group": "build"
                },
                {
                    "label": "PyTestEmbed: Convert File",
                    "type": "shell",
                    "command": "python",
                    "args": ["-m", "pytestembed", "--convert", "${file}", "--ai-provider", "ollama"],
                    "group": "build"
                }
            ]
        }
        
        tasks_path = self.project_path / ".vscode" / "tasks.json"
        with open(tasks_path, 'w') as f:
            json.dump(tasks, f, indent=2)
    
    def _setup_git(self):
        """Initialize git repository with appropriate .gitignore."""
        click.echo("📦 Setting up Git repository...")
        
        # Initialize git
        try:
            subprocess.run(["git", "init"], cwd=self.project_path, check=True, capture_output=True)
        except subprocess.CalledProcessError:
            click.echo("⚠️  Git not available, skipping git initialization")
            return
        
        # Create .gitignore
        gitignore_content = '''# PyTestEmbed
.pytestembed_cache/
.pytestembed_temp/
*.pytestembed

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/

# Documentation
docs/_build/
'''
        
        gitignore_path = self.project_path / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
    
    def _setup_ci_cd(self):
        """Setup CI/CD workflows."""
        click.echo("🔄 Setting up CI/CD workflows...")
        
        # GitHub Actions workflow
        workflow_content = f'''name: PyTestEmbed CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v4
      with:
        python-version: ${{{{ matrix.python-version }}}}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytestembed
        pip install -r requirements.txt
    
    - name: Run PyTestEmbed tests
      run: |
        python -m pytestembed --test src/ --verbose
    
    - name: Generate documentation
      run: |
        python -m pytestembed --doc src/ --output docs/api.md
    
    - name: Upload documentation
      uses: actions/upload-artifact@v3
      with:
        name: documentation
        path: docs/
'''
        
        workflow_path = self.project_path / ".github" / "workflows" / "ci.yml"
        with open(workflow_path, 'w') as f:
            f.write(workflow_content)
    
    def _create_documentation(self):
        """Create initial documentation."""
        click.echo("📚 Creating documentation...")
        
        readme_content = f'''# {self.project_name}

A PyTestEmbed project with embedded testing and documentation.

## Quick Start

```bash
# Run tests
pixi run test

# Generate documentation
pixi run doc

# Watch for changes
pixi run test-watch
```

## Project Structure

```
{self.project_name}/
├── src/                 # Source code with embedded tests
├── examples/           # Example files and demos
├── docs/              # Generated documentation
├── scripts/           # Utility scripts
├── .pytestembed.json  # PyTestEmbed configuration
└── pixi.toml         # Project dependencies and tasks
```

## Features

- ✅ Embedded testing with `test:` blocks
- ✅ Inline documentation with `doc:` blocks  
- ✅ AI-powered test generation
- ✅ Live test execution in IDE
- ✅ Automatic documentation generation

## Development

```bash
# Setup development environment
pixi install

# Run tests with live reload
pixi run test-watch

# Format code
pixi run format

# Type checking
pixi run type-check
```

## Examples

See the `examples/` directory for:
- Basic PyTestEmbed syntax
- Framework integrations
- Conversion from legacy code

## Documentation

- [API Documentation](docs/api.md) - Generated from `doc:` blocks
- [Syntax Guide](https://pytestembed.dev/syntax) - Complete syntax reference
- [Best Practices](https://pytestembed.dev/best-practices) - Recommended patterns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests using PyTestEmbed syntax
4. Submit a pull request

## License

MIT License - see LICENSE file for details.
'''
        
        readme_path = self.project_path / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
    
    def _setup_dependencies(self):
        """Setup project dependencies."""
        click.echo("📦 Setting up dependencies...")
        
        # Requirements.txt
        requirements = '''pytestembed>=0.1.0
black>=22.0.0
flake8>=5.0.0
mypy>=1.0.0
'''
        
        req_path = self.project_path / "requirements.txt"
        with open(req_path, 'w') as f:
            f.write(requirements)
    
    def _finalize_setup(self):
        """Final setup steps."""
        click.echo("🎯 Finalizing setup...")
        
        # Create watch script for live testing
        watch_script = '''#!/usr/bin/env python3
"""
Live test watcher for PyTestEmbed.
Automatically runs tests when files change.
"""

import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PyTestEmbedHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_run = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if not event.src_path.endswith('.py'):
            return
            
        # Debounce rapid file changes
        now = time.time()
        if now - self.last_run < 1:
            return
        self.last_run = now
        
        print(f"\\n🔄 File changed: {event.src_path}")
        print("Running tests...")
        
        try:
            result = subprocess.run([
                "python", "-m", "pytestembed", 
                "--test", event.src_path, 
                "--verbose"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Tests passed!")
            else:
                print("❌ Tests failed!")
                print(result.stdout)
                print(result.stderr)
                
        except Exception as e:
            print(f"Error running tests: {e}")

def main():
    print("🚀 PyTestEmbed Live Test Watcher")
    print("Watching for changes in src/ directory...")
    print("Press Ctrl+C to stop")
    
    event_handler = PyTestEmbedHandler()
    observer = Observer()
    observer.schedule(event_handler, "src", recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\\n👋 Stopped watching")
    
    observer.join()

if __name__ == "__main__":
    main()
'''
        
        watch_path = self.project_path / "scripts" / "watch_tests.py"
        with open(watch_path, 'w') as f:
            f.write(watch_script)
        
        # Make script executable
        watch_path.chmod(0o755)
    
    def _print_next_steps(self):
        """Print next steps for the user."""
        click.echo("\n🎉 Setup Complete! Next steps:")
        click.echo(f"   cd {self.project_name}")
        click.echo("   pixi install              # Install dependencies")
        click.echo("   pixi run example          # Run example")
        click.echo("   pixi run test             # Run tests")
        click.echo("   pixi run test-watch       # Live test watching")
        click.echo("   code .                    # Open in VSCode")
        click.echo("\n📚 Learn more:")
        click.echo("   • Check out examples/ directory")
        click.echo("   • Read the generated README.md")
        click.echo("   • Visit https://pytestembed.dev for documentation")


@click.command()
@click.argument('project_name')
@click.option('--path', help='Project directory path')
@click.option('--framework', default='basic', 
              type=click.Choice(['basic', 'django', 'fastapi', 'flask']),
              help='Framework template to use')
@click.option('--ai-provider', 
              type=click.Choice(['ollama', 'lmstudio']),
              help='AI provider for code generation')
@click.option('--ide', default='vscode',
              type=click.Choice(['vscode', 'pycharm', 'both']),
              help='IDE to configure')
@click.option('--no-git', is_flag=True, help='Skip git initialization')
@click.option('--no-ci', is_flag=True, help='Skip CI/CD setup')
def init_command(project_name, path, framework, ai_provider, ide, no_git, no_ci):
    """Initialize a new PyTestEmbed project with one command."""
    
    initializer = ProjectInitializer(project_name, path)
    success = initializer.init_project(
        framework=framework,
        ai_provider=ai_provider,
        ide=ide,
        git=not no_git,
        ci=not no_ci
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    init_command()
