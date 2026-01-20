"""
Adaptation Manager - Этап 15

ВАЖНО: Adaptation НЕ является оптимизацией, reinforcement learning или управлением поведением.
Adaptation только медленно перестраивает поведение на основе статистики Learning.

Архитектурные ограничения:
- ❌ Запрещено: оптимизация, цели, намерения, reward, utility, scoring
- ❌ Запрещено: оценка эффективности действий, корректировка поведения
- ❌ Запрещено: циклы обратной связи, внешние метрики
- ❌ Запрещено: прямое управление Decision, Action или Feedback
- ✅ Разрешено: постепенное изменение внутренних параметров поведения (макс. 0.01 за раз)
- ✅ Разрешено: фиксация изменений без интерпретации
- ✅ Разрешено: использование внутренней статистики из Learning
"""

import logging
import threading
import time
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from src.state.self_state import SelfState

logger = logging.getLogger(__name__)


class AdaptationManager:
    """
    Adaptation Manager - медленная перестройка поведения на основе статистики Learning.

    Adaptation не отвечает на вопрос "что делать дальше".
    Adaptation только медленно перестраивает внутренние параметры поведения без интерпретации.

    ВАЖНО: Параметры adaptation_params изменяются и используются в:
    - MeaningEngine: behavior_sensitivity для модификации значимости событий,
      behavior_thresholds для модификации порогов реакций,
      behavior_coefficients для модификации эффектов паттернов
    - Decision: behavior_thresholds для модификации порогов dampen/ignore
    - Action: behavior_coefficients для модификации эффектов действий
    """

    # Максимальное изменение параметра за один вызов
    MAX_ADAPTATION_DELTA = 0.01

    # Минимальное изменение для применения (чтобы избежать микро-изменений)
    MIN_ADAPTATION_DELTA = 0.001

    # Максимальный размер истории адаптаций
    MAX_HISTORY_SIZE = 50

    # Допуск для проверки изменений параметров (для учета погрешностей вычислений с плавающей точкой)
    # Используется при сравнении delta с MAX_ADAPTATION_DELTA
    _VALIDATION_TOLERANCE = 0.001

    def __init__(self):
        """Инициализация AdaptationManager с блокировкой для защиты от параллельных вызовов."""
        self._lock = threading.Lock()

    def analyze_changes(
        self, learning_params: Dict, adaptation_history: List[Dict]
    ) -> Dict:
        """
        Анализирует изменения параметров от Learning.

        Сравнивает текущие learning_params с историей изменений.
        Извлекает паттерны изменений (без интерпретации).

        ВАЖНО: Без оценки эффективности, без выбора "лучших" изменений.
        Только фиксирует факты изменений.

        Args:
            learning_params: Текущие параметры Learning из SelfState
            adaptation_history: История адаптаций из SelfState

        Returns:
            Словарь с анализом изменений (без интерпретации)
        """
        analysis = {
            "learning_params_snapshot": learning_params.copy(),
            "recent_changes": {},
            "change_patterns": {},
        }

        # Если есть история, сравниваем с последней адаптацией
        if adaptation_history:
            last_adaptation = adaptation_history[-1]
            last_learning_snapshot = last_adaptation.get("learning_params_snapshot", {})

            # Сравниваем текущие learning_params с последним снимком
            for key, current_value_dict in learning_params.items():
                if key in last_learning_snapshot:
                    last_value_dict = last_learning_snapshot[key]
                    changes = {}

                    # Сравниваем вложенные словари
                    if isinstance(current_value_dict, dict) and isinstance(
                        last_value_dict, dict
                    ):
                        for param_name, current_value in current_value_dict.items():
                            if param_name in last_value_dict:
                                last_value = last_value_dict[param_name]
                                delta = current_value - last_value
                                if abs(delta) >= self.MIN_ADAPTATION_DELTA:
                                    changes[param_name] = {
                                        "old": last_value,
                                        "new": current_value,
                                        "delta": delta,
                                    }

                    if changes:
                        analysis["recent_changes"][key] = changes

        # Извлекаем паттерны изменений (без интерпретации)
        # Просто фиксируем, какие параметры изменились чаще всего
        if adaptation_history:
            change_frequency = {}
            for entry in adaptation_history[-10:]:  # Последние 10 адаптаций
                changes = entry.get("changes", {})
                for param_key, param_changes in changes.items():
                    if param_key not in change_frequency:
                        change_frequency[param_key] = {}
                    if isinstance(param_changes, dict):
                        for param_name in param_changes.keys():
                            change_frequency[param_key][param_name] = (
                                change_frequency[param_key].get(param_name, 0) + 1
                            )
            analysis["change_patterns"] = change_frequency

        return analysis

    def apply_adaptation(
        self,
        analysis: Dict,
        current_behavior_params: Dict,
        self_state,
    ) -> Dict:
        """
        Медленно перестраивает параметры поведения на основе анализа.

        Изменяет параметры, которые влияют на поведение (не Decision/Action напрямую).
        Максимальное изменение: не более 0.01 за раз.

        ВАЖНО:
        - Не изменяет Decision или Action напрямую
        - Не инициирует новые действия
        - Только изменяет внутренние параметры поведения
        - Без оценки эффективности

        Args:
            analysis: Результат analyze_changes
            current_behavior_params: Текущие параметры поведения из SelfState
            self_state: SelfState для доступа к learning_params

        Returns:
            Новые параметры поведения (словарь с измененными значениями)
        """
        # ВАЛИДАЦИЯ: Проверяем входные параметры
        if not isinstance(analysis, dict):
            raise TypeError(f"analysis должен быть словарем, получен {type(analysis)}")

        if not isinstance(current_behavior_params, dict):
            raise TypeError(
                f"current_behavior_params должен быть словарем, получен {type(current_behavior_params)}"
            )

        # ПРОВЕРКА: Adaptation не должен напрямую изменять Decision/Action
        # Проверяем ключи словаря рекурсивно с точным совпадением
        def _check_forbidden_keys(params_dict: Dict, path: str = "") -> None:
            """Рекурсивно проверяет наличие запрещенных ключей с точным совпадением."""
            # Используем точное совпадение ключей вместо подстроки
            forbidden_keys_exact = {"decision", "action"}
            for key, value in params_dict.items():
                current_path = f"{path}.{key}" if path else key
                # Проверяем ключ на точное совпадение (case-insensitive)
                key_lower = str(key).lower()
                if key_lower in forbidden_keys_exact:
                    raise ValueError(
                        f"Adaptation не может напрямую изменять Decision/Action. "
                        f"Обнаружен запрещенный ключ: {current_path}"
                    )
                # Рекурсивно проверяем вложенные словари
                if isinstance(value, dict):
                    _check_forbidden_keys(value, current_path)

        new_params = {}

        # Получаем learning_params из анализа
        learning_params = analysis.get("learning_params_snapshot", {})

        # Используем self_state.adaptation_params напрямую для получения актуальных значений
        # Это гарантирует, что мы работаем с реальными параметрами, даже если
        # current_behavior_params был передан пустым (старый snapshot)
        actual_params = getattr(self_state, "adaptation_params", {})
        if not actual_params:
            # Если adaptation_params действительно пустой, используем current_behavior_params
            # (для обратной совместимости со старыми snapshots)
            actual_params = current_behavior_params

        # Проверяем actual_params, который фактически используется
        _check_forbidden_keys(actual_params)

        # 1. Адаптация чувствительности к типам событий
        if (
            "behavior_sensitivity" in actual_params
            and actual_params["behavior_sensitivity"]
        ):
            new_params["behavior_sensitivity"] = self._adapt_behavior_sensitivity(
                learning_params, actual_params["behavior_sensitivity"]
            )
        else:
            # Инициализация, если параметр действительно отсутствует
            new_params["behavior_sensitivity"] = self._init_behavior_sensitivity(
                learning_params
            )

        # 2. Адаптация порогов для реакций
        if (
            "behavior_thresholds" in actual_params
            and actual_params["behavior_thresholds"]
        ):
            new_params["behavior_thresholds"] = self._adapt_behavior_thresholds(
                learning_params, actual_params["behavior_thresholds"]
            )
        else:
            # Инициализация, если параметр действительно отсутствует
            new_params["behavior_thresholds"] = self._init_behavior_thresholds(
                learning_params
            )

        # 3. Адаптация коэффициентов для паттернов
        if (
            "behavior_coefficients" in actual_params
            and actual_params["behavior_coefficients"]
        ):
            new_params["behavior_coefficients"] = self._adapt_behavior_coefficients(
                learning_params, actual_params["behavior_coefficients"]
            )
        else:
            # Инициализация, если параметр действительно отсутствует
            new_params["behavior_coefficients"] = self._init_behavior_coefficients(
                learning_params
            )

        # ПРОВЕРКА: Убеждаемся, что изменения медленные (<= 0.01)
        # Используем actual_params для проверки, так как это актуальные значения
        for key, new_value_dict in new_params.items():
            if key in actual_params:
                old_value_dict = actual_params[key]
                if isinstance(new_value_dict, dict) and isinstance(
                    old_value_dict, dict
                ):
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
                            if delta > self.MAX_ADAPTATION_DELTA + self._VALIDATION_TOLERANCE:
                                raise ValueError(
                                    f"Изменение параметра {key}.{param_name} слишком большое: "
                                    f"{delta} > {self.MAX_ADAPTATION_DELTA}"
                                )

        # ПРОВЕРКА: Проверяем new_params на выходе на наличие запрещенных ключей
        _check_forbidden_keys(new_params)

        return new_params

    def _adapt_behavior_sensitivity(
        self, learning_params: Dict, current_sensitivity: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Медленно адаптирует чувствительность к типам событий.

        Использует данные из learning_params.event_type_sensitivity.
        Медленно адаптируется на основе частоты изменений Learning.
        """
        new_sensitivity = current_sensitivity.copy()
        learning_sensitivity = learning_params.get("event_type_sensitivity", {})

        for event_type, current_value in current_sensitivity.items():
            if event_type in learning_sensitivity:
                learning_value = learning_sensitivity[event_type]

                # Медленное приближение к значению Learning (не копирование!)
                # Разница между текущим и learning значением
                diff = learning_value - current_value

                # Направление изменения: медленное приближение
                # БЕЗ оценки эффективности, только медленное изменение
                direction = 1.0 if diff > 0 else -1.0 if diff < 0 else 0.0

                # Медленное изменение: максимум 0.01
                delta = direction * min(abs(diff), self.MAX_ADAPTATION_DELTA)

                # Применяем изменение с учетом границ [0.0, 1.0]
                new_value = max(0.0, min(1.0, current_value + delta))

                # Применяем только если изменение значимо
                if abs(new_value - current_value) >= self.MIN_ADAPTATION_DELTA:
                    new_sensitivity[event_type] = new_value

        return new_sensitivity

    def _init_behavior_sensitivity(self, learning_params: Dict) -> Dict[str, float]:
        """Инициализирует behavior_sensitivity на основе learning_params."""
        learning_sensitivity = learning_params.get("event_type_sensitivity", {})
        # Копируем начальные значения из Learning
        return learning_sensitivity.copy()

    def _adapt_behavior_thresholds(
        self, learning_params: Dict, current_thresholds: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Медленно адаптирует пороги для реакций.

        Использует данные из learning_params.significance_thresholds.
        Медленно адаптируется на основе паттернов Learning.
        """
        new_thresholds = current_thresholds.copy()
        learning_thresholds = learning_params.get("significance_thresholds", {})

        for event_type, current_value in current_thresholds.items():
            if event_type in learning_thresholds:
                learning_value = learning_thresholds[event_type]

                # Медленное приближение к значению Learning
                diff = learning_value - current_value
                direction = 1.0 if diff > 0 else -1.0 if diff < 0 else 0.0
                delta = direction * min(abs(diff), self.MAX_ADAPTATION_DELTA)

                new_value = max(0.0, min(1.0, current_value + delta))

                if abs(new_value - current_value) >= self.MIN_ADAPTATION_DELTA:
                    new_thresholds[event_type] = new_value

        return new_thresholds

    def _init_behavior_thresholds(self, learning_params: Dict) -> Dict[str, float]:
        """Инициализирует behavior_thresholds на основе learning_params."""
        learning_thresholds = learning_params.get("significance_thresholds", {})
        return learning_thresholds.copy()

    def _adapt_behavior_coefficients(
        self, learning_params: Dict, current_coefficients: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Медленно адаптирует коэффициенты для паттернов.

        Использует данные из learning_params.response_coefficients.
        Медленно адаптируется на основе частоты использования паттернов.
        """
        new_coefficients = current_coefficients.copy()
        learning_coefficients = learning_params.get("response_coefficients", {})

        for pattern, current_value in current_coefficients.items():
            if pattern in learning_coefficients:
                learning_value = learning_coefficients[pattern]

                # Медленное приближение к значению Learning
                diff = learning_value - current_value
                direction = 1.0 if diff > 0 else -1.0 if diff < 0 else 0.0
                delta = direction * min(abs(diff), self.MAX_ADAPTATION_DELTA)

                new_value = max(0.0, min(1.0, current_value + delta))

                if abs(new_value - current_value) >= self.MIN_ADAPTATION_DELTA:
                    new_coefficients[pattern] = new_value

        return new_coefficients

    def _init_behavior_coefficients(self, learning_params: Dict) -> Dict[str, float]:
        """Инициализирует behavior_coefficients на основе learning_params."""
        learning_coefficients = learning_params.get("response_coefficients", {})
        return learning_coefficients.copy()

    def store_history(
        self, old_params: Dict, new_params: Dict, self_state: "SelfState"
    ) -> None:
        """
        Хранит историю адаптаций для обратимости.

        Сохраняет изменения в self_state.adaptation_history.
        Фиксирует timestamp и изменения без интерпретации.

        ВАЖНО: Только хранение фактов, без интерпретации и оптимизации.
        Защищено блокировкой от параллельных вызовов.

        Args:
            old_params: Старые параметры поведения
            new_params: Новые параметры поведения
            self_state: SelfState для обновления adaptation_history
        """
        # Защита от параллельных вызовов
        with self._lock:
            # Вычисляем только измененные параметры
            changes = {}
            for key, new_value_dict in new_params.items():
                if key in old_params:
                    old_value_dict = old_params[key]
                    if isinstance(new_value_dict, dict) and isinstance(
                        old_value_dict, dict
                    ):
                        param_changes = {}
                        for param_name, new_value in new_value_dict.items():
                            if param_name in old_value_dict:
                                old_value = old_value_dict[param_name]
                                # Проверка на None для избежания TypeError
                                # УНИФИЦИРОВАННАЯ ОБРАБОТКА: выбрасываем исключение как в apply_adaptation()
                                if old_value is None or new_value is None:
                                    logger.warning(
                                        f"Параметр {key}.{param_name} имеет значение None: "
                                        f"old_value={old_value}, new_value={new_value}. Пропускаем."
                                    )
                                    continue
                                if abs(new_value - old_value) >= self.MIN_ADAPTATION_DELTA:
                                    param_changes[param_name] = {
                                        "old": old_value,
                                        "new": new_value,
                                        "delta": new_value - old_value,
                                    }
                        if param_changes:
                            changes[key] = param_changes
                else:
                    # Новый параметр
                    changes[key] = new_value_dict

            # Создаем запись истории
            history_entry = {
                "timestamp": time.time(),
                "tick": getattr(self_state, "ticks", 0),
                "old_params": old_params.copy(),
                "new_params": new_params.copy(),
                "changes": changes,
                "learning_params_snapshot": getattr(
                    self_state, "learning_params", {}
                ).copy(),
            }

            # Добавляем в историю
            if not hasattr(self_state, "adaptation_history"):
                self_state.adaptation_history = []

            self_state.adaptation_history.append(history_entry)

            # Ограничиваем размер истории
            if len(self_state.adaptation_history) > self.MAX_HISTORY_SIZE:
                self_state.adaptation_history = self_state.adaptation_history[
                    -self.MAX_HISTORY_SIZE :
                ]

            # ВАЖНО: Не интерпретируем историю, не используем для оптимизации
            # Просто храним факты для возможной обратимости

    def _init_behavior_params_from_learning(self, learning_params: Dict) -> Dict:
        """
        Инициализирует параметры поведения на основе параметров Learning.

        Args:
            learning_params: Параметры Learning для копирования

        Returns:
            Инициализированные параметры поведения
        """
        behavior_params = {}

        # Копируем event_type_sensitivity -> behavior_sensitivity
        if "event_type_sensitivity" in learning_params:
            behavior_params["behavior_sensitivity"] = learning_params["event_type_sensitivity"].copy()
        else:
            # Fallback на значения по умолчанию
            behavior_params["behavior_sensitivity"] = {
                "noise": 0.2,
                "decay": 0.2,
                "recovery": 0.2,
                "shock": 0.2,
                "idle": 0.2,
            }

        # Копируем significance_thresholds -> behavior_thresholds
        if "significance_thresholds" in learning_params:
            behavior_params["behavior_thresholds"] = learning_params["significance_thresholds"].copy()
        else:
            # Fallback на значения по умолчанию
            behavior_params["behavior_thresholds"] = {
                "noise": 0.1,
                "decay": 0.1,
                "recovery": 0.1,
                "shock": 0.1,
                "idle": 0.1,
            }

        # Копируем response_coefficients -> behavior_coefficients
        if "response_coefficients" in learning_params:
            behavior_params["behavior_coefficients"] = learning_params["response_coefficients"].copy()
        else:
            # Fallback на значения по умолчанию
            behavior_params["behavior_coefficients"] = {
                "dampen": 0.5,
                "absorb": 1.0,
                "ignore": 0.0,
            }

        return behavior_params
