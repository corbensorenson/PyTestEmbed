"""
PyTestEmbed Migration Tool

Helps migrate between different versions of PyTestEmbed and
provides tools for upgrading syntax and features.
"""

import re
import json
import shutil
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from .parser import PyTestEmbedParser
from .formatter import PyTestEmbedFormatter
from .error_handler import get_error_handler, with_error_recovery


@dataclass
class MigrationRule:
    """Represents a migration rule."""
    version_from: str
    version_to: str
    description: str
    pattern: str
    replacement: str
    is_regex: bool = True


class PyTestEmbedMigrator:
    """Handles migration between PyTestEmbed versions."""
    
    def __init__(self):
        self.parser = PyTestEmbedParser()
        self.formatter = PyTestEmbedFormatter()
        self.error_handler = get_error_handler()
        
        # Migration rules for different versions
        self.migration_rules = self._load_migration_rules()
        
        # Current version
        self.current_version = "1.0.0"
    
    def _load_migration_rules(self) -> List[MigrationRule]:
        """Load migration rules for different versions."""
        return [
            # Example migration rules (would be expanded based on actual version changes)
            MigrationRule(
                version_from="0.1.0",
                version_to="0.2.0",
                description="Update test syntax from old format",
                pattern=r"tests:\s*\n",
                replacement="test:\n"
            ),
            MigrationRule(
                version_from="0.2.0",
                version_to="1.0.0",
                description="Update documentation format",
                pattern=r"docs:\s*\n",
                replacement="doc:\n"
            ),
            MigrationRule(
                version_from="0.9.0",
                version_to="1.0.0",
                description="Remove deprecated assert syntax",
                pattern=r"assert\s+(.+?)\s*:\s*\"(.+?)\"",
                replacement=r"\1: \"\2\""
            )
        ]
    
    @with_error_recovery(context="migrate_file", default_return=False)
    def migrate_file(self, file_path: str, target_version: str = None, 
                    backup: bool = True) -> bool:
        """Migrate a single file to target version."""
        target_version = target_version or self.current_version
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect current version
            current_version = self._detect_version(content)
            
            if current_version == target_version:
                print(f"File {file_path} is already at version {target_version}")
                return True
            
            # Create backup if requested
            if backup:
                self._create_backup(file_path)
            
            # Apply migrations
            migrated_content = self._apply_migrations(content, current_version, target_version)
            
            # Format the migrated content
            formatted_content = self.formatter.format_content(migrated_content)
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            print(f"Successfully migrated {file_path} from {current_version} to {target_version}")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, f"migrate_file_{file_path}")
            return False
    
    def migrate_directory(self, directory: str, target_version: str = None,
                         pattern: str = "*.py", backup: bool = True) -> Dict[str, bool]:
        """Migrate all PyTestEmbed files in a directory."""
        results = {}
        directory_path = Path(directory)
        
        for file_path in directory_path.rglob(pattern):
            if file_path.is_file() and self._is_pytestembed_file(str(file_path)):
                success = self.migrate_file(str(file_path), target_version, backup)
                results[str(file_path)] = success
        
        return results
    
    def _detect_version(self, content: str) -> str:
        """Detect PyTestEmbed version from file content."""
        # Look for version markers in comments
        version_pattern = r"#\s*PyTestEmbed\s+version\s*:\s*([0-9]+\.[0-9]+\.[0-9]+)"
        match = re.search(version_pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Detect version based on syntax patterns
        if "tests:" in content:
            return "0.1.0"  # Old syntax
        elif "docs:" in content:
            return "0.2.0"  # Intermediate syntax
        elif re.search(r"assert\s+.+?\s*:\s*\"", content):
            return "0.9.0"  # Pre-1.0 syntax
        elif "test:" in content or "doc:" in content:
            return "1.0.0"  # Current syntax

        # Default to current version if can't detect
        return "1.0.0"
    
    def _apply_migrations(self, content: str, from_version: str, to_version: str) -> str:
        """Apply migration rules to transform content."""
        migrated_content = content
        
        # Find migration path
        migration_path = self._find_migration_path(from_version, to_version)
        
        for step in migration_path:
            applicable_rules = [
                rule for rule in self.migration_rules
                if rule.version_from == step[0] and rule.version_to == step[1]
            ]
            
            for rule in applicable_rules:
                if rule.is_regex:
                    migrated_content = re.sub(
                        rule.pattern, rule.replacement, migrated_content
                    )
                else:
                    migrated_content = migrated_content.replace(
                        rule.pattern, rule.replacement
                    )
                
                print(f"Applied migration rule: {rule.description}")
        
        # Add version marker
        version_comment = f"# PyTestEmbed version: {to_version}\n"
        if not migrated_content.startswith("#"):
            migrated_content = version_comment + migrated_content
        
        return migrated_content
    
    def _find_migration_path(self, from_version: str, to_version: str) -> List[Tuple[str, str]]:
        """Find the migration path between versions."""
        # Simple linear migration path for now
        # In a real implementation, this would handle complex version graphs
        
        versions = ["0.1.0", "0.2.0", "0.9.0", "1.0.0"]
        
        try:
            from_idx = versions.index(from_version)
            to_idx = versions.index(to_version)
        except ValueError:
            return []
        
        if from_idx >= to_idx:
            return []  # No migration needed or downgrade not supported
        
        path = []
        for i in range(from_idx, to_idx):
            path.append((versions[i], versions[i + 1]))
        
        return path
    
    def _create_backup(self, file_path: str):
        """Create a backup of the file before migration."""
        backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"Created backup: {backup_path}")
    
    def _is_pytestembed_file(self, file_path: str) -> bool:
        """Check if file contains PyTestEmbed syntax."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for PyTestEmbed markers
            markers = ["test:", "doc:", "tests:", "docs:"]
            return any(marker in content for marker in markers)
            
        except Exception:
            return False
    
    def generate_migration_report(self, directory: str) -> Dict[str, Any]:
        """Generate a report of files that need migration."""
        report = {
            "total_files": 0,
            "pytestembed_files": 0,
            "files_by_version": {},
            "migration_needed": [],
            "up_to_date": []
        }
        
        directory_path = Path(directory)
        
        for file_path in directory_path.rglob("*.py"):
            if file_path.is_file():
                report["total_files"] += 1
                
                if self._is_pytestembed_file(str(file_path)):
                    report["pytestembed_files"] += 1
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    version = self._detect_version(content)
                    
                    if version not in report["files_by_version"]:
                        report["files_by_version"][version] = 0
                    report["files_by_version"][version] += 1
                    
                    if version != self.current_version:
                        report["migration_needed"].append({
                            "file": str(file_path),
                            "current_version": version,
                            "target_version": self.current_version
                        })
                    else:
                        report["up_to_date"].append(str(file_path))
        
        return report
    
    def validate_migration(self, file_path: str) -> Dict[str, Any]:
        """Validate that a migrated file is correct."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse the migrated file
            try:
                parsed = self.parser.parse_content(content)
                validation_result["parsed_successfully"] = True
            except Exception as e:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Parse error: {str(e)}")
            
            # Check for common migration issues
            if "tests:" in content:
                validation_result["warnings"].append("Old 'tests:' syntax found, should be 'test:'")
            
            if "docs:" in content:
                validation_result["warnings"].append("Old 'docs:' syntax found, should be 'doc:'")
            
            # Check version marker
            version = self._detect_version(content)
            if version != self.current_version:
                validation_result["warnings"].append(f"Version marker indicates {version}, expected {self.current_version}")
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"File read error: {str(e)}")
        
        return validation_result


class LegacyConverter:
    """Converts legacy Python files to PyTestEmbed format."""
    
    def __init__(self):
        self.migrator = PyTestEmbedMigrator()
    
    def convert_unittest_file(self, file_path: str, output_path: str = None) -> bool:
        """Convert unittest-based test file to PyTestEmbed format."""
        # This would be a complex conversion process
        # For now, just a placeholder
        print(f"Converting unittest file {file_path} (feature coming soon)")
        return False
    
    def convert_pytest_file(self, file_path: str, output_path: str = None) -> bool:
        """Convert pytest-based test file to PyTestEmbed format."""
        # This would be a complex conversion process
        # For now, just a placeholder
        print(f"Converting pytest file {file_path} (feature coming soon)")
        return False


def migrate_file(file_path: str, target_version: str = None, backup: bool = True) -> bool:
    """Convenience function to migrate a single file."""
    migrator = PyTestEmbedMigrator()
    return migrator.migrate_file(file_path, target_version, backup)


def migrate_project(directory: str, target_version: str = None, backup: bool = True) -> Dict[str, bool]:
    """Convenience function to migrate an entire project."""
    migrator = PyTestEmbedMigrator()
    return migrator.migrate_directory(directory, target_version, backup=backup)


def generate_migration_report(directory: str) -> Dict[str, Any]:
    """Convenience function to generate migration report."""
    migrator = PyTestEmbedMigrator()
    return migrator.generate_migration_report(directory)
