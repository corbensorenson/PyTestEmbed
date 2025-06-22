"""
File Watcher Service for PyTestEmbed

This service is responsible for monitoring file changes in the workspace
and notifying other services (live test runner and dependency graph service)
about changes that require their attention.

Architecture:
- Watches for file changes using watchdog
- Filters relevant changes (Python files, configuration files)
- Broadcasts change notifications via WebSocket to connected services
- Maintains a registry of connected services and their interests
"""

import asyncio
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable
from dataclasses import dataclass, asdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
import websockets
import websockets.server


@dataclass
class FileChangeEvent:
    """Represents a file change event."""
    file_path: str
    event_type: str  # 'modified', 'created', 'deleted'
    timestamp: float
    is_python_file: bool
    relative_path: str


@dataclass
class ServiceRegistration:
    """Represents a registered service that wants file change notifications."""
    service_name: str
    websocket: object
    file_patterns: List[str]  # File patterns this service is interested in
    port: int
    last_ping: float


class FileWatcherService:
    """Dedicated service for monitoring file changes and notifying other services."""
    
    def __init__(self, workspace_path: str, port: int = 8767):
        self.workspace_path = Path(workspace_path)
        self.port = port
        self.observer = None
        self.server = None
        self._loop = None
        
        # Service registry
        self.registered_services: Dict[str, ServiceRegistration] = {}
        self.clients = set()
        
        # File change tracking
        self.recent_changes: List[FileChangeEvent] = []
        self.max_recent_changes = 100
        
        # Skip patterns for files we don't want to watch
        self.skip_patterns = [
            '__pycache__',
            '.git',
            '.pytest_cache',
            '.pytestembed_temp',
            'node_modules',
            '.vscode',
            '.idea',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.DS_Store',
            'Thumbs.db'
        ]
        
        # Files to skip for test execution (but still track for dependency updates)
        self.skip_test_files = [
            'quick_test.py',
            'simple_dependency_test.py', 
            'test_enhanced_tooltips.py'
        ]
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped from watching."""
        file_str = str(file_path)
        
        # Check skip patterns
        for pattern in self.skip_patterns:
            if pattern in file_str:
                return True
        
        # Skip temporary files
        if file_path.name.startswith('.') and file_path.suffix in ['.tmp', '.swp', '.swo']:
            return True
            
        return False
    
    def _is_python_file(self, file_path: Path) -> bool:
        """Check if a file is a Python file."""
        return file_path.suffix == '.py'
    
    async def start_server(self):
        """Start the WebSocket server for service communication."""
        print(f"🔗 Starting File Watcher Service on port {self.port}")
        
        async def handle_client(websocket, path):
            await self.handle_client_connection(websocket, path)
        
        self.server = await websockets.serve(handle_client, "localhost", self.port)
        print(f"✅ File Watcher Service running at ws://localhost:{self.port}")
    
    async def handle_client_connection(self, websocket, path):
        """Handle new client connections."""
        self.clients.add(websocket)
        print(f"📡 New client connected to File Watcher Service")
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print(f"📡 Client disconnected from File Watcher Service")
        finally:
            self.clients.discard(websocket)
            # Remove from service registry if it was registered
            to_remove = []
            for service_name, registration in self.registered_services.items():
                if registration.websocket == websocket:
                    to_remove.append(service_name)
            for service_name in to_remove:
                del self.registered_services[service_name]
                print(f"🔌 Unregistered service: {service_name}")
    
    async def handle_message(self, websocket, message):
        """Handle incoming messages from clients."""
        try:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'register_service':
                await self.register_service(websocket, data)
            elif command == 'unregister_service':
                await self.unregister_service(websocket, data)
            elif command == 'get_recent_changes':
                await self.send_recent_changes(websocket, data)
            elif command == 'ping':
                await self.handle_ping(websocket, data)
            elif command == 'get_registered_services':
                await self.send_registered_services(websocket)
            else:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Unknown command: {command}'
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON message'
            }))
        except Exception as e:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Error handling message: {str(e)}'
            }))
    
    async def register_service(self, websocket, data):
        """Register a service for file change notifications."""
        service_name = data.get('service_name')
        file_patterns = data.get('file_patterns', ['*.py'])
        port = data.get('port', 0)
        
        if not service_name:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'service_name is required'
            }))
            return
        
        registration = ServiceRegistration(
            service_name=service_name,
            websocket=websocket,
            file_patterns=file_patterns,
            port=port,
            last_ping=time.time()
        )
        
        self.registered_services[service_name] = registration
        
        await websocket.send(json.dumps({
            'type': 'service_registered',
            'service_name': service_name,
            'file_patterns': file_patterns,
            'timestamp': time.time()
        }))
        
        print(f"✅ Registered service: {service_name} (patterns: {file_patterns})")
    
    async def unregister_service(self, websocket, data):
        """Unregister a service."""
        service_name = data.get('service_name')
        
        if service_name in self.registered_services:
            del self.registered_services[service_name]
            await websocket.send(json.dumps({
                'type': 'service_unregistered',
                'service_name': service_name,
                'timestamp': time.time()
            }))
            print(f"🔌 Unregistered service: {service_name}")
        else:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Service {service_name} not found'
            }))
    
    async def send_recent_changes(self, websocket, data):
        """Send recent file changes to a client."""
        limit = data.get('limit', 50)
        recent = self.recent_changes[-limit:] if limit > 0 else self.recent_changes
        
        await websocket.send(json.dumps({
            'type': 'recent_changes',
            'changes': [asdict(change) for change in recent],
            'timestamp': time.time()
        }))
    
    async def handle_ping(self, websocket, data):
        """Handle ping from registered services."""
        service_name = data.get('service_name')
        
        if service_name in self.registered_services:
            self.registered_services[service_name].last_ping = time.time()
            await websocket.send(json.dumps({
                'type': 'pong',
                'service_name': service_name,
                'timestamp': time.time()
            }))
        else:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Service {service_name} not registered'
            }))
    
    async def send_registered_services(self, websocket):
        """Send list of registered services."""
        services = []
        for name, registration in self.registered_services.items():
            services.append({
                'service_name': name,
                'file_patterns': registration.file_patterns,
                'port': registration.port,
                'last_ping': registration.last_ping
            })
        
        await websocket.send(json.dumps({
            'type': 'registered_services',
            'services': services,
            'timestamp': time.time()
        }))

    def start_file_watcher(self):
        """Start watching for file changes."""
        class FileChangeHandler(FileSystemEventHandler):
            def __init__(self, watcher_service):
                self.watcher_service = watcher_service

            def on_modified(self, event):
                if not event.is_directory:
                    self._handle_file_event(event.src_path, 'modified')

            def on_created(self, event):
                if not event.is_directory:
                    self._handle_file_event(event.src_path, 'created')

            def on_deleted(self, event):
                if not event.is_directory:
                    self._handle_file_event(event.src_path, 'deleted')

            def _handle_file_event(self, file_path, event_type):
                try:
                    # Ensure both paths are absolute for comparison
                    src_path = Path(file_path).resolve()
                    workspace_path = Path(self.watcher_service.workspace_path).resolve()

                    # Check if the file is within the workspace
                    if workspace_path in src_path.parents or src_path == workspace_path:
                        # Skip files we don't want to watch
                        if self.watcher_service._should_skip_file(src_path):
                            return

                        relative_path = str(src_path.relative_to(workspace_path))
                        is_python_file = self.watcher_service._is_python_file(src_path)

                        print(f"📝 File {event_type}: {relative_path}")

                        # Create file change event
                        change_event = FileChangeEvent(
                            file_path=str(src_path),
                            event_type=event_type,
                            timestamp=time.time(),
                            is_python_file=is_python_file,
                            relative_path=relative_path
                        )

                        # Add to recent changes
                        self.watcher_service.recent_changes.append(change_event)
                        if len(self.watcher_service.recent_changes) > self.watcher_service.max_recent_changes:
                            self.watcher_service.recent_changes.pop(0)

                        # Schedule notification to registered services
                        if hasattr(self.watcher_service, '_loop') and self.watcher_service._loop:
                            self.watcher_service._loop.call_soon_threadsafe(
                                lambda: asyncio.create_task(
                                    self.watcher_service.notify_services(change_event)
                                )
                            )

                except (ValueError, OSError) as e:
                    print(f"Error processing file change for {file_path}: {e}")

        handler = FileChangeHandler(self)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.workspace_path), recursive=True)
        self.observer.start()
        print(f"👀 Watching for changes in {self.workspace_path}")

    async def notify_services(self, change_event: FileChangeEvent):
        """Notify registered services about file changes."""
        # Determine which services should be notified based on file patterns
        interested_services = []

        for service_name, registration in self.registered_services.items():
            # Check if this service is interested in this file
            should_notify = False

            for pattern in registration.file_patterns:
                if pattern == '*':
                    should_notify = True
                    break
                elif pattern == '*.py' and change_event.is_python_file:
                    should_notify = True
                    break
                elif pattern in change_event.relative_path:
                    should_notify = True
                    break

            if should_notify:
                interested_services.append(registration)

        # Send notifications to interested services
        notification = {
            'type': 'file_change',
            'data': asdict(change_event),
            'skip_test_execution': any(skip_file in change_event.relative_path
                                     for skip_file in self.skip_test_files)
        }

        for registration in interested_services:
            try:
                await registration.websocket.send(json.dumps(notification))
                print(f"📤 Notified {registration.service_name} about {change_event.relative_path}")
            except Exception as e:
                print(f"⚠️ Failed to notify {registration.service_name}: {e}")
                # Remove dead connections
                if registration.service_name in self.registered_services:
                    del self.registered_services[registration.service_name]

    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients."""
        if self.clients:
            dead_clients = set()
            for client in self.clients:
                try:
                    await client.send(json.dumps(message))
                except Exception:
                    dead_clients.add(client)

            # Remove dead clients
            for client in dead_clients:
                self.clients.discard(client)

    async def run(self):
        """Run the file watcher service."""
        # Store the event loop for file watcher
        self._loop = asyncio.get_running_loop()

        # Start file watcher
        self.start_file_watcher()

        # Start WebSocket server
        await self.start_server()

        # Keep running
        try:
            await self.server.wait_closed()
        except KeyboardInterrupt:
            print("\n🛑 Stopping File Watcher Service...")
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()

    def stop(self):
        """Stop the file watcher service."""
        if self.server:
            self.server.close()
        if self.observer:
            self.observer.stop()


# CLI command for starting file watcher service
async def start_file_watcher_service(workspace: str = ".", port: int = 8767):
    """Start the file watcher service."""
    service = FileWatcherService(workspace, port)
    await service.run()


if __name__ == "__main__":
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8767

    asyncio.run(start_file_watcher_service(workspace, port))
