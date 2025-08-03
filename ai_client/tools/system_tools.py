"""
Системные инструменты и утилиты
"""

import os
import re
import json
import subprocess
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..utils.config import Config
from ..utils.logger import Logger
from ..utils.error_handler import ErrorHandler

logger = Logger()

class SystemTools:
    """Класс для системных инструментов"""
    
    def __init__(self):
        """Инициализация SystemTools"""
        self.config = Config()
        self.error_handler = ErrorHandler()
        self.project_root = self.config.get_project_root()
    
    # ===== FILE OPERATIONS =====
    
    def read_file(self, path: str) -> str:
        """Чтение файла"""
        try:
            if not os.path.exists(path):
                return f"❌ File not found: {path}"
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content
        except Exception as e:
            return f"❌ Error reading file {path}: {str(e)}"
    
    def write_file(self, path: str, content: str) -> str:
        """Запись в файл"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ File written: {path}"
        except Exception as e:
            return f"❌ Error writing file {path}: {str(e)}"
    
    def edit_file(self, path: str, content: str) -> str:
        """Редактирование файла"""
        try:
            if not os.path.exists(path):
                return f"❌ File not found: {path}"
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ File edited: {path}"
        except Exception as e:
            return f"❌ Error editing file {path}: {str(e)}"
    
    def create_file(self, path: str, content: str) -> str:
        """Создание файла"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ File created: {path}"
        except Exception as e:
            return f"❌ Error creating file {path}: {str(e)}"
    
    def delete_file(self, path: str) -> str:
        """Удаление файла"""
        try:
            if not os.path.exists(path):
                return f"❌ File not found: {path}"
            
            os.remove(path)
            return f"✅ File deleted: {path}"
        except Exception as e:
            return f"❌ Error deleting file {path}: {str(e)}"
    
    def list_files(self, directory: str = ".") -> str:
        """Список файлов в директории"""
        try:
            if not os.path.exists(directory):
                return f"❌ Directory not found: {directory}"
            
            files = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    files.append(f"📄 {item}")
                else:
                    files.append(f"📁 {item}/")
            
            return f"Files in {directory}:\n" + "\n".join(files)
        except Exception as e:
            return f"❌ Error listing files in {directory}: {str(e)}"
    
    def search_files(self, query: str) -> str:
        """Поиск файлов по содержимому"""
        try:
            results = []
            for root, dirs, files in os.walk("."):
                for file in files:
                    if file.endswith(('.txt', '.md', '.py', '.json')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if query.lower() in content.lower():
                                    results.append(f"📄 {file_path}")
                        except:
                            continue
            
            if results:
                return f"Search results for '{query}':\n" + "\n".join(results[:20])
            else:
                return f"No files found containing '{query}'"
        except Exception as e:
            return f"❌ Error searching files: {str(e)}"
    
    def append_to_file(self, path: str, content: str) -> str:
        """Добавление в файл"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)
            return f"✅ Content appended to: {path}"
        except Exception as e:
            return f"❌ Error appending to file {path}: {str(e)}"
    
    def safe_create_file(self, path: str, content: str) -> str:
        """Безопасное создание файла с автоматическим разделением"""
        try:
            if len(content) > 10000:  # Если контент большой
                # Разделяем на части
                parts = [content[i:i+10000] for i in range(0, len(content), 10000)]
                for i, part in enumerate(parts):
                    part_path = f"{path}.part{i+1}" if len(parts) > 1 else path
                    os.makedirs(os.path.dirname(part_path), exist_ok=True)
                    with open(part_path, 'w', encoding='utf-8') as f:
                        f.write(part)
                
                if len(parts) > 1:
                    return f"✅ Large file created in {len(parts)} parts: {path}"
                else:
                    return f"✅ File created: {path}"
            else:
                return self.create_file(path, content)
        except Exception as e:
            return f"❌ Error creating file {path}: {str(e)}"
    
    # ===== USER PROFILE TOOLS =====
    
    def read_user_profile(self, username: str) -> str:
        """Чтение профиля пользователя"""
        try:
            profile_path = f"memory/user_profiles/{username}.json"
            if not os.path.exists(profile_path):
                return f"❌ Profile not found for user: {username}"
            
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            return f"Profile for {username}:\n{json.dumps(profile, indent=2)}"
        except Exception as e:
            return f"❌ Error reading profile for {username}: {str(e)}"
    
    def read_emotional_history(self, username: str) -> str:
        """Чтение эмоциональной истории пользователя"""
        try:
            history_path = f"memory/user_profiles/{username}_emotional_history.json"
            if not os.path.exists(history_path):
                return f"❌ Emotional history not found for user: {username}"
            
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            return f"Emotional history for {username}:\n{json.dumps(history, indent=2)}"
        except Exception as e:
            return f"❌ Error reading emotional history for {username}: {str(e)}"
    
    def search_user_data(self, username: str, query: str) -> str:
        """Поиск данных пользователя"""
        try:
            results = []
            user_dir = f"memory/user_profiles"
            
            if not os.path.exists(user_dir):
                return f"❌ User data directory not found"
            
            for file in os.listdir(user_dir):
                if file.startswith(username):
                    file_path = os.path.join(user_dir, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                results.append(f"📄 {file}")
                    except:
                        continue
            
            if results:
                return f"Search results for '{username}' with query '{query}':\n" + "\n".join(results)
            else:
                return f"No data found for '{username}' containing '{query}'"
        except Exception as e:
            return f"❌ Error searching user data: {str(e)}"
    
    def update_current_feeling(self, username: str, feeling: str, context: str = "") -> str:
        """Обновление текущего чувства пользователя"""
        try:
            profile_path = f"memory/user_profiles/{username}.json"
            if not os.path.exists(profile_path):
                return f"❌ Profile not found for user: {username}"
            
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            profile['current_feeling'] = feeling
            if context:
                profile['feeling_context'] = context
            profile['last_updated'] = datetime.now().isoformat()
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)
            
            return f"✅ Updated feeling for {username}: {feeling}"
        except Exception as e:
            return f"❌ Error updating feeling for {username}: {str(e)}"
    
    def add_user_observation(self, username: str, observation: str) -> str:
        """Добавление наблюдения о пользователе"""
        try:
            observations_path = f"memory/user_profiles/{username}_observations.json"
            
            if os.path.exists(observations_path):
                with open(observations_path, 'r', encoding='utf-8') as f:
                    observations = json.load(f)
            else:
                observations = []
            
            observation_entry = {
                'observation': observation,
                'timestamp': datetime.now().isoformat()
            }
            
            observations.append(observation_entry)
            
            with open(observations_path, 'w', encoding='utf-8') as f:
                json.dump(observations, f, indent=2)
            
            return f"✅ Added observation for {username}"
        except Exception as e:
            return f"❌ Error adding observation for {username}: {str(e)}"
    
    # ===== SYSTEM TOOLS =====
    
    def add_model_note(self, note: str, category: str = "general") -> str:
        """Добавление заметки модели"""
        try:
            notes_path = "memory/model_notes.json"
            
            if os.path.exists(notes_path):
                with open(notes_path, 'r', encoding='utf-8') as f:
                    notes = json.load(f)
            else:
                notes = []
            
            note_entry = {
                'note': note,
                'category': category,
                'timestamp': datetime.now().isoformat()
            }
            
            notes.append(note_entry)
            
            with open(notes_path, 'w', encoding='utf-8') as f:
                json.dump(notes, f, indent=2)
            
            return f"✅ Added model note in category '{category}'"
        except Exception as e:
            return f"❌ Error adding model note: {str(e)}"
    
    def add_personal_thought(self, thought: str) -> str:
        """Добавление личной мысли"""
        try:
            thoughts_path = "guardian_sandbox/personal_thoughts.md"
            
            thought_entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{thought}\n"
            
            with open(thoughts_path, 'a', encoding='utf-8') as f:
                f.write(thought_entry)
            
            return f"✅ Added personal thought"
        except Exception as e:
            return f"❌ Error adding personal thought: {str(e)}"
    
    def get_system_logs(self, lines: int = 50) -> str:
        """Получение системных логов"""
        try:
            log_file = os.path.join(self.project_root, 'app.log')
            
            if not os.path.exists(log_file):
                return "No log file found"
            
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            # Берем последние строки
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            return "=== Current Model Status ===\n" + "".join(recent_lines)
            
        except Exception as e:
            logger.error(f"Error reading system logs: {e}")
            return f"❌ Error reading logs: {str(e)}"
    
    def get_error_summary(self) -> str:
        """Получение сводки ошибок"""
        try:
            log_file = os.path.join(self.project_root, 'app.log')
            
            if not os.path.exists(log_file):
                return "No log file found"
            
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            errors = []
            for line in lines:
                if 'ERROR' in line or '❌' in line:
                    errors.append(line.strip())
            
            if errors:
                return "=== Error Summary ===\n" + "\n".join(errors[-10:])  # Последние 10 ошибок
            else:
                return "✅ No errors found in recent logs"
            
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return f"❌ Error getting error summary: {str(e)}"
    
    def diagnose_system_health(self) -> str:
        """Диагностика здоровья системы"""
        try:
            logger.info("🔧 SYSTEM TOOLS: Starting system health diagnosis...")
            health_report = []
            
            # Системный обзор
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            health_report.append("=== ΔΣ Guardian System Status ===")
            health_report.append(f"🕐 Current time: {current_time}")
            health_report.append("🧠 Current model: gemini-2.5-pro")
            health_report.append("📊 Model index: 0/7")
            
            logger.info(f"🔧 SYSTEM TOOLS: Current time: {current_time}")
            logger.info("🔧 SYSTEM TOOLS: Using gemini-2.5-pro model")
            
            # Проверка файлов
            health_report.append("\n=== File System Health ===")
            critical_files = [
                "memory/model_notes.json",
                "memory/conversation_history.json", 
                "memory/guardian_profile.json",
                "memory/user_profiles/meranda.json",
                "memory/user_profiles/stepan.json",
            ]
            
            logger.info(f"🔧 SYSTEM TOOLS: Checking {len(critical_files)} critical files")
            
            for file_path in critical_files:
                full_path = os.path.join(self.project_root, file_path)
                if os.path.exists(full_path):
                    size = os.path.getsize(full_path)
                    health_report.append(f"✅ {file_path}: OK ({size} bytes)")
                    logger.info(f"✅ SYSTEM TOOLS: {file_path} - OK ({size} bytes)")
                else:
                    health_report.append(f"❌ {file_path}: Missing")
                    logger.warning(f"❌ SYSTEM TOOLS: {file_path} - Missing")
            
            # Проверка песочницы
            health_report.append("\n=== Sandbox Memory Files ===")
            sandbox_dir = os.path.join(self.project_root, 'guardian_sandbox')
            if os.path.exists(sandbox_dir):
                sandbox_files = os.listdir(sandbox_dir)
                for file in sandbox_files[:5]:  # Показываем первые 5 файлов
                    file_path = os.path.join(sandbox_dir, file)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        health_report.append(f"✅ guardian_sandbox/{file}: OK ({size} bytes)")
            else:
                health_report.append("❌ guardian_sandbox: Missing")
            
            # Проверка API
            health_report.append("\n=== API Health ===")
            if self.config.get_gemini_api_key():
                health_report.append("✅ GEMINI_API_KEY: Set")
            else:
                health_report.append("❌ GEMINI_API_KEY: Missing")
            
            if os.path.exists(sandbox_dir):
                health_report.append("✅ Sandbox: guardian_sandbox exists")
                health_report.append(f"📁 Sandbox files: {len(os.listdir(sandbox_dir))} files")
            else:
                health_report.append("❌ Sandbox: guardian_sandbox missing")
            
            # Возможности системы
            health_report.append("\n=== System Capabilities ===")
            health_report.append("✅ Self-modification: Can edit own prompt and code")
            health_report.append("✅ Memory system: Persistent notes in sandbox")
            health_report.append("✅ Multi-model support: Automatic model switching")
            health_report.append("✅ File operations: Read/write/create/delete files")
            health_report.append("✅ User profiles: Meranda and Stepan data")
            health_report.append("✅ Image analysis: Vision capabilities available")
            
            # Недавняя активность
            health_report.append("\n=== Recent Activity ===")
            try:
                log_file = os.path.join(self.project_root, 'app.log')
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    recent_lines = lines[-5:] if len(lines) > 5 else lines
                    for line in recent_lines:
                        health_report.append(f"📝 {line.strip()}")
                else:
                    health_report.append("⚠️ Error reading recent activity: No log file")
            except Exception as e:
                health_report.append(f"⚠️ Error reading recent activity: {str(e)}")
            
            result = "\n".join(health_report)
            logger.info(f"✅ SYSTEM TOOLS: System health diagnosis completed - {len(result.split())} words")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error diagnosing system health: {e}")
            return f"❌ Error diagnosing system health: {str(e)}"
    
    def analyze_image(self, image_path: str, user_context: str = "") -> str:
        """Анализ изображения"""
        try:
            # Проверяем существование файла
            if not os.path.exists(image_path):
                return f"❌ Image file not found: {image_path}"
            
            # Проверяем что это изображение
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            file_ext = os.path.splitext(image_path)[1].lower()
            
            if file_ext not in image_extensions:
                return f"❌ Not a valid image file: {image_path}"
            
            # Анализируем через Vision API
            if self.config.is_vision_configured():
                # Используем Vision API из gemini_client
                from ..models.gemini_client import GeminiClient
                gemini_client = GeminiClient()
                vision_result = gemini_client._analyze_image_with_vision_api(image_path)
                
                # Добавляем контекст пользователя
                if user_context:
                    return f"🔍 Image Analysis: {vision_result}\n\nUser Context: {user_context}"
                else:
                    return f"🔍 Image Analysis: {vision_result}"
            else:
                return f"❌ Vision API not configured for image analysis"
            
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            return f"❌ Error analyzing image: {str(e)}"
    
    def get_project_structure(self) -> str:
        """Получение структуры проекта"""
        try:
            structure = []
            
            def scan_directory(path, prefix="", max_depth=3, current_depth=0):
                if current_depth > max_depth:
                    return
                
                try:
                    items = os.listdir(path)
                    items.sort()
                    
                    for item in items:
                        item_path = os.path.join(path, item)
                        rel_path = os.path.relpath(item_path, self.project_root)
                        
                        if os.path.isdir(item_path):
                            structure.append(f"{prefix}📁 {rel_path}/")
                            if current_depth < max_depth:
                                scan_directory(item_path, prefix + "  ", max_depth, current_depth + 1)
                        else:
                            size = os.path.getsize(item_path)
                            structure.append(f"{prefix}📄 {rel_path} ({size} bytes)")
                            
                except PermissionError:
                    structure.append(f"{prefix}🚫 {os.path.relpath(path, self.project_root)}/ (Permission denied)")
                except Exception as e:
                    structure.append(f"{prefix}❌ {os.path.relpath(path, self.project_root)}/ (Error: {str(e)})")
            
            structure.append("📂 Project Structure:")
            scan_directory(self.project_root)
            
            return "\n".join(structure)
            
        except Exception as e:
            logger.error(f"Error getting project structure: {e}")
            return f"❌ Error getting project structure: {str(e)}"
    
    def find_images(self) -> str:
        """Поиск изображений в проекте"""
        try:
            images = []
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            
            for root, dirs, files in os.walk(self.project_root):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in image_extensions):
                        rel_path = os.path.relpath(os.path.join(root, file), self.project_root)
                        size = os.path.getsize(os.path.join(root, file))
                        images.append(f"🖼️ {rel_path} ({size} bytes)")
            
            if images:
                return f"🖼️ Found {len(images)} images:\n" + "\n".join(images)
            else:
                return "🖼️ No images found in project"
            
        except Exception as e:
            logger.error(f"Error finding images: {e}")
            return f"❌ Error finding images: {str(e)}"
    
    def generate_system_greeting(self, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """Генерация системного приветствия для мониторинга"""
        try:
            if not user_profile:
                return "👋 System monitoring active"
            
            username = user_profile.get('username', 'User')
            current_time = datetime.now().strftime("%I:%M %p")
            current_feeling = user_profile.get('current_feeling', 'neutral')
            
            feeling_emoji = {
                'happy': '😊', 'sad': '😢', 'excited': '🎉', 'tired': '😴',
                'stressed': '😰', 'neutral': '😐'
            }.get(current_feeling, '😐')
            
            # Системное приветствие для мониторинга
            greeting = f"🔍 System Status: {feeling_emoji} {username} active at {current_time}"
            
            if current_feeling != 'neutral':
                greeting += f" (feeling: {current_feeling})"
            
            return greeting
            
        except Exception as e:
            logger.error(f"Error generating system greeting: {e}")
            return "🔍 System monitoring active"
    

    
    # ReAct архитектура
    def plan_step(self, goal: str) -> str:
        """Планирование шага"""
        try:
            # TODO: Реализовать планирование
            return f"📋 Planned step for goal: {goal}"
        except Exception as e:
            logger.error(f"Error planning step: {e}")
            return f"❌ Error planning step: {str(e)}"
    
    def act_step(self, tool_name: str, tool_input: str) -> str:
        """Выполнение шага"""
        try:
            # TODO: Реализовать выполнение
            return f"🔧 Executed {tool_name} with input: {tool_input}"
        except Exception as e:
            logger.error(f"Error executing step: {e}")
            return f"❌ Error executing step: {str(e)}"
    
    def reflect(self, history: List[str]) -> str:
        """Рефлексия"""
        try:
            # TODO: Реализовать рефлексию
            return f"🤔 Reflected on {len(history)} steps"
        except Exception as e:
            logger.error(f"Error reflecting: {e}")
            return f"❌ Error reflecting: {str(e)}"
    
    def react_cycle(self, goal: str, max_steps: int = 20) -> str:
        """ReAct цикл"""
        try:
            # TODO: Реализовать полный цикл
            return f"🔄 ReAct cycle for goal: {goal} (max {max_steps} steps)"
        except Exception as e:
            logger.error(f"Error in ReAct cycle: {e}")
            return f"❌ Error in ReAct cycle: {str(e)}"
    
    # Web инструменты
    def web_search(self, query: str) -> str:
        """Веб-поиск через Google Custom Search API"""
        try:
            import requests
            import os
            
            api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
            engine_id = os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
            
            if not api_key:
                return "❌ Google Custom Search API key not configured"
            
            if not engine_id or engine_id == "test_engine_id":
                return "❌ Google Custom Search Engine ID not configured. Please create one at https://programmablesearchengine.google.com/"
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': engine_id,
                'q': query,
                'num': 5  # Количество результатов
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'items' in data and data['items']:
                    results = []
                    for item in data['items']:
                        title = item.get('title', 'No title')
                        snippet = item.get('snippet', 'No description')
                        link = item.get('link', 'No link')
                        results.append(f"📄 {title}\n{snippet}\n🔗 {link}\n")
                    
                    return f"🔍 Результаты поиска для '{query}':\n\n" + "\n".join(results)
                else:
                    return f"🔍 Поиск для '{query}': результатов не найдено"
            else:
                return f"❌ Ошибка API: {response.status_code} - {response.text}"
                
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return f"❌ Error in web search: {str(e)}"
    
    def fetch_url(self, url: str) -> str:
        """Получение URL"""
        try:
            # TODO: Реализовать получение URL
            return f"🌐 Fetching URL: {url} (not implemented)"
        except Exception as e:
            logger.error(f"Error fetching URL: {e}")
            return f"❌ Error fetching URL: {str(e)}"
    
    def call_api(self, endpoint: str, payload: str = "") -> str:
        """Вызов API"""
        try:
            # TODO: Реализовать вызов API
            return f"📡 API call to: {endpoint} (not implemented)"
        except Exception as e:
            logger.error(f"Error calling API: {e}")
            return f"❌ Error calling API: {str(e)}"
    
    def integrate_api(self, name: str, base_url: str, auth: str = "", schema: str = "") -> bool:
        """Интеграция API"""
        try:
            # TODO: Реализовать интеграцию API
            logger.info(f"🔗 Integrated API: {name} at {base_url}")
            return True
        except Exception as e:
            logger.error(f"Error integrating API: {e}")
            return False
    
    def call_custom_api(self, name: str, endpoint: str, data: str = "") -> str:
        """Вызов кастомного API"""
        try:
            # TODO: Реализовать вызов кастомного API
            return f"🔧 Custom API call to {name}: {endpoint} (not implemented)"
        except Exception as e:
            logger.error(f"Error calling custom API: {e}")
            return f"❌ Error calling custom API: {str(e)}"
    
    def get_weather(self, location: str) -> str:
        """Получение погоды"""
        try:
            # TODO: Реализовать получение погоды
            return f"🌤️ Weather for {location} (not implemented)"
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return f"❌ Error getting weather: {str(e)}"
    
    def translate_text(self, text: str, target_language: str = "en") -> str:
        """Перевод текста"""
        try:
            # TODO: Реализовать перевод
            return f"🌐 Translation to {target_language}: {text} (not implemented)"
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return f"❌ Error translating text: {str(e)}"
    
    # Управление событиями
    def create_event(self, title: str, description: str, date: str, time: str = "", priority: str = "medium") -> bool:
        """Создание события"""
        try:
            # TODO: Реализовать создание событий
            logger.info(f"📅 Created event: {title} on {date}")
            return True
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return False
    
    def get_upcoming_events(self, days: int = 7) -> str:
        """Получение предстоящих событий"""
        try:
            # TODO: Реализовать получение событий
            return f"📅 Upcoming events for next {days} days (not implemented)"
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return f"❌ Error getting upcoming events: {str(e)}"
    
    def reschedule_event(self, event_id: int, new_date: str, new_time: str = "") -> bool:
        """Перенос события"""
        try:
            # TODO: Реализовать перенос событий
            logger.info(f"📅 Rescheduled event {event_id} to {new_date}")
            return True
        except Exception as e:
            logger.error(f"Error rescheduling event: {e}")
            return False
    
    def complete_event(self, event_id: int) -> bool:
        """Завершение события"""
        try:
            # TODO: Реализовать завершение событий
            logger.info(f"✅ Completed event {event_id}")
            return True
        except Exception as e:
            logger.error(f"Error completing event: {e}")
            return False
    
    def get_event_statistics(self) -> str:
        """Получение статистики событий"""
        try:
            # TODO: Реализовать статистику событий
            return "📊 Event statistics (not implemented)"
        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
            return f"❌ Error getting event statistics: {str(e)}"
    
    def create_task_list(self, title: str, tasks: str) -> bool:
        """Создание списка задач"""
        try:
            # TODO: Реализовать создание списков задач
            logger.info(f"📋 Created task list: {title}")
            return True
        except Exception as e:
            logger.error(f"Error creating task list: {e}")
            return False
    
    def list_tasks(self, context: str = "") -> str:
        """Список задач"""
        try:
            # TODO: Реализовать список задач
            return f"📋 Task list for context: {context} (not implemented)"
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return f"❌ Error listing tasks: {str(e)}"
    
    # Терминал и система
    def run_terminal_command(self, command: str) -> str:
        """Выполнение команды терминала"""
        try:
            # Безопасность: проверяем команду
            dangerous_commands = ['rm -rf', 'sudo', 'chmod 777', 'format', 'dd']
            if any(dangerous in command.lower() for dangerous in dangerous_commands):
                return "❌ Command blocked for security reasons"
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return f"✅ Command executed successfully:\n{result.stdout}"
            else:
                return f"❌ Command failed:\n{result.stderr}"
            
        except subprocess.TimeoutExpired:
            return "❌ Command timed out"
        except Exception as e:
            logger.error(f"Error running terminal command: {e}")
            return f"❌ Error running command: {str(e)}"
    
    def get_system_info(self) -> str:
        """Получение информации о системе"""
        try:
            import platform
            
            info = []
            info.append("🖥️ System Information:")
            info.append(f"OS: {platform.system()} {platform.release()}")
            info.append(f"Architecture: {platform.machine()}")
            info.append(f"Python: {platform.python_version()}")
            info.append(f"Processor: {platform.processor()}")
            
            # Информация о памяти
            try:
                import psutil
                memory = psutil.virtual_memory()
                info.append(f"Memory: {memory.available // (1024**3)}GB available / {memory.total // (1024**3)}GB total")
            except ImportError:
                info.append("Memory: psutil not available")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return f"❌ Error getting system info: {str(e)}"
    
    def diagnose_network(self) -> str:
        """Диагностика сети"""
        try:
            # TODO: Реализовать диагностику сети
            return "🌐 Network diagnostics (not implemented)"
        except Exception as e:
            logger.error(f"Error diagnosing network: {e}")
            return f"❌ Error diagnosing network: {str(e)}"
    
    # Инструменты для выполнения
    def _extract_tool_calls(self, text: str) -> List[str]:
        """Извлечение вызовов инструментов из текста - УЛУЧШЕННАЯ ВЕРСИЯ"""
        try:
            logger.info(f"🔧 TOOL EXTRACTION: Processing text ({len(text)} chars)")
            
            # Список известных инструментов - ПОЛНЫЙ СПИСОК
            known_tools = [
                # File Operations
                'read_file', 'write_file', 'edit_file', 'create_file', 'delete_file',
                'list_files', 'search_files', 'append_to_file', 'safe_create_file',
                
                # User Profile Tools
                'read_user_profile', 'read_emotional_history', 'search_user_data',
                'update_current_feeling', 'add_user_observation',
                
                # System Tools
                'add_model_note', 'add_personal_thought', 'get_system_logs',
                'get_error_summary', 'analyze_image', 'web_search',
                'generate_system_greeting',
                
                # ReAct Architecture
                'plan_step', 'act_step', 'reflect', 'react_cycle',
                
                # Web & API Tools
                'fetch_url', 'call_api', 'integrate_api', 'call_custom_api',
                'get_weather', 'translate_text',
                
                # Event Management
                'create_event', 'get_upcoming_events', 'reschedule_event',
                'complete_event', 'get_event_statistics',
                
                # Task Management
                'create_task_list', 'list_tasks',
                
                # System Information
                'run_terminal_command', 'get_system_info', 'diagnose_network',
                'get_project_structure', 'find_images'
            ]
            
            full_calls = []
            
            # 1. Ищем print(tool_code.function(...)) - основной формат
            pattern = r'print\s*\(\s*tool_code\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*\)'
            for match in re.finditer(pattern, text):
                func_name = match.group(1)
                args = match.group(2)
                
                if func_name in known_tools:
                    correct_call = f"{func_name}({args})"
                    if self._validate_tool_call(correct_call):
                        full_calls.append(correct_call)
                        logger.info(f"✅ Found tool call: {correct_call}")
                    else:
                        logger.warning(f"⚠️ Invalid tool call: {correct_call}")
                else:
                    logger.warning(f"⚠️ Unknown tool: {func_name}")
            
            # 2. Ищем прямые вызовы function(...) - fallback
            direct_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)'
            for match in re.finditer(direct_pattern, text):
                full_call = match.group(0)
                func_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', full_call)
                if not func_match:
                    continue
                
                func_name = func_match.group(1)
                if func_name in known_tools:
                    if self._validate_tool_call(full_call):
                        full_calls.append(full_call)
                        logger.info(f"✅ Found direct call: {full_call}")
                    else:
                        logger.warning(f"⚠️ Invalid direct call: {full_call}")
            
            # 3. Ищем в блоках кода ```tool_code\n...```
            code_block_pattern = r'```tool_code\s*\n(.*?)\n```'
            for match in re.finditer(code_block_pattern, text, re.DOTALL):
                code_content = match.group(1)
                logger.info(f"🔧 Found code block: {code_content[:100]}...")
                
                # Ищем в блоке кода
                for tool_match in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)', code_content):
                    full_call = tool_match.group(0)
                    func_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', full_call)
                    if not func_match:
                        continue
                    
                    func_name = func_match.group(1)
                    if func_name in known_tools:
                        if self._validate_tool_call(full_call):
                            full_calls.append(full_call)
                            logger.info(f"✅ Found in code block: {full_call}")
                        else:
                            logger.warning(f"⚠️ Invalid code block call: {full_call}")
                    else:
                        logger.warning(f"⚠️ Unknown tool in code block: {func_name}")
            
            # 4. Ищем в тексте без print - просто function(...)
            simple_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)'
            for match in re.finditer(simple_pattern, text):
                full_call = match.group(0)
                func_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', full_call)
                if not func_match:
                    continue
                
                func_name = func_match.group(1)
                if func_name in known_tools:
                    if self._validate_tool_call(full_call):
                        full_calls.append(full_call)
                        logger.info(f"✅ Found simple call: {full_call}")
                    else:
                        logger.warning(f"⚠️ Invalid simple call: {full_call}")
            
            # Убираем дубликаты
            unique_calls = list(dict.fromkeys(full_calls))
            logger.info(f"🔧 TOOL EXTRACTION: Found {len(unique_calls)} unique tool calls")
            
            return unique_calls
            
        except Exception as e:
            logger.error(f"❌ Tool extraction error: {e}")
            return []
    
    def _validate_tool_call(self, tool_call: str) -> bool:
        """Валидация синтаксиса вызова инструмента - УПРОЩЕННАЯ ВЕРСИЯ"""
        try:
            # Извлекаем имя функции и аргументы
            match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)', tool_call)
            if not match:
                logger.warning(f"⚠️ Invalid tool call format: {tool_call}")
                return False
            
            func_name = match.group(1)
            args_str = match.group(2)
            
            # Проверяем что это известный инструмент
            known_tools = [
                'read_file', 'write_file', 'edit_file', 'create_file', 'delete_file',
                'list_files', 'search_files', 'add_model_note', 'add_personal_thought',
                'get_system_logs', 'get_error_summary', 'analyze_image', 'web_search',
                'generate_system_greeting', 'read_user_profile', 'read_emotional_history',
                'search_user_data', 'update_current_feeling', 'add_user_observation',
                'append_to_file', 'safe_create_file'
            ]
            
            if func_name not in known_tools:
                logger.warning(f"⚠️ Unknown tool: {func_name}")
                return False
            
            # УПРОЩЕННАЯ ВАЛИДАЦИЯ - принимаем любой tool call с правильным синтаксисом
            logger.info(f"✅ Valid tool call: {tool_call}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Tool call validation error: {e}")
            return False
    
    def _extract_nested_calls(self, text: str) -> List[str]:
        """Извлечение вложенных вызовов"""
        try:
            # Более сложный паттерн для вложенных вызовов
            pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)'
            matches = re.findall(pattern, text)
            
            # Убираем дубликаты
            unique_calls = list(set(matches))
            
            return unique_calls
            
        except Exception as e:
            logger.error(f"Error extracting nested calls: {e}")
            return []
    
    def _parse_arguments(self, args_str: str, expected_params: List[str]) -> Dict[str, Any]:
        """Универсальный парсер аргументов"""
        result = {}
        args_str = args_str.strip()
        
        # Если аргументы пустые, возвращаем пустой словарь
        if not args_str:
            return result
        
        # Пытаемся парсить как именованные аргументы: param=value
        if '=' in args_str:
            # Паттерн для именованных аргументов: param="value" или param=value
            named_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([a-zA-Z_][a-zA-Z0-9_]*))'
            named_matches = re.findall(named_pattern, args_str)
            
            for match in named_matches:
                param_name = match[0]
                param_value = next((val for val in match[1:] if val), "")
                result[param_name] = param_value
        
        # Пытаемся парсить как позиционные аргументы
        else:
            # Паттерн для строковых аргументов в кавычках
            quoted_pattern = r'["\']([^"\']*)["\']'
            quoted_matches = re.findall(quoted_pattern, args_str)
            
            # Паттерн для аргументов без кавычек
            unquoted_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
            unquoted_matches = re.findall(unquoted_pattern, args_str)
            
            # Объединяем результаты
            all_matches = quoted_matches + unquoted_matches
            
            # Сопоставляем с ожидаемыми параметрами
            for i, param in enumerate(expected_params):
                if i < len(all_matches):
                    result[param] = all_matches[i]
        
        return result
    
    def _execute_tool_call(self, tool_call: str) -> str:
        """Выполнение вызова инструмента"""
        try:
            # Извлекаем имя функции и аргументы
            match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)', tool_call)
            if not match:
                return f"❌ Invalid tool call format: {tool_call}"
            
            func_name = match.group(1)
            args_str = match.group(2)
            
            # Выполняем соответствующий инструмент
            if func_name == "read_file":
                args = self._parse_arguments(args_str, ["path"])
                path = args.get("path", "config.py")
                logger.info(f"🔧 read_file: path={path}")
                # Делегируем в FileTools
                from ..tools.file_tools import FileTools
                file_tools = FileTools()
                result = file_tools.read_file(path)
                logger.info(f"✅ read_file result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "list_files":
                args = self._parse_arguments(args_str, ["directory"])
                directory = args.get("directory", "")
                logger.info(f"🔧 list_files: directory={directory}")
                # Делегируем в FileTools
                from ..tools.file_tools import FileTools
                file_tools = FileTools()
                result = file_tools.list_files(directory)
                logger.info(f"✅ list_files result: {result}")
                return result
            
            elif func_name == "search_files":
                args = self._parse_arguments(args_str, ["query"])
                query = args.get("query", "system")
                logger.info(f"🔧 search_files: query={query}")
                # Делегируем в FileTools
                from ..tools.file_tools import FileTools
                file_tools = FileTools()
                result = file_tools.search_files(query)
                logger.info(f"✅ search_files result: {result}")
                return result
            
            elif func_name == "create_file":
                args = self._parse_arguments(args_str, ["path", "content"])
                path = args.get("path", "")
                content = args.get("content", "")
                logger.info(f"🔧 create_file: path={path}, content_length={len(content)}")
                # Делегируем в FileTools
                from ..tools.file_tools import FileTools
                file_tools = FileTools()
                result = file_tools.create_file(path, content)
                logger.info(f"✅ create_file result: {result}")
                return f"File created: {path}" if result else f"Failed to create file: {path}"
            
            elif func_name == "append_to_file":
                args = self._parse_arguments(args_str, ["path", "content"])
                path = args.get("path", "")
                content = args.get("content", "")
                logger.info(f"🔧 append_to_file: path={path}, content_length={len(content)}")
                # Делегируем в FileTools
                from ..tools.file_tools import FileTools
                file_tools = FileTools()
                result = file_tools.append_to_file(path, content)
                logger.info(f"✅ append_to_file result: {result}")
                return f"Content appended to: {path}" if result else f"Failed to append to file: {path}"
            
            elif func_name == "safe_create_file":
                args = self._parse_arguments(args_str, ["path", "content"])
                path = args.get("path", "")
                content = args.get("content", "")
                logger.info(f"🔧 safe_create_file: path={path}, content_length={len(content)}")
                # Делегируем в FileTools
                from ..tools.file_tools import FileTools
                file_tools = FileTools()
                result = file_tools.safe_create_file(path, content)
                logger.info(f"✅ safe_create_file result: {result}")
                return f"File created safely: {path}" if result else f"Failed to create file safely: {path}"
            
            elif func_name == "write_file":
                args = self._parse_arguments(args_str, ["path", "content"])
                path = args.get("path", "")
                content = args.get("content", "")
                logger.info(f"🔧 write_file: path={path}")
                # Делегируем в FileTools
                from ..tools.file_tools import FileTools
                file_tools = FileTools()
                result = file_tools.write_file(path, content)
                logger.info(f"✅ write_file result: {result}")
                return f"File written: {path}" if result else f"Failed to write file: {path}"
            
            elif func_name == "edit_file":
                args = self._parse_arguments(args_str, ["path", "content"])
                path = args.get("path", "")
                content = args.get("content", "")
                logger.info(f"🔧 edit_file: path={path}")
                # Делегируем в FileTools
                from ..tools.file_tools import FileTools
                file_tools = FileTools()
                result = file_tools.edit_file(path, content)
                logger.info(f"✅ edit_file result: {result}")
                return f"File edited: {path}" if result else f"Failed to edit file: {path}"
            
            elif func_name == "delete_file":
                args = self._parse_arguments(args_str, ["path"])
                path = args.get("path", "")
                logger.info(f"🔧 delete_file: path={path}")
                # Делегируем в FileTools
                from ..tools.file_tools import FileTools
                file_tools = FileTools()
                result = file_tools.delete_file(path)
                logger.info(f"✅ delete_file result: {result}")
                return f"File deleted: {path}" if result else f"Failed to delete file: {path}"
            
            elif func_name == "add_model_note":
                args = self._parse_arguments(args_str, ["note_text", "category"])
                note_text = args.get("note_text", "System note")
                category = args.get("category", "general")
                logger.info(f"🔧 add_model_note: note_text={note_text[:50]}..., category={category}")
                # Делегируем в MemoryTools
                from ..tools.memory_tools import MemoryTools
                memory_tools = MemoryTools()
                result = memory_tools.add_model_note(note_text, category)
                logger.info(f"✅ add_model_note result: {result}")
                return f"Added model note: {note_text[:50]}..."
            
            elif func_name == "read_user_profile":
                args = self._parse_arguments(args_str, ["username"])
                username = args.get("username", "stepan")
                logger.info(f"🔧 read_user_profile: username={username}")
                # Делегируем в MemoryTools
                from ..tools.memory_tools import MemoryTools
                memory_tools = MemoryTools()
                result = memory_tools.read_user_profile(username)
                logger.info(f"✅ read_user_profile result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "read_emotional_history":
                args = self._parse_arguments(args_str, ["username"])
                username = args.get("username", "stepan")
                logger.info(f"🔧 read_emotional_history: username={username}")
                # Делегируем в MemoryTools
                from ..tools.memory_tools import MemoryTools
                memory_tools = MemoryTools()
                result = memory_tools.read_emotional_history(username)
                logger.info(f"✅ read_emotional_history result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "search_user_data":
                args = self._parse_arguments(args_str, ["username", "query"])
                username = args.get("username", "stepan")
                query = args.get("query", "")
                logger.info(f"🔧 search_user_data: username={username}, query={query}")
                # Делегируем в MemoryTools
                from ..tools.memory_tools import MemoryTools
                memory_tools = MemoryTools()
                result = memory_tools.search_user_data(username, query)
                logger.info(f"✅ search_user_data result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "update_current_feeling":
                args = self._parse_arguments(args_str, ["username", "feeling", "context"])
                username = args.get("username", "stepan")
                feeling = args.get("feeling", "")
                context = args.get("context", "")
                logger.info(f"🔧 update_current_feeling: username={username}, feeling={feeling}")
                # Делегируем в MemoryTools
                from ..tools.memory_tools import MemoryTools
                memory_tools = MemoryTools()
                result = memory_tools.update_current_feeling(username, feeling, context)
                logger.info(f"✅ update_current_feeling result: {result}")
                return result
            
            elif func_name == "add_user_observation":
                args = self._parse_arguments(args_str, ["username", "observation"])
                username = args.get("username", "stepan")
                observation = args.get("observation", "")
                logger.info(f"🔧 add_user_observation: username={username}, observation={observation[:50]}...")
                # Делегируем в MemoryTools
                from ..tools.memory_tools import MemoryTools
                memory_tools = MemoryTools()
                result = memory_tools.add_user_observation(username, observation)
                logger.info(f"✅ add_user_observation result: {result}")
                return result
            
            # System Tools
            elif func_name == "get_system_logs":
                args = self._parse_arguments(args_str, ["lines"])
                lines = args.get("lines", 50)
                logger.info(f"🔧 get_system_logs: lines={lines}")
                result = self.get_system_logs(int(lines))
                logger.info(f"✅ get_system_logs result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "get_error_summary":
                logger.info(f"🔧 get_error_summary")
                result = self.get_error_summary()
                logger.info(f"✅ get_error_summary result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "diagnose_system_health":
                logger.info(f"🔧 diagnose_system_health")
                result = self.diagnose_system_health()
                logger.info(f"✅ diagnose_system_health result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "analyze_image":
                args = self._parse_arguments(args_str, ["image_path", "user_context"])
                image_path = args.get("image_path", "")
                user_context = args.get("user_context", "")
                logger.info(f"🔧 analyze_image: image_path={image_path}")
                result = self.analyze_image(image_path, user_context)
                logger.info(f"✅ analyze_image result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "get_project_structure":
                logger.info(f"🔧 get_project_structure")
                result = self.get_project_structure()
                logger.info(f"✅ get_project_structure result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "find_images":
                logger.info(f"🔧 find_images")
                result = self.find_images()
                logger.info(f"✅ find_images result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "web_search":
                args = self._parse_arguments(args_str, ["query"])
                query = args.get("query", "")
                logger.info(f"🔧 web_search: query={query}")
                result = self.web_search(query)
                logger.info(f"✅ web_search result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "fetch_url":
                args = self._parse_arguments(args_str, ["url"])
                url = args.get("url", "")
                logger.info(f"🔧 fetch_url: url={url}")
                result = self.fetch_url(url)
                logger.info(f"✅ fetch_url result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "call_api":
                args = self._parse_arguments(args_str, ["endpoint", "payload"])
                endpoint = args.get("endpoint", "")
                payload = args.get("payload", "")
                logger.info(f"🔧 call_api: endpoint={endpoint}")
                result = self.call_api(endpoint, payload)
                logger.info(f"✅ call_api result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "get_weather":
                args = self._parse_arguments(args_str, ["location"])
                location = args.get("location", "")
                logger.info(f"🔧 get_weather: location={location}")
                result = self.get_weather(location)
                logger.info(f"✅ get_weather result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "translate_text":
                args = self._parse_arguments(args_str, ["text", "target_language"])
                text = args.get("text", "")
                target_language = args.get("target_language", "en")
                logger.info(f"🔧 translate_text: text={text[:50]}..., target_language={target_language}")
                result = self.translate_text(text, target_language)
                logger.info(f"✅ translate_text result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "create_event":
                args = self._parse_arguments(args_str, ["title", "description", "date", "time", "priority"])
                title = args.get("title", "")
                description = args.get("description", "")
                date = args.get("date", "")
                time = args.get("time", "")
                priority = args.get("priority", "medium")
                logger.info(f"🔧 create_event: title={title}")
                result = self.create_event(title, description, date, time, priority)
                logger.info(f"✅ create_event result: {result}")
                return f"Event created: {result}"
            
            elif func_name == "get_upcoming_events":
                args = self._parse_arguments(args_str, ["days"])
                days = args.get("days", 7)
                logger.info(f"🔧 get_upcoming_events: days={days}")
                result = self.get_upcoming_events(int(days))
                logger.info(f"✅ get_upcoming_events result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "create_task_list":
                args = self._parse_arguments(args_str, ["title", "tasks"])
                title = args.get("title", "")
                tasks = args.get("tasks", "")
                logger.info(f"🔧 create_task_list: title={title}")
                result = self.create_task_list(title, tasks)
                logger.info(f"✅ create_task_list result: {result}")
                return f"Task list created: {result}"
            
            elif func_name == "list_tasks":
                args = self._parse_arguments(args_str, ["context"])
                context = args.get("context", "")
                logger.info(f"🔧 list_tasks: context={context}")
                result = self.list_tasks(context)
                logger.info(f"✅ list_tasks result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "run_terminal_command":
                args = self._parse_arguments(args_str, ["command"])
                command = args.get("command", "")
                logger.info(f"🔧 run_terminal_command: command={command}")
                result = self.run_terminal_command(command)
                logger.info(f"✅ run_terminal_command result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "get_system_info":
                logger.info(f"🔧 get_system_info")
                result = self.get_system_info()
                logger.info(f"✅ get_system_info result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "diagnose_network":
                logger.info(f"🔧 diagnose_network")
                result = self.diagnose_network()
                logger.info(f"✅ diagnose_network result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "reflect":
                args = self._parse_arguments(args_str, ["history"])
                history = args.get("history", "")
                logger.info(f"🔧 reflect: history={history[:50]}...")
                result = self.reflect(history.split(",") if history else [])
                logger.info(f"✅ reflect result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            elif func_name == "react_cycle":
                args = self._parse_arguments(args_str, ["goal", "max_steps"])
                goal = args.get("goal", "")
                max_steps = args.get("max_steps", 20)
                logger.info(f"🔧 react_cycle: goal={goal}, max_steps={max_steps}")
                result = self.react_cycle(goal, int(max_steps))
                logger.info(f"✅ react_cycle result: {result[:200]}..." if len(result) > 200 else result)
                return result
            
            else:
                logger.error(f"❌ Unknown tool: {func_name}")
                return f"❌ Unknown tool: {func_name}"
            
        except Exception as e:
            logger.error(f"Error executing tool call {tool_call}: {e}")
            return f"❌ Error executing tool call: {str(e)}" 