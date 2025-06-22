#!/usr/bin/env python3
"""
Dedicated Dependency Service for PyTestEmbed

This service only handles dependency graph operations and navigation,
separate from test execution to avoid message conflicts.
"""

import asyncio
import websockets
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from .dependency_graph import CodeDependencyGraph
from .file_watcher_service import FileWatcherService, FileChangeEvent


class DependencyService:
    """Dedicated service for dependency graph operations."""
    
    def __init__(self, workspace_path: str, port: int = 8769):
        self.workspace_path = Path(workspace_path)
        self.port = port
        self.dependency_graph = CodeDependencyGraph(workspace_path)
        self.clients = set()

        # File watcher will be added later - for now focus on dynamic discovery
        self.file_watcher = None
        
    async def start(self):
        """Start the dependency service."""
        print(f"🔗 Starting Dependency Service on port {self.port}")

        # Store the event loop for file watcher
        self._loop = asyncio.get_running_loop()

        # Perform dynamic project discovery and build dependency graph
        await self.discover_and_build_graph()

        # Start WebSocket server
        try:
            async with websockets.serve(self.handle_client, "localhost", self.port):
                print(f"✅ Dependency Service running at ws://localhost:{self.port}")
                await asyncio.Future()  # Run forever
        finally:
            pass  # File watcher cleanup will be added later

    async def discover_and_build_graph(self):
        """Dynamically discover project structure and build dependency graph."""
        print(f"🔍 Discovering project structure in {self.workspace_path}")

        # Find all Python files in the workspace (respecting .pytestembedignore)
        python_files = self._discover_python_files()

        print(f"📁 Found {len(python_files)} Python files:")
        for file_path in python_files[:10]:  # Show first 10
            print(f"   📄 {file_path}")
        if len(python_files) > 10:
            print(f"   ... and {len(python_files) - 10} more files")

        # Build dependency graph with discovered files
        self.dependency_graph.build_graph()

        print(f"✅ Dependency graph built with {len(self.dependency_graph.elements)} elements")

    def _discover_python_files(self) -> List[str]:
        """Discover all Python files in the workspace, respecting .pytestembedignore."""
        python_files = []
        ignore_patterns = self._load_ignore_patterns()

        # Walk through all directories
        for root, dirs, files in os.walk(self.workspace_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d), ignore_patterns)]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.workspace_path)

                    # Check if file should be ignored
                    if not self._should_ignore(file_path, ignore_patterns):
                        python_files.append(relative_path)

        return python_files

    def _load_ignore_patterns(self) -> List[str]:
        """Load ignore patterns from .pytestembedignore file."""
        ignore_file = self.workspace_path / '.pytestembedignore'
        patterns = [
            # Default ignore patterns
            '__pycache__',
            '*.pyc',
            '.git',
            '.vscode',
            '.idea',
            'node_modules',
            '.pytest_cache',
            'venv',
            'env',
            '.env'
        ]

        if ignore_file.exists():
            try:
                with open(ignore_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
                print(f"📋 Loaded {len(patterns)} ignore patterns from .pytestembedignore")
            except Exception as e:
                print(f"⚠️ Error reading .pytestembedignore: {e}")
        else:
            print(f"📋 Using default ignore patterns (no .pytestembedignore found)")

        return patterns

    def _should_ignore(self, file_path: str, patterns: List[str]) -> bool:
        """Check if a file/directory should be ignored based on patterns."""
        import fnmatch

        # Convert to relative path for pattern matching
        try:
            relative_path = os.path.relpath(file_path, self.workspace_path)
        except ValueError:
            relative_path = file_path

        for pattern in patterns:
            if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True

        return False
    
    async def handle_client(self, websocket, path):
        """Handle a client connection."""
        self.clients.add(websocket)
        print(f"📱 Dependency client connected")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_command(websocket, data)
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Invalid JSON")
                except Exception as e:
                    await self.send_error(websocket, str(e))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            print(f"📱 Dependency client disconnected")
    
    async def handle_command(self, websocket, data: dict):
        """Handle a command from a client."""
        command = data.get('command')
        
        if command == 'get_dependencies':
            await self.send_dependency_info(
                websocket,
                data.get('file_path'),
                data.get('element_name'),
                data.get('line_number')
            )
        elif command == 'get_dependency_graph':
            await self.send_full_dependency_graph(websocket)
        elif command == 'navigate_to':
            await self.handle_navigation(
                websocket,
                data.get('file_path'),
                data.get('line_number')
            )
        elif command == 'get_element_documentation':
            await self.send_element_documentation(
                websocket,
                data.get('file_path'),
                data.get('element_name')
            )
        elif command == 'analyze_file_change':
            await self.handle_analyze_file_change(
                websocket,
                data.get('file_path')
            )
        elif command == 'get_test_impact':
            await self.handle_get_test_impact(
                websocket,
                data.get('file_path')
            )
        elif command == 'get_dependents':
            await self.handle_get_dependents(
                websocket,
                data.get('file_path'),
                data.get('element_name')
            )
        elif command == 'health_check':
            await self.handle_health_check(websocket)
        else:
            await self.send_error(websocket, f"Unknown command: {command}")

    async def on_file_changed(self, event: FileChangeEvent):
        """Callback for file change events from the modular file watcher."""
        changed_file = event.file_path
        print(f"🔗 Dependency service detected file change: {changed_file}")

        try:
            # Check if this is a structural change that requires full rebuild
            if self._is_structural_change(changed_file, event):
                print(f"🔄 Structural change detected, rebuilding dependency graph...")
                await self.discover_and_build_graph()

                # Broadcast full graph rebuild to connected clients
                await self.broadcast({
                    'type': 'dependency_graph_rebuilt',
                    'data': {
                        'trigger_file': changed_file,
                        'reason': 'structural_change',
                        'timestamp': asyncio.get_event_loop().time()
                    }
                })
            else:
                # Update dependency graph for the changed file only
                full_path = str(self.workspace_path / changed_file)
                self.dependency_graph.update_file_dependencies(full_path)

                # Broadcast incremental update to connected clients
                await self.broadcast({
                    'type': 'dependency_graph_updated',
                    'data': {
                        'changed_file': changed_file,
                        'timestamp': asyncio.get_event_loop().time()
                    }
                })

            print(f"✅ Dependency graph updated for {changed_file}")

        except Exception as e:
            print(f"⚠️ Error updating dependencies for {changed_file}: {e}")
            # On error, try full rebuild as fallback
            try:
                print(f"🔄 Attempting full rebuild as fallback...")
                await self.discover_and_build_graph()
            except Exception as rebuild_error:
                print(f"❌ Full rebuild failed: {rebuild_error}")

    def _is_structural_change(self, changed_file: str, event: FileChangeEvent) -> bool:
        """Determine if a file change represents a structural change requiring full rebuild."""
        # File creation/deletion is always structural
        if event.event_type in ['created', 'deleted']:
            return True

        # Check if the file was previously unknown to the dependency graph
        relative_path = self._get_relative_path(changed_file)
        file_elements = [
            element_id for element_id, element in self.dependency_graph.elements.items()
            if element.file_path == changed_file or element.file_path == relative_path
        ]

        # If no elements found for this file, it might be a new file or moved file
        if not file_elements:
            print(f"🔍 File {changed_file} not found in dependency graph, treating as structural change")
            return True

        # TODO: Could add more sophisticated detection here:
        # - Check if imports changed significantly
        # - Check if class/function definitions were added/removed
        # - Check if file was moved (different path but same content)

        return False

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        if self.clients:
            message_str = json.dumps(message)
            disconnected_clients = []

            for client in self.clients:
                try:
                    await client.send(message_str)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.append(client)

            # Remove disconnected clients
            for client in disconnected_clients:
                self.clients.discard(client)

    async def send_dependency_info(self, websocket, file_path: str, element_name: str, line_number: int):
        """Send dependency information for a code element."""
        try:
            print(f"🔍 Getting dependencies for {element_name} in {file_path}")
            
            # Find the element in the dependency graph
            element_id = self._find_element_by_location(file_path, element_name, line_number)
            
            if not element_id:
                # Element not found
                response = {
                    'type': 'dependency_info',
                    'element_name': element_name,
                    'file_path': file_path,
                    'line_number': line_number,
                    'dependencies': [],
                    'dependents': [],
                    'enhanced_dependencies': [],
                    'enhanced_dependents': [],
                    'error': 'Element not found in dependency graph'
                }
                await websocket.send(json.dumps(response))
                return
            
            # Get dependencies and dependents
            dependencies = self.dependency_graph.get_dependencies(element_id)
            dependents = self.dependency_graph.get_dependents(element_id)
            
            # Create enhanced dependency info with documentation and deduplication
            enhanced_dependencies = []
            seen_deps = set()
            for dep_id in dependencies:
                if dep_id in self.dependency_graph.elements:
                    dep_element = self.dependency_graph.elements[dep_id]
                    # Create a unique key for deduplication
                    dep_key = (dep_element.name, dep_element.file_path, dep_element.element_type)
                    if dep_key not in seen_deps:
                        seen_deps.add(dep_key)
                        enhanced_dependencies.append({
                            'id': dep_id,
                            'name': dep_element.name,
                            'file_path': dep_element.file_path,
                            'line_number': dep_element.line_number,
                            'documentation': dep_element.documentation,
                            'element_type': dep_element.element_type
                        })

            enhanced_dependents = []
            seen_dependents = set()
            for dep_id in dependents:
                if dep_id in self.dependency_graph.elements:
                    dep_element = self.dependency_graph.elements[dep_id]
                    # Create a unique key for deduplication
                    dep_key = (dep_element.name, dep_element.file_path, dep_element.element_type)
                    if dep_key not in seen_dependents:
                        seen_dependents.add(dep_key)
                        enhanced_dependents.append({
                            'id': dep_id,
                            'name': dep_element.name,
                            'file_path': dep_element.file_path,
                            'line_number': dep_element.line_number,
                            'documentation': dep_element.documentation,
                            'element_type': dep_element.element_type
                        })
            
            # Get the actual element to return its real line number
            found_element = self.dependency_graph.elements.get(element_id)
            actual_line_number = found_element.line_number if found_element else line_number
            actual_file_path = found_element.file_path if found_element else file_path

            response = {
                'type': 'dependency_info',
                'element_id': element_id,
                'element_name': element_name,
                'file_path': actual_file_path,
                'line_number': actual_line_number,
                'dependencies': dependencies,
                'dependents': dependents,
                'enhanced_dependencies': enhanced_dependencies,
                'enhanced_dependents': enhanced_dependents,
                'dependency_count': len(dependencies),
                'dependent_count': len(dependents)
            }
            
            await websocket.send(json.dumps(response))
            print(f"✅ Sent dependency info for {element_name}: {len(dependencies)} deps, {len(dependents)} dependents")
            
        except Exception as e:
            print(f"⚠️ Error getting dependency info: {e}")
            await self.send_error(websocket, str(e))

    async def send_element_documentation(self, websocket, file_path: str, element_name: str):
        """Send documentation for a specific element."""
        try:
            print(f"📖 Getting documentation for {element_name} in {file_path}")

            # Find the element in the dependency graph
            element_id = self._find_element_by_name(file_path, element_name)

            if not element_id:
                response = {
                    'type': 'element_documentation',
                    'element_name': element_name,
                    'file_path': file_path,
                    'documentation': None,
                    'error': 'Element not found'
                }
                await websocket.send(json.dumps(response))
                return

            element = self.dependency_graph.elements[element_id]
            response = {
                'type': 'element_documentation',
                'element_name': element_name,
                'file_path': file_path,
                'documentation': element.documentation,
                'element_type': element.element_type
            }

            await websocket.send(json.dumps(response))
            print(f"✅ Sent documentation for {element_name}: {'found' if element.documentation else 'not found'}")

        except Exception as e:
            print(f"⚠️ Error getting documentation: {e}")
            await self.send_error(websocket, str(e))

    async def send_full_dependency_graph(self, websocket):
        """Send the complete dependency graph."""
        try:
            graph_data = {
                'type': 'dependency_graph',
                'elements': {
                    element_id: {
                        'name': element.name,
                        'file_path': element.file_path,
                        'line_number': element.line_number,
                        'element_type': element.element_type,
                        'parent_class': element.parent_class,
                        'documentation': element.documentation
                    }
                    for element_id, element in self.dependency_graph.elements.items()
                },
                'edges': [
                    {
                        'from': edge.from_element,
                        'to': edge.to_element,
                        'type': edge.edge_type
                    }
                    for edge in self.dependency_graph.edges
                ]
            }
            
            await websocket.send(json.dumps(graph_data))
            print(f"✅ Sent complete dependency graph")
            
        except Exception as e:
            print(f"⚠️ Error sending dependency graph: {e}")
            await self.send_error(websocket, str(e))
    
    async def handle_navigation(self, websocket, file_path: str, line_number: int):
        """Handle navigation request."""
        try:
            response = {
                'type': 'navigation_result',
                'file_path': file_path,
                'line_number': line_number,
                'success': True
            }
            await websocket.send(json.dumps(response))
            
        except Exception as e:
            await self.send_error(websocket, str(e))
    
    async def send_error(self, websocket, error_message: str):
        """Send an error response."""
        try:
            response = {
                'type': 'error',
                'message': error_message
            }
            await websocket.send(json.dumps(response))
        except:
            pass  # Connection might be closed
    
    def _find_element_by_location(self, file_path: str, element_name: str, line_number: int) -> Optional[str]:
        """Find an element by file path, name, and approximate line number."""
        # Normalize file path - try both absolute and relative paths
        relative_path = self._get_relative_path(file_path)

        # Try exact matches with both absolute and relative paths
        candidates = [
            f"{file_path}:{element_name}",  # Global function (absolute path)
            f"{relative_path}:{element_name}",  # Global function (relative path)
        ]

        # Dynamically discover all classes in the target file and try method lookups
        discovered_classes = self._get_classes_in_file(relative_path)
        for class_name in discovered_classes:
            candidates.extend([
                f"{file_path}:{class_name}.{element_name}",
                f"{relative_path}:{class_name}.{element_name}",
            ])

        print(f"🔍 Checking candidates: {candidates}")
        for candidate in candidates:
            if candidate in self.dependency_graph.elements:
                print(f"🎯 Found element: {candidate}")
                return candidate
            else:
                print(f"❌ Candidate not found: {candidate}")

        # Try cross-file search - look for this element in any file
        print(f"🔍 Searching across all files for {element_name}")
        for element_id, element in self.dependency_graph.elements.items():
            if element.name == element_name:
                print(f"🎯 Found cross-file element: {element_id}")
                return element_id

        # Try fuzzy matching by name and file (check both absolute and relative paths)
        for element_id, element in self.dependency_graph.elements.items():
            element_file_path = element.file_path
            if ((element_file_path == file_path or element_file_path == relative_path) and
                element.name == element_name and
                abs(element.line_number - line_number) <= 5):
                print(f"🎯 Found element by fuzzy match: {element_id}")
                return element_id

        print(f"❌ Element not found: {element_name} in {file_path} (relative: {relative_path})")
        return None

    def _find_element_by_name(self, file_path: str, element_name: str) -> Optional[str]:
        """Find an element by file path and name (for documentation lookup)."""
        # Normalize file path - try both absolute and relative paths
        relative_path = self._get_relative_path(file_path)

        # Try exact matches with both absolute and relative paths
        candidates = [
            f"{file_path}:{element_name}",  # Global function or class (absolute path)
            f"{relative_path}:{element_name}",  # Global function or class (relative path)
        ]

        # Dynamically discover all classes in the target file and try method lookups
        discovered_classes = self._get_classes_in_file(relative_path)
        for class_name in discovered_classes:
            candidates.extend([
                f"{file_path}:{class_name}.{element_name}",
                f"{relative_path}:{class_name}.{element_name}",
            ])

        for candidate in candidates:
            if candidate in self.dependency_graph.elements:
                return candidate

        # Try cross-file search - look for this element in any file
        for element_id, element in self.dependency_graph.elements.items():
            if element.name == element_name:
                return element_id

        # Try fuzzy matching by name and file (check both absolute and relative paths)
        for element_id, element in self.dependency_graph.elements.items():
            element_file_path = element.file_path
            if ((element_file_path == file_path or element_file_path == relative_path) and
                element.name == element_name):
                return element_id

        return None

    def _get_classes_in_file(self, file_path: str) -> List[str]:
        """Dynamically discover all class names in the given file."""
        classes = []

        # Look through all elements in the dependency graph for classes in this file
        for element_id, element in self.dependency_graph.elements.items():
            if (element.file_path == file_path and
                element.element_type == 'class'):
                classes.append(element.name)

        print(f"🔍 Discovered classes in {file_path}: {classes}")
        return classes

    def _get_relative_path(self, file_path: str) -> str:
        """Convert absolute path to relative path from workspace root."""
        try:
            abs_path = Path(file_path)
            if abs_path.is_absolute():
                # Try to make it relative to workspace (resolve workspace path first)
                workspace_abs = self.workspace_path.resolve()
                relative = abs_path.relative_to(workspace_abs)
                result = str(relative)
                print(f"🔄 Converted {file_path} -> {result}")
                return result
            else:
                # Already relative
                print(f"🔄 Already relative: {file_path}")
                return file_path
        except ValueError as e:
            # Path is not under workspace, return as-is
            print(f"⚠️ Could not make relative: {file_path} (workspace: {self.workspace_path.resolve()}) - {e}")
            return file_path

    async def handle_analyze_file_change(self, websocket, file_path: str):
        """Handle file change analysis request from live test service."""
        try:
            # Update dependency graph for the changed file
            full_path = str(self.workspace_path / file_path)
            self.dependency_graph.update_file_dependencies(full_path)

            # Send confirmation back to the requesting service
            await websocket.send(json.dumps({
                'type': 'file_analysis_complete',
                'file_path': file_path,
                'timestamp': time.time()
            }))

            print(f"✅ Analyzed file change for {file_path}")

        except Exception as e:
            print(f"⚠️ Error analyzing file change for {file_path}: {e}")
            await self.send_error(websocket, str(e))

    async def handle_get_test_impact(self, websocket, file_path: str):
        """Handle test impact analysis request from live test service."""
        try:
            # Get files that might be affected by changes to this file
            impact_files = self.dependency_graph.get_test_impact(file_path)

            # Send impact analysis back to the requesting service
            await websocket.send(json.dumps({
                'type': 'test_impact_analysis',
                'changed_file': file_path,
                'impact_files': impact_files,
                'timestamp': time.time()
            }))

            print(f"✅ Sent test impact analysis for {file_path}: {len(impact_files)} files affected")

        except Exception as e:
            print(f"⚠️ Error getting test impact for {file_path}: {e}")
            await self.send_error(websocket, str(e))

    async def handle_get_dependents(self, websocket, file_path: str, element_name: str):
        """Handle request for dependents of a specific element."""
        try:
            # Find the element
            element_id = self._find_element_by_name(file_path, element_name)

            if not element_id:
                await websocket.send(json.dumps({
                    'type': 'dependents',
                    'file_path': file_path,
                    'element_name': element_name,
                    'dependents': [],
                    'error': 'Element not found'
                }))
                return

            # Get dependents
            dependents = self.dependency_graph.get_dependents(element_id)

            # Convert to detailed info
            dependent_info = []
            for dep_id in dependents:
                if dep_id in self.dependency_graph.elements:
                    element = self.dependency_graph.elements[dep_id]
                    dependent_info.append({
                        'file_path': element.file_path,
                        'element_name': element.name,
                        'element_type': element.element_type,
                        'line_number': element.line_number
                    })

            await websocket.send(json.dumps({
                'type': 'dependents',
                'file_path': file_path,
                'element_name': element_name,
                'dependents': dependent_info,
                'timestamp': time.time()
            }))

            print(f"✅ Sent dependents for {element_name}: {len(dependent_info)} dependents")

        except Exception as e:
            print(f"⚠️ Error getting dependents for {element_name}: {e}")
            await self.send_error(websocket, str(e))

    async def handle_health_check(self, websocket):
        """Handle health check request - lightweight status check."""
        try:
            await websocket.send(json.dumps({
                'type': 'health_check',
                'status': 'healthy',
                'service': 'dependency_service',
                'elements_count': len(self.dependency_graph.elements),
                'dependencies_count': len(self.dependency_graph.edges),
                'timestamp': time.time()
            }))
        except Exception as e:
            print(f"⚠️ Error in health check: {e}")


async def main():
    """Main entry point for the dependency service."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m pytestembed.dependency_service <workspace_path> [port]")
        sys.exit(1)
    
    workspace_path = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8769
    
    service = DependencyService(workspace_path, port)
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
