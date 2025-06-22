"""Command-line interface for PyTestEmbed."""

import sys
import os
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Optional

import click

from .parser import PyTestEmbedParser
from .generator import TestGenerator
from .doc_generator import DocGenerator
from .runner import TestRunner
from .converter import PythonToPyTestEmbedConverter
from .ai_integration import get_ai_manager
from .init import init_command


@click.group(invoke_without_command=True)
@click.option('--test', 'run_test', is_flag=True, help='Run embedded tests (shortcut)')
@click.argument('file_path', required=False)
@click.pass_context
def cli(ctx, run_test, file_path):
    """PyTestEmbed - Embedded Testing and Documentation Framework"""
    # Handle direct --test flag for VSCode compatibility
    if run_test and file_path:
        # Run tests directly without subcommand
        try:
            parser = PyTestEmbedParser()
            parsed_program = parser.parse_file(file_path)
            success = run_tests(parsed_program, file_path, False, None)
            sys.exit(0 if success else 1)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    elif ctx.invoked_subcommand is None:
        # Show help if no command or options provided
        click.echo(ctx.get_help())


@cli.command()
@click.option('--test', is_flag=True, help='Run embedded tests')
@click.option('--doc', is_flag=True, help='Generate documentation')
@click.option('--convert', is_flag=True, help='Convert Python file to PyTestEmbed syntax')
@click.option('--verbose', is_flag=True, help='Verbose output')
@click.option('--output', help='Output file path')
@click.option('--ai-provider', type=click.Choice(['ollama', 'lmstudio']), help='AI provider for conversion (ollama or lmstudio)')
@click.option('--no-ai', is_flag=True, help='Disable AI assistance for conversion')
@click.argument('file_path')
def run(test, doc, convert, verbose, output, ai_provider, no_ai, file_path):
    """PyTestEmbed command-line interface.

    Process PyTestEmbed files to run tests, generate documentation, or convert existing Python files.

    Examples:
        pytestembed --test myfile.py
        pytestembed --doc myfile.py --output docs.md
        pytestembed --convert existing_file.py --output converted_file.py
        pytestembed --convert existing_file.py --ai-provider ollama
        pytestembed --test --verbose myfile.py
    """

    # Validate file exists
    if not os.path.exists(file_path):
        click.echo(f"Error: File '{file_path}' not found.", err=True)
        sys.exit(1)

    # Ensure at least one action is specified
    if not test and not doc and not convert:
        click.echo("Error: Please specify --test, --doc, or --convert", err=True)
        sys.exit(1)

    try:
        if convert:
            # Handle conversion mode
            convert_file(file_path, verbose, output, ai_provider, no_ai)
            return

        # Parse the file for test/doc operations
        parser = PyTestEmbedParser()
        if verbose:
            click.echo(f"Parsing {file_path}...")

        parsed_program = parser.parse_file(file_path)

        if test:
            success = run_tests(parsed_program, file_path, verbose, output)
            sys.exit(0 if success else 1)

        if doc:
            generate_documentation(parsed_program, file_path, verbose, output)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def run_tests(parsed_program, file_path, verbose, output):
    """Run the embedded tests using direct execution (like live runner)."""
    if verbose:
        click.echo("Running PyTestEmbed tests...")

    # Use the same approach as the live runner for consistency
    from .live_runner import LiveTestRunner

    # Create a temporary live runner just for test execution
    temp_runner = LiveTestRunner(".", port=None)  # No server needed

    # Set up the parsed program for context
    temp_runner._current_parsed_program = parsed_program

    if output:
        # For output mode, generate and save test code using the old generator
        generator = TestGenerator()
        test_code = generator.generate_tests(parsed_program)

        # Add import for the original module
        module_name = Path(file_path).stem
        if module_name.isidentifier() and not module_name[0].isdigit():
            original_code = f"from {module_name} import *\n\n"
            full_test_code = original_code + test_code
        else:
            full_test_code = test_code

        with open(output, 'w') as f:
            f.write(full_test_code)
        if verbose:
            click.echo(f"Test code saved to {output}")
        return True

    # Run tests directly using live runner logic
    import asyncio

    async def run_all_tests():
        """Run all tests in the file."""
        try:
            # Get the absolute path
            full_path = Path(file_path).resolve()

            # Run tests using the live runner's logic
            await temp_runner.run_file_tests(str(full_path))

            # Get the results from the live runner's stored results
            file_results = temp_runner.file_results.get(str(full_path))
            if not file_results:
                click.echo("No test results found")
                return True

            test_results = file_results.tests

            # Display results
            passed = 0
            failed = 0
            errors = 0

            for result in test_results:
                if result.status == 'pass':
                    passed += 1
                    if verbose:
                        click.echo(f"✅ {result.test_name}: {result.assertion}")
                elif result.status == 'fail':
                    failed += 1
                    click.echo(f"❌ {result.test_name}: {result.assertion}")
                    if result.message:
                        click.echo(f"   {result.message}")
                else:  # error
                    errors += 1
                    click.echo(f"💥 {result.test_name}: {result.assertion}")
                    if result.message:
                        click.echo(f"   {result.message}")

            # Summary
            total = passed + failed + errors
            if verbose or failed > 0 or errors > 0:
                click.echo(f"\nRan {total} tests: {passed} passed, {failed} failed, {errors} errors")

            return failed == 0 and errors == 0

        except Exception as e:
            click.echo(f"Error running tests: {e}", err=True)
            if verbose:
                import traceback
                traceback.print_exc()
            return False

    # Run the async test function
    try:
        return asyncio.run(run_all_tests())
    except Exception as e:
        click.echo(f"Error running tests: {e}", err=True)
        return False


def convert_file(file_path, verbose, output, ai_provider, no_ai):
    """Convert a Python file to PyTestEmbed syntax."""
    if verbose:
        click.echo(f"Converting {file_path} to PyTestEmbed syntax...")

    # Check AI availability
    ai_manager = get_ai_manager()
    use_ai = not no_ai and ai_manager.is_ai_available()

    if not use_ai and not no_ai:
        click.echo("Warning: No AI provider available. Conversion will use basic placeholders.")
        click.echo("To use AI assistance, ensure Ollama or LMStudio is running.")

    if use_ai and ai_provider:
        # Set the specified AI provider
        try:
            ai_manager.set_active_provider(ai_provider)
            if verbose:
                click.echo(f"Using AI provider: {ai_provider}")
        except ValueError as e:
            click.echo(f"Warning: {e}. Using default provider.")

    # Create converter
    converter = PythonToPyTestEmbedConverter(use_ai=use_ai, ai_provider=ai_provider)

    try:
        # Convert the file
        if output:
            converted_content = converter.convert_file(file_path, output)
            click.echo(f"Converted file saved to {output}")
        else:
            # Generate output filename
            input_path = Path(file_path)
            output_path = input_path.parent / f"{input_path.stem}_pytestembed{input_path.suffix}"
            converted_content = converter.convert_file(file_path, str(output_path))
            click.echo(f"Converted file saved to {output_path}")

        if verbose:
            click.echo("Conversion completed successfully!")
            if use_ai:
                click.echo("AI-generated tests and documentation have been added.")
            else:
                click.echo("Basic placeholders have been added. Consider using AI for better results.")

    except Exception as e:
        click.echo(f"Conversion failed: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def generate_documentation(parsed_program, file_path, verbose, output):
    """Generate documentation from doc blocks."""
    if verbose:
        click.echo("Generating documentation...")

    # Generate documentation
    generator = DocGenerator()
    module_name = Path(file_path).stem
    title = f"{module_name.capitalize()} Documentation"
    docs = generator.generate_docs(parsed_program, title)

    if output:
        # Save to specified file
        with open(output, 'w') as f:
            f.write(docs)
        click.echo(f"Documentation saved to {output}")
    else:
        # Print to stdout
        click.echo(docs)


def remove_test_doc_blocks(content):
    """Remove test: and doc: blocks from content for normal execution."""
    lines = content.split('\n')
    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this is a test: or doc: block
        if stripped in ['test:', 'doc:']:
            # Skip this line and all indented lines that follow
            i += 1
            if i < len(lines):
                base_indent = len(line) - len(line.lstrip())
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.strip() == '':
                        # Skip empty lines
                        i += 1
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent > base_indent:
                        # This line is part of the test/doc block, skip it
                        i += 1
                    else:
                        # This line is not part of the block, process it normally
                        break
        else:
            result_lines.append(line)
            i += 1

    return '\n'.join(result_lines)


# Add the init command to the CLI group
@cli.command()
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
def init(project_name, path, framework, ai_provider, ide, no_git, no_ci):
    """Initialize a new PyTestEmbed project with one command."""
    from .init import ProjectInitializer

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


@cli.command()
@click.option('--port', default=8765, help='Port for live test server')
@click.option('--workspace', default='.', help='Workspace directory to watch')
@click.option('--file-watcher-port', default=8767, help='Port for file watcher service')
@click.option('--dependency-port', default=8769, help='Port for dependency service')
def live(port, workspace, file_watcher_port, dependency_port):
    """Start live test server for IDE integration (requires file watcher and dependency services)."""
    import asyncio
    from .live_runner import start_live_server

    click.echo(f"🚀 Starting PyTestEmbed Live Server on port {port}")
    click.echo(f"📁 Workspace: {workspace}")
    click.echo(f"🔗 Connecting to File Watcher on port {file_watcher_port}")
    click.echo(f"🔗 Connecting to Dependency Service on port {dependency_port}")
    click.echo("Press Ctrl+C to stop")

    try:
        asyncio.run(start_live_server(workspace, port, file_watcher_port, dependency_port))
    except KeyboardInterrupt:
        click.echo("\n👋 Live server stopped")


@cli.command()
@click.option('--port', default=8767, help='Port for file watcher service')
@click.option('--workspace', default='.', help='Workspace directory to watch')
def file_watcher(port, workspace):
    """Start file watcher service."""
    import asyncio
    from .file_watcher_service import start_file_watcher_service

    click.echo(f"👀 Starting File Watcher Service on port {port}")
    click.echo(f"📁 Watching workspace: {workspace}")
    click.echo("Press Ctrl+C to stop")

    try:
        asyncio.run(start_file_watcher_service(workspace, port))
    except KeyboardInterrupt:
        click.echo("\n👋 File watcher stopped")


@cli.command()
@click.option('--port', default=8769, help='Port for dependency service')
@click.option('--workspace', default='.', help='Workspace directory')
@click.option('--file-watcher-port', default=8767, help='Port for file watcher service')
def dependency_service(port, workspace, file_watcher_port):
    """Start dependency graph service."""
    import asyncio
    from .dependency_service import main as start_dependency_service

    click.echo(f"🔗 Starting Dependency Service on port {port}")
    click.echo(f"📁 Workspace: {workspace}")
    click.echo(f"🔗 Connecting to File Watcher on port {file_watcher_port}")
    click.echo("Press Ctrl+C to stop")

    try:
        # Set up sys.argv for the dependency service main function
        import sys
        original_argv = sys.argv
        sys.argv = ['dependency_service', workspace, str(port)]
        asyncio.run(start_dependency_service())
    except KeyboardInterrupt:
        click.echo("\n👋 Dependency service stopped")
    finally:
        sys.argv = original_argv


@cli.command()
@click.option('--workspace', default='.', help='Workspace directory')
@click.option('--live-port', default=8765, help='Port for live test server')
@click.option('--file-watcher-port', default=8767, help='Port for file watcher service')
@click.option('--dependency-port', default=8769, help='Port for dependency service')
def start_all(workspace, live_port, file_watcher_port, dependency_port):
    """Start all PyTestEmbed services (file watcher, dependency service, and live test server)."""
    import asyncio
    import subprocess
    import sys
    import time

    click.echo("🚀 Starting all PyTestEmbed services...")
    click.echo(f"📁 Workspace: {workspace}")

    processes = []

    try:
        # Start file watcher service
        click.echo(f"👀 Starting File Watcher Service on port {file_watcher_port}")
        file_watcher_proc = subprocess.Popen([
            sys.executable, '-m', 'pytestembed.file_watcher_service',
            workspace, str(file_watcher_port)
        ])
        processes.append(('File Watcher', file_watcher_proc))
        time.sleep(2)  # Give it time to start

        # Start dependency service
        click.echo(f"🔗 Starting Dependency Service on port {dependency_port}")
        dependency_proc = subprocess.Popen([
            sys.executable, '-m', 'pytestembed.dependency_service',
            workspace, str(dependency_port)
        ])
        processes.append(('Dependency Service', dependency_proc))
        time.sleep(2)  # Give it time to start

        # Start live test server
        click.echo(f"🚀 Starting Live Test Server on port {live_port}")
        live_proc = subprocess.Popen([
            sys.executable, '-m', 'pytestembed.live_runner',
            workspace, str(live_port), str(file_watcher_port), str(dependency_port)
        ])
        processes.append(('Live Test Server', live_proc))

        click.echo("✅ All services started successfully!")
        click.echo("Press Ctrl+C to stop all services")

        # Wait for all processes
        while True:
            time.sleep(1)
            # Check if any process has died
            for name, proc in processes:
                if proc.poll() is not None:
                    click.echo(f"⚠️ {name} has stopped unexpectedly")
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        click.echo("\n🛑 Stopping all services...")
        for name, proc in processes:
            click.echo(f"🛑 Stopping {name}")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        click.echo("👋 All services stopped")


@cli.command()
def config():
    """Open PyTestEmbed configuration GUI."""
    try:
        from .config_gui import launch_config_gui
        click.echo("🔧 Opening PyTestEmbed configuration...")
        launch_config_gui()
    except ImportError as e:
        click.echo(f"❌ Error: Missing GUI dependencies. Install with: pip install tkinter", err=True)
    except Exception as e:
        click.echo(f"❌ Error opening configuration: {e}", err=True)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--format', 'output_format', default='text', type=click.Choice(['text', 'json']),
              help='Output format for lint results')
@click.option('--config-file', type=click.Path(exists=True), help='Linting configuration file')
def lint(path, output_format, config_file):
    """Lint PyTestEmbed files for syntax and style issues."""
    try:
        from .linter import PyTestEmbedLinter, lint_directory
        import json as json_module

        click.echo(f"🔍 Linting {path}...")

        # Load configuration if provided
        rules = None
        if config_file:
            with open(config_file, 'r') as f:
                rules = json_module.load(f)

        if Path(path).is_file():
            from .linter import lint_file
            issues = lint_file(path, rules)

            if not issues:
                click.echo("✅ No issues found!")
                return

            linter = PyTestEmbedLinter()
            linter.issues = issues
            output = linter.format_issues(output_format)
            click.echo(output)

            # Exit with error code if issues found
            summary = linter.get_issue_summary()
            if summary['error'] > 0:
                raise click.ClickException(f"Found {summary['error']} error(s)")

        else:
            results = lint_directory(path, rules=rules)

            if not results:
                click.echo("✅ No issues found in any files!")
                return

            total_issues = sum(len(issues) for issues in results.values())
            click.echo(f"Found {total_issues} issue(s) in {len(results)} file(s):")

            for file_path, issues in results.items():
                click.echo(f"\n📄 {file_path}:")
                linter = PyTestEmbedLinter()
                linter.issues = issues
                output = linter.format_issues(output_format)
                click.echo(output)

    except Exception as e:
        click.echo(f"❌ Error during linting: {e}", err=True)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--in-place', '-i', is_flag=True, help='Format files in place')
@click.option('--config-file', type=click.Path(exists=True), help='Formatting configuration file')
@click.option('--check', is_flag=True, help='Check if files are formatted without changing them')
def format(path, in_place, config_file, check):
    """Format PyTestEmbed files for consistent style."""
    try:
        from .formatter import PyTestEmbedFormatter, format_directory
        import json as json_module

        # Load configuration if provided
        config = None
        if config_file:
            with open(config_file, 'r') as f:
                config = json_module.load(f)

        if Path(path).is_file():
            formatter = PyTestEmbedFormatter()
            if config:
                formatter.configure(config)

            if check:
                with open(path, 'r') as f:
                    content = f.read()
                is_formatted = formatter.check_formatting(content)
                if is_formatted:
                    click.echo(f"✅ {path} is already formatted")
                else:
                    click.echo(f"❌ {path} needs formatting")
                    raise click.ClickException("File needs formatting")
            else:
                click.echo(f"🎨 Formatting {path}...")
                formatted = formatter.format_file(path, in_place)

                if not in_place:
                    click.echo(formatted)
                else:
                    click.echo("✅ File formatted successfully")

        else:
            click.echo(f"🎨 Formatting files in {path}...")
            results = format_directory(path, in_place=in_place, config=config)
            click.echo(f"✅ Formatted {len(results)} file(s)")

    except Exception as e:
        click.echo(f"❌ Error during formatting: {e}", err=True)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--target-version', help='Target PyTestEmbed version')
@click.option('--backup/--no-backup', default=True, help='Create backup files')
@click.option('--report-only', is_flag=True, help='Generate migration report only')
def migrate(path, target_version, backup, report_only):
    """Migrate PyTestEmbed files to newer version."""
    try:
        from .migration_tool import PyTestEmbedMigrator, generate_migration_report

        if report_only:
            click.echo(f"📊 Generating migration report for {path}...")
            report = generate_migration_report(path)

            click.echo(f"\n📈 Migration Report:")
            click.echo(f"Total files: {report['total_files']}")
            click.echo(f"PyTestEmbed files: {report['pytestembed_files']}")
            click.echo(f"Files by version: {report['files_by_version']}")
            click.echo(f"Files needing migration: {len(report['migration_needed'])}")
            click.echo(f"Up-to-date files: {len(report['up_to_date'])}")

            if report['migration_needed']:
                click.echo("\n📋 Files needing migration:")
                for item in report['migration_needed']:
                    click.echo(f"  {item['file']}: {item['current_version']} → {item['target_version']}")

            return

        migrator = PyTestEmbedMigrator()

        if Path(path).is_file():
            click.echo(f"🔄 Migrating {path}...")
            success = migrator.migrate_file(path, target_version, backup)

            if success:
                click.echo("✅ Migration completed successfully")
            else:
                raise click.ClickException("Migration failed")

        else:
            click.echo(f"🔄 Migrating files in {path}...")
            results = migrator.migrate_directory(path, target_version, backup=backup)

            successful = sum(1 for success in results.values() if success)
            total = len(results)

            click.echo(f"✅ Successfully migrated {successful}/{total} file(s)")

            if successful < total:
                click.echo("❌ Some files failed to migrate:")
                for file_path, success in results.items():
                    if not success:
                        click.echo(f"  {file_path}")

    except Exception as e:
        click.echo(f"❌ Error during migration: {e}", err=True)


@cli.command()
@click.argument('file_path')
@click.argument('line_number', type=int)
@click.option('--type', 'generation_type', default='both',
              type=click.Choice(['test', 'doc', 'both']),
              help='Type of content to generate')
@click.option('--ai-provider',
              type=click.Choice(['ollama', 'lmstudio']),
              help='AI provider for smart generation')
@click.option('--no-ai', is_flag=True, help='Disable AI and use template generation')
@click.option('--no-interactive', is_flag=True, help='Skip interactive prompts and auto-insert blocks')
@click.option('--output', help='Output file (default: modify in place)')
def generate(file_path, line_number, generation_type, ai_provider, no_ai, no_interactive, output):
    """Generate smart test and doc blocks for a function at specified line."""
    from .smart_generator import generate_smart_blocks

    click.echo(f"🧠 Generating {generation_type} blocks for {file_path}:{line_number}")

    # Generate the blocks
    effective_ai_provider = None if no_ai else ai_provider
    result = generate_smart_blocks(file_path, line_number, generation_type, effective_ai_provider)

    if 'error' in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        sys.exit(1)

    # Display generated content
    if 'test' in result:
        click.echo("\n🧪 Generated Test Block:")
        click.echo(result['test'])

    if 'doc' in result:
        click.echo("\n📚 Generated Documentation Block:")
        click.echo(result['doc'])

    # Optionally insert into file
    should_insert = output or no_interactive or click.confirm('\nInsert generated blocks into the file?')
    if should_insert:
        try:
            insert_blocks_into_file(file_path, line_number, result, output)
            target_file = output or file_path
            click.echo(f"✅ Blocks inserted into {target_file}")
        except Exception as e:
            click.echo(f"❌ Failed to insert blocks: {e}", err=True)


def insert_blocks_into_file(file_path: str, line_number: int,
                          generated_blocks: Dict[str, str],
                          output_file: Optional[str] = None):
    """Insert generated blocks into a file."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Get the function's indentation level
    function_line = lines[line_number - 1]  # line_number is 1-based
    function_indent = len(function_line) - len(function_line.lstrip())

    # Find the end of the function
    insert_line = line_number  # Start after the function definition

    # Look for the end of the function
    for i in range(line_number, len(lines)):
        line = lines[i]
        if line.strip():  # Non-empty line
            current_indent = len(line) - len(line.lstrip())
            # If we hit something at same or lower indentation, this is where we insert
            if current_indent <= function_indent:
                insert_line = i
                break
    else:
        # If we reach the end of file, insert at the end
        insert_line = len(lines)

    # Insert the generated blocks with proper indentation
    new_lines = []
    for block_type in ['test', 'doc']:
        if block_type in generated_blocks:
            block_content = generated_blocks[block_type]
            block_lines = block_content.split('\n')

            # Apply function-level indentation to each line
            indented_lines = []
            for block_line in block_lines:
                if block_line.strip():  # Non-empty line
                    # Add function indentation to the block
                    indented_line = ' ' * function_indent + block_line
                    indented_lines.append(indented_line)
                else:
                    indented_lines.append('')  # Keep empty lines as-is

            new_lines.extend(indented_lines)
            new_lines.append('')  # Add blank line after block

    # Insert into the file
    lines[insert_line:insert_line] = [line + '\n' for line in new_lines if line != '']

    # Write to output file
    target_file = output_file or file_path
    with open(target_file, 'w') as f:
        f.writelines(lines)


# Legacy main function for backward compatibility
def main():
    """Legacy main function - redirects to CLI group."""
    cli()


if __name__ == '__main__':
    cli()
