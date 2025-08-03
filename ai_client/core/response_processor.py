"""
Response Processor - Правильная обработка ответов модели
Разделяет парсинг tool calls и форматирование для чата
"""

import re
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass

from ..tools.system_tools import SystemTools
from .parallel_executor import ParallelToolExecutor

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
        """Извлекает tool calls из текста с поддержкой многострочных строк"""
        tool_calls = []
        
        # Сначала ищем print(tool_code.function()) паттерны
        print_matches = re.finditer(self.tool_patterns[0], text, re.MULTILINE | re.DOTALL)
        
        for match in print_matches:
            try:
                function_name = match.group(1)
                args_str = match.group(2)
                
                # Проверяем на неполный вызов (учитываем многострочные строки)
                if not self._is_complete_tool_call(args_str):
                    logger.warning(f"⚠️ TOOL EXTRACTOR: Incomplete print tool call detected: {match.group(0)[:100]}...")
                    continue
                
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
                    
                    # Проверяем на неполный вызов (учитываем многострочные строки)
                    if not self._is_complete_tool_call(args_str):
                        logger.warning(f"⚠️ TOOL EXTRACTOR: Incomplete direct tool call detected: {match.group(0)[:100]}...")
                        continue
                    
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
    
    def _is_complete_tool_call(self, args_str: str) -> bool:
        """Проверяет, является ли tool call полным (учитывает многострочные строки)"""
        args_str = args_str.strip()
        
        # Если строка заканчивается на ), то это полный вызов
        if args_str.endswith(')'):
            return True
        
        # Проверяем баланс скобок и кавычек
        open_parens = args_str.count('(')
        close_parens = args_str.count(')')
        open_quotes = args_str.count('"') + args_str.count("'")
        
        # Если количество открывающих и закрывающих скобок равно
        # и количество кавычек четное, то это полный вызов
        if open_parens == close_parens and open_quotes % 2 == 0:
            return True
        
        # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: если есть \n внутри кавычек, это может быть полный вызов
        if '\n' in args_str:
            # Ищем последнюю кавычку после \n
            last_quote_pos = args_str.rfind('"')
            if last_quote_pos > args_str.find('\n'):
                # Проверяем, что после последней кавычки есть закрывающая скобка
                remaining = args_str[last_quote_pos + 1:].strip()
                if remaining.endswith(')'):
                    return True
        
        # АГРЕССИВНАЯ ПРОВЕРКА: если есть многострочное содержимое, считаем полным
        if args_str.count('"') >= 2 and args_str.count(')') > 0:
            # Если есть хотя бы две кавычки и закрывающая скобка, считаем полным
            return True
        
        return False
    
    def _parse_arguments(self, args_str: str) -> Dict[str, Any]:
        """Парсит аргументы tool call с улучшенной обработкой многострочных строк"""
        arguments = {}
        
        # Очищаем строку аргументов
        args_str = args_str.strip()
        
        # Проверяем на неполный вызов (без закрывающей скобки)
        if not args_str.endswith(')'):
            logger.warning(f"⚠️ TOOL EXTRACTOR: Incomplete tool call detected: {args_str}")
            # Пытаемся извлечь хотя бы первый аргумент
            if args_str.startswith('"') or args_str.startswith("'"):
                # Ищем закрывающую кавычку
                quote_char = args_str[0]
                end_quote = args_str.find(quote_char, 1)
                if end_quote != -1:
                    first_arg = args_str[1:end_quote]
                    arguments["arg_0"] = first_arg
                    logger.info(f"🔧 TOOL EXTRACTOR: Extracted first argument: {first_arg}")
                    return arguments
        
        # Ищем именованные аргументы: name=value
        named_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*["\']([^"\']*)["\']'
        named_matches = re.findall(named_pattern, args_str)
        
        for name, value in named_matches:
            arguments[name] = value
        
        # Если нет именованных аргументов, берем позиционные
        if not arguments:
            # Для многострочных строк используем более сложный парсинг
            if '\n' in args_str:
                # Многострочная строка - извлекаем первый и второй аргументы
                parts = self._parse_multiline_arguments(args_str)
                for i, part in enumerate(parts):
                    if part:
                        arguments[f"arg_{i}"] = part
            else:
                # Обычная однострочная строка
                parts = re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', args_str)
                for i, part in enumerate(parts):
                    part = part.strip()
                    if part:
                        # Убираем кавычки снаружи
                        if part.startswith('"') and part.endswith('"'):
                            part = part[1:-1]
                        elif part.startswith("'") and part.endswith("'"):
                            part = part[1:-1]
                        
                        # Обрабатываем f-строки - извлекаем содержимое
                        if part.startswith('f"') and part.endswith('"'):
                            part = part[2:-1]  # Убираем f" и "
                        elif part.startswith("f'") and part.endswith("'"):
                            part = part[2:-1]  # Убираем f' и '
                        
                        # Если это переменная без кавычек, сохраняем как есть
                        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', part):
                            arguments[f"arg_{i}"] = part
                        else:
                            arguments[f"arg_{i}"] = part
        
        return arguments
    
    def _parse_multiline_arguments(self, args_str: str) -> List[str]:
        """Парсит аргументы из многострочной строки"""
        parts = []
        
        # Убираем внешние скобки
        if args_str.startswith('(') and args_str.endswith(')'):
            args_str = args_str[1:-1]
        
        # Ищем первый аргумент (путь к файлу)
        first_quote = args_str.find('"')
        if first_quote != -1:
            # Ищем закрывающую кавычку для первого аргумента
            end_quote = args_str.find('"', first_quote + 1)
            if end_quote != -1:
                first_arg = args_str[first_quote + 1:end_quote]
                parts.append(first_arg)
                
                # Ищем второй аргумент (содержимое)
                remaining = args_str[end_quote + 1:].strip()
                if remaining.startswith(','):
                    remaining = remaining[1:].strip()
                
                # Извлекаем второй аргумент (многострочное содержимое)
                if remaining.startswith('"'):
                    # Ищем последнюю кавычку (учитываем экранирование и \n)
                    content_start = 1
                    content_end = remaining.rfind('"')
                    if content_end > content_start:
                        second_arg = remaining[content_start:content_end]
                        # Заменяем \n на реальные переносы строк
                        second_arg = second_arg.replace('\\n', '\n')
                        parts.append(second_arg)
        
        return parts

class ToolExecutor:
    """Выполняет tool calls"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
    
    def execute_tool_call(self, tool_call: ToolCall, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Выполняет один tool call"""
        try:
            logger.info(f"🔧 TOOL EXECUTOR: Executing {tool_call.function_name}")
            
            # Получаем функцию из system_tools
            system_tools = self.ai_client.system_tools
            tool_function = getattr(system_tools, tool_call.function_name, None)
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
            
            # Преобразуем именованные аргументы в позиционные
            positional_args = []
            for i in range(len(resolved_arguments)):
                arg_key = f"arg_{i}"
                if arg_key in resolved_arguments:
                    positional_args.append(resolved_arguments[arg_key])
            
            # Выполняем функцию с позиционными аргументами (не async)
            result = tool_function(*positional_args)
            
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
    """Обрабатывает ответы модели с разделением парсинга и форматирования"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.extractor = ToolExtractor()
        self.executor = ToolExecutor(ai_client)
        self.formatter = ResponseFormatter()
        self.parallel_executor = ParallelToolExecutor()  # Добавляем параллельный исполнитель
    
    async def process_complete_response(self, text: str, context: Dict[str, Any] = None) -> ProcessedResponse:
        """Обрабатывает полный ответ модели"""
        try:
            # Извлекаем tool calls
            tool_calls = self.extractor.extract_tool_calls(text)
            logger.info(f"🔧 RESPONSE PROCESSOR: Found {len(tool_calls)} tool calls")
            
            tool_results = []
            
            if tool_calls:
                # Пробуем параллельное выполнение для множественных tool calls
                if len(tool_calls) > 1:
                    logger.info(f"🚀 RESPONSE PROCESSOR: Using parallel execution for {len(tool_calls)} tools")
                    tool_call_strings = [tc.original_text for tc in tool_calls]
                    parallel_results = await self.parallel_executor.execute_tools_parallel(tool_call_strings)
                    tool_results = parallel_results
                else:
                    # Обычное последовательное выполнение для одного tool call
                    for tool_call in tool_calls:
                        result = self.executor.execute_tool_call(tool_call, context)
                        tool_results.append(result)
            
            # Форматируем ответ для чата
            formatted_text = self.formatter.format_for_chat(text, tool_results)
            
            return ProcessedResponse(
                original_text=text,
                tool_calls=tool_calls,
                formatted_text=formatted_text,
                tool_results=tool_results
            )
            
        except Exception as e:
            logger.error(f"❌ RESPONSE PROCESSOR ERROR: {e}")
            return ProcessedResponse(
                original_text=text,
                tool_calls=[],
                formatted_text=text,
                tool_results=[]
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
        
        # Если есть результаты tool calls, заменяем только tool calls на результаты
        if processed.tool_results:
            # Заменяем только tool calls, не весь текст
            for result in processed.tool_results:
                if result.get('success', False):
                    replacement = f"\n\n**Результат выполнения:**\n{result.get('result', '')}\n\n"
                else:
                    replacement = f"\n\n**Ошибка выполнения:**\n{result.get('error', '')}\n\n"
                
                # Заменяем оригинальный tool call на результат
                original_text = result.get('original_text', '')
                if original_text:
                    full_text = full_text.replace(original_text, replacement)
            
            # Возвращаем обновленный текст
            yield full_text 