"""
Unified File Management System for ΔΣ Guardian AI Client
Replaces all scattered file operations with a single, intelligent interface
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..utils.config import Config
from ..utils.error_handler import error_handler
from ..utils.logger import ai_logger

class FileManager:
    """Unified file management system"""
    
    def __init__(self):
        self.config = Config()
        self.logger = ai_logger
    
    def read(self, path: str, smart_resolve: bool = True) -> str:
        """Read file with smart path resolution"""
        try:
            resolved_path = self._resolve_path(path) if smart_resolve else path
            
            if not os.path.exists(resolved_path):
                suggestions = self._find_similar_files(path)
                return f"File not found: {path}\n\nSimilar files found:\n{suggestions}"
            
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.log_success(f"Read file: {resolved_path} ({len(content)} chars)")
            return content
            
        except Exception as e:
            return error_handler.handle_file_error(e, "read", path)
    
    def write(self, path: str, content: str) -> bool:
        """Write content to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.log_success(f"Wrote file: {path} ({len(content)} chars)")
            return True
            
        except Exception as e:
            error_handler.handle_file_error(e, "write", path)
            return False
    
    def edit(self, path: str, content: str) -> bool:
        """Edit existing file"""
        try:
            if not os.path.exists(path):
                return self.write(path, content)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.log_success(f"Edited file: {path}")
            return True
            
        except Exception as e:
            error_handler.handle_file_error(e, "edit", path)
            return False
    
    def delete(self, path: str) -> bool:
        """Delete file"""
        try:
            if os.path.exists(path):
                os.remove(path)
                self.logger.log_success(f"Deleted file: {path}")
                return True
            else:
                return False
                
        except Exception as e:
            error_handler.handle_file_error(e, "delete", path)
            return False
    
    def list(self, directory: str = "") -> str:
        """List files in directory"""
        try:
            if not directory:
                directory = "."
            
            if not os.path.exists(directory):
                return f"Directory not found: {directory}"
            
            files = []
            for root, dirs, filenames in os.walk(directory):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
                
                for filename in filenames:
                    if not filename.startswith('.'):
                        rel_path = os.path.relpath(os.path.join(root, filename), directory)
                        files.append(rel_path)
            
            if not files:
                return f"No files found in {directory}"
            
            result = f"Files in {directory}:\n" + "\n".join(sorted(files))
            self.logger.log_success(f"Listed {len(files)} files in {directory}")
            return result
            
        except Exception as e:
            return error_handler.handle_file_error(e, "list", directory)
    
    def search(self, query: str) -> str:
        """Search for files containing query"""
        try:
            results = []
            query_lower = query.lower()
            
            # Search in key directories
            search_dirs = [
                ".", "guardian_sandbox", "memory", "prompts", 
                "static", "templates"
            ]
            
            for directory in search_dirs:
                if os.path.exists(directory):
                    for root, dirs, files in os.walk(directory):
                        # Skip hidden directories
                        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
                        
                        for filename in files:
                            if not filename.startswith('.'):
                                file_path = os.path.join(root, filename)
                                
                                # Check filename
                                if query_lower in filename.lower():
                                    results.append(f"📁 {file_path} (filename match)")
                                    continue
                                
                                # Check file content
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                        if query_lower in content.lower():
                                            results.append(f"📄 {file_path} (content match)")
                                except:
                                    continue
            
            if not results:
                return f"No files found containing '{query}'"
            
            result = f"Search results for '{query}':\n" + "\n".join(results[:20])  # Limit results
            self.logger.log_success(f"Found {len(results)} files containing '{query}'")
            return result
            
        except Exception as e:
            return error_handler.handle_file_error(e, "search", query)
    
    def _resolve_path(self, path: str) -> str:
        """Smart path resolution"""
        if os.path.exists(path):
            return path
        
        # Try common directories
        possible_paths = [
            path,
            os.path.join("guardian_sandbox", path),
            os.path.join("memory", path),
            os.path.join("prompts", path),
            os.path.join("static", path),
            os.path.join("templates", path)
        ]
        
        for possible_path in possible_paths:
            if os.path.exists(possible_path):
                return possible_path
        
        return path  # Return original if not found
    
    def _find_similar_files(self, target_path: str) -> str:
        """Find similar files to help with path resolution"""
        try:
            similar_files = []
            target_lower = target_path.lower()
            
            # Walk through project
            for root, dirs, files in os.walk("."):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
                
                for filename in files:
                    if not filename.startswith('.'):
                        file_path = os.path.join(root, filename)
                        
                        # Check if filename contains target
                        if target_lower in filename.lower():
                            similar_files.append(f"  📁 {file_path}")
                        # Check if path contains target
                        elif target_lower in file_path.lower():
                            similar_files.append(f"  📄 {file_path}")
            
            if similar_files:
                return "\n".join(similar_files[:5])  # Top 5 matches
            else:
                return "No similar files found"
                
        except Exception as e:
            return f"Error finding similar files: {str(e)}"

# Global file manager instance
file_manager = FileManager() 