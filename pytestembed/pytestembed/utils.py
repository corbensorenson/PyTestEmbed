"""Utility functions for PyTestEmbed."""

import hashlib
import os
from pathlib import Path
from typing import Optional


def get_file_hash(file_path: str) -> str:
    """Get SHA256 hash of a file."""
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def get_cache_dir() -> Path:
    """Get the cache directory for PyTestEmbed."""
    cache_dir = Path.cwd() / '.pytestembed_cache'
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def is_file_cached(file_path: str) -> bool:
    """Check if a file is cached and up to date."""
    cache_dir = get_cache_dir()
    cache_file = cache_dir / f"{Path(file_path).name}.hash"
    
    if not cache_file.exists():
        return False
    
    with open(cache_file, 'r') as f:
        cached_hash = f.read().strip()
    
    current_hash = get_file_hash(file_path)
    return cached_hash == current_hash


def cache_file_hash(file_path: str) -> None:
    """Cache the hash of a file."""
    cache_dir = get_cache_dir()
    cache_file = cache_dir / f"{Path(file_path).name}.hash"
    
    file_hash = get_file_hash(file_path)
    with open(cache_file, 'w') as f:
        f.write(file_hash)
