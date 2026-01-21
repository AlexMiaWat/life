"""
Observability module for Life system.

Simplified observability with passive data collection and automated reporting.
Provides essential monitoring tools for developers without runtime interference.
"""

from .external_observer import RawDataCollector, RawSystemCounters, RawDataReport
from .async_passive_observer import AsyncPassiveObserver
from .developer_reports import DeveloperReports
from .structured_logger import StructuredLogger

__all__ = [
    "RawDataCollector", "RawSystemCounters", "RawDataReport",
    "AsyncPassiveObserver",
    "DeveloperReports",
    "StructuredLogger"
]
