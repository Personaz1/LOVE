"""
Response Processor - Правильная обработка ответов модели
Разделяет парсинг tool calls и форматирование для чата
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
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
    """Извлекает tool calls из оригинального текста (БЕЗ форматирования)"""
    
    def __init__(self):
        # Паттерны для поиска tool calls
        self.tool_patterns = [
            r'print\s*\(\s*tool_code\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*([^)]+)\s*\)\s*\)',
            r'tool_code\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*([^)]+)\s*\)',
        ]
        
        # Паттерн для извлечения tool_code из print
        self.print_tool_pattern = r'print\s*\(\s*tool_code\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*([^)]+)\s*\)\s*\)'
    
    def extract_tool_calls(self, text: str) -> List[ToolCall]:
        """Извлекает tool calls из текста"""
        tool_calls = []
        
        # Сначала ищем print(tool_code.function()) паттерны
        print_matches = re.finditer(self.print_tool_pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in print_matches:
            try:
                function_name = match.group(1)
                args_str = match.group(2)
                
                # Парсим аргументы
                arguments = self._parse_arguments(args_str)
                
                tool_call = ToolCall(
                    function_name=function_name,
                    arguments=arguments,
                    original_text=match.group(0),  # print(tool_code.function())
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                
                tool_calls.append(tool_call)
                logger.info(f"🔧 TOOL EXTRACTOR: Found print tool call: {function_name}({arguments})")
                
            except Exception as e:
                logger.error(f"❌ TOOL EXTRACTOR: Error parsing print tool call: {e}")
        
        # Затем ищем обычные tool_code.function() паттерны (НО ИСКЛЮЧАЕМ УЖЕ НАЙДЕННЫЕ)
        for pattern in self.tool_patterns[1:]:  # Пропускаем print паттерн
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                # Проверяем, не найден ли уже этот tool call в print паттернах
                already_found = False
                for existing_call in tool_calls:
                    if (match.start() >= existing_call.start_pos and 
                        match.end() <= existing_call.end_pos):
                        already_found = True
                        break
                
                if already_found:
                    continue
                
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
                    logger.info(f"🔧 TOOL EXTRACTOR: Found direct tool call: {function_name}({arguments})")
                    
                except Exception as e:
                    logger.error(f"❌ TOOL EXTRACTOR: Error parsing direct tool call: {e}")
        
        return tool_calls
    
    def _parse_arguments(self, args_str: str) -> Dict[str, Any]:
        """Парсит аргументы tool call"""
        arguments = {}
        
        # Очищаем строку аргументов
        args_str = args_str.strip()
        
        # Ищем именованные аргументы: name=value
        named_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*["\']([^"\']*)["\']'
        named_matches = re.findall(named_pattern, args_str)
        
        for name, value in named_matches:
            arguments[name] = value
        
        # Если нет именованных аргументов, берем позиционные
        if not arguments:
            # Разделяем по запятой, но учитываем кавычки
            parts = re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', args_str)
            for i, part in enumerate(parts):
                part = part.strip().strip('"\'')
                if part:
                    # Если это переменная без кавычек, сохраняем как есть
                    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', part):
                        arguments[f"arg_{i}"] = part
                    else:
                        arguments[f"arg_{i}"] = part
        
        return arguments

class ToolExecutor:
    """Выполняет tool calls"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
    
    async def execute_tool_call(self, tool_call: ToolCall, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Выполняет один tool call"""
        try:
            logger.info(f"🔧 TOOL EXECUTOR: Executing {tool_call.function_name}")
            
            # Получаем функцию из ai_client
            tool_function = getattr(self.ai_client, tool_call.function_name, None)
            if not tool_function:
                raise Exception(f"Tool function {tool_call.function_name} not found")
            
            # Разрешаем переменные в аргументах
            resolved_arguments = {}
            for key, value in tool_call.arguments.items():
                if isinstance(value, str) and value == 'user_profile' and context:
                    # Получаем user_profile из контекста
                    resolved_arguments[key] = context.get('user_profile')
                else:
                    resolved_arguments[key] = value
            
            # Выполняем функцию с разрешенными аргументами
            result = await tool_function(**resolved_arguments)
            
            return {
                'success': True,
                'function': tool_call.function_name,
                'arguments': tool_call.arguments,
                'result': result,
                'original_text': tool_call.original_text
            }
            
        except Exception as e:
            logger.error(f"❌ TOOL EXECUTOR: Error executing {tool_call.function_name}: {e}")
            return {
                'success': False,
                'function': tool_call.function_name,
                'arguments': tool_call.arguments,
                'error': str(e),
                'original_text': tool_call.original_text
            }

class ResponseFormatter:
    """Форматирует ответ для чата (ПОСЛЕ парсинга)"""
    
    def format_for_chat(self, text: str, tool_results: List[Dict[str, Any]]) -> str:
        """Форматирует текст для чата с результатами tools"""
        formatted_text = text
        
        # Заменяем tool calls на результаты
        for result in tool_results:
            if result['success']:
                replacement = f"\n\n**Результат выполнения:**\n{result['result']}\n\n"
            else:
                replacement = f"\n\n**Ошибка выполнения:**\n{result['error']}\n\n"
            
            # Заменяем оригинальный tool call на результат
            formatted_text = formatted_text.replace(result['original_text'], replacement)
        
        return formatted_text

class ResponseProcessor:
    """Главный процессор ответов модели"""
    
    def __init__(self, ai_client):
        self.tool_extractor = ToolExtractor()
        self.tool_executor = ToolExecutor(ai_client)
        self.response_formatter = ResponseFormatter()
        self.ai_client = ai_client  # Сохраняем для доступа к переменным
    
    async def process_complete_response(self, text: str, context: Dict[str, Any] = None) -> ProcessedResponse:
        """Обрабатывает полный ответ модели"""
        logger.info(f"🔧 RESPONSE PROCESSOR: Processing response ({len(text)} chars)")
        
        # 1. Извлекаем tool calls из оригинального текста
        tool_calls = self.tool_extractor.extract_tool_calls(text)
        logger.info(f"🔧 RESPONSE PROCESSOR: Found {len(tool_calls)} tool calls")
        
        # 2. Выполняем tool calls с контекстом
        tool_results = []
        for tool_call in tool_calls:
            result = await self.tool_executor.execute_tool_call(tool_call, context)
            tool_results.append(result)
        
        # 3. Форматируем для чата
        formatted_text = self.response_formatter.format_for_chat(text, tool_results)
        
        return ProcessedResponse(
            original_text=text,
            tool_calls=tool_calls,
            formatted_text=formatted_text,
            tool_results=tool_results
        )
    
    async def process_streaming_response(self, text_stream):
        """Обрабатывает потоковый ответ модели"""
        # Собираем полный текст
        full_text = ""
        
        async for chunk in text_stream:
            full_text += chunk
            yield chunk
        
        # Обрабатываем tool calls после получения полного текста
        processed = await self.process_complete_response(full_text)
        
        # Если есть результаты tool calls, заменяем весь текст
        if processed.tool_results:
            # Возвращаем только форматированный текст (без дублирования)
            yield processed.formatted_text 