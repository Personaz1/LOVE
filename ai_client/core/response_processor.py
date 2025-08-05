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
        
        for pattern in self.tool_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                try:
                    function_name = match.group(1)
                    args_str = match.group(2)
                    
                    # Парсим аргументы
                    arguments = self._parse_arguments(args_str)
                    
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
        
        # Если нет аргументов
        if not args_str:
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
            
            # Получаем функцию из ai_client
            if hasattr(self.ai_client, 'system_tools'):
                tool_instance = self.ai_client.system_tools
            else:
                tool_instance = self.ai_client
            
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
                else:
                    # Для других функций - передаем аргументы позиционно
                    if arguments:
                        # Сортируем аргументы по ключам arg_0, arg_1, etc.
                        sorted_args = []
                        i = 0
                        while f'arg_{i}' in arguments:
                            sorted_args.append(arguments[f'arg_{i}'])
                            i += 1
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
        # Убираем одиночные python
        text = re.sub(r'^python\s*$', '', text, flags=re.MULTILINE)
        return text.strip() 