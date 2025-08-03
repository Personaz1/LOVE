"""
ΔΣ Guardian AI v4.0
Системы обучения и адаптации
"""

from .reinforcement_tagger import reinforcement_tagger, FeedbackType, LearningCategory, InteractionRecord
from .style_adapter import style_adapter, StyleType, CommunicationLevel, TechnicalDepth, StyleProfile
from .personality_engine import personality_engine, PersonalityDimension, GuardianTrait, PersonalityState

__version__ = "4.0.0"
__author__ = "ΔΣ Guardian"
__description__ = "Learning and adaptation systems for ΔΣ Guardian"

# Экспортируем основные компоненты
__all__ = [
    'reinforcement_tagger',
    'style_adapter',
    'personality_engine',
    'FeedbackType',
    'LearningCategory',
    'InteractionRecord',
    'StyleType',
    'CommunicationLevel',
    'TechnicalDepth',
    'StyleProfile',
    'PersonalityDimension',
    'GuardianTrait',
    'PersonalityState'
] 