"""
Observability module for Life system.

True passive observation system with UnifiedObservationAPI as the main entry point.
Provides passive data collection and raw counters only - no derived metrics or analysis.
"""

from .unified_observation_api import UnifiedObservationAPI  # Main entry point
from .async_passive_observer import PassiveDataSink  # Core passive component
from .external_observer import RawDataCollector, RawSystemCounters, RawDataReport
from .structured_logger import StructuredLogger
from .developer_reports import RawDataAccess

__all__ = [
    # Main API - use this for all observability operations
    "UnifiedObservationAPI",

    # Core components
    "PassiveDataSink",
    "RawDataCollector",
    "StructuredLogger",
    "RawDataAccess",

    # Data structures
    "RawSystemCounters",
    "RawDataReport"
]
