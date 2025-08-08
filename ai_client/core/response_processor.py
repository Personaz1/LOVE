"""
Response Processor - Правильная обработка ответов модели
Разделяет парсинг tool calls и форматирование для чата
"""

import re
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ToolCall:
    """Структура для tool call"""
    function_name: str
    arguments: Dict[str, Any]
    original_text: str
    start_pos: int
    end_pos: int

@dataclass
class ProcessedResponse:
    """Результат обработки ответа"""
    original_text: str
    tool_calls: List[ToolCall]
    formatted_text: str
    tool_results: List[Dict[str, Any]]

class ToolExtractor:
    """Простой экстрактор tool calls"""
    
    def __init__(self):
        # Простые паттерны для поиска tool calls
        self.tool_patterns = [
            r'SystemTools\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*(.*?)\s*\)',
            r'VisionTools\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*(.*?)\s*\)',
        ]
    
    def extract_tool_calls(self, text: str) -> List[ToolCall]:
        """Извлекает tool calls из текста"""
        tool_calls = []
        seen = set()
        
        for pattern in self.tool_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                try:
                    function_name = match.group(1)
                    args_str = match.group(2)
                    
                    # Парсим аргументы
                    arguments = self._parse_arguments(args_str)
                    
                    key = (function_name, args_str.strip())
                    if key in seen:
                        continue
                    seen.add(key)

                    tool_call = ToolCall(
                        function_name=function_name,
                        arguments=arguments,
                        original_text=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    
                    tool_calls.append(tool_call)
                    logger.info(f"🔧 TOOL EXTRACTOR: Found tool call: {function_name}({arguments})")
                    
                except Exception as e:
                    logger.error(f"❌ TOOL EXTRACTOR: Error parsing tool call: {e}")
        
        return tool_calls
    
    def _parse_arguments(self, args_str: str) -> Dict[str, Any]:
        """Парсит аргументы tool call"""
        arguments = {}
        args_str = args_str.strip()
        
        # Если нет аргументов или пустые скобки
        if not args_str or args_str == '{}':
            return arguments
        
        # Ищем первый аргумент (путь к файлу)
        first_quote = args_str.find('"')
        if first_quote != -1:
            end_quote = args_str.find('"', first_quote + 1)
            if end_quote != -1:
                file_path = args_str[first_quote + 1:end_quote]
                arguments["arg_0"] = file_path
                
                # Ищем второй аргумент (содержимое)
                remaining = args_str[end_quote + 1:].strip()
                if remaining.startswith(','):
                    remaining = remaining[1:].strip()
                
                # Если есть второй аргумент
                if remaining.startswith('"'):
                    # Берем все что осталось как контент
                    content = remaining[1:]  # Убираем первую кавычку
                    arguments["arg_1"] = content
                else:
                    # Если нет кавычки, берем все что осталось
                    arguments["arg_1"] = remaining
        
        return arguments

class ToolExecutor:
    """Выполняет tool calls"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
    
    def execute_tool_call(self, tool_call: ToolCall, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Выполняет tool call"""
        try:
            function_name = tool_call.function_name
            arguments = tool_call.arguments
            
            # Определяем целевой набор инструментов по имени функции
            # По умолчанию используем системные инструменты
            tool_instance = getattr(self.ai_client, 'system_tools', self.ai_client)

            # Функции зрения, которые должны исполняться через VisionTools
            vision_functions = {
                'list_cameras',
                'capture_image',
                'detect_motion',
                'get_camera_status',
            }

            # Если обнаружили вызов функции зрения — маршрутизируем в VisionTools
            if function_name in vision_functions and hasattr(self.ai_client, 'vision_tools'):
                tool_instance = self.ai_client.vision_tools
            
            if hasattr(tool_instance, function_name):
                func = getattr(tool_instance, function_name)
                
                # Вызываем функцию с аргументами
                if function_name in ['create_file', 'append_to_file']:
                    # Для файловых операций
                    file_path = arguments.get('arg_0', '')
                    content = arguments.get('arg_1', '')
                    
                    if function_name == 'create_file':
                        result = func(file_path, content)
                    else:  # append_to_file
                        result = func(file_path, content)
                    
                    return {
                        'success': True,
                        'result': result,
                        'function': function_name,
                        'file_path': file_path
                    }
                elif function_name == 'read_file':
                    # Для read_file - только путь к файлу
                    file_path = arguments.get('arg_0', '')
                    result = func(file_path)
                    return {
                        'success': True,
                        'result': result,
                        'function': function_name,
                        'file_path': file_path
                    }
                elif function_name == 'list_files':
                    # Для list_files - только директория
                    directory = arguments.get('arg_0', '.')
                    result = func(directory)
                    return {
                        'success': True,
                        'result': result,
                        'function': function_name,
                        'directory': directory
                    }
                elif function_name == 'analyze_file':
                    # Для analyze_file - file_path и user_context
                    if arguments:
                        # Сортируем аргументы по ключам arg_0, arg_1, etc.
                        sorted_args = []
                        i = 0
                        while f'arg_{i}' in arguments:
                            sorted_args.append(arguments[f'arg_{i}'])
                            i += 1
                        # Убираем пустые хвостовые аргументы
                        while sorted_args and (sorted_args[-1] is None or (isinstance(sorted_args[-1], str) and sorted_args[-1].strip() == '')):
                            sorted_args.pop()
                        result = func(*sorted_args)
                    else:
                        # Если нет аргументов, возвращаем ошибку
                        return {
                            'success': False,
                            'error': 'analyze_file requires at least one argument (file_path)'
                        }
                    return {
                        'success': True,
                        'result': result,
                        'function': function_name
                    }
                elif function_name == 'analyze_image':
                    # Явная поддержка VisionTools.analyze_image(image_path)
                    # Маршрутизируем в VisionTools при наличии
                    tool_for_call = tool_instance
                    if hasattr(self.ai_client, 'vision_tools'):
                        tool_for_call = self.ai_client.vision_tools
                        func = getattr(tool_for_call, function_name, func)
                    # Собираем позиционные аргументы
                    if arguments:
                        sorted_args = []
                        i = 0
                        while f'arg_{i}' in arguments:
                            sorted_args.append(arguments[f'arg_{i}'])
                            i += 1
                        # Убираем пустые хвостовые аргументы
                        while sorted_args and (sorted_args[-1] is None or (isinstance(sorted_args[-1], str) and sorted_args[-1].strip() == '')):
                            sorted_args.pop()
                        result = func(*sorted_args)
                        # Auto-log insight to memory graph if possible
                        try:
                            image_path = sorted_args[0] if sorted_args else ''
                            if image_path:
                                analysis_json = image_path.rsplit('.', 1)[0] + '_analysis.json'
                                import os, json, datetime
                                if os.path.exists(analysis_json):
                                    with open(analysis_json, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                    # Сформируем краткий инсайт
                                    gv = data.get('google_vision') or {}
                                    basics = data.get('basic') or {}
                                    labels = ', '.join((gv.get('labels') or [])[:5])
                                    objects = ', '.join((gv.get('objects') or [])[:5])
                                    faces = gv.get('faces_detected')
                                    dims = basics.get('dimensions')
                                    insight = (
                                        f"Image {os.path.basename(image_path)} | {dims} | "
                                        f"GV labels: {labels or '—'} | GV objects: {objects or '—'} | GV faces: {faces}"
                                    )
                                    title = datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + ' - Vision Insight'
                                    content = f"\n## {title}\n- {insight}\n"
                                    # Append to memory graph
                                    if hasattr(self.ai_client, 'system_tools'):
                                        self.ai_client.system_tools.append_to_file('guardian_sandbox/memory_graph.md', content)
                        except Exception:
                            pass
                    else:
                        return {
                            'success': False,
                            'error': 'analyze_image requires image_path'
                        }
                    return {
                        'success': True,
                        'result': result,
                        'function': function_name
                    }
                else:
                    # Для других функций - передаем аргументы позиционно
                    if arguments:
                        # Сортируем аргументы по ключам arg_0, arg_1, etc.
                        sorted_args = []
                        i = 0
                        while f'arg_{i}' in arguments:
                            sorted_args.append(arguments[f'arg_{i}'])
                            i += 1
                        # Убираем пустые хвостовые аргументы
                        while sorted_args and (sorted_args[-1] is None or (isinstance(sorted_args[-1], str) and sorted_args[-1].strip() == '')):
                            sorted_args.pop()
                        result = func(*sorted_args)
                    else:
                        result = func()
                    return {
                        'success': True,
                        'result': result,
                        'function': function_name
                    }
            else:
                return {
                    'success': False,
                    'error': f'Function {function_name} not found'
                }
                
        except Exception as e:
            logger.error(f"❌ TOOL EXECUTOR: Error executing {tool_call.function_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

class ResponseFormatter:
    """Форматирует ответы для чата"""
    
    def format_for_chat(self, text: str, tool_results: List[Dict[str, Any]]) -> str:
        """Форматирует ответ для отображения в чате"""
        formatted_text = text
        
        # Добавляем результаты выполнения инструментов
        for result in tool_results:
            if result.get('success'):
                formatted_text += f"\n\n✅ {result.get('result', '')}"
            else:
                formatted_text += f"\n\n❌ Error: {result.get('error', '')}"
        
        return formatted_text

class ResponseProcessor:
    """Обрабатывает ответы AI"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.tool_extractor = ToolExtractor()
        self.tool_executor = ToolExecutor(ai_client)
        self.response_formatter = ResponseFormatter()
    
    async def process_complete_response(self, text: str, context: Dict[str, Any] = None) -> ProcessedResponse:
        """Обрабатывает полный ответ"""
        # Извлекаем tool calls
        tool_calls = self.tool_extractor.extract_tool_calls(text)
        
        # Выполняем tool calls
        tool_results = []
        for tool_call in tool_calls:
            result = self.tool_executor.execute_tool_call(tool_call, context)
            tool_results.append(result)
        
        # Форматируем ответ
        formatted_text = self.response_formatter.format_for_chat(text, tool_results)
        
        return ProcessedResponse(
            original_text=text,
            tool_calls=tool_calls,
            formatted_text=formatted_text,
            tool_results=tool_results
        )
    
    async def process_streaming_response(self, text_stream):
        """Обрабатывает стриминг ответ"""
        full_text = ""
        async for chunk in text_stream:
            full_text += chunk
            yield chunk
        
        # После получения полного ответа обрабатываем tool calls
        if full_text:
            processed = await self.process_complete_response(full_text)
            if processed.tool_calls:
                # Отправляем результаты выполнения
                for result in processed.tool_results:
                    if result.get('success'):
                        yield f"\n\n✅ {result.get('result', '')}"
                    else:
                        yield f"\n\n❌ Error: {result.get('error', '')}"
    
    def _clean_ai_internal_code(self, text: str) -> str:
        """Очищает внутренний код AI из ответа"""
        # Убираем python блоки
        text = re.sub(r'```python\s*\n.*?\n```', '', text, flags=re.DOTALL)
        # Убираем tool_code блоки
        text = re.sub(r'```tool_code\s*\n.*?\n```', '', text, flags=re.DOTALL)
        # Убираем строки, начинающиеся с 'tool_code' и следующий JSON/вставку кода до пустой строки
        text = re.sub(r'^tool_code\n[\s\S]*?(?:\n\s*\n|$)', '', text, flags=re.MULTILINE)
        # Убираем одиночные python
        text = re.sub(r'^python\s*$', '', text, flags=re.MULTILINE)
        # Убираем лишние тройные бектики без языка
        text = re.sub(r'```\s*\n[\s\S]*?\n```', '', text, flags=re.DOTALL)
        return text.strip() 