"""
Feature flags для экспериментальных компонентов системы Life.

Позволяет включать/отключать экспериментальные компоненты через конфигурацию.
"""

from typing import Any, Dict, Optional

from src.config_loader import ConfigLoader


class FeatureFlags:
    """
    Менеджер feature flags для экспериментальных компонентов.

    Предоставляет унифицированный интерфейс для проверки состояния
    экспериментальных компонентов через конфигурацию.
    """

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """
        Инициализация менеджера feature flags.

        Args:
            config_loader: Загрузчик конфигурации (опционально)
        """
        self.config_loader = config_loader or ConfigLoader()
        self._cache: Dict[str, bool] = {}
        self._cache_timestamp: float = 0.0
        self._cache_ttl: float = 5.0  # Кэш на 5 секунд для производительности

    def is_enabled(self, component_name: str) -> bool:
        """
        Проверить, включен ли экспериментальный компонент.
        Оптимизированная версия с TTL кэшированием и логированием.

        Args:
            component_name: Название компонента

        Returns:
            True если компонент включен, False иначе
        """
        import time
        import logging

        logger = logging.getLogger(__name__)
        current_time = time.time()

        # Проверяем кэш с TTL
        if (component_name in self._cache and
            current_time - self._cache_timestamp < self._cache_ttl):
            cached_value = self._cache[component_name]
            logger.debug(f"Feature flag '{component_name}' from cache: {cached_value}")
            return cached_value

        try:
            features_config = self.config_loader.get('features', {})
            experimental_config = features_config.get('experimental', {})

            enabled = experimental_config.get(component_name, False)

            # Логируем проверку feature flag для transparency
            logger.info(f"Feature flag '{component_name}' checked: {enabled}")

            self._cache[component_name] = enabled
            self._cache_timestamp = current_time
            return enabled

        except Exception as e:
            # В случае ошибки конфигурации, отключаем экспериментальные компоненты
            # Кэшируем False на короткое время для предотвращения частых ошибок
            logger.warning(f"Error checking feature flag '{component_name}': {e}. Defaulting to False.")
            self._cache[component_name] = False
            self._cache_timestamp = current_time
            return False

    def is_memory_hierarchy_enabled(self) -> bool:
        """Проверить, включен ли MemoryHierarchyManager."""
        return self.is_enabled('memory_hierarchy_manager')

    def is_adaptive_processing_enabled(self) -> bool:
        """Проверить, включен ли AdaptiveProcessingManager."""
        return self.is_enabled('adaptive_processing_manager')

    def is_sensory_buffer_enabled(self) -> bool:
        """Проверить, включен ли SensoryBuffer."""
        return self.is_enabled('sensory_buffer')

    def is_clarity_moments_enabled(self) -> bool:
        """Проверить, включены ли Clarity Moments."""
        return self.is_enabled('clarity_moments')

    def is_parallel_consciousness_enabled(self) -> bool:
        """Проверить, включен ли Parallel Consciousness Engine."""
        return self.is_enabled('parallel_consciousness_engine')

    def is_decision_logging_enabled(self) -> bool:
        """Проверить, включено ли логирование решений DecisionEngine."""
        return self.is_enabled('decision_logging')

    def get_all_flags(self) -> Dict[str, Any]:
        """
        Получить все feature flags.

        Returns:
            Словарь со всеми флагами
        """
        try:
            return self.config_loader.get('features', {}).get('experimental', {})
        except Exception:
            return {}

    def clear_cache(self) -> None:
        """Очистить кэш флагов (для тестирования или при изменении конфигурации)."""
        self._cache.clear()

    def get_status_report(self) -> Dict[str, Any]:
        """
        Получить отчет о состоянии всех feature flags.

        Returns:
            Отчет с информацией о каждом флаге
        """
        all_flags = self.get_all_flags()
        report = {
            "total_flags": len(all_flags),
            "enabled_flags": [],
            "disabled_flags": [],
            "flags_status": {}
        }

        for flag_name, enabled in all_flags.items():
            report["flags_status"][flag_name] = enabled
            if enabled:
                report["enabled_flags"].append(flag_name)
            else:
                report["disabled_flags"].append(flag_name)

        return report


# Глобальный экземпляр для удобства использования
feature_flags = FeatureFlags()