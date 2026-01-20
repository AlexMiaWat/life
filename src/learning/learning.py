"""
Learning Engine - Этап 14

ВАЖНО: Learning НЕ является оптимизацией, reinforcement learning или управлением поведением.
Learning только медленно изменяет внутренние параметры без целей и оценки эффективности.

Архитектурные ограничения:
- ❌ Запрещено: оптимизация, цели, намерения, reward, utility, scoring
- ❌ Запрещено: оценка эффективности действий, корректировка поведения
- ❌ Запрещено: циклы обратной связи, внешние метрики
- ✅ Разрешено: постепенное изменение внутренних параметров (макс. 0.01 за раз)
- ✅ Разрешено: фиксация изменений без интерпретации
- ✅ Разрешено: использование внутренней статистики из Memory
"""

import copy
import logging
import threading
from typing import TYPE_CHECKING, Dict, List

from src.memory.memory import MemoryEntry

if TYPE_CHECKING:
    from src.state.self_state import SelfState

logger = logging.getLogger(__name__)


class LearningEngine:
    """
    Learning Engine - медленное изменение внутренних параметров без оптимизации.

    Learning не отвечает на вопрос "что делать дальше".
    Learning только изменяет внутренние параметры без интерпретации.

    ВАЖНО: Параметры learning_params изменяются и используются в:
    - MeaningEngine: event_type_sensitivity для модификации значимости событий
    - Decision: significance_thresholds для модификации порогов игнорирования
    - Action: response_coefficients для модификации эффектов действий
    Параметры также используются в Adaptation Manager (Этап 15) для адаптации поведения.
    """

    # Максимальное изменение параметра за один вызов
    MAX_PARAMETER_DELTA = 0.01

    # Минимальное изменение для применения (чтобы избежать микро-изменений)
    MIN_PARAMETER_DELTA = 0.001

    # Допуск для проверки изменений параметров (для учета погрешностей вычислений с плавающей точкой)
    # Используется при сравнении delta с MAX_PARAMETER_DELTA
    _VALIDATION_TOLERANCE = 0.001

    # Пороги частоты для изменения чувствительности к типам событий
    # Если частота события > HIGH_FREQUENCY_THRESHOLD, увеличиваем чувствительность
    # Если частота события < LOW_FREQUENCY_THRESHOLD, уменьшаем чувствительность
    HIGH_FREQUENCY_THRESHOLD = 0.2  # 20% всех событий
    LOW_FREQUENCY_THRESHOLD = 0.1  # 10% всех событий

    # Пороги значимости для изменения порогов значимости
    # Если средняя значимость > HIGH_SIGNIFICANCE_THRESHOLD, снижаем порог
    # Если средняя значимость < LOW_SIGNIFICANCE_THRESHOLD, повышаем порог
    HIGH_SIGNIFICANCE_THRESHOLD = 0.5  # 50% средней значимости
    LOW_SIGNIFICANCE_THRESHOLD = 0.2  # 20% средней значимости

    # Пороги частоты для изменения коэффициентов реакции
    # Если паттерн используется > HIGH_PATTERN_FREQUENCY_THRESHOLD, увеличиваем коэффициент
    # Если паттерн используется < LOW_PATTERN_FREQUENCY_THRESHOLD, уменьшаем коэффициент
    HIGH_PATTERN_FREQUENCY_THRESHOLD = 0.3  # 30% всех паттернов
    LOW_PATTERN_FREQUENCY_THRESHOLD = 0.1  # 10% всех паттернов

    def __init__(self):
        """Инициализация LearningEngine с блокировкой для защиты от параллельных вызовов."""
        self._lock = threading.Lock()

    def process_statistics(self, memory: List[MemoryEntry]) -> Dict:
        """
        Анализирует Memory для извлечения статистики.

        Собирает данные о:
        - Типах событий и их частоте
        - Паттернах действий из Feedback
        - Изменениях состояния из Feedback

        ВАЖНО: Без интерпретации, только сбор статистики.

        Args:
            memory: Список записей Memory

        Returns:
            Словарь со статистикой (без интерпретации)
        """
        statistics = {
            "event_type_counts": {},
            "event_type_total_significance": {},
            "feedback_pattern_counts": {},
            "feedback_state_deltas": {
                "energy": [],
                "stability": [],
                "integrity": [],
            },
            "total_entries": len(memory),
            "feedback_entries": 0,
        }

        for entry in memory:
            # Статистика по типам событий
            if entry.event_type != "feedback":
                event_type = entry.event_type
                statistics["event_type_counts"][event_type] = (
                    statistics["event_type_counts"].get(event_type, 0) + 1
                )
                statistics["event_type_total_significance"][event_type] = (
                    statistics["event_type_total_significance"].get(event_type, 0.0)
                    + entry.meaning_significance
                )
            else:
                # Статистика по Feedback
                statistics["feedback_entries"] += 1
                if entry.feedback_data:
                    # Паттерны действий
                    pattern = entry.feedback_data.get("action_pattern", "")
                    if pattern:
                        statistics["feedback_pattern_counts"][pattern] = (
                            statistics["feedback_pattern_counts"].get(pattern, 0) + 1
                        )

                    # Изменения состояния
                    state_delta = entry.feedback_data.get("state_delta", {})
                    for key in ["energy", "stability", "integrity"]:
                        if key in state_delta:
                            statistics["feedback_state_deltas"][key].append(
                                state_delta[key]
                            )

        return statistics

    def adjust_parameters(
        self, statistics: Dict, current_params: Dict
    ) -> Dict[str, Dict[str, float]]:
        """
        Медленно изменяет внутренние параметры на основе статистики.

        ВАЖНО:
        - Без оценки эффективности
        - Без целей и намерений
        - Только медленное изменение на основе частоты/паттернов
        - Максимальное изменение: 0.01 за раз

        Args:
            statistics: Статистика из process_statistics
            current_params: Текущие параметры (learning_params из SelfState)

        Returns:
            Новые параметры (словарь с измененными значениями)

        Raises:
            ValueError: При некорректных входных параметрах
            TypeError: При некорректных типах данных
        """
        # ВАЛИДАЦИЯ: Проверяем входные параметры
        if not isinstance(current_params, dict):
            raise TypeError(
                f"current_params должен быть словарем, получен {type(current_params)}"
            )

        if not isinstance(statistics, dict):
            raise TypeError(f"statistics должен быть словарем, получен {type(statistics)}")

        if not current_params:
            raise ValueError("current_params не может быть пустым")

        # Валидация и нормализация значений в current_params
        validated_params = {}
        for key, value_dict in current_params.items():
            if not isinstance(value_dict, dict):
                logger.warning(f"Параметр {key} должен быть словарем, пропускаем")
                continue

            validated_params[key] = {}
            for param_name, param_value in value_dict.items():
                # Проверяем границы значений [0.0, 1.0]
                if not isinstance(param_value, (int, float)):
                    logger.warning(
                        f"Параметр {key}.{param_name} должен быть числом, пропускаем"
                    )
                    continue

                # Нормализуем значение до диапазона [0.0, 1.0]
                normalized_value = max(0.0, min(1.0, float(param_value)))
                if normalized_value != param_value:
                    logger.debug(
                        f"Нормализован параметр {key}.{param_name}: {param_value} -> {normalized_value}"
                    )
                validated_params[key][param_name] = normalized_value

        # Используем валидированные параметры
        current_params = validated_params

        # Проверяем, что после валидации остались валидные параметры
        if not current_params:
            raise ValueError("После валидации current_params стал пустым")
        new_params = {}

        # 1. Изменение чувствительности к типам событий
        if "event_type_sensitivity" in current_params:
            new_params["event_type_sensitivity"] = self._adjust_event_sensitivity(
                statistics, current_params["event_type_sensitivity"]
            )
        else:
            logger.warning(
                "adjust_parameters: отсутствует 'event_type_sensitivity' в current_params"
            )

        # 2. Изменение порогов значимости
        if "significance_thresholds" in current_params:
            new_params[
                "significance_thresholds"
            ] = self._adjust_significance_thresholds(
                statistics, current_params["significance_thresholds"]
            )
        else:
            logger.warning(
                "adjust_parameters: отсутствует 'significance_thresholds' в current_params"
            )

        # 3. Изменение коэффициентов реакции
        if "response_coefficients" in current_params:
            new_params["response_coefficients"] = self._adjust_response_coefficients(
                statistics, current_params["response_coefficients"]
            )
        else:
            logger.warning(
                "adjust_parameters: отсутствует 'response_coefficients' в current_params"
            )

        return new_params

    def _adjust_event_sensitivity(
        self, statistics: Dict, current_sensitivity: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Медленно изменяет чувствительность к типам событий.

        Изменение основано на частоте событий, не на оценке эффективности.
        """
        new_sensitivity = current_sensitivity.copy()
        event_counts = statistics.get("event_type_counts", {})
        total_events = sum(event_counts.values())

        if total_events == 0:
            return new_sensitivity

        for event_type, current_value in current_sensitivity.items():
            # Вычисляем частоту события
            count = event_counts.get(event_type, 0)
            frequency = count / total_events if total_events > 0 else 0.0

            # Направление изменения: если событие частое, немного увеличиваем чувствительность
            # БЕЗ оценки эффективности, только на основе частоты
            direction = (
                1.0
                if frequency > self.HIGH_FREQUENCY_THRESHOLD
                else -1.0
                if frequency < self.LOW_FREQUENCY_THRESHOLD
                else 0.0
            )

            # Медленное изменение: максимум 0.01
            delta = direction * self.MAX_PARAMETER_DELTA

            # Применяем изменение с учетом границ [0.0, 1.0]
            new_value = max(0.0, min(1.0, current_value + delta))

            # Применяем только если изменение значимо
            if abs(new_value - current_value) >= self.MIN_PARAMETER_DELTA:
                new_sensitivity[event_type] = new_value

        return new_sensitivity

    def _adjust_significance_thresholds(
        self, statistics: Dict, current_thresholds: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Медленно изменяет пороги значимости.

        Изменение основано на средней значимости событий, не на оценке эффективности.
        """
        new_thresholds = current_thresholds.copy()
        event_significance = statistics.get("event_type_total_significance", {})
        event_counts = statistics.get("event_type_counts", {})

        for event_type, current_value in current_thresholds.items():
            count = event_counts.get(event_type, 0)
            if count == 0:
                continue

            # Средняя значимость для этого типа события
            avg_significance = event_significance.get(event_type, 0.0) / count

            # Направление изменения: если средняя значимость высокая, немного снижаем порог
            # БЕЗ оценки эффективности, только на основе статистики
            if avg_significance > self.HIGH_SIGNIFICANCE_THRESHOLD:
                direction = -1.0  # Снижаем порог
            elif avg_significance < self.LOW_SIGNIFICANCE_THRESHOLD:
                direction = 1.0  # Повышаем порог
            else:
                direction = 0.0

            # Медленное изменение: максимум 0.01
            delta = direction * self.MAX_PARAMETER_DELTA

            # Применяем изменение с учетом границ [0.0, 1.0]
            new_value = max(0.0, min(1.0, current_value + delta))

            # Применяем только если изменение значимо
            if abs(new_value - current_value) >= self.MIN_PARAMETER_DELTA:
                new_thresholds[event_type] = new_value

        return new_thresholds

    def _adjust_response_coefficients(
        self, statistics: Dict, current_coefficients: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Медленно изменяет коэффициенты реакции.

        Изменение основано на частоте использования паттернов, не на оценке эффективности.
        """
        new_coefficients = current_coefficients.copy()
        pattern_counts = statistics.get("feedback_pattern_counts", {})
        total_patterns = sum(pattern_counts.values())

        if total_patterns == 0:
            return new_coefficients

        for pattern, current_value in current_coefficients.items():
            # Частота использования паттерна
            count = pattern_counts.get(pattern, 0)
            frequency = count / total_patterns if total_patterns > 0 else 0.0

            # Направление изменения: если паттерн часто используется, немного увеличиваем коэффициент
            # БЕЗ оценки эффективности, только на основе частоты
            direction = (
                1.0
                if frequency > self.HIGH_PATTERN_FREQUENCY_THRESHOLD
                else -1.0
                if frequency < self.LOW_PATTERN_FREQUENCY_THRESHOLD
                else 0.0
            )

            # Медленное изменение: максимум 0.01
            delta = direction * self.MAX_PARAMETER_DELTA

            # Применяем изменение с учетом границ [0.0, 1.0]
            new_value = max(0.0, min(1.0, current_value + delta))

            # Применяем только если изменение значимо
            if abs(new_value - current_value) >= self.MIN_PARAMETER_DELTA:
                new_coefficients[pattern] = new_value

        return new_coefficients

    def record_changes(
        self, old_params: Dict, new_params: Dict, self_state: "SelfState"
    ) -> None:
        """
        Фиксирует изменения параметров без интерпретации.

        ВАЖНО: Только фиксация, без оценки правильности изменений.
        Защищено блокировкой от параллельных вызовов.

        Args:
            old_params: Старые параметры
            new_params: Новые параметры (может содержать только часть параметров)
            self_state: SelfState для обновления learning_params

        Примечание: Метод выполняет глубокое объединение (merge) параметров,
        чтобы сохранить существующие значения, которые не были обновлены.
        """
        # Защита от параллельных вызовов
        with self._lock:
            # ПРОВЕРКА: Убеждаемся, что изменения медленные (<= 0.01)
            for key, new_value_dict in new_params.items():
                if key in old_params:
                    old_value_dict = old_params[key]
                    for param_name, new_value in new_value_dict.items():
                        if param_name in old_value_dict:
                            old_value = old_value_dict[param_name]
                            # Проверка на None для избежания TypeError
                            if old_value is None or new_value is None:
                                raise ValueError(
                                    f"Параметр {key}.{param_name} не может быть None: "
                                    f"old_value={old_value}, new_value={new_value}"
                                )
                            delta = abs(new_value - old_value)
                            # Проверка: изменения не должны превышать MAX_PARAMETER_DELTA
                            # Используем константу для допуска проверки
                            if delta > self.MAX_PARAMETER_DELTA + self._VALIDATION_TOLERANCE:
                                raise ValueError(
                                    f"Изменение параметра {key}.{param_name} слишком большое: "
                                    f"{delta} > {self.MAX_PARAMETER_DELTA}"
                                )

            # Обновляем параметры в SelfState ВНУТРИ блокировки
            # ВАЖНО: Выполняем глубокое объединение (merge), а не полную перезапись
            # ИСПРАВЛЕНИЕ RACE CONDITION: Используем deepcopy для создания полностью
            # независимой копии перед обновлением, чтобы избежать изменения словаря,
            # который может быть использован другим потоком
            if not hasattr(self_state, "learning_params"):
                self_state.learning_params = {}

            # Создаем глубокую копию текущих параметров для безопасного обновления
            updated_params = copy.deepcopy(self_state.learning_params)

            # Объединяем старые и новые параметры
            # Для каждого ключа в new_params объединяем вложенные словари
            for key, new_value_dict in new_params.items():
                if key not in updated_params:
                    # Если ключа нет, просто копируем новый словарь
                    updated_params[key] = copy.deepcopy(new_value_dict)
                else:
                    # Если ключ есть, объединяем вложенные словари
                    # Обновляем только те параметры, которые есть в new_params
                    for param_name, new_value in new_value_dict.items():
                        updated_params[key][param_name] = new_value

            # Атомарно заменяем все параметры одной операцией
            self_state.learning_params = updated_params

        # ВАЖНО: Не сохраняем историю изменений, не интерпретируем, не оцениваем
        # Просто обновляем параметры
