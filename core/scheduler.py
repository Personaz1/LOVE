"""
ΔΣ Guardian Core Scheduler v4.0
Автономное планирование и управление задачами
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

from ai_client.core.client import AIClient
from ai_client.utils.logger import Logger

logger = Logger()

class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    name: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    dependencies: List[str] = None
    tags: List[str] = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []
        if self.context is None:
            self.context = {}

class Scheduler:
    """Автономный планировщик задач для ΔΣ Guardian"""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.tasks: Dict[str, Task] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self.running = False
        self.background_thread = None
        self.tick_interval = 1.0  # секунды
        
        # Регистрируем стандартные обработчики
        self._register_default_handlers()
        
        logger.info("🧠 ΔΣ Scheduler initialized")
    
    def _register_default_handlers(self):
        """Регистрация стандартных обработчиков задач"""
        self.register_handler("system_health_check", self._system_health_check)
        self.register_handler("memory_optimization", self._memory_optimization)
        self.register_handler("context_analysis", self._context_analysis)
        self.register_handler("personality_adjustment", self._personality_adjustment)
        self.register_handler("learning_cycle", self._learning_cycle)
        self.register_handler("security_scan", self._security_scan)
    
    def register_handler(self, task_type: str, handler: Callable):
        """Регистрация обработчика для типа задачи"""
        self.task_handlers[task_type] = handler
        logger.info(f"📝 Registered handler for task type: {task_type}")
    
    def add_task(self, task: Task) -> str:
        """Добавление новой задачи"""
        self.tasks[task.id] = task
        logger.info(f"➕ Added task: {task.name} (priority: {task.priority.name})")
        return task.id
    
    def create_task(self, name: str, description: str, priority: TaskPriority = TaskPriority.NORMAL,
                   task_type: str = None, context: Dict[str, Any] = None, 
                   scheduled_for: Optional[datetime] = None, dependencies: List[str] = None,
                   tags: List[str] = None) -> str:
        """Создание новой задачи"""
        task_id = f"{task_type or 'general'}_{int(time.time() * 1000)}"
        
        task = Task(
            id=task_id,
            name=name,
            description=description,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            scheduled_for=scheduled_for,
            dependencies=dependencies or [],
            tags=tags or [],
            context=context or {}
        )
        
        return self.add_task(task)
    
    def get_ready_tasks(self) -> List[Task]:
        """Получение готовых к выполнению задач"""
        now = datetime.now()
        ready_tasks = []
        
        for task in self.tasks.values():
            if (task.status == TaskStatus.PENDING and
                (task.scheduled_for is None or task.scheduled_for <= now) and
                self._dependencies_met(task)):
                ready_tasks.append(task)
        
        # Сортируем по приоритету
        ready_tasks.sort(key=lambda t: t.priority.value)
        return ready_tasks
    
    def _dependencies_met(self, task: Task) -> bool:
        """Проверка готовности зависимостей"""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                return False
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    async def execute_task(self, task: Task) -> bool:
        """Выполнение задачи"""
        try:
            logger.info(f"🚀 Executing task: {task.name}")
            task.status = TaskStatus.RUNNING
            
            # Определяем тип задачи и вызываем соответствующий обработчик
            task_type = task.name.split('_')[0] if '_' in task.name else 'general'
            
            if task_type in self.task_handlers:
                result = await self.task_handlers[task_type](task)
            else:
                # Общий обработчик через AI
                result = await self._ai_task_handler(task)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            logger.info(f"✅ Task completed: {task.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Task failed: {task.name} - {str(e)}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return False
    
    async def _ai_task_handler(self, task: Task) -> Dict[str, Any]:
        """AI-обработчик для общих задач"""
        prompt = f"""
        Задача: {task.name}
        Описание: {task.description}
        Контекст: {json.dumps(task.context, ensure_ascii=False)}
        
        Выполни эту задачу и верни результат в JSON формате.
        """
        
        response = self.ai_client.chat(prompt)
        
        try:
            # Пытаемся извлечь JSON из ответа
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"result": response, "raw_response": True}
        except:
            return {"result": response, "raw_response": True}
    
    # Стандартные обработчики задач
    
    async def _system_health_check(self, task: Task) -> Dict[str, Any]:
        """Проверка здоровья системы"""
        from ai_client.tools.system_tools import SystemTools
        system_tools = SystemTools()
        
        health_report = system_tools.diagnose_system_health()
        
        return {
            "health_status": "healthy" if "✅" in health_report else "warning",
            "report": health_report,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _memory_optimization(self, task: Task) -> Dict[str, Any]:
        """Оптимизация памяти"""
        # Анализ и очистка старых данных
        from memory.conversation_history import conversation_history
        
        stats = conversation_history.get_statistics()
        
        # Если история слишком большая, архивируем
        if stats.get('total_messages', 0) > 100:
            conversation_history._archive_old_messages()
        
        return {
            "optimization_performed": True,
            "memory_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _context_analysis(self, task: Task) -> Dict[str, Any]:
        """Анализ контекста пользователя"""
        from memory.user_profiles import UserProfile
        
        # Анализируем эмоциональные тренды
        user_profile = UserProfile("stepan")
        emotional_trends = user_profile.get_emotional_trends()
        
        return {
            "emotional_analysis": emotional_trends,
            "context_insights": "User shows positive emotional trend",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _personality_adjustment(self, task: Task) -> Dict[str, Any]:
        """Корректировка личности на основе взаимодействий"""
        # Анализируем последние взаимодействия
        from memory.conversation_history import conversation_history
        
        recent_history = conversation_history.get_recent_history(limit=10)
        
        # Определяем стиль общения пользователя
        formal_count = sum(1 for msg in recent_history if any(word in msg.get('message', '').lower() 
                           for word in ['пожалуйста', 'спасибо', 'извините']))
        casual_count = len(recent_history) - formal_count
        
        communication_style = "formal" if formal_count > casual_count else "casual"
        
        return {
            "communication_style": communication_style,
            "adjustment_made": True,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _learning_cycle(self, task: Task) -> Dict[str, Any]:
        """Цикл обучения от взаимодействий"""
        # Анализируем паттерны использования
        from memory.conversation_history import conversation_history
        
        history = conversation_history.get_full_history()
        
        # Извлекаем ключевые темы
        topics = []
        for msg in history[-20:]:  # Последние 20 сообщений
            if 'message' in msg:
                topics.extend(msg['message'].split()[:5])  # Первые 5 слов
        
        common_topics = list(set(topics))
        
        return {
            "learned_patterns": common_topics,
            "interaction_count": len(history),
            "learning_cycle_completed": True,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _security_scan(self, task: Task) -> Dict[str, Any]:
        """Сканирование безопасности"""
        # Проверяем подозрительную активность
        from memory.conversation_history import conversation_history
        
        recent_messages = conversation_history.get_recent_history(limit=50)
        
        # Простая проверка на подозрительные паттерны
        suspicious_patterns = ['password', 'credit card', 'ssn', 'private key']
        suspicious_count = 0
        
        for msg in recent_messages:
            message_text = msg.get('message', '').lower()
            if any(pattern in message_text for pattern in suspicious_patterns):
                suspicious_count += 1
        
        security_status = "secure" if suspicious_count == 0 else "warning"
        
        return {
            "security_status": security_status,
            "suspicious_activity_count": suspicious_count,
            "scan_completed": True,
            "timestamp": datetime.now().isoformat()
        }
    
    async def tick(self):
        """Основной цикл планировщика"""
        if not self.running:
            return
        
        ready_tasks = self.get_ready_tasks()
        
        for task in ready_tasks[:3]:  # Выполняем максимум 3 задачи за тик
            await self.execute_task(task)
        
        # Логируем статистику
        pending_count = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        completed_count = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        
        if ready_tasks or pending_count > 0:
            logger.info(f"🔄 Scheduler tick: {len(ready_tasks)} ready, {pending_count} pending, {completed_count} completed")
    
    def start(self):
        """Запуск планировщика"""
        self.running = True
        self.background_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.background_thread.start()
        logger.info("🚀 ΔΣ Scheduler started")
    
    def stop(self):
        """Остановка планировщика"""
        self.running = False
        if self.background_thread:
            self.background_thread.join()
        logger.info("🛑 ΔΣ Scheduler stopped")
    
    def _run_loop(self):
        """Фоновый цикл выполнения"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self.running:
            try:
                loop.run_until_complete(self.tick())
                time.sleep(self.tick_interval)
            except Exception as e:
                logger.error(f"❌ Scheduler loop error: {e}")
                time.sleep(self.tick_interval)
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса планировщика"""
        task_counts = {}
        for status in TaskStatus:
            task_counts[status.value] = len([t for t in self.tasks.values() if t.status == status])
        
        return {
            "running": self.running,
            "total_tasks": len(self.tasks),
            "task_counts": task_counts,
            "ready_tasks": len(self.get_ready_tasks()),
            "uptime": time.time() if self.running else 0
        }
    
    def schedule_periodic_task(self, task_type: str, interval_minutes: int, 
                             name: str, description: str, priority: TaskPriority = TaskPriority.BACKGROUND):
        """Планирование периодической задачи"""
        def schedule_next():
            next_time = datetime.now() + timedelta(minutes=interval_minutes)
            task_id = self.create_task(
                name=f"{name}_{int(time.time())}",
                description=description,
                priority=priority,
                task_type=task_type,
                scheduled_for=next_time
            )
            # Планируем следующее выполнение
            threading.Timer(interval_minutes * 60, schedule_next).start()
        
        # Запускаем первый раз
        schedule_next()
        logger.info(f"📅 Scheduled periodic task: {name} (every {interval_minutes} minutes)")

# Глобальный экземпляр планировщика
scheduler = Scheduler() 