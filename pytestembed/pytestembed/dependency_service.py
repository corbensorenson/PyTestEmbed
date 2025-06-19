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
from pathlib import Path
from typing import Dict, List, Optional
from .dependency_graph import CodeDependencyGraph


class DependencyService:
    """Dedicated service for dependency graph operations."""
    
    def __init__(self, workspace_path: str, port: int = 8769):
        self.workspace_path = Path(workspace_path)
        self.port = port
        self.dependency_graph = CodeDependencyGraph(workspace_path)
        self.clients = set()
        
    async def start(self):
        """Start the dependency service."""
        print(f"🔗 Starting Dependency Service on port {self.port}")
        
        # Build initial dependency graph
        self.dependency_graph.build_graph()
        
        # Start WebSocket server
        async with websockets.serve(self.handle_client, "localhost", self.port):
            print(f"✅ Dependency Service running at ws://localhost:{self.port}")
            await asyncio.Future()  # Run forever
    
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
        else:
            await self.send_error(websocket, f"Unknown command: {command}")
    
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
            
            # Create enhanced dependency info with documentation
            enhanced_dependencies = []
            for dep_id in dependencies:
                if dep_id in self.dependency_graph.elements:
                    dep_element = self.dependency_graph.elements[dep_id]
                    enhanced_dependencies.append({
                        'id': dep_id,
                        'name': dep_element.name,
                        'file_path': dep_element.file_path,
                        'line_number': dep_element.line_number,
                        'documentation': dep_element.documentation,
                        'element_type': dep_element.element_type
                    })
            
            enhanced_dependents = []
            for dep_id in dependents:
                if dep_id in self.dependency_graph.elements:
                    dep_element = self.dependency_graph.elements[dep_id]
                    enhanced_dependents.append({
                        'id': dep_id,
                        'name': dep_element.name,
                        'file_path': dep_element.file_path,
                        'line_number': dep_element.line_number,
                        'documentation': dep_element.documentation,
                        'element_type': dep_element.element_type
                    })
            
            response = {
                'type': 'dependency_info',
                'element_id': element_id,
                'element_name': element_name,
                'file_path': file_path,
                'line_number': line_number,
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
        # Try exact matches first
        candidates = [
            f"{file_path}:{element_name}",  # Global function
            f"{file_path}:Derp.{element_name}",  # Method in Derp class (common in tests)
        ]
        
        for candidate in candidates:
            if candidate in self.dependency_graph.elements:
                return candidate
        
        # Try fuzzy matching by name and file
        for element_id, element in self.dependency_graph.elements.items():
            if (element.file_path == file_path and 
                element.name == element_name and
                abs(element.line_number - line_number) <= 5):
                return element_id
        
        return None

    def _find_element_by_name(self, file_path: str, element_name: str) -> Optional[str]:
        """Find an element by file path and name (for documentation lookup)."""
        # Try exact matches first
        candidates = [
            f"{file_path}:{element_name}",  # Global function or class
            f"{file_path}:Derp.{element_name}",  # Method in Derp class
        ]

        for candidate in candidates:
            if candidate in self.dependency_graph.elements:
                return candidate

        # Try fuzzy matching by name and file
        for element_id, element in self.dependency_graph.elements.items():
            if element.file_path == file_path and element.name == element_name:
                return element_id

        return None


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
