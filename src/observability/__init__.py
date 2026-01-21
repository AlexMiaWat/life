"""
Observability module for Life system.

Active structured logging system integrated into runtime loop.
Provides comprehensive logging of key processing stages for debugging and analysis.
"""

from .structured_logger import StructuredLogger

__all__ = [
    "StructuredLogger"  # Active structured logger for runtime integration
]
