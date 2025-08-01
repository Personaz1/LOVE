"""
Инструменты для работы с файлами
"""

import os
import glob
from typing import Optional, Dict, Any
import mimetypes
from datetime import datetime

from ..utils.config import Config
from ..utils.logger import Logger
from ..utils.error_handler import ErrorHandler

logger = Logger()

class FileTools:
    """Класс для работы с файлами"""
    
    def __init__(self):
        """Инициализация FileTools"""
        self.config = Config()
        self.error_handler = ErrorHandler()
        self.project_root = self.config.get_project_root()
    
    def read_file(self, path: str) -> str:
        """Чтение файла"""
        try:
            if path.startswith('/'):
                # Если передан абсолютный путь, конвертируем в относительный
                path = path.lstrip('/')
                full_path = os.path.join(self.project_root, path)
            else:
                # Относительный путь
                full_path = os.path.join(self.project_root, path)
            
            # Безопасность: убеждаемся что файл в пределах проекта
            full_path = os.path.abspath(full_path)
            if not full_path.startswith(self.project_root):
                logger.error(f"Access denied: File {path} is outside project directory")
                return "❌ Access denied: File is outside project directory"
            
            if not os.path.exists(full_path):
                # Пробуем найти похожие файлы
                similar_files = self._find_similar_files(path)
                if similar_files:
                    return f"❌ File not found: {path}\n\nSimilar files found:\n{similar_files}"
                else:
                    return f"❌ File not found: {path}"
            
            # Определяем кодировку
            encoding = 'utf-8'
            try:
                with open(full_path, 'r', encoding=encoding) as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Пробуем другие кодировки
                for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        with open(full_path, 'r', encoding=enc) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    return f"❌ Cannot read file {path}: encoding issues"
            
            return content
            
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return f"❌ Error reading file: {str(e)}"
    
    def write_file(self, path: str, content: str) -> bool:
        """Запись содержимого в файл"""
        try:
            # Безопасность: разрешаем доступ только к директории проекта
            full_path = os.path.abspath(path)
            
            # Убеждаемся что путь в пределах директории проекта
            if not full_path.startswith(self.project_root):
                logger.error(f"Access denied: Path {path} is outside project directory")
                return False
            
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"📝 Wrote file: {path} ({len(content)} chars)")
            return True
            
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            return False
    
    def create_file(self, path: str, content: str = "") -> bool:
        """Создание нового файла"""
        try:
            # Безопасность: разрешаем доступ только к директории проекта
            full_path = os.path.abspath(path)
            
            # Убеждаемся что путь в пределах директории проекта
            if not full_path.startswith(self.project_root):
                logger.error(f"Access denied: Path {path} is outside project directory")
                return False
            
            # Проверяем существует ли файл
            if os.path.exists(full_path):
                logger.warning(f"File already exists: {path}")
                return False
            
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✨ Created file: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating file {path}: {e}")
            return False
    
    def edit_file(self, path: str, content: str) -> bool:
        """Редактирование существующего файла"""
        try:
            # Безопасность: разрешаем доступ только к директории проекта
            full_path = os.path.abspath(path)
            
            # Убеждаемся что путь в пределах директории проекта
            if not full_path.startswith(self.project_root):
                logger.error(f"Access denied: Path {path} is outside project directory")
                return False
            
            # Проверяем существует ли файл
            if not os.path.exists(full_path):
                logger.error(f"File not found: {path}")
                return False
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✏️ Edited file: {path} ({len(content)} chars)")
            return True
            
        except Exception as e:
            logger.error(f"Error editing file {path}: {e}")
            return False
    
    def list_files(self, directory: str = "") -> str:
        """Список файлов в директории"""
        try:
            if not directory:
                directory = self.project_root
            elif directory.startswith('/'):
                # Если передан абсолютный путь, конвертируем в относительный
                directory = directory.lstrip('/')
                if directory == "":
                    directory = self.project_root
                else:
                    directory = os.path.join(self.project_root, directory)
            else:
                # Относительный путь
                directory = os.path.join(self.project_root, directory)
            
            # Безопасность: убеждаемся что директория в пределах проекта
            full_path = os.path.abspath(directory)
            if not full_path.startswith(self.project_root):
                logger.error(f"Access denied: Directory {directory} is outside project directory")
                return "❌ Access denied: Directory is outside project"
            
            if not os.path.exists(full_path):
                return f"❌ Directory not found: {directory}"
            
            files = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    files.append(f"📄 {item} ({size} bytes)")
                elif os.path.isdir(item_path):
                    files.append(f"📁 {item}/")
            
            if not files:
                return f"📂 Directory {directory} is empty"
            
            return f"📂 Contents of {directory}:\n" + "\n".join(files)
            
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {e}")
            return f"❌ Error listing files: {str(e)}"
    
    def search_files(self, query: str) -> str:
        """Поиск файлов по запросу"""
        try:
            results = []
            
            # Ищем в основных директориях проекта
            search_dirs = [
                self.project_root,
                os.path.join(self.project_root, 'guardian_sandbox'),
                os.path.join(self.project_root, 'memory'),
                os.path.join(self.project_root, 'prompts'),
                os.path.join(self.project_root, 'static'),
                os.path.join(self.project_root, 'templates')
            ]
            
            for search_dir in search_dirs:
                if os.path.exists(search_dir):
                    for root, dirs, files in os.walk(search_dir):
                        for file in files:
                            if query.lower() in file.lower():
                                rel_path = os.path.relpath(os.path.join(root, file), self.project_root)
                                results.append(f"📄 {rel_path}")
            
            if results:
                return f"🔍 Search results for '{query}':\n" + "\n".join(results[:20])  # Ограничиваем 20 результатами
            else:
                return f"🔍 No files found matching '{query}'"
            
        except Exception as e:
            logger.error(f"Error searching files for '{query}': {e}")
            return f"❌ Error searching files: {str(e)}"
    
    def get_file_info(self, path: str) -> str:
        """Получение информации о файле"""
        try:
            full_path = os.path.abspath(path)
            
            # Безопасность: убеждаемся что путь в пределах проекта
            if not full_path.startswith(self.project_root):
                return "❌ Access denied: File is outside project directory"
            
            if not os.path.exists(full_path):
                return f"❌ File not found: {path}"
            
            stat = os.stat(full_path)
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime)
            
            # Определяем MIME тип
            mime_type, _ = mimetypes.guess_type(full_path)
            
            info = f"📄 File: {path}\n"
            info += f"📏 Size: {size} bytes\n"
            info += f"📅 Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}\n"
            info += f"🔧 Type: {mime_type or 'unknown'}\n"
            
            if os.path.isfile(full_path):
                info += "📄 Type: File"
            elif os.path.isdir(full_path):
                info += "📁 Type: Directory"
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return f"❌ Error getting file info: {str(e)}"
    
    def delete_file(self, path: str) -> bool:
        """Удаление файла"""
        try:
            full_path = os.path.abspath(path)
            
            # Безопасность: убеждаемся что путь в пределах проекта
            if not full_path.startswith(self.project_root):
                logger.error(f"Access denied: Path {path} is outside project directory")
                return False
            
            if not os.path.exists(full_path):
                logger.error(f"File not found: {path}")
                return False
            
            os.remove(full_path)
            logger.info(f"🗑️ Deleted file: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            return False
    
    def create_directory(self, path: str) -> bool:
        """Создание директории"""
        try:
            full_path = os.path.abspath(path)
            
            # Безопасность: убеждаемся что путь в пределах проекта
            if not full_path.startswith(self.project_root):
                logger.error(f"Access denied: Path {path} is outside project directory")
                return False
            
            if os.path.exists(full_path):
                logger.warning(f"Directory already exists: {path}")
                return False
            
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"📁 Created directory: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            return False
    
    def _find_similar_files(self, target_path: str) -> str:
        """Поиск похожих файлов"""
        try:
            similar_files = []
            
            # Извлекаем имя файла из пути
            target_name = os.path.basename(target_path)
            
            # Ищем файлы с похожими именами
            search_dirs = [
                self.project_root,
                os.path.join(self.project_root, 'guardian_sandbox'),
                os.path.join(self.project_root, 'memory'),
                os.path.join(self.project_root, 'prompts'),
                os.path.join(self.project_root, 'static'),
                os.path.join(self.project_root, 'templates')
            ]
            
            for search_dir in search_dirs:
                if os.path.exists(search_dir):
                    for root, dirs, files in os.walk(search_dir):
                        for file in files:
                            if target_name.lower() in file.lower() or file.lower() in target_name.lower():
                                rel_path = os.path.relpath(os.path.join(root, file), self.project_root)
                                similar_files.append(f"📄 {rel_path}")
            
            if similar_files:
                return "\n".join(similar_files[:10])  # Ограничиваем 10 результатами
            else:
                return "No similar files found"
            
        except Exception as e:
            logger.error(f"Error finding similar files for {target_path}: {e}")
            return "Error finding similar files"
    
    # Sandbox операции
    def create_sandbox_file(self, path: str, content: str = "") -> bool:
        """Создание файла в песочнице"""
        sandbox_path = os.path.join(self.project_root, 'guardian_sandbox', path)
        return self.create_file(sandbox_path, content)
    
    def create_downloadable_file(self, filename: str, content: str, file_type: str = "txt") -> str:
        """Создание файла для скачивания"""
        try:
            # Создаем директорию для загрузок если не существует
            downloads_dir = os.path.join(self.project_root, 'guardian_sandbox', 'downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            
            file_path = os.path.join(downloads_dir, f"{filename}.{file_type}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"📥 Created downloadable file: {file_path}")
            return f"✅ File created: {file_path}"
            
        except Exception as e:
            logger.error(f"Error creating downloadable file: {e}")
            return f"❌ Error creating file: {str(e)}"
    
    def edit_sandbox_file(self, path: str, content: str) -> bool:
        """Редактирование файла в песочнице"""
        sandbox_path = os.path.join(self.project_root, 'guardian_sandbox', path)
        return self.edit_file(sandbox_path, content)
    
    def read_sandbox_file(self, path: str) -> str:
        """Чтение файла из песочницы"""
        sandbox_path = os.path.join(self.project_root, 'guardian_sandbox', path)
        return self.read_file(sandbox_path)
    
    def list_sandbox_files(self, directory: str = "") -> str:
        """Список файлов в песочнице"""
        sandbox_dir = os.path.join(self.project_root, 'guardian_sandbox', directory)
        return self.list_files(sandbox_dir)
    
    def delete_sandbox_file(self, path: str) -> bool:
        """Удаление файла из песочницы"""
        sandbox_path = os.path.join(self.project_root, 'guardian_sandbox', path)
        return self.delete_file(sandbox_path) 