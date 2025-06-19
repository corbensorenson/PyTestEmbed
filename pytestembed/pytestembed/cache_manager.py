"""
PyTestEmbed Cache Manager

Provides intelligent caching for parsed files, AI generations,
and test results to improve performance and reduce redundant work.
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import pickle

from .config_manager import get_config_manager


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    key: str
    data: Any
    timestamp: float
    file_hash: str
    version: str = "1.0"
    access_count: int = 0
    last_access: float = 0.0


class CacheManager:
    """Manages caching for PyTestEmbed operations."""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.cache_dir = Path(self.config_manager.config.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache subdirectories
        self.parsed_cache_dir = self.cache_dir / "parsed"
        self.ai_cache_dir = self.cache_dir / "ai_generations"
        self.test_cache_dir = self.cache_dir / "test_results"
        
        # Create subdirectories
        for cache_subdir in [self.parsed_cache_dir, self.ai_cache_dir, self.test_cache_dir]:
            cache_subdir.mkdir(exist_ok=True)
        
        # Cache settings
        self.max_cache_size_mb = 100  # Maximum cache size in MB
        self.max_cache_age_days = 7   # Maximum age for cache entries
        self.cleanup_interval = 3600  # Cleanup interval in seconds
        
        # In-memory cache for frequently accessed items
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.max_memory_entries = 100
        
        # Last cleanup time
        self.last_cleanup = time.time()
    
    def _get_file_hash(self, file_path: str) -> str:
        """Get hash of file content for cache invalidation."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.sha256(content).hexdigest()
        except Exception:
            return ""
    
    def _get_cache_key(self, category: str, identifier: str) -> str:
        """Generate cache key for given category and identifier."""
        return f"{category}_{hashlib.md5(identifier.encode()).hexdigest()}"
    
    def _get_cache_file_path(self, category: str, cache_key: str) -> Path:
        """Get file path for cache entry."""
        if category == "parsed":
            return self.parsed_cache_dir / f"{cache_key}.pkl"
        elif category == "ai":
            return self.ai_cache_dir / f"{cache_key}.pkl"
        elif category == "test":
            return self.test_cache_dir / f"{cache_key}.pkl"
        else:
            return self.cache_dir / f"{cache_key}.pkl"
    
    def _save_cache_entry(self, cache_file: Path, entry: CacheEntry) -> bool:
        """Save cache entry to disk."""
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
            return True
        except Exception as e:
            print(f"Failed to save cache entry: {e}")
            return False
    
    def _load_cache_entry(self, cache_file: Path) -> Optional[CacheEntry]:
        """Load cache entry from disk."""
        try:
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                entry = pickle.load(f)
            
            # Update access info
            entry.access_count += 1
            entry.last_access = time.time()
            
            return entry
        except Exception as e:
            print(f"Failed to load cache entry: {e}")
            return None
    
    def _is_cache_valid(self, entry: CacheEntry, file_path: str = None) -> bool:
        """Check if cache entry is still valid."""
        # Check age
        age_seconds = time.time() - entry.timestamp
        if age_seconds > (self.max_cache_age_days * 24 * 3600):
            return False
        
        # Check file hash if file path provided
        if file_path and os.path.exists(file_path):
            current_hash = self._get_file_hash(file_path)
            if current_hash != entry.file_hash:
                return False
        
        return True
    
    def get_parsed_file_cache(self, file_path: str) -> Optional[Any]:
        """Get cached parsed file data."""
        if not self.config_manager.config.cache_enabled:
            return None
        
        cache_key = self._get_cache_key("parsed", file_path)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if self._is_cache_valid(entry, file_path):
                return entry.data
            else:
                del self.memory_cache[cache_key]
        
        # Check disk cache
        cache_file = self._get_cache_file_path("parsed", cache_key)
        entry = self._load_cache_entry(cache_file)
        
        if entry and self._is_cache_valid(entry, file_path):
            # Add to memory cache
            self.memory_cache[cache_key] = entry
            self._cleanup_memory_cache()
            return entry.data
        
        return None
    
    def set_parsed_file_cache(self, file_path: str, parsed_data: Any) -> bool:
        """Cache parsed file data."""
        if not self.config_manager.config.cache_enabled:
            return False
        
        cache_key = self._get_cache_key("parsed", file_path)
        file_hash = self._get_file_hash(file_path)
        
        entry = CacheEntry(
            key=cache_key,
            data=parsed_data,
            timestamp=time.time(),
            file_hash=file_hash
        )
        
        # Save to disk
        cache_file = self._get_cache_file_path("parsed", cache_key)
        success = self._save_cache_entry(cache_file, entry)
        
        if success:
            # Add to memory cache
            self.memory_cache[cache_key] = entry
            self._cleanup_memory_cache()
        
        return success
    
    def get_ai_generation_cache(self, prompt: str, provider: str, **kwargs) -> Optional[str]:
        """Get cached AI generation result."""
        if not self.config_manager.config.cache_enabled:
            return None
        
        # Create cache identifier from prompt and parameters
        cache_id = f"{provider}_{prompt}_{json.dumps(sorted(kwargs.items()))}"
        cache_key = self._get_cache_key("ai", cache_id)
        
        # Check memory cache
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if self._is_cache_valid(entry):
                return entry.data
        
        # Check disk cache
        cache_file = self._get_cache_file_path("ai", cache_key)
        entry = self._load_cache_entry(cache_file)
        
        if entry and self._is_cache_valid(entry):
            self.memory_cache[cache_key] = entry
            self._cleanup_memory_cache()
            return entry.data
        
        return None
    
    def set_ai_generation_cache(self, prompt: str, provider: str, result: str, **kwargs) -> bool:
        """Cache AI generation result."""
        if not self.config_manager.config.cache_enabled:
            return False
        
        cache_id = f"{provider}_{prompt}_{json.dumps(sorted(kwargs.items()))}"
        cache_key = self._get_cache_key("ai", cache_id)
        
        entry = CacheEntry(
            key=cache_key,
            data=result,
            timestamp=time.time(),
            file_hash=""  # Not file-based
        )
        
        # Save to disk
        cache_file = self._get_cache_file_path("ai", cache_key)
        success = self._save_cache_entry(cache_file, entry)
        
        if success:
            self.memory_cache[cache_key] = entry
            self._cleanup_memory_cache()
        
        return success
    
    def get_test_results_cache(self, file_path: str, test_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached test results."""
        if not self.config_manager.config.cache_enabled:
            return None
        
        cache_id = f"{file_path}_{json.dumps(sorted(test_config.items()))}"
        cache_key = self._get_cache_key("test", cache_id)
        
        # Check memory cache
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if self._is_cache_valid(entry, file_path):
                return entry.data
        
        # Check disk cache
        cache_file = self._get_cache_file_path("test", cache_key)
        entry = self._load_cache_entry(cache_file)
        
        if entry and self._is_cache_valid(entry, file_path):
            self.memory_cache[cache_key] = entry
            self._cleanup_memory_cache()
            return entry.data
        
        return None
    
    def set_test_results_cache(self, file_path: str, test_config: Dict[str, Any], results: Dict[str, Any]) -> bool:
        """Cache test results."""
        if not self.config_manager.config.cache_enabled:
            return False
        
        cache_id = f"{file_path}_{json.dumps(sorted(test_config.items()))}"
        cache_key = self._get_cache_key("test", cache_id)
        file_hash = self._get_file_hash(file_path)
        
        entry = CacheEntry(
            key=cache_key,
            data=results,
            timestamp=time.time(),
            file_hash=file_hash
        )
        
        # Save to disk
        cache_file = self._get_cache_file_path("test", cache_key)
        success = self._save_cache_entry(cache_file, entry)
        
        if success:
            self.memory_cache[cache_key] = entry
            self._cleanup_memory_cache()
        
        return success
    
    def _cleanup_memory_cache(self):
        """Clean up memory cache to maintain size limits."""
        if len(self.memory_cache) <= self.max_memory_entries:
            return
        
        # Sort by last access time and remove oldest entries
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].last_access
        )
        
        # Remove oldest entries
        entries_to_remove = len(self.memory_cache) - self.max_memory_entries
        for i in range(entries_to_remove):
            key = sorted_entries[i][0]
            del self.memory_cache[key]
    
    def cleanup_cache(self, force: bool = False):
        """Clean up old and invalid cache entries."""
        current_time = time.time()
        
        # Check if cleanup is needed
        if not force and (current_time - self.last_cleanup) < self.cleanup_interval:
            return
        
        self.last_cleanup = current_time
        
        # Clean up disk cache
        for cache_subdir in [self.parsed_cache_dir, self.ai_cache_dir, self.test_cache_dir]:
            self._cleanup_directory(cache_subdir)
        
        # Clean up memory cache
        expired_keys = []
        for key, entry in self.memory_cache.items():
            if not self._is_cache_valid(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
    
    def _cleanup_directory(self, directory: Path):
        """Clean up cache files in a directory."""
        if not directory.exists():
            return
        
        current_time = time.time()
        max_age_seconds = self.max_cache_age_days * 24 * 3600
        
        for cache_file in directory.glob("*.pkl"):
            try:
                # Check file age
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > max_age_seconds:
                    cache_file.unlink()
                    continue
                
                # Load and validate entry
                entry = self._load_cache_entry(cache_file)
                if not entry or not self._is_cache_valid(entry):
                    cache_file.unlink()
                    
            except Exception as e:
                print(f"Error cleaning cache file {cache_file}: {e}")
                try:
                    cache_file.unlink()
                except:
                    pass
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "memory_cache_size": len(self.memory_cache),
            "cache_enabled": self.config_manager.config.cache_enabled,
            "cache_dir": str(self.cache_dir),
            "disk_cache_files": 0,
            "total_cache_size_mb": 0.0
        }
        
        # Count disk cache files and calculate size
        total_size = 0
        for cache_subdir in [self.parsed_cache_dir, self.ai_cache_dir, self.test_cache_dir]:
            if cache_subdir.exists():
                for cache_file in cache_subdir.glob("*.pkl"):
                    stats["disk_cache_files"] += 1
                    total_size += cache_file.stat().st_size
        
        stats["total_cache_size_mb"] = total_size / (1024 * 1024)
        
        return stats
    
    def clear_cache(self, category: str = None):
        """Clear cache entries."""
        if category:
            # Clear specific category
            if category == "parsed":
                self._clear_directory(self.parsed_cache_dir)
            elif category == "ai":
                self._clear_directory(self.ai_cache_dir)
            elif category == "test":
                self._clear_directory(self.test_cache_dir)
        else:
            # Clear all cache
            self._clear_directory(self.cache_dir)
        
        # Clear memory cache
        self.memory_cache.clear()
    
    def _clear_directory(self, directory: Path):
        """Clear all files in a directory."""
        if not directory.exists():
            return
        
        for cache_file in directory.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"Error clearing cache file {cache_file}: {e}")


# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
