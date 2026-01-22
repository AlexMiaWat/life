"""
Observability module for Life system.

Active structured logging system integrated into runtime loop.
Provides comprehensive logging of key processing stages for debugging and analysis.
"""

from .structured_logger import StructuredLogger
from .passive_data_sink import PassiveDataSink, ObservationData
from .async_data_sink import AsyncDataSink, RawObservationData

# All observation is handled by StructuredLogger

__all__ = [
    "StructuredLogger",      # Active structured logger for runtime integration
    "PassiveDataSink",       # Passive data collection component
    "AsyncDataSink",         # Asynchronous data sink with queue
    "ObservationData",       # Data structure for observations
    "RawObservationData",    # Raw observation data structure
]
