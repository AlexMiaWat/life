"""
Observability module for Life system.

Active structured logging system integrated into runtime loop.
Provides comprehensive logging of key processing stages for debugging and analysis.
"""

from .structured_logger import StructuredLogger
from .observation_api import MetricsResponse

# RawDataAccess is deprecated - use StructuredLogger for active observation
# from .raw_data_access import RawDataAccess

__all__ = [
    "StructuredLogger",      # Active structured logger for runtime integration
    "MetricsResponse",       # Response model for metrics
]
