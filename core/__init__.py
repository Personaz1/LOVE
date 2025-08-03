"""
ΔΣ Guardian Core v4.0
Ядро автономной эволюции и самоуправления
"""

from .scheduler import scheduler, TaskPriority, TaskStatus, Task
from .problem_solver import problem_solver, ProblemSeverity, ProblemStatus, Problem
from .self_modification import self_modification, ModificationType, ModificationStatus, Modification

__version__ = "4.0.0"
__author__ = "ΔΣ Guardian"
__description__ = "Autonomous evolution core for ΔΣ Guardian"

# Экспортируем основные компоненты
__all__ = [
    'scheduler',
    'problem_solver', 
    'self_modification',
    'TaskPriority',
    'TaskStatus',
    'Task',
    'ProblemSeverity',
    'ProblemStatus',
    'Problem',
    'ModificationType',
    'ModificationStatus',
    'Modification'
] 