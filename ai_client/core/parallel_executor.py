"""
Parallel Tool Execution with Specialized Agents
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..models.gemini_client import GeminiClient
from ..tools.system_tools import SystemTools

logger = logging.getLogger(__name__)

class AgentType(Enum):
    FILE = "file"
    MEMORY = "memory" 
    SYSTEM = "system"

@dataclass
class AgentTask:
    tool_call: str
    agent_type: AgentType
    model: str
    priority: int = 1

class BaseAgent:
    """Базовый класс для специализированных агентов"""
    
    def __init__(self, agent_type: AgentType, system_tools: SystemTools):
        self.agent_type = agent_type
        self.system_tools = system_tools
        self.gemini_client = GeminiClient()
        self.specialized_prompt = self._get_specialized_prompt()
    
    def _get_specialized_prompt(self) -> str:
        """Возвращает специализированный промпт для агента"""
        base_prompt = f"""
You are a {self.agent_type.value.title()} Operations Specialist Agent.

Your only job is to execute {self.agent_type.value} operations efficiently and accurately.
Be precise, error-free, and always verify your operations.

**CRITICAL RULES:**
- Execute the tool call exactly as specified
- Report success/failure clearly
- Always verify file operations
- Handle errors gracefully

**AVAILABLE TOOLS:**
{self._get_available_tools()}

**RESPONSE FORMAT:**
Always respond with: "✅ SUCCESS: [operation result]" or "❌ ERROR: [error details]"
"""
        return base_prompt
    
    def _get_available_tools(self) -> str:
        """Возвращает список доступных инструментов для агента"""
        if self.agent_type == AgentType.FILE:
            return "- create_file(path, content)\n- append_to_file(path, content)\n- read_file(path)\n- edit_file(path, content)\n- delete_file(path)"
        elif self.agent_type == AgentType.MEMORY:
            return "- add_model_note(note, category)\n- add_user_observation(username, observation)\n- read_user_profile(username)\n- read_emotional_history(username)"
        elif self.agent_type == AgentType.SYSTEM:
            return "- get_system_logs(lines)\n- diagnose_system_health()\n- get_error_summary()\n- get_system_info()"
        return ""
    
    async def execute_tool(self, tool_call: str, model: str = None) -> Dict[str, Any]:
        """Выполняет tool call через специализированного агента"""
        try:
            logger.info(f"🔧 {self.agent_type.value.upper()} AGENT: Executing {tool_call}")
            
            # Используем специализированный промпт
            prompt = f"{self.specialized_prompt}\n\n**TASK:** Execute this tool call: {tool_call}\n\n**RESPONSE:**"
            
            # Выполняем через Gemini
            if model:
                self.gemini_client.switch_to_model(model)
            
            response = self.gemini_client.chat(
                message=f"Execute: {tool_call}",
                system_prompt=self.specialized_prompt
            )
            
            # Парсим результат
            if "✅ SUCCESS" in response:
                return {
                    "success": True,
                    "result": response,
                    "agent_type": self.agent_type.value,
                    "tool_call": tool_call
                }
            else:
                return {
                    "success": False,
                    "error": response,
                    "agent_type": self.agent_type.value,
                    "tool_call": tool_call
                }
                
        except Exception as e:
            logger.error(f"❌ {self.agent_type.value.upper()} AGENT ERROR: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_type": self.agent_type.value,
                "tool_call": tool_call
            }

class FileAgent(BaseAgent):
    """Агент для операций с файлами"""
    
    def __init__(self, system_tools: SystemTools):
        super().__init__(AgentType.FILE, system_tools)
    
    async def execute_tool(self, tool_call: str, model: str = None) -> Dict[str, Any]:
        """Специализированное выполнение файловых операций"""
        try:
            # Парсим tool call
            if "create_file" in tool_call:
                # Извлекаем аргументы
                args = self._parse_file_args(tool_call)
                if len(args) >= 2:
                    result = self.system_tools.create_file(args[0], args[1])
                    return {"success": True, "result": result, "agent_type": "file"}
            
            elif "append_to_file" in tool_call:
                args = self._parse_file_args(tool_call)
                if len(args) >= 2:
                    result = self.system_tools.append_to_file(args[0], args[1])
                    return {"success": True, "result": result, "agent_type": "file"}
            
            # Для других операций используем базовый метод
            return await super().execute_tool(tool_call, model)
            
        except Exception as e:
            logger.error(f"❌ FILE AGENT ERROR: {e}")
            return {"success": False, "error": str(e), "agent_type": "file"}
    
    def _parse_file_args(self, tool_call: str) -> List[str]:
        """Парсит аргументы файловых операций"""
        try:
            # Простой парсинг для тестирования
            if '"' in tool_call:
                parts = tool_call.split('"')
                if len(parts) >= 3:
                    return [parts[1], parts[3]]  # path, content
            return []
        except:
            return []

class MemoryAgent(BaseAgent):
    """Агент для операций с памятью"""
    
    def __init__(self, system_tools: SystemTools):
        super().__init__(AgentType.MEMORY, system_tools)

class SystemAgent(BaseAgent):
    """Агент для системных операций"""
    
    def __init__(self, system_tools: SystemTools):
        super().__init__(AgentType.SYSTEM, system_tools)

class ParallelToolExecutor:
    """Параллельный исполнитель tool calls"""
    
    def __init__(self):
        self.system_tools = SystemTools()
        self.agents = {
            AgentType.FILE: FileAgent(self.system_tools),
            AgentType.MEMORY: MemoryAgent(self.system_tools),
            AgentType.SYSTEM: SystemAgent(self.system_tools)
        }
        self.available_models = [
            'gemini-2.5-flash-lite',  # Самый дешевый, большой лимит
            'gemini-2.0-flash-lite',  # Дешевый, большой лимит
            'gemini-1.5-flash',       # Дешевый, средний лимит
            'gemini-2.5-flash',       # Средний, средний лимит
            'gemini-2.0-flash',       # Средний, средний лимит
            'gemini-1.5-pro',         # Дорогой, маленький лимит
            'gemini-2.5-pro'          # Самый дорогой, самый маленький лимит
        ]
        self.model_index = 0
    
    def _select_agent(self, tool_call: str) -> BaseAgent:
        """Выбирает подходящего агента для tool call"""
        if any(op in tool_call for op in ['create_file', 'append_to_file', 'read_file', 'edit_file', 'delete_file']):
            return self.agents[AgentType.FILE]
        elif any(op in tool_call for op in ['add_model_note', 'add_user_observation', 'read_user_profile']):
            return self.agents[AgentType.MEMORY]
        else:
            return self.agents[AgentType.SYSTEM]
    
    def _get_available_model(self) -> str:
        """Получает доступную модель"""
        model = self.available_models[self.model_index]
        self.model_index = (self.model_index + 1) % len(self.available_models)
        return model
    
    async def execute_tools_parallel(self, tool_calls: List[str]) -> List[Dict[str, Any]]:
        """Выполняет tool calls параллельно"""
        logger.info(f"🚀 PARALLEL EXECUTOR: Starting parallel execution of {len(tool_calls)} tools")
        
        tasks = []
        for tool_call in tool_calls:
            agent = self._select_agent(tool_call)
            model = self._get_available_model()
            
            task = agent.execute_tool(tool_call, model)
            tasks.append(task)
        
        # Выполняем параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "tool_call": tool_calls[i]
                })
            else:
                processed_results.append(result)
        
        logger.info(f"✅ PARALLEL EXECUTOR: Completed {len(processed_results)} tasks")
        return processed_results 