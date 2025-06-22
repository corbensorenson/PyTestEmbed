"""
Modular file watcher service for PyTestEmbed.

This service provides file watching functionality that can be used by:
- Live test runner
- Dependency graph service  
- Any other service that needs to react to file changes

The watcher is completely decoupled from testing logic and uses an event-driven architecture.
"""

import time
import asyncio
import threading
from pathlib import Path
from typing import Callable, Dict, List, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileChangeEvent:
    """Represents a file change event."""
    
    def __init__(self, file_path: str, change_type: str, timestamp: float = None):
        self.file_path = file_path
        self.change_type = change_type  # 'modified', 'created', 'deleted', 'moved'
        self.timestamp = timestamp or time.time()
    
    def __repr__(self):
        return f"FileChangeEvent(file_path='{self.file_path}', change_type='{self.change_type}')"


class FileWatcherService:
    """
    Modular file watcher service that monitors file changes and notifies subscribers.
    
    This service is completely independent of testing logic and can be used by any
    component that needs to react to file changes.
    """
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path).resolve()
        self.observer = None
        self.subscribers: Dict[str, List[Callable]] = {
            'file_changed': [],
            'file_created': [],
            'file_deleted': [],
            'file_moved': []
        }
        self.debounce_time = 1.0  # 1 second debounce
        self.last_events: Dict[str, float] = {}
        self._loop = None
        
        # Skip patterns for files/directories that should be ignored
        self.skip_patterns = {
            '__pycache__', '.git', '.pytest_cache', 'venv', 'env',
            'node_modules', '.vscode', '.pytestembed_temp', '.DS_Store',
            '*.pyc', '*.pyo', '*.pyd', '.coverage'
        }
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during monitoring."""
        file_str = str(file_path)
        return any(pattern in file_str for pattern in self.skip_patterns)
    
    def subscribe(self, event_type: str, callback: Callable[[FileChangeEvent], None]):
        """
        Subscribe to file change events.
        
        Args:
            event_type: One of 'file_changed', 'file_created', 'file_deleted', 'file_moved'
            callback: Function to call when event occurs
        """
        if event_type not in self.subscribers:
            raise ValueError(f"Invalid event type: {event_type}")
        
        self.subscribers[event_type].append(callback)
        print(f"📡 Subscribed to {event_type} events")
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from file change events."""
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            print(f"📡 Unsubscribed from {event_type} events")
    
    def _notify_subscribers(self, event_type: str, event: FileChangeEvent):
        """Notify all subscribers of a file change event."""
        for callback in self.subscribers[event_type]:
            try:
                # If we have an event loop, schedule the callback
                if self._loop and asyncio.iscoroutinefunction(callback):
                    self._loop.call_soon_threadsafe(
                        lambda: asyncio.create_task(callback(event))
                    )
                else:
                    # Synchronous callback
                    callback(event)
            except Exception as e:
                print(f"⚠️ Error in file watcher callback: {e}")
    
    def _is_debounced(self, file_path: str) -> bool:
        """Check if a file change should be debounced."""
        current_time = time.time()
        last_time = self.last_events.get(file_path, 0)
        
        if current_time - last_time < self.debounce_time:
            return True
        
        self.last_events[file_path] = current_time
        return False
    
    def start_watching(self, event_loop=None):
        """Start watching for file changes."""
        self._loop = event_loop
        
        class PyTestEmbedFileHandler(FileSystemEventHandler):
            def __init__(self, watcher_service):
                self.watcher = watcher_service
            
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                file_path = Path(event.src_path)
                
                # Skip non-Python files and excluded patterns
                if not file_path.suffix == '.py' or self.watcher.should_skip_file(file_path):
                    return
                
                # Check if file is within workspace
                try:
                    relative_path = str(file_path.relative_to(self.watcher.workspace_path))
                except ValueError:
                    # File is outside workspace
                    return
                
                # Apply debouncing
                if self.watcher._is_debounced(relative_path):
                    return
                
                print(f"📝 File watcher detected change: {relative_path}")
                
                # Create and dispatch event
                change_event = FileChangeEvent(relative_path, 'modified')
                self.watcher._notify_subscribers('file_changed', change_event)
            
            def on_created(self, event):
                if event.is_directory:
                    return
                
                file_path = Path(event.src_path)
                if not file_path.suffix == '.py' or self.watcher.should_skip_file(file_path):
                    return
                
                try:
                    relative_path = str(file_path.relative_to(self.watcher.workspace_path))
                    change_event = FileChangeEvent(relative_path, 'created')
                    self.watcher._notify_subscribers('file_created', change_event)
                except ValueError:
                    return
            
            def on_deleted(self, event):
                if event.is_directory:
                    return
                
                file_path = Path(event.src_path)
                if not file_path.suffix == '.py' or self.watcher.should_skip_file(file_path):
                    return
                
                try:
                    relative_path = str(file_path.relative_to(self.watcher.workspace_path))
                    change_event = FileChangeEvent(relative_path, 'deleted')
                    self.watcher._notify_subscribers('file_deleted', change_event)
                except ValueError:
                    return
        
        handler = PyTestEmbedFileHandler(self)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.workspace_path), recursive=True)
        self.observer.start()
        
        print(f"👀 File watcher started for {self.workspace_path}")
    
    def stop_watching(self):
        """Stop watching for file changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("👀 File watcher stopped")
    
    def is_watching(self) -> bool:
        """Check if the file watcher is currently active."""
        return self.observer is not None and self.observer.is_alive()


# Convenience function for creating a file watcher
def create_file_watcher(workspace_path: str) -> FileWatcherService:
    """Create a new file watcher service for the given workspace."""
    return FileWatcherService(workspace_path)
