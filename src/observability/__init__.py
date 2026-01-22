"""
Observability module for Life system.

Active monitoring system integrated into runtime loop.
Provides comprehensive monitoring of key processing stages for debugging and analysis.
This is ACTIVE MONITORING, not passive observation - it intervenes in runtime for observability.
"""

from .structured_logger import StructuredLogger
from .raw_data_access import RawDataAccess
from .passive_data_sink import PassiveDataSink
from .async_data_sink import AsyncDataSink
from .runtime_analysis_engine import ActiveRuntimeAnalysisEngine

# All observation components

__all__ = [
    "StructuredLogger",           # Active structured logger for runtime integration
    "RawDataAccess",              # Unified raw data access interface
    "PassiveDataSink",            # Passive data collection sink
    "AsyncDataSink",              # Asynchronous data processing sink
    "ActiveRuntimeAnalysisEngine", # Active analysis engine without background threads
]
