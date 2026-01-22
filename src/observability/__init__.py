"""
Observability module for Life system.

Active structured logging system integrated into runtime loop.
Provides comprehensive logging of key processing stages for debugging and analysis.
"""

from .structured_logger import StructuredLogger
from .passive_data_sink import PassiveDataSink, get_passive_data_sink, ObservationData
from .async_data_sink import AsyncDataSink, create_async_data_sink
from .raw_data_access import RawDataAccess

# All observation components

__all__ = [
    "StructuredLogger",      # Active structured logger for runtime integration
    "PassiveDataSink",       # Passive data collection sink
    "AsyncDataSink",         # Asynchronous data collection sink
    "RawDataAccess",         # Unified raw data access interface
    "ObservationData",       # Data structure for observations
    "get_passive_data_sink", # Factory function for passive sink
    "create_async_data_sink", # Factory function for async sink
]
