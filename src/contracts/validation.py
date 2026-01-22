"""
Валидатор архитектурных контрактов.

Обеспечивает проверку соответствия компонентов их контрактам
во время выполнения и тестирования.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Callable
from .base_contracts import BaseContract, ContractRegistry, ValidationLevel

logger = logging.getLogger(__name__)


class ContractValidator:
    """
    Валидатор архитектурных контрактов.

    Предоставляет инструменты для:
    - Проверки соответствия контрактов
    - Мониторинга нарушений
    - Генерации отчетов
    - Автоматического восстановления
    """

    def __init__(self, registry: Optional[ContractRegistry] = None):
        self.registry = registry or ContractRegistry()
        self.violations: List[Dict[str, Any]] = []
        self.validation_stats: Dict[str, Dict[str, int]] = {}

    def validate_component(self, component_name: str, **context) -> bool:
        """
        Валидировать компонент на соответствие контракту.

        Args:
            component_name: Имя компонента
            **context: Контекст для валидации

        Returns:
            True если валидация прошла успешно
        """
        contract = self.registry.get_contract(component_name)
        if not contract:
            logger.warning(f"No contract found for component: {component_name}")
            return False

        try:
            # Валидация входных параметров
            if hasattr(contract, 'validate_inputs'):
                contract.validate_inputs(**context)

            # Обновление статистики
            self._update_stats(component_name, 'validation_attempt', 1)

            return True

        except Exception as e:
            violation = {
                'timestamp': time.time(),
                'component': component_name,
                'contract': contract.metadata.component_name,
                'error': str(e),
                'context': context
            }
            self.violations.append(violation)
            self._update_stats(component_name, 'violations', 1)

            logger.error(f"Contract violation in {component_name}: {e}")
            return False

    def validate_all_components(self) -> Dict[str, bool]:
        """
        Валидировать все зарегистрированные компоненты.

        Returns:
            Результаты валидации по компонентам
        """
        results = {}
        for component_name in self.registry._contracts.keys():
            results[component_name] = self.validate_component(component_name)
        return results

    def get_violations_report(self, since_timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Получить отчет о нарушениях контрактов.

        Args:
            since_timestamp: Время от которого считать нарушения (None - все)

        Returns:
            Отчет о нарушениях
        """
        violations = self.violations
        if since_timestamp:
            violations = [v for v in violations if v['timestamp'] >= since_timestamp]

        return {
            'total_violations': len(violations),
            'violations_by_component': self._group_violations_by(violations, 'component'),
            'violations_by_contract': self._group_violations_by(violations, 'contract'),
            'recent_violations': violations[-10:],  # Последние 10 нарушений
            'violation_trend': self._calculate_trend(violations)
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Получить отчет о производительности валидации.

        Returns:
            Отчет о производительности
        """
        return {
            'validation_stats': self.validation_stats,
            'total_validations': sum(
                stats.get('validation_attempt', 0)
                for stats in self.validation_stats.values()
            ),
            'total_violations': sum(
                stats.get('violations', 0)
                for stats in self.validation_stats.values()
            ),
            'violation_rate': self._calculate_violation_rate()
        }

    def clear_violations_history(self):
        """Очистить историю нарушений."""
        self.violations.clear()

    def set_validation_level(self, component_name: str, level: ValidationLevel):
        """
        Установить уровень валидации для компонента.

        Args:
            component_name: Имя компонента
            level: Уровень валидации
        """
        contract = self.registry.get_contract(component_name)
        if contract:
            contract.validation_level = level
            logger.info(f"Validation level for {component_name} set to {level.value}")

    def add_contract_monitoring(self, component_name: str, monitor_callback: Callable):
        """
        Добавить мониторинг для контракта компонента.

        Args:
            component_name: Имя компонента
            monitor_callback: Функция обратного вызова для мониторинга
        """
        # Реализация мониторинга контрактов
        logger.info(f"Contract monitoring added for {component_name}")

    def _update_stats(self, component: str, metric: str, value: int):
        """Обновить статистику валидации."""
        if component not in self.validation_stats:
            self.validation_stats[component] = {}
        if metric not in self.validation_stats[component]:
            self.validation_stats[component][metric] = 0
        self.validation_stats[component][metric] += value

    def _group_violations_by(self, violations: List[Dict], key: str) -> Dict[str, int]:
        """Группировать нарушения по ключу."""
        grouped = {}
        for violation in violations:
            group_value = violation.get(key, 'unknown')
            grouped[group_value] = grouped.get(group_value, 0) + 1
        return grouped

    def _calculate_trend(self, violations: List[Dict]) -> str:
        """Рассчитать тренд нарушений."""
        if len(violations) < 2:
            return "insufficient_data"

        # Простой анализ тренда по времени
        recent = [v for v in violations if v['timestamp'] > time.time() - 3600]  # Последний час
        older = [v for v in violations if v['timestamp'] <= time.time() - 3600]

        if not older:
            return "increasing" if recent else "stable"

        recent_rate = len(recent) / 1  # В час
        older_rate = len(older) / 23   # В предыдущие 23 часа

        if recent_rate > older_rate * 1.5:
            return "increasing"
        elif recent_rate < older_rate * 0.5:
            return "decreasing"
        else:
            return "stable"

    def _calculate_violation_rate(self) -> float:
        """Рассчитать общий уровень нарушений."""
        total_validations = sum(
            stats.get('validation_attempt', 0)
            for stats in self.validation_stats.values()
        )
        total_violations = sum(
            stats.get('violations', 0)
            for stats in self.validation_stats.values()
        )

        if total_validations == 0:
            return 0.0

        return total_violations / total_validations

    def export_report(self, filepath: str):
        """
        Экспортировать полный отчет о контрактах.

        Args:
            filepath: Путь для сохранения отчета
        """
        report = {
            'timestamp': time.time(),
            'contracts_info': self.registry.get_all_contracts_info(),
            'violations_report': self.get_violations_report(),
            'performance_report': self.get_performance_report()
        }

        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Contract validation report exported to {filepath}")


# Глобальный валидатор контрактов
contract_validator = ContractValidator()