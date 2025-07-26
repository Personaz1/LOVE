# Multi-Step Reasoning Architecture

## Overview

ΔΣ Guardian теперь использует продвинутую multi-step reasoning архитектуру, которая разделяет процесс генерации ответа на два этапа:

1. **Thinking Phase** - анализ и выполнение tool calls
2. **Response Phase** - генерация финального ответа

## Архитектура

### Step 1: Thinking Phase
```
User Message → Thinking Prompt → Model Response → Extract Tool Calls → Execute Tools
```

**Thinking Prompt включает:**
- System prompt (ΔΣ Guardian identity)
- User profile и emotional history
- Conversation context
- Tool calling instructions
- Примеры использования tool_code блоков

**Tool Code Format:**
```markdown
```tool_code
update_current_feeling("username", "feeling", "context")
```
```

### Step 2: Response Phase
```
Tool Results → Final Prompt → Streaming Response → User
```

**Final Prompt включает:**
- Original system prompt
- User message
- Thinking phase results
- Tool execution results
- Instructions для финального ответа

## Available Tools

### Emotional Management
- `update_current_feeling(username, feeling, context)` - обновление эмоционального состояния
- `update_relationship_status(username, status)` - обновление статуса отношений
- `update_user_profile(username, profile_data)` - обновление профиля

### Data Access
- `read_user_profile(username)` - чтение профиля пользователя
- `read_emotional_history(username)` - чтение эмоциональной истории
- `read_diary_entries(username)` - чтение дневниковых записей
- `search_user_data(username, query)` - поиск по данным пользователя

### File System Operations
- `read_file(path)` - чтение файлов
- `write_file(path, content)` - запись в файлы
- `list_files(directory)` - список файлов
- `search_files(query)` - поиск файлов
- `get_file_info(path)` - информация о файле
- `delete_file(path)` - удаление файлов

### Relationship Insights
- `add_diary_entry(username, entry)` - добавление записи в дневник
- `add_relationship_insight(insight)` - добавление инсайта

## Implementation Details

### Tool Call Extraction
```python
def _extract_tool_calls(self, text: str) -> List[str]:
    tool_code_pattern = r'```tool_code\s*\n(.*?)\n```'
    matches = re.findall(tool_code_pattern, text, re.DOTALL)
    return [match.strip() for match in matches]
```

### Tool Execution
```python
def _execute_tool_call(self, tool_call: str) -> str:
    # Parse function name and arguments
    # Execute appropriate method
    # Return result string
```

### Streaming Response
```python
async def _generate_gemini_streaming_response(self, ...):
    # Step 1: Thinking phase
    thinking_prompt = self._build_thinking_prompt(...)
    initial_response = self.gemini_model.generate_content(thinking_prompt)
    tool_calls = self._extract_tool_calls(initial_response.text)
    
    # Execute tools
    tool_results = []
    for tool_call in tool_calls:
        result = self._execute_tool_call(tool_call)
        tool_results.append(f"Tool {tool_call} returned: {result}")
    
    # Step 2: Final response
    final_prompt = self._build_final_prompt(..., tool_results)
    response_stream = self.gemini_model.generate_content(final_prompt, stream=True)
    
    for chunk in response_stream:
        yield chunk.text
```

## Benefits

1. **Proper Tool Separation** - tool calls выполняются отдельно от пользовательского ответа
2. **Context Awareness** - модель имеет доступ к результатам выполнения инструментов
3. **Streaming Support** - финальный ответ стримится пользователю
4. **Error Handling** - ошибки tool execution не влияют на основной ответ
5. **Multi-Step Reasoning** - модель может думать, действовать, и затем отвечать

## Example Flow

```
User: "я чувствую себя счастливой сегодня"

Thinking Phase:
```tool_code
update_current_feeling("meranda", "Happy", "User expressed happiness")
```
I need to update the user's emotional state since they're expressing happiness.

Tool Execution:
Tool update_current_feeling("meranda", "Happy", "User expressed happiness") returned: Updated feeling to 'Happy' for meranda

Response Phase:
That's wonderful to hear! I'm so glad you're feeling happy today. Happiness is such a beautiful emotion that can brighten not just your day, but also positively impact your relationships...
```

## Testing

Запустите тест:
```bash
python3 test_multi_step_reasoning.py
```

Или протестируйте через веб-интерфейс:
```bash
python3 web_app.py
# Откройте http://localhost:8000/chat?username=meranda&password=musser
```

## Future Enhancements

1. **Tool Chaining** - возможность цепочки инструментов
2. **Conditional Execution** - условное выполнение инструментов
3. **Tool Validation** - валидация параметров инструментов
4. **Tool Caching** - кэширование результатов
5. **Tool Metrics** - метрики использования инструментов 