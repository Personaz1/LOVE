#!/usr/bin/env python3
"""
File Agent - Dynamic interface modification system
Allows the AI to read, edit, and create files for live interface adaptation
"""
import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FileAgent:
    """Agent for file system operations with safety constraints"""
    
    def __init__(self, base_path: str = "/Users/stefan/FAMILY"):
        self.base_path = Path(base_path)
        self.allowed_extensions = {
            '.py', '.js', '.css', '.html', '.json', '.md', '.txt', '.yml', '.yaml'
        }
        self.allowed_directories = {
            'static', 'templates', 'prompts', 'memory', 'scripts', 'tests'
        }
        self.backup_dir = self.base_path / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    def _is_safe_path(self, file_path: Path) -> bool:
        """Check if file path is safe to operate on"""
        try:
            # Resolve to absolute path
            abs_path = file_path.resolve()
            base_abs = self.base_path.resolve()
            
            # Must be within base directory
            if not str(abs_path).startswith(str(base_abs)):
                return False
                
            # Check extension
            if abs_path.suffix not in self.allowed_extensions:
                return False
                
            # Check if in allowed directory
            for part in abs_path.parts:
                if part in self.allowed_directories:
                    return True
                    
            return False
            
        except Exception:
            return False
    
    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create backup of file before modification"""
        try:
            if not file_path.exists():
                return None
                
            backup_path = self.backup_dir / f"{file_path.name}.backup"
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def read_file(self, file_path: str) -> Dict[str, any]:
        """Read file content safely"""
        try:
            path = Path(file_path)
            if not self._is_safe_path(path):
                return {"error": "Access denied: unsafe path"}
                
            if not path.exists():
                return {"error": "File not found"}
                
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return {
                "success": True,
                "content": content,
                "path": str(path),
                "size": len(content)
            }
            
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
    
    def write_file(self, file_path: str, content: str, create_backup: bool = True) -> Dict[str, any]:
        """Write content to file safely"""
        try:
            path = Path(file_path)
            if not self._is_safe_path(path):
                return {"error": "Access denied: unsafe path"}
                
            # Create backup if requested
            backup_path = None
            if create_backup and path.exists():
                backup_path = self._create_backup(path)
                
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return {
                "success": True,
                "path": str(path),
                "backup": str(backup_path) if backup_path else None,
                "size": len(content)
            }
            
        except Exception as e:
            return {"error": f"Failed to write file: {str(e)}"}
    
    def list_files(self, directory: str = "") -> Dict[str, any]:
        """List files in directory safely"""
        try:
            dir_path = self.base_path / directory if directory else self.base_path
            
            if not self._is_safe_path(dir_path):
                return {"error": "Access denied: unsafe directory"}
                
            if not dir_path.exists() or not dir_path.is_dir():
                return {"error": "Directory not found"}
                
            files = []
            for item in dir_path.iterdir():
                if item.is_file() and self._is_safe_path(item):
                    files.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.base_path)),
                        "size": item.stat().st_size,
                        "extension": item.suffix
                    })
                    
            return {
                "success": True,
                "files": files,
                "directory": str(dir_path.relative_to(self.base_path))
            }
            
        except Exception as e:
            return {"error": f"Failed to list files: {str(e)}"}
    
    def delete_file(self, file_path: str) -> Dict[str, any]:
        """Delete file safely with backup"""
        try:
            path = Path(file_path)
            if not self._is_safe_path(path):
                return {"error": "Access denied: unsafe path"}
                
            if not path.exists():
                return {"error": "File not found"}
                
            # Create backup before deletion
            backup_path = self._create_backup(path)
            
            # Delete file
            path.unlink()
            
            return {
                "success": True,
                "path": str(path),
                "backup": str(backup_path) if backup_path else None
            }
            
        except Exception as e:
            return {"error": f"Failed to delete file: {str(e)}"}
    
    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """Get detailed file information"""
        try:
            path = Path(file_path)
            if not self._is_safe_path(path):
                return {"error": "Access denied: unsafe path"}
                
            if not path.exists():
                return {"error": "File not found"}
                
            stat = path.stat()
            
            return {
                "success": True,
                "name": path.name,
                "path": str(path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "extension": path.suffix,
                "is_readable": os.access(path, os.R_OK),
                "is_writable": os.access(path, os.W_OK)
            }
            
        except Exception as e:
            return {"error": f"Failed to get file info: {str(e)}"}
    
    def search_files(self, query: str, directory: str = "") -> Dict[str, any]:
        """Search for files containing query"""
        try:
            dir_path = self.base_path / directory if directory else self.base_path
            
            if not self._is_safe_path(dir_path):
                return {"error": "Access denied: unsafe directory"}
                
            if not dir_path.exists():
                return {"error": "Directory not found"}
                
            results = []
            for root, dirs, files in os.walk(dir_path):
                root_path = Path(root)
                
                # Skip unsafe directories
                if not self._is_safe_path(root_path):
                    continue
                    
                for file in files:
                    file_path = root_path / file
                    if self._is_safe_path(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if query.lower() in content.lower():
                                    results.append({
                                        "name": file,
                                        "path": str(file_path.relative_to(self.base_path)),
                                        "matches": content.lower().count(query.lower())
                                    })
                        except Exception:
                            continue
                            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            return {"error": f"Failed to search files: {str(e)}"}

# Global instance
file_agent = FileAgent() 