"""
Конфигурационные модули системы Life.
"""

from .feature_flags import FeatureFlags, feature_flags
from .observability_config import ObservabilityConfig

__all__ = [
    'FeatureFlags',
    'feature_flags',
    'ObservabilityConfig'
]