"""
PyTestEmbed Performance Optimizer

Provides performance optimizations including incremental parsing,
parallel execution, memory optimization, and background processing.
"""

import os
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable, Tuple
from pathlib import Path
import queue
import weakref
import gc

from .cache_manager import get_cache_manager
from .config_manager import get_config_manager


class IncrementalParser:
    """Handles incremental parsing of modified files."""
    
    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.file_timestamps: Dict[str, float] = {}
        self.file_hashes: Dict[str, str] = {}
    
    def needs_reparsing(self, file_path: str) -> bool:
        """Check if file needs reparsing based on modification time."""
        try:
            current_mtime = os.path.getmtime(file_path)
            last_mtime = self.file_timestamps.get(file_path, 0)
            
            if current_mtime > last_mtime:
                self.file_timestamps[file_path] = current_mtime
                return True
            
            return False
        except OSError:
            return True  # File doesn't exist or can't be accessed
    
    def get_modified_functions(self, file_path: str, new_content: str, old_parsed_data: Any) -> List[str]:
        """Get list of functions that have been modified."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated AST diffing
        modified_functions = []
        
        try:
            # Compare line counts and basic structure
            old_lines = str(old_parsed_data).split('\n') if old_parsed_data else []
            new_lines = new_content.split('\n')
            
            # Simple heuristic: if line count changed significantly, reparse everything
            if abs(len(new_lines) - len(old_lines)) > 10:
                return ["*"]  # Indicates full reparse needed
            
            # More sophisticated diffing would go here
            # For now, return empty list (no incremental parsing)
            return []
            
        except Exception:
            return ["*"]  # Full reparse on error
    
    def parse_incrementally(self, file_path: str, parser_func: Callable) -> Any:
        """Parse file incrementally if possible."""
        # Check cache first
        cached_data = self.cache_manager.get_parsed_file_cache(file_path)
        
        if cached_data and not self.needs_reparsing(file_path):
            return cached_data
        
        # File needs reparsing
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if we can do incremental parsing
            if cached_data:
                modified_functions = self.get_modified_functions(file_path, content, cached_data)
                
                if modified_functions and "*" not in modified_functions:
                    # TODO: Implement incremental parsing for specific functions
                    # For now, fall back to full parsing
                    pass
            
            # Full parsing
            parsed_data = parser_func(content)
            
            # Cache the result
            self.cache_manager.set_parsed_file_cache(file_path, parsed_data)
            
            return parsed_data
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None


class ParallelExecutor:
    """Handles parallel execution of tests and AI generation."""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.max_workers = min(multiprocessing.cpu_count(), 8)
        self.ai_semaphore = threading.Semaphore(2)  # Limit concurrent AI requests
    
    def execute_tests_parallel(self, test_tasks: List[Tuple[str, Callable, Any]]) -> Dict[str, Any]:
        """Execute multiple test tasks in parallel."""
        results = {}
        
        if len(test_tasks) <= 1:
            # Single task, execute directly
            for task_id, func, args in test_tasks:
                results[task_id] = func(args)
            return results
        
        # Parallel execution
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(func, args): task_id 
                for task_id, func, args in test_tasks
            }
            
            for future in as_completed(future_to_task):
                task_id = future_to_task[future]
                try:
                    results[task_id] = future.result(timeout=30)
                except Exception as e:
                    results[task_id] = {"error": str(e)}
        
        return results
    
    def generate_ai_content_parallel(self, ai_tasks: List[Tuple[str, Callable, Any]]) -> Dict[str, Any]:
        """Generate AI content in parallel with rate limiting."""
        results = {}
        
        def ai_task_wrapper(task_id: str, func: Callable, args: Any) -> Tuple[str, Any]:
            with self.ai_semaphore:  # Rate limit AI requests
                try:
                    result = func(args)
                    return task_id, result
                except Exception as e:
                    return task_id, {"error": str(e)}
        
        if len(ai_tasks) <= 1:
            # Single task
            for task_id, func, args in ai_tasks:
                _, result = ai_task_wrapper(task_id, func, args)
                results[task_id] = result
            return results
        
        # Parallel execution with rate limiting
        with ThreadPoolExecutor(max_workers=min(len(ai_tasks), 3)) as executor:
            futures = [
                executor.submit(ai_task_wrapper, task_id, func, args)
                for task_id, func, args in ai_tasks
            ]
            
            for future in as_completed(futures):
                try:
                    task_id, result = future.result(timeout=120)
                    results[task_id] = result
                except Exception as e:
                    # Handle timeout or other errors
                    results[f"error_{len(results)}"] = {"error": str(e)}
        
        return results
    
    def process_files_parallel(self, file_paths: List[str], processor_func: Callable) -> Dict[str, Any]:
        """Process multiple files in parallel."""
        results = {}
        
        if len(file_paths) <= 1:
            # Single file
            for file_path in file_paths:
                results[file_path] = processor_func(file_path)
            return results
        
        # Parallel processing
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(processor_func, file_path): file_path 
                for file_path in file_paths
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    results[file_path] = future.result(timeout=60)
                except Exception as e:
                    results[file_path] = {"error": str(e)}
        
        return results


class MemoryOptimizer:
    """Optimizes memory usage for large codebases."""
    
    def __init__(self):
        self.weak_references: Dict[str, weakref.ref] = {}
        self.memory_threshold_mb = 500  # Trigger cleanup at 500MB
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # Fallback if psutil not available
            return 0.0
    
    def should_cleanup(self) -> bool:
        """Check if memory cleanup is needed."""
        current_time = time.time()
        memory_usage = self.get_memory_usage_mb()
        
        return (
            memory_usage > self.memory_threshold_mb or
            (current_time - self.last_cleanup) > self.cleanup_interval
        )
    
    def cleanup_memory(self):
        """Perform memory cleanup."""
        # Clean up weak references
        dead_refs = []
        for key, ref in self.weak_references.items():
            if ref() is None:
                dead_refs.append(key)
        
        for key in dead_refs:
            del self.weak_references[key]
        
        # Force garbage collection
        gc.collect()
        
        self.last_cleanup = time.time()
    
    def register_object(self, key: str, obj: Any):
        """Register object with weak reference for memory management."""
        self.weak_references[key] = weakref.ref(obj)
        
        if self.should_cleanup():
            self.cleanup_memory()
    
    def get_object(self, key: str) -> Optional[Any]:
        """Get object from weak reference."""
        ref = self.weak_references.get(key)
        if ref:
            return ref()
        return None
    
    def optimize_large_file_processing(self, file_path: str, chunk_size: int = 1000) -> bool:
        """Optimize processing of large files by chunking."""
        try:
            file_size = os.path.getsize(file_path)
            # If file is larger than 1MB, consider chunking
            return file_size > (1024 * 1024)
        except OSError:
            return False


class BackgroundProcessor:
    """Handles background processing tasks."""
    
    def __init__(self):
        self.task_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        self.results: Dict[str, Any] = {}
        self.callbacks: Dict[str, Callable] = {}
    
    def start(self):
        """Start background processing."""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def stop(self):
        """Stop background processing."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _worker_loop(self):
        """Main worker loop for background processing."""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:  # Shutdown signal
                    break
                
                task_id, func, args, callback = task
                
                try:
                    result = func(args)
                    self.results[task_id] = result
                    
                    if callback:
                        callback(task_id, result)
                        
                except Exception as e:
                    error_result = {"error": str(e)}
                    self.results[task_id] = error_result
                    
                    if callback:
                        callback(task_id, error_result)
                
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Background processor error: {e}")
    
    def submit_task(self, task_id: str, func: Callable, args: Any, callback: Callable = None):
        """Submit task for background processing."""
        if not self.running:
            self.start()
        
        self.task_queue.put((task_id, func, args, callback))
    
    def get_result(self, task_id: str) -> Optional[Any]:
        """Get result of background task."""
        return self.results.get(task_id)
    
    def is_task_complete(self, task_id: str) -> bool:
        """Check if task is complete."""
        return task_id in self.results
    
    def wait_for_task(self, task_id: str, timeout: float = 30) -> Optional[Any]:
        """Wait for task completion and return result."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_task_complete(task_id):
                return self.get_result(task_id)
            time.sleep(0.1)
        
        return None


class PerformanceMonitor:
    """Monitors and reports performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.start_times: Dict[str, float] = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """End timing and record duration."""
        if operation not in self.start_times:
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append(duration)
        del self.start_times[operation]
        
        return duration
    
    def get_average_time(self, operation: str) -> float:
        """Get average time for an operation."""
        times = self.metrics.get(operation, [])
        return sum(times) / len(times) if times else 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        report = {}
        
        for operation, times in self.metrics.items():
            if times:
                report[operation] = {
                    "count": len(times),
                    "total_time": sum(times),
                    "average_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
        
        return report
    
    def clear_metrics(self):
        """Clear all performance metrics."""
        self.metrics.clear()
        self.start_times.clear()


# Global instances
_incremental_parser = None
_parallel_executor = None
_memory_optimizer = None
_background_processor = None
_performance_monitor = None

def get_incremental_parser() -> IncrementalParser:
    """Get global incremental parser instance."""
    global _incremental_parser
    if _incremental_parser is None:
        _incremental_parser = IncrementalParser()
    return _incremental_parser

def get_parallel_executor() -> ParallelExecutor:
    """Get global parallel executor instance."""
    global _parallel_executor
    if _parallel_executor is None:
        _parallel_executor = ParallelExecutor()
    return _parallel_executor

def get_memory_optimizer() -> MemoryOptimizer:
    """Get global memory optimizer instance."""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer()
    return _memory_optimizer

def get_background_processor() -> BackgroundProcessor:
    """Get global background processor instance."""
    global _background_processor
    if _background_processor is None:
        _background_processor = BackgroundProcessor()
    return _background_processor

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
