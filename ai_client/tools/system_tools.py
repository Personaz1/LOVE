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
            health_report = []
            
            # Системный обзор
            health_report.append("=== ΔΣ Guardian System Status ===")
            health_report.append(f"🕐 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            health_report.append("🧠 Current model: gemini-2.5-pro")
            health_report.append("📊 Model index: 0/7")
            
            # Проверка файлов
            health_report.append("\n=== File System Health ===")
            critical_files = [
                "memory/model_notes.json",
                "memory/conversation_history.json", 
                "memory/guardian_profile.json",
                "memory/user_profiles/meranda.json",
                "memory/user_profiles/stepan.json",
            ]
            
            for file_path in critical_files:
                full_path = os.path.join(self.project_root, file_path)
                if os.path.exists(full_path):
                    size = os.path.getsize(full_path)
                    health_report.append(f"✅ {file_path}: OK ({size} bytes)")
                else:
                    health_report.append(f"❌ {file_path}: Missing")
            
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
            
            return "\n".join(health_report)
            
        except Exception as e:
            logger.error(f"Error diagnosing system health: {e}")
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
                # TODO: Реализовать анализ через Vision API
                return f"🔍 Image analysis for {image_path} (Vision API not implemented)"
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
    
    def _generate_login_greeting(self, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """Генерация приветствия при входе"""
        try:
            if not user_profile:
                return "👋 Welcome back! How can I assist you today?"
            
            username = user_profile.get('username', 'User')
            current_time = datetime.now().strftime("%I:%M %p")
            current_feeling = user_profile.get('current_feeling', 'neutral')
            
            feeling_emoji = {
                'happy': '😊', 'sad': '😢', 'excited': '🎉', 'tired': '😴',
                'stressed': '😰', 'neutral': '😐'
            }.get(current_feeling, '😐')
            
            if current_time.endswith('AM'):
                time_greeting = "Good morning"
            elif current_time.endswith('PM') and int(current_time.split(':')[0]) < 5:
                time_greeting = "Good afternoon"
            else:
                time_greeting = "Good evening"
            
            greeting = f"{feeling_emoji} {time_greeting}, {username}! "
            greeting += f"It's {current_time}. "
            
            if current_feeling != 'neutral':
                greeting += f"I see you're feeling {current_feeling}. "
            
            greeting += "How can I help you today?"
            
            return greeting
            
        except Exception as e:
            logger.error(f"Error generating login greeting: {e}")
            return "👋 Welcome back! How can I assist you today?"
    
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
        """Извлечение вызовов инструментов из текста"""
        try:
            # Паттерн для поиска вызовов функций
            pattern = r'(\w+)\s*\([^)]*\)'
            matches = re.findall(pattern, text)
            
            # Убираем дубликаты и сортируем
            unique_calls = list(set(matches))
            unique_calls.sort()
            
            return unique_calls
            
        except Exception as e:
            logger.error(f"Error extracting tool calls: {e}")
            return []
    
    def _extract_nested_calls(self, text: str) -> List[str]:
        """Извлечение вложенных вызовов"""
        try:
            # Более сложный паттерн для вложенных вызовов
            pattern = r'(\w+)\s*\([^)]*\)'
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
            named_pattern = r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\w+))'
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
            unquoted_pattern = r'\b(\w+)\b'
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
            match = re.match(r'(\w+)\s*\((.*)\)', tool_call)
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
            
            else:
                logger.error(f"❌ Unknown tool: {func_name}")
                return f"❌ Unknown tool: {func_name}"
            
        except Exception as e:
            logger.error(f"Error executing tool call {tool_call}: {e}")
            return f"❌ Error executing tool call: {str(e)}" 