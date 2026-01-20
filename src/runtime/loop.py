import copy
import logging
import time

from src.action import execute_action
from src.activation.activation import activate_memory
from src.adaptation.adaptation import AdaptationManager
from src.decision.decision import decide_response
from src.feedback import observe_consequences, register_action
from src.intelligence.intelligence import process_information
from src.learning.learning import LearningEngine
from src.meaning.engine import MeaningEngine
from src.memory.memory import MemoryEntry
from src.planning.planning import record_potential_sequences
from src.runtime.life_policy import LifePolicy
from src.runtime.log_manager import FlushPolicy, LogManager
from src.runtime.snapshot_manager import SnapshotManager
from src.runtime.subjective_time import compute_subjective_dt
from src.state.self_state import SelfState, save_snapshot

logger = logging.getLogger(__name__)

# Константы для интервалов вызова компонентов (в тиках)
LEARNING_INTERVAL = 75  # Вызов Learning раз в 75 тиков (между 50-100)
ADAPTATION_INTERVAL = 100  # Вызов Adaptation раз в 100 тиков (реже чем Learning)
ARCHIVE_INTERVAL = 50  # Вызов архивации раз в 50 тиков
DECAY_INTERVAL = 10  # Вызов затухания весов раз в 10 тиков

# Константы для работы с памятью
MEMORY_DECAY_FACTOR = 0.99  # Фактор затухания весов памяти
MEMORY_MIN_WEIGHT = 0.1  # Минимальный вес для архивации
MEMORY_MAX_AGE_SECONDS = (
    7 * 24 * 3600
)  # Максимальный возраст записей (7 дней в секундах)
MEMORY_DECAY_MIN_WEIGHT = 0.0  # Минимальный вес при затухании (для полного забывания)

# Константы для обработки ошибок
# Штраф integrity при ошибке в цикле
ERROR_INTEGRITY_PENALTY = 0.05

# Константы для модификации impact
# Коэффициент для уменьшения impact при обработке событий
IMPACT_REDUCTION_COEFFICIENT = 0.5


def _get_default_learning_params() -> dict:
    """
    Получить параметры learning по умолчанию без создания временного объекта SelfState.

    Returns:
        dict: словарь с параметрами learning по умолчанию
    """
    return {
        "event_type_sensitivity": {
            "noise": 0.2,
            "decay": 0.2,
            "recovery": 0.2,
            "shock": 0.2,
            "idle": 0.2,
        },
        "significance_thresholds": {
            "noise": 0.1,
            "decay": 0.1,
            "recovery": 0.1,
            "shock": 0.1,
            "idle": 0.1,
        },
        "response_coefficients": {
            "dampen": 0.5,
            "absorb": 1.0,
            "ignore": 0.0,
        },
    }


def _get_default_adaptation_params() -> dict:
    """
    Получить параметры adaptation по умолчанию без создания временного объекта SelfState.

    Returns:
        dict: словарь с параметрами adaptation по умолчанию
    """
    return {
        "behavior_sensitivity": {
            "noise": 0.2,
            "decay": 0.2,
            "recovery": 0.2,
            "shock": 0.2,
            "idle": 0.2,
        },
        "behavior_thresholds": {
            "noise": 0.1,
            "decay": 0.1,
            "recovery": 0.1,
            "shock": 0.1,
            "idle": 0.1,
        },
        "behavior_coefficients": {
            "dampen": 0.5,
            "absorb": 1.0,
            "ignore": 0.0,
        },
    }


def _validate_learning_params(learning_params: dict) -> bool:
    """
    Валидирует структуру learning_params.

    Returns:
        True если параметры валидны, False иначе
    """
    if not isinstance(learning_params, dict):
        return False

    required_keys = [
        "event_type_sensitivity",
        "significance_thresholds",
        "response_coefficients",
    ]
    for key in required_keys:
        if key not in learning_params:
            return False
        if not isinstance(learning_params[key], dict):
            return False

    return True


def _validate_adaptation_params(adaptation_params: dict) -> bool:
    """
    Валидирует структуру adaptation_params.

    Returns:
        True если параметры валидны, False иначе
    """
    if not isinstance(adaptation_params, dict):
        return False

    # adaptation_params может быть пустым при первой инициализации
    # Проверяем только если есть ключи
    if adaptation_params:
        expected_keys = [
            "behavior_sensitivity",
            "behavior_thresholds",
            "behavior_coefficients",
        ]
        for key in expected_keys:
            if key in adaptation_params and not isinstance(
                adaptation_params[key], dict
            ):
                return False

    return True


def _safe_copy_dict(d: dict) -> dict:
    """
    Безопасное копирование словаря.
    Использует поверхностное копирование для простых словарей с числами,
    глубокое копирование только при необходимости.
    """
    if not d:
        return {}

    # Проверяем, нужна ли глубокая копия
    # Если все значения - простые типы (числа, строки), используем поверхностное копирование
    needs_deepcopy = False
    for value in d.values():
        if isinstance(value, dict):
            # Рекурсивно проверяем вложенные словари
            for nested_value in value.values():
                if isinstance(nested_value, (dict, list)):
                    needs_deepcopy = True
                    break
            if needs_deepcopy:
                break

    if needs_deepcopy:
        return copy.deepcopy(d)
    else:
        return d.copy()


def run_loop(
    self_state: SelfState,
    monitor,
    tick_interval=1.0,
    snapshot_period=10,
    stop_event=None,
    event_queue=None,
    disable_weakness_penalty=False,
):
    """
    Runtime Loop с интеграцией Environment (этап 07)

    Args:
        self_state: Состояние Life
        monitor: Функция мониторинга
        tick_interval: Интервал между тиками
        snapshot_period: Периодичность snapshot
        stop_event: threading.Event для остановки
        event_queue: Очередь событий из Environment
    """
    engine = MeaningEngine()
    learning_engine = LearningEngine()  # Learning Engine (Этап 14)
    adaptation_manager = AdaptationManager()  # Adaptation Manager (Этап 15)
    last_time = time.time()
    pending_actions = []  # Список ожидающих Feedback действий

    # Менеджеры для управления снапшотами, логами и политикой
    snapshot_manager = SnapshotManager(
        period_ticks=snapshot_period, saver=save_snapshot
    )
    flush_policy = FlushPolicy(
        flush_period_ticks=10,
        flush_before_snapshot=True,
        flush_on_exception=True,
        flush_on_shutdown=True,
    )
    log_manager = LogManager(
        flush_policy=flush_policy,
        flush_fn=self_state._flush_log_buffer,
    )
    life_policy = (
        LifePolicy()
    )  # Использует значения по умолчанию (совпадают с предыдущими константами)

    # Счетчики ошибок для отслеживания проблем
    learning_errors = 0
    adaptation_errors = 0
    max_errors_before_warning = 10  # Порог для предупреждения о частых ошибках

    while stop_event is None or not stop_event.is_set():
        try:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # Обновление состояния
            self_state.apply_delta({"ticks": 1})
            self_state.apply_delta({"age": dt})
            # Subjective time increment (metric only)
            subjective_dt = compute_subjective_dt(
                dt=dt,
                base_rate=self_state.subjective_time_base_rate,
                intensity=self_state.last_event_intensity,
                stability=self_state.stability,
                energy=self_state.energy,
                intensity_coeff=self_state.subjective_time_intensity_coeff,
                stability_coeff=self_state.subjective_time_stability_coeff,
                energy_coeff=self_state.subjective_time_energy_coeff,
                rate_min=self_state.subjective_time_rate_min,
                rate_max=self_state.subjective_time_rate_max,
            )
            self_state.apply_delta({"subjective_time": subjective_dt})

            # Наблюдаем последствия прошлых действий (Feedback)
            feedback_records = observe_consequences(
                self_state, pending_actions, event_queue
            )

            # Сохраняем Feedback в Memory
            for feedback in feedback_records:
                feedback_entry = MemoryEntry(
                    event_type="feedback",
                    meaning_significance=0.0,  # Feedback не имеет значимости
                    timestamp=feedback.timestamp,
                    subjective_timestamp=self_state.subjective_time,
                    feedback_data={
                        "action_id": feedback.action_id,
                        "action_pattern": feedback.action_pattern,
                        "state_delta": feedback.state_delta,
                        "delay_ticks": feedback.delay_ticks,
                        "associated_events": feedback.associated_events,
                    },
                )
                self_state.memory.append(feedback_entry)

            # === ШАГ 1: Получить события из среды ===
            if event_queue and not event_queue.is_empty():
                logger.debug(f"[LOOP] Queue not empty, size={event_queue.size()}")
                events = event_queue.pop_all()
                logger.debug(f"[LOOP] POPPED {len(events)} events")
                # Update intensity signal for this tick using exponential smoothing
                try:
                    current_max_intensity = max(
                        [float(e.intensity) for e in events] + [0.0]
                    )
                    # Exponential smoothing: new_value = alpha * current + (1-alpha) * previous
                    alpha = self_state.subjective_time_intensity_smoothing
                    self_state.last_event_intensity = (
                        alpha * current_max_intensity
                        + (1 - alpha) * self_state.last_event_intensity
                    )
                except Exception:
                    self_state.last_event_intensity = 0.0

                # === ШАГ 2: Интерпретировать события ===
                for event in events:
                    logger.debug(
                        f"[LOOP] Interpreting event: type={event.type}, intensity={event.intensity}"
                    )
                    meaning = engine.process(
                        event, self_state.get_safe_status_dict(include_optional=False)
                    )
                    if meaning.significance > 0:
                        # Активация памяти для события
                        activated = activate_memory(event.type, self_state.memory)
                        self_state.activated_memory = activated
                        logger.debug(
                            f"[LOOP] Activated {len(activated)} memories for type '{event.type}'"
                        )

                        # Decision
                        pattern = decide_response(self_state, meaning)
                        self_state.last_pattern = pattern
                        if pattern == "ignore":
                            continue  # skip apply_delta
                        elif pattern == "dampen":
                            meaning.impact = {
                                k: v * IMPACT_REDUCTION_COEFFICIENT
                                for k, v in meaning.impact.items()
                            }
                        # else "absorb" — no change

                        # КРИТИЧНО: Сохраняем снимок состояния ДО действия
                        state_before = {
                            "energy": self_state.energy,
                            "stability": self_state.stability,
                            "integrity": self_state.integrity,
                        }

                        self_state.apply_delta(meaning.impact)
                        execute_action(pattern, self_state)

                        # Регистрируем для Feedback (после выполнения)
                        # Action не знает о Feedback - регистрация происходит в Loop
                        action_id = f"action_{self_state.ticks}_{pattern}_{int(time.time()*1000)}"
                        action_timestamp = time.time()
                        register_action(
                            action_id,
                            pattern,
                            state_before,
                            action_timestamp,
                            pending_actions,
                        )
                        self_state.recent_events.append(event.type)
                        self_state.last_significance = meaning.significance
                        self_state.memory.append(
                            MemoryEntry(
                                event_type=event.type,
                                meaning_significance=meaning.significance,
                                timestamp=time.time(),
                                subjective_timestamp=self_state.subjective_time,
                            )
                        )
                    logger.debug(
                        f"[LOOP] After interpret: energy={self_state.energy:.2f}, stability={self_state.stability:.4f}"
                    )

                record_potential_sequences(self_state)
                process_information(self_state)
            else:
                # No events this tick -> gradually decay intensity signal using smoothing
                alpha = self_state.subjective_time_intensity_smoothing
                self_state.last_event_intensity = (
                    1 - alpha
                ) * self_state.last_event_intensity

            # Learning (Этап 14) - медленное изменение внутренних параметров
            # Вызывается раз в LEARNING_INTERVAL тиков, после Feedback, перед Planning/Intelligence
            if self_state.ticks > 0 and self_state.ticks % LEARNING_INTERVAL == 0:
                try:
                    # Проверяем инициализацию параметров
                    if (
                        not hasattr(self_state, "learning_params")
                        or not self_state.learning_params
                    ):
                        # Автоматическая инициализация при первом запуске
                        logger.info(
                            "learning_params не инициализирован, инициализируем значениями по умолчанию"
                        )
                        # Используем метод из SelfState для получения значений по умолчанию
                        if hasattr(self_state, "_get_default_learning_params"):
                            self_state.learning_params = (
                                self_state._get_default_learning_params()
                            )
                        else:
                            # Fallback: используем вспомогательную функцию без создания временного объекта
                            self_state.learning_params = _get_default_learning_params()

                    # Валидируем структуру параметров
                    if not _validate_learning_params(self_state.learning_params):
                        logger.error(
                            "learning_params имеет некорректную структуру, исправляем значениями по умолчанию"
                        )
                        # Исправляем некорректную структуру значениями по умолчанию
                        if hasattr(self_state, "_get_default_learning_params"):
                            self_state.learning_params = (
                                self_state._get_default_learning_params()
                            )
                        else:
                            # Fallback: используем вспомогательную функцию без создания временного объекта
                            self_state.learning_params = _get_default_learning_params()

                    # Обрабатываем статистику из Memory
                    statistics = learning_engine.process_statistics(self_state.memory)

                    # Получаем текущие параметры
                    current_params = self_state.learning_params

                    # Медленно изменяем параметры (без оптимизации, без целей)
                    new_params = learning_engine.adjust_parameters(
                        statistics, current_params
                    )

                    # Фиксируем изменения в SelfState (пустой словарь означает отсутствие изменений)
                    if new_params:
                        learning_engine.record_changes(
                            current_params, new_params, self_state
                        )
                except (TypeError, ValueError) as e:
                    learning_errors += 1
                    logger.error(
                        f"Критическая ошибка в Learning (параметры): {e}", exc_info=True
                    )
                    # При критичных ошибках валидации пропускаем только блок Learning,
                    # но продолжаем выполнение остальных частей итерации
                    if learning_errors >= max_errors_before_warning:
                        logger.warning(
                            f"Обнаружено {learning_errors} ошибок в Learning. "
                            "Возможна деградация функциональности."
                        )
                except Exception as e:
                    learning_errors += 1
                    logger.error(f"Неожиданная ошибка в Learning: {e}", exc_info=True)
                    # При неожиданных ошибках пропускаем только блок Learning,
                    # но продолжаем выполнение остальных частей итерации
                    if learning_errors >= max_errors_before_warning:
                        logger.warning(
                            f"Обнаружено {learning_errors} ошибок в Learning. "
                            "Возможна деградация функциональности."
                        )

            # Затухание весов памяти (Memory v2.0) - механизм забывания
            # Вызывается раз в DECAY_INTERVAL тиков
            if self_state.ticks > 0 and self_state.ticks % DECAY_INTERVAL == 0:
                try:
                    self_state.memory.decay_weights(
                        decay_factor=MEMORY_DECAY_FACTOR,
                        min_weight=MEMORY_DECAY_MIN_WEIGHT,
                    )
                except Exception as e:
                    logger.error(f"Ошибка в decay_weights: {e}", exc_info=True)

            # Архивация старых записей памяти (Memory v2.0)
            # Вызывается раз в ARCHIVE_INTERVAL тиков
            if self_state.ticks > 0 and self_state.ticks % ARCHIVE_INTERVAL == 0:
                try:
                    # Архивируем записи старше MEMORY_MAX_AGE_SECONDS или с весом < MEMORY_MIN_WEIGHT
                    archived_count = self_state.memory.archive_old_entries(
                        max_age=MEMORY_MAX_AGE_SECONDS, min_weight=MEMORY_MIN_WEIGHT
                    )
                    if archived_count > 0:
                        logger.info(
                            f"[LOOP] Заархивировано {archived_count} записей памяти"
                        )
                except Exception as e:
                    logger.error(f"Ошибка в archive_old_entries: {e}", exc_info=True)

            # Adaptation (Этап 15) - медленная перестройка поведения на основе статистики Learning
            # Вызывается раз в ADAPTATION_INTERVAL тиков, после Learning, перед Planning/Intelligence
            if self_state.ticks > 0 and self_state.ticks % ADAPTATION_INTERVAL == 0:
                try:
                    # Проверяем инициализацию параметров
                    if (
                        not hasattr(self_state, "learning_params")
                        or not self_state.learning_params
                    ):
                        # Автоматическая инициализация при первом запуске
                        logger.info(
                            "learning_params не инициализирован, инициализируем значениями по умолчанию"
                        )
                        if hasattr(self_state, "_get_default_learning_params"):
                            self_state.learning_params = (
                                self_state._get_default_learning_params()
                            )
                        else:
                            # Используем вспомогательную функцию без создания временного объекта
                            self_state.learning_params = _get_default_learning_params()

                    if (
                        not hasattr(self_state, "adaptation_params")
                        or not self_state.adaptation_params
                    ):
                        # Автоматическая инициализация при первом запуске
                        logger.info(
                            "adaptation_params не инициализирован, инициализируем значениями по умолчанию"
                        )
                        if hasattr(self_state, "_get_default_adaptation_params"):
                            self_state.adaptation_params = (
                                self_state._get_default_adaptation_params()
                            )
                        else:
                            # Fallback: используем вспомогательную функцию без создания временного объекта
                            self_state.adaptation_params = (
                                _get_default_adaptation_params()
                            )

                    # Валидируем структуру параметров
                    if not _validate_learning_params(self_state.learning_params):
                        logger.error(
                            "learning_params имеет некорректную структуру, исправляем значениями по умолчанию"
                        )
                        if hasattr(self_state, "_get_default_learning_params"):
                            self_state.learning_params = (
                                self_state._get_default_learning_params()
                            )
                        else:
                            # Используем вспомогательную функцию без создания временного объекта
                            self_state.learning_params = _get_default_learning_params()

                    if not _validate_adaptation_params(self_state.adaptation_params):
                        logger.error(
                            "adaptation_params имеет некорректную структуру, исправляем значениями по умолчанию"
                        )
                        if hasattr(self_state, "_get_default_adaptation_params"):
                            self_state.adaptation_params = (
                                self_state._get_default_adaptation_params()
                            )
                        else:
                            # Fallback: используем вспомогательную функцию без создания временного объекта
                            self_state.adaptation_params = (
                                _get_default_adaptation_params()
                            )

                    # Анализируем изменения от Learning
                    analysis = adaptation_manager.analyze_changes(
                        self_state.learning_params,
                        self_state.adaptation_history,
                    )

                    # Получаем текущие параметры поведения (безопасная копия для истории)
                    # Используем оптимизированное копирование вместо глубокого
                    old_behavior_params = _safe_copy_dict(self_state.adaptation_params)

                    # Применяем адаптацию (медленная перестройка поведения)
                    new_behavior_params = adaptation_manager.apply_adaptation(
                        analysis, old_behavior_params, self_state
                    )

                    # Сохраняем историю и обновляем параметры
                    if new_behavior_params:
                        # Оптимизированное объединение параметров в SelfState
                        # Гарантируем, что все существующие параметры сохраняются
                        for key, new_value_dict in new_behavior_params.items():
                            if key not in self_state.adaptation_params:
                                # Новый параметр - копируем безопасно
                                self_state.adaptation_params[key] = _safe_copy_dict(
                                    new_value_dict
                                )
                            else:
                                # Существующий параметр - объединение
                                current_value_dict = self_state.adaptation_params[key]
                                if isinstance(new_value_dict, dict) and isinstance(
                                    current_value_dict, dict
                                ):
                                    # Обновляем только измененные параметры, сохраняя остальные
                                    for param_name, new_value in new_value_dict.items():
                                        current_value_dict[param_name] = new_value
                                    # Не перезаписываем весь словарь, чтобы сохранить ключи,
                                    # которые не были в new_value_dict

                        # Сохраняем историю адаптаций с актуальными старыми параметрами
                        adaptation_manager.store_history(
                            old_behavior_params,
                            new_behavior_params,
                            self_state,
                        )
                except (TypeError, ValueError) as e:
                    logger.error(
                        f"Критическая ошибка в Adaptation (параметры): {e}",
                        exc_info=True,
                    )
                    # При критичных ошибках валидации пропускаем только блок Adaptation,
                    # но продолжаем выполнение остальных частей итерации
                    pass
                except Exception as e:
                    logger.error(f"Неожиданная ошибка в Adaptation: {e}", exc_info=True)
                    # При неожиданных ошибках пропускаем только блок Adaptation,
                    # но продолжаем выполнение остальных частей итерации
                    pass

            # Логика слабости: когда параметры низкие, добавляем штрафы за немощность
            if not disable_weakness_penalty and life_policy.is_weak(self_state):
                penalty_deltas = life_policy.weakness_penalty(dt)
                self_state.apply_delta(penalty_deltas)
                penalty = abs(penalty_deltas["energy"])
                logger.debug(
                    f"[LOOP] Слабость: штрафы penalty={penalty:.4f}, energy={self_state.energy:.2f}"
                )

            # Вызов мониторинга
            try:
                monitor(self_state)
            except Exception as e:
                logger.error(f"Ошибка в monitor: {e}", exc_info=True)

            # Flush логов перед снапшотом (если политика требует)
            log_manager.maybe_flush(self_state, phase="before_snapshot")

            # Snapshot через SnapshotManager
            snapshot_was_made = snapshot_manager.maybe_snapshot(self_state)

            # Flush логов после снапшота (если политика требует)
            if snapshot_was_made:
                log_manager.maybe_flush(self_state, phase="after_snapshot")

            # Flush логов по периодичности (редко, не на каждом тике)
            # Примечание: flush после снапшота обрабатывается только в фазе "after_snapshot" выше,
            # чтобы избежать двойного flush.
            log_manager.maybe_flush(self_state, phase="tick")

            # Поддержка постоянного интервала тиков
            tick_end = time.time()
            elapsed_tick = tick_end - current_time
            sleep_duration = max(0.0, tick_interval - elapsed_tick)
            time.sleep(sleep_duration)

        except Exception as e:
            self_state.apply_delta({"integrity": -ERROR_INTEGRITY_PENALTY})
            logger.error(f"[LOOP] Ошибка в цикле: {e}", exc_info=True)
            # Flush логов при исключении (если политика требует)
            log_manager.maybe_flush(self_state, phase="exception")

        finally:
            # Flush логов при завершении (обязательно)
            log_manager.maybe_flush(self_state, phase="shutdown")

            # NOTE: Система Life не останавливается при параметрах <= 0
            # Она продолжает работать в degraded состоянии ("бессмертная слабость")
            # Остановка происходит только по внешнему сигналу (stop_event)
