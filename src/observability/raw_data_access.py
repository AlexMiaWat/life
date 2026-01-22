"""
Raw Data Access - RawDataAccess

Компонент для доступа к raw данным наблюдений без интерпретации.
Предоставляет прямой доступ к хранимым данным в различных форматах.
"""

import json
import time
from typing import Dict, List, Any, Optional, Iterator, Union
from pathlib import Path
from dataclasses import asdict
from collections import defaultdict

# RawDataAccess is deprecated in active observation architecture.
# All observation is handled by StructuredLogger in runtime loop.
# This module is kept for backward compatibility but should not be used.

import logging

logger = logging.getLogger(__name__)
logger.warning("RawDataAccess is deprecated. Use StructuredLogger for active observation.")


class RawDataAccess:
    """
    DEPRECATED: RawDataAccess is deprecated in active observation architecture.

    All observation is handled by StructuredLogger in runtime loop.
    This class is kept for backward compatibility but should not be used.
    """

    def __init__(self, data_sources=None):
        logger.warning("RawDataAccess is deprecated. Use StructuredLogger for active observation.")
        self.data_sources = data_sources or []

    def __getattr__(self, name):
        """All methods are deprecated."""
        logger.warning(f"RawDataAccess.{name} is deprecated. Use StructuredLogger for active observation.")
        return lambda *args, **kwargs: None