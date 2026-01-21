"""
Life Comparison System - система для сравнения разных "жизней" и их паттернов

Этот модуль предоставляет инструменты для:
- Запуска и управления множественными инстансами Life
- Сбора и анализа данных от разных жизней
- Сравнения паттернов поведения и эволюции
- REST API для управления сравнением
- Визуализации результатов сравнения
"""

from .comparison_manager import ComparisonManager
from .life_instance import LifeInstance
from .pattern_analyzer import PatternAnalyzer
from .comparison_metrics import ComparisonMetrics
from .comparison_api import ComparisonAPI

__all__ = [
    'ComparisonManager',
    'LifeInstance',
    'PatternAnalyzer',
    'ComparisonMetrics',
    'ComparisonAPI'
]