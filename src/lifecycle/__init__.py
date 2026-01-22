"""
Lifecycle Management System.

Этот модуль предоставляет управление жизненным циклом системы Life,
включая состояния (init, run, degrade, dead) и соответствующие хуки.
"""

from .lifecycle import LifecycleManager, LifecycleState

__all__ = [
    "LifecycleManager",
    "LifecycleState",
]