"""
ΔΣ Guardian Problem Solver v4.0
Автономное решение проблем и самоисправление
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ai_client.core.client import AIClient
from ai_client.utils.logger import Logger
from core.scheduler import scheduler, TaskPriority

logger = Logger()

class ProblemSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ProblemStatus(Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    SOLVING = "solving"
    SOLVED = "solved"
    FAILED = "failed"
    IGNORED = "ignored"

@dataclass
class Problem:
    id: str
    title: str
    description: str
    severity: ProblemSeverity
    status: ProblemStatus
    detected_at: datetime
    category: str
    context: Dict[str, Any]
    solution_attempts: List[Dict[str, Any]]
    auto_fix_enabled: bool = True
    
    def __post_init__(self):
        if self.solution_attempts is None:
            self.solution_attempts = []

class ProblemSolver:
    """Автономный решатель проблем для ΔΣ Guardian"""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.problems: Dict[str, Problem] = {}
        self.solution_templates: Dict[str, str] = {}
        self.auto_fix_enabled = True
        
        # Загружаем шаблоны решений
        self._load_solution_templates()
        
        logger.info("🔧 ΔΣ Problem Solver initialized")
    
    def _load_solution_templates(self):
        """Загрузка шаблонов решений"""
        self.solution_templates = {
            "memory_overflow": """
            Проблема: Переполнение памяти
            Решение:
            1. Архивировать старые сообщения
            2. Очистить кэш
            3. Оптимизировать структуры данных
            """,
            "api_error": """
            Проблема: Ошибка API
            Решение:
            1. Проверить подключение к API
            2. Обновить ключи доступа
            3. Переключиться на резервную модель
            """,
            "performance_degradation": """
            Проблема: Снижение производительности
            Решение:
            1. Оптимизировать запросы
            2. Очистить временные файлы
            3. Перезапустить критические сервисы
            """,
            "security_issue": """
            Проблема: Проблема безопасности
            Решение:
            1. Сканировать на уязвимости
            2. Обновить конфигурацию безопасности
            3. Логировать подозрительную активность
            """,
            "user_experience": """
            Проблема: Проблема пользовательского опыта
            Решение:
            1. Анализировать паттерны использования
            2. Адаптировать интерфейс
            3. Улучшить персонализацию
            """
        }
    
    def detect_problem(self, title: str, description: str, severity: ProblemSeverity,
                      category: str = "general", context: Dict[str, Any] = None) -> str:
        """Обнаружение новой проблемы"""
        problem_id = f"problem_{int(datetime.now().timestamp() * 1000)}"
        
        problem = Problem(
            id=problem_id,
            title=title,
            description=description,
            severity=severity,
            status=ProblemStatus.DETECTED,
            detected_at=datetime.now(),
            category=category,
            context=context or {},
            solution_attempts=[]
        )
        
        self.problems[problem_id] = problem
        logger.warning(f"🚨 Problem detected: {title} ({severity.value})")
        
        # Автоматически запускаем анализ если проблема критическая
        if severity in [ProblemSeverity.CRITICAL, ProblemSeverity.HIGH]:
            self.analyze_problem(problem_id)
        
        return problem_id
    
    def analyze_problem(self, problem_id: str) -> Dict[str, Any]:
        """AI-анализ проблемы"""
        if problem_id not in self.problems:
            return {"error": "Problem not found"}
        
        problem = self.problems[problem_id]
        problem.status = ProblemStatus.ANALYZING
        
        logger.info(f"🔍 Analyzing problem: {problem.title}")
        
        # Создаем AI-промпт для анализа
        analysis_prompt = f"""
        Проблема: {problem.title}
        Описание: {problem.description}
        Категория: {problem.category}
        Контекст: {json.dumps(problem.context, ensure_ascii=False)}
        
        Проанализируй эту проблему и предложи:
        1. Корень проблемы
        2. Возможные решения
        3. Приоритет действий
        4. Риски и последствия
        
        Верни анализ в JSON формате.
        """
        
        try:
            response = self.ai_client.chat(analysis_prompt)
            
            # Извлекаем JSON из ответа
            analysis = self._extract_json_from_response(response)
            
            # Добавляем анализ к проблеме
            problem.solution_attempts.append({
                "type": "analysis",
                "timestamp": datetime.now().isoformat(),
                "result": analysis
            })
            
            logger.info(f"✅ Problem analyzed: {problem.title}")
            
            # Автоматически запускаем решение если включено
            if self.auto_fix_enabled and problem.auto_fix_enabled:
                self.solve_problem(problem_id)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Problem analysis failed: {e}")
            problem.status = ProblemStatus.FAILED
            return {"error": str(e)}
    
    def solve_problem(self, problem_id: str) -> Dict[str, Any]:
        """Решение проблемы"""
        if problem_id not in self.problems:
            return {"error": "Problem not found"}
        
        problem = self.problems[problem_id]
        problem.status = ProblemStatus.SOLVING
        
        logger.info(f"🛠️ Solving problem: {problem.title}")
        
        # Получаем последний анализ
        if not problem.solution_attempts:
            self.analyze_problem(problem_id)
        
        # Создаем план решения
        solution_plan = self._create_solution_plan(problem)
        
        # Выполняем план
        results = []
        for step in solution_plan:
            try:
                result = self._execute_solution_step(step, problem)
                results.append({
                    "step": step,
                    "result": result,
                    "success": "error" not in result
                })
            except Exception as e:
                results.append({
                    "step": step,
                    "result": {"error": str(e)},
                    "success": False
                })
        
        # Обновляем статус проблемы
        success_count = sum(1 for r in results if r["success"])
        if success_count > 0:
            problem.status = ProblemStatus.SOLVED
            logger.info(f"✅ Problem solved: {problem.title}")
        else:
            problem.status = ProblemStatus.FAILED
            logger.error(f"❌ Problem solving failed: {problem.title}")
        
        # Сохраняем результаты
        problem.solution_attempts.append({
            "type": "solution",
            "timestamp": datetime.now().isoformat(),
            "results": results
        })
        
        return {
            "problem_id": problem_id,
            "status": problem.status.value,
            "results": results,
            "success_rate": success_count / len(results) if results else 0
        }
    
    def _create_solution_plan(self, problem: Problem) -> List[Dict[str, Any]]:
        """Создание плана решения проблемы"""
        # Используем шаблоны или AI для создания плана
        if problem.category in self.solution_templates:
            template = self.solution_templates[problem.category]
            
            # Создаем план на основе шаблона
            plan = []
            lines = template.split('\n')
            current_step = None
            
            for line in lines:
                if line.strip().startswith('1.') or line.strip().startswith('2.') or line.strip().startswith('3.'):
                    if current_step:
                        plan.append(current_step)
                    current_step = {
                        "action": line.strip(),
                        "type": "template_based"
                    }
            
            if current_step:
                plan.append(current_step)
            
            return plan
        else:
            # Используем AI для создания плана
            plan_prompt = f"""
            Проблема: {problem.title}
            Описание: {problem.description}
            
            Создай пошаговый план решения этой проблемы.
            Каждый шаг должен быть конкретным действием.
            
            Верни план в JSON формате:
            [
                {{"action": "описание действия", "type": "ai_generated"}},
                ...
            ]
            """
            
            response = self.ai_client.chat(plan_prompt)
            try:
                return self._extract_json_from_response(response)
            except:
                return [{"action": "Manual intervention required", "type": "manual"}]
    
    def _execute_solution_step(self, step: Dict[str, Any], problem: Problem) -> Dict[str, Any]:
        """Выполнение шага решения"""
        action = step.get("action", "")
        step_type = step.get("type", "unknown")
        
        logger.info(f"🔧 Executing step: {action}")
        
        # Выполняем действие в зависимости от типа
        if step_type == "template_based":
            return self._execute_template_action(action, problem)
        elif step_type == "ai_generated":
            return self._execute_ai_action(action, problem)
        else:
            return {"error": f"Unknown step type: {step_type}"}
    
    def _execute_template_action(self, action: str, problem: Problem) -> Dict[str, Any]:
        """Выполнение действия из шаблона"""
        action_lower = action.lower()
        
        if "архивировать" in action_lower or "archive" in action_lower:
            return self._archive_old_data()
        elif "очистить" in action_lower or "clear" in action_lower:
            return self._clear_cache()
        elif "оптимизировать" in action_lower or "optimize" in action_lower:
            return self._optimize_performance()
        elif "проверить" in action_lower or "check" in action_lower:
            return self._check_system_health()
        elif "перезапустить" in action_lower or "restart" in action_lower:
            return self._restart_services()
        else:
            return {"warning": f"Unknown template action: {action}"}
    
    def _execute_ai_action(self, action: str, problem: Problem) -> Dict[str, Any]:
        """Выполнение AI-сгенерированного действия"""
        # Используем AI для выполнения действия
        execution_prompt = f"""
        Действие: {action}
        Контекст проблемы: {problem.description}
        
        Выполни это действие и верни результат в JSON формате.
        """
        
        try:
            response = self.ai_client.chat(execution_prompt)
            return self._extract_json_from_response(response)
        except Exception as e:
            return {"error": f"AI action execution failed: {str(e)}"}
    
    def _archive_old_data(self) -> Dict[str, Any]:
        """Архивирование старых данных"""
        try:
            from memory.conversation_history import conversation_history
            conversation_history._archive_old_messages()
            return {"success": True, "action": "archived_old_data"}
        except Exception as e:
            return {"error": f"Archive failed: {str(e)}"}
    
    def _clear_cache(self) -> Dict[str, Any]:
        """Очистка кэша"""
        try:
            from ai_client.utils.cache import system_cache
            system_cache.clear()
            return {"success": True, "action": "cleared_cache"}
        except Exception as e:
            return {"error": f"Cache clear failed: {str(e)}"}
    
    def _optimize_performance(self) -> Dict[str, Any]:
        """Оптимизация производительности"""
        try:
            # Создаем задачу оптимизации в планировщике
            scheduler.create_task(
                name="performance_optimization",
                description="System performance optimization",
                priority=TaskPriority.HIGH,
                task_type="optimization"
            )
            return {"success": True, "action": "scheduled_optimization"}
        except Exception as e:
            return {"error": f"Optimization failed: {str(e)}"}
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Проверка здоровья системы"""
        try:
            from ai_client.tools.system_tools import SystemTools
            system_tools = SystemTools()
            health_report = system_tools.diagnose_system_health()
            return {"success": True, "action": "health_check", "report": health_report}
        except Exception as e:
            return {"error": f"Health check failed: {str(e)}"}
    
    def _restart_services(self) -> Dict[str, Any]:
        """Перезапуск сервисов"""
        try:
            # Создаем задачу перезапуска
            scheduler.create_task(
                name="service_restart",
                description="Restart critical services",
                priority=TaskPriority.CRITICAL,
                task_type="restart"
            )
            return {"success": True, "action": "scheduled_restart"}
        except Exception as e:
            return {"error": f"Restart failed: {str(e)}"}
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Извлечение JSON из AI-ответа"""
        try:
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"result": response, "raw_response": True}
        except:
            return {"result": response, "raw_response": True}
    
    def get_problem_status(self, problem_id: str) -> Dict[str, Any]:
        """Получение статуса проблемы"""
        if problem_id not in self.problems:
            return {"error": "Problem not found"}
        
        problem = self.problems[problem_id]
        return {
            "id": problem.id,
            "title": problem.title,
            "status": problem.status.value,
            "severity": problem.severity.value,
            "detected_at": problem.detected_at.isoformat(),
            "solution_attempts": len(problem.solution_attempts)
        }
    
    def get_all_problems(self) -> List[Dict[str, Any]]:
        """Получение всех проблем"""
        return [self.get_problem_status(pid) for pid in self.problems.keys()]
    
    def auto_detect_problems(self) -> List[str]:
        """Автоматическое обнаружение проблем"""
        detected_problems = []
        
        try:
            # Проверяем здоровье системы
            from ai_client.tools.system_tools import SystemTools
            system_tools = SystemTools()
            health_report = system_tools.diagnose_system_health()
            
            if "❌" in health_report:
                problem_id = self.detect_problem(
                    title="System Health Issues",
                    description="System health check revealed problems",
                    severity=ProblemSeverity.HIGH,
                    category="system_health",
                    context={"health_report": health_report}
                )
                detected_problems.append(problem_id)
            
            # Проверяем память
            from memory.conversation_history import conversation_history
            stats = conversation_history.get_statistics()
            
            if stats.get('total_messages', 0) > 200:
                problem_id = self.detect_problem(
                    title="Memory Overflow",
                    description="Conversation history is getting large",
                    severity=ProblemSeverity.MEDIUM,
                    category="memory_overflow",
                    context={"stats": stats}
                )
                detected_problems.append(problem_id)
            
            # Проверяем производительность
            if len(self.problems) > 10:
                problem_id = self.detect_problem(
                    title="Performance Degradation",
                    description="Too many problems detected",
                    severity=ProblemSeverity.MEDIUM,
                    category="performance",
                    context={"problem_count": len(self.problems)}
                )
                detected_problems.append(problem_id)
                
        except Exception as e:
            logger.error(f"❌ Auto-detection failed: {e}")
        
        return detected_problems
    
    def schedule_periodic_checks(self):
        """Планирование периодических проверок"""
        # Проверка каждые 5 минут
        scheduler.schedule_periodic_task(
            task_type="problem_detection",
            interval_minutes=5,
            name="Auto Problem Detection",
            description="Automatically detect and solve problems",
            priority=TaskPriority.BACKGROUND
        )
        
        logger.info("📅 Scheduled periodic problem detection")

# Глобальный экземпляр решателя проблем
problem_solver = ProblemSolver() 