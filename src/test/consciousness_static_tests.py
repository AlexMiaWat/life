"""
Статические тесты для экспериментальной функциональности Consciousness States.

Включает unit тесты, валидацию типов, проверку контрактов сериализации.
"""

import pytest
import time
from typing import Dict, Any, List
from unittest.mock import Mock

from src.experimental.consciousness.states import (
    ConsciousnessState,
    ConsciousnessStateData,
    ConsciousnessStateManager
)


class TestConsciousnessState:
    """Тесты для ConsciousnessState."""

    def test_consciousness_state_enum_values(self):
        """Тест значений enum ConsciousnessState."""
        assert ConsciousnessState.INACTIVE.value == "inactive"
        assert ConsciousnessState.INITIALIZING.value == "initializing"
        assert ConsciousnessState.ACTIVE.value == "active"
        assert ConsciousnessState.PROCESSING.value == "processing"
        assert ConsciousnessState.ANALYZING.value == "analyzing"
        assert ConsciousnessState.REFLECTING.value == "reflecting"
        assert ConsciousnessState.ERROR.value == "error"
        assert ConsciousnessState.SHUTDOWN.value == "shutdown"

    def test_all_consciousness_states_exist(self):
        """Тест что все необходимые состояния сознания определены."""
        states = [state.value for state in ConsciousnessState]
        expected_states = [
            "inactive", "initializing", "active", "processing",
            "analyzing", "reflecting", "error", "shutdown"
        ]
        assert set(states) == set(expected_states)


class TestConsciousnessStateData:
    """Тесты для ConsciousnessStateData."""

    def test_state_data_initialization(self):
        """Тест инициализации ConsciousnessStateData."""
        state_data = ConsciousnessStateData(
            state=ConsciousnessState.ACTIVE,
            timestamp=123.45,
            metadata={"test": "metadata"},
            metrics={"efficiency": 0.8},
            error_message="Test error"
        )

        assert state_data.state == ConsciousnessState.ACTIVE
        assert state_data.timestamp == 123.45
        assert state_data.metadata == {"test": "metadata"}
        assert state_data.metrics == {"efficiency": 0.8}
        assert state_data.error_message == "Test error"

    def test_state_data_default_values(self):
        """Тест значений по умолчанию ConsciousnessStateData."""
        state_data = ConsciousnessStateData(
            state=ConsciousnessState.PROCESSING,
            timestamp=123.45,
            metadata={"test": "metadata"}
        )

        assert state_data.metrics is None
        assert state_data.error_message is None

    def test_to_dict_conversion(self):
        """Тест конвертации в словарь."""
        state_data = ConsciousnessStateData(
            state=ConsciousnessState.ANALYZING,
            timestamp=123.45,
            metadata={"test": "metadata"},
            metrics={"efficiency": 0.8},
            error_message="Test error"
        )

        result = state_data.to_dict()

        expected = {
            'state': 'analyzing',
            'timestamp': 123.45,
            'metadata': {"test": "metadata"},
            'metrics': {"efficiency": 0.8},
            'error_message': "Test error"
        }

        assert result == expected

    def test_to_dict_without_optional_fields(self):
        """Тест конвертации в словарь без опциональных полей."""
        state_data = ConsciousnessStateData(
            state=ConsciousnessState.ACTIVE,
            timestamp=123.45,
            metadata={"test": "metadata"}
        )

        result = state_data.to_dict()

        expected = {
            'state': 'active',
            'timestamp': 123.45,
            'metadata': {"test": "metadata"}
        }

        assert result == expected
        assert 'metrics' not in result
        assert 'error_message' not in result

    def test_from_dict_conversion(self):
        """Тест создания из словаря."""
        data = {
            'state': 'processing',
            'timestamp': 123.45,
            'metadata': {"test": "metadata"},
            'metrics': {"efficiency": 0.8},
            'error_message': "Test error"
        }

        state_data = ConsciousnessStateData.from_dict(data)

        assert state_data.state == ConsciousnessState.PROCESSING
        assert state_data.timestamp == 123.45
        assert state_data.metadata == {"test": "metadata"}
        assert state_data.metrics == {"efficiency": 0.8}
        assert state_data.error_message == "Test error"

    def test_from_dict_without_optional_fields(self):
        """Тест создания из словаря без опциональных полей."""
        data = {
            'state': 'reflecting',
            'timestamp': 123.45,
            'metadata': {"test": "metadata"}
        }

        state_data = ConsciousnessStateData.from_dict(data)

        assert state_data.state == ConsciousnessState.REFLECTING
        assert state_data.timestamp == 123.45
        assert state_data.metadata == {"test": "metadata"}
        assert state_data.metrics is None
        assert state_data.error_message is None

    def test_from_dict_invalid_state(self):
        """Тест создания из словаря с некорректным состоянием."""
        data = {
            'state': 'invalid_state',
            'timestamp': 123.45,
            'metadata': {}
        }

        with pytest.raises(ValueError, match="Unknown consciousness state"):
            ConsciousnessStateData.from_dict(data)


class TestConsciousnessStateManager:
    """Тесты для ConsciousnessStateManager."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.manager = ConsciousnessStateManager()

    def test_initialization(self):
        """Тест инициализации менеджера."""
        assert self.manager.current_state == ConsciousnessState.INACTIVE
        assert len(self.manager.state_history) == 0
        assert len(self.manager.transition_handlers) == 0

    def test_transition_to_valid_transition(self):
        """Тест валидного перехода состояния."""
        # INACTIVE -> INITIALIZING
        result = self.manager.transition_to(ConsciousnessState.INITIALIZING)
        assert result is True
        assert self.manager.current_state == ConsciousnessState.INITIALIZING
        assert len(self.manager.state_history) == 1

        state_data = self.manager.state_history[0]
        assert state_data.state == ConsciousnessState.INITIALIZING
        assert isinstance(state_data.timestamp, float)
        assert state_data.metadata == {}

    def test_transition_to_with_metadata_and_metrics(self):
        """Тест перехода с метаданными и метриками."""
        metadata = {"reason": "startup", "component": "system"}
        metrics = {"efficiency": 0.9, "stability": 0.8}

        result = self.manager.transition_to(
            ConsciousnessState.INITIALIZING,  # Начинаем с допустимого перехода
            metadata=metadata,
            metrics=metrics
        )

        assert result is True
        assert self.manager.current_state == ConsciousnessState.INITIALIZING

        state_data = self.manager.state_history[0]
        assert state_data.metadata == metadata
        assert state_data.metrics == metrics

    def test_transition_to_with_error_message(self):
        """Тест перехода с сообщением об ошибке."""
        error_msg = "System initialization failed"

        # Сначала перейдем в состояние, из которого можно перейти в ERROR
        self.manager.transition_to(ConsciousnessState.INITIALIZING)

        result = self.manager.transition_to(
            ConsciousnessState.ERROR,
            error_message=error_msg
        )

        assert result is True
        assert self.manager.current_state == ConsciousnessState.ERROR

        # Проверим последнее состояние в истории
        state_data = self.manager.state_history[-1]
        assert state_data.error_message == error_msg

    def test_transition_to_invalid_transition(self):
        """Тест некорректного перехода состояния."""
        # INACTIVE -> ACTIVE (недопустимый переход)
        result = self.manager.transition_to(ConsciousnessState.ACTIVE)
        assert result is False
        assert self.manager.current_state == ConsciousnessState.INACTIVE
        assert len(self.manager.state_history) == 0

    def test_multiple_transitions(self):
        """Тест множественных переходов."""
        # INACTIVE -> INITIALIZING -> ACTIVE -> PROCESSING
        transitions = [
            ConsciousnessState.INITIALIZING,
            ConsciousnessState.ACTIVE,
            ConsciousnessState.PROCESSING
        ]

        for state in transitions:
            result = self.manager.transition_to(state)
            assert result is True

        assert self.manager.current_state == ConsciousnessState.PROCESSING
        assert len(self.manager.state_history) == 3

        # Проверка последовательности
        assert self.manager.state_history[0].state == ConsciousnessState.INITIALIZING
        assert self.manager.state_history[1].state == ConsciousnessState.ACTIVE
        assert self.manager.state_history[2].state == ConsciousnessState.PROCESSING

    def test_transition_with_handler(self):
        """Тест перехода с обработчиком."""
        handler_called = False
        handler_params = None

        def test_handler(from_state, to_state):
            nonlocal handler_called, handler_params
            handler_called = True
            handler_params = (from_state, to_state)

        # Добавление обработчика
        self.manager.add_transition_handler(
            ConsciousnessState.INACTIVE,
            ConsciousnessState.INITIALIZING,
            test_handler
        )

        # Выполнение перехода
        result = self.manager.transition_to(ConsciousnessState.INITIALIZING)

        assert result is True
        assert handler_called is True
        assert handler_params == (ConsciousnessState.INACTIVE, ConsciousnessState.INITIALIZING)

    def test_transition_handler_exception_handling(self):
        """Тест обработки исключений в обработчике переходов."""
        def failing_handler(from_state, to_state):
            raise Exception("Handler failed")

        # Добавление проблемного обработчика
        self.manager.add_transition_handler(
            ConsciousnessState.INACTIVE,
            ConsciousnessState.INITIALIZING,
            failing_handler
        )

        # Переход должен выполниться несмотря на исключение в обработчике
        result = self.manager.transition_to(ConsciousnessState.INITIALIZING)

        assert result is True
        assert self.manager.current_state == ConsciousnessState.INITIALIZING

    def test_get_state_history_empty(self):
        """Тест получения пустой истории состояний."""
        history = self.manager.get_state_history()
        assert history == []

    def test_get_state_history_full(self):
        """Тест получения полной истории состояний."""
        # Создание истории переходов
        states = [ConsciousnessState.INITIALIZING, ConsciousnessState.ACTIVE, ConsciousnessState.PROCESSING]
        for state in states:
            self.manager.transition_to(state)

        history = self.manager.get_state_history()

        assert len(history) == 3
        assert all(isinstance(item, ConsciousnessStateData) for item in history)
        assert [item.state for item in history] == states

    def test_get_state_history_limited(self):
        """Тест получения ограниченной истории состояний."""
        # Создание истории переходов
        states = [ConsciousnessState.INITIALIZING, ConsciousnessState.ACTIVE,
                 ConsciousnessState.PROCESSING, ConsciousnessState.ANALYZING]
        for state in states:
            self.manager.transition_to(state)

        history = self.manager.get_state_history(limit=2)

        assert len(history) == 2
        assert [item.state for item in history] == [ConsciousnessState.PROCESSING, ConsciousnessState.ANALYZING]

    def test_get_current_state_info_inactive(self):
        """Тест получения информации о текущем состоянии (неактивном)."""
        info = self.manager.get_current_state_info()

        expected = {
            'current_state': 'inactive',
            'state_since': None,
            'total_transitions': 0,
            'latest_metadata': {}
        }

        assert info == expected

    def test_get_current_state_info_after_transitions(self):
        """Тест получения информации о текущем состоянии после переходов."""
        # Выполнение переходов
        self.manager.transition_to(ConsciousnessState.INITIALIZING)
        time.sleep(0.001)  # Небольшая задержка для изменения времени
        self.manager.transition_to(ConsciousnessState.ACTIVE, metadata={"test": "metadata"})

        info = self.manager.get_current_state_info()

        assert info['current_state'] == 'active'
        assert isinstance(info['state_since'], float)
        assert info['total_transitions'] == 2
        assert info['latest_metadata'] == {"test": "metadata"}

    def test_state_machine_valid_transitions(self):
        """Тест валидности переходов в конечном автомате."""
        # Тест всех допустимых переходов
        valid_transitions = {
            ConsciousnessState.INACTIVE: [ConsciousnessState.INITIALIZING],
            ConsciousnessState.INITIALIZING: [ConsciousnessState.ACTIVE, ConsciousnessState.ERROR],
            ConsciousnessState.ACTIVE: [ConsciousnessState.PROCESSING, ConsciousnessState.ERROR, ConsciousnessState.SHUTDOWN],
            ConsciousnessState.PROCESSING: [ConsciousnessState.ACTIVE, ConsciousnessState.ANALYZING, ConsciousnessState.ERROR],
            ConsciousnessState.ANALYZING: [ConsciousnessState.ACTIVE, ConsciousnessState.REFLECTING, ConsciousnessState.ERROR],
            ConsciousnessState.REFLECTING: [ConsciousnessState.ACTIVE, ConsciousnessState.ERROR],
            ConsciousnessState.ERROR: [ConsciousnessState.INACTIVE, ConsciousnessState.INITIALIZING],
            ConsciousnessState.SHUTDOWN: [ConsciousnessState.INACTIVE]
        }

        for from_state, to_states in valid_transitions.items():
            for to_state in to_states:
                # Сброс состояния
                self.manager = ConsciousnessStateManager()
                self.manager.current_state = from_state

                # Проверка валидности перехода
                assert self.manager.transition_to(to_state) is True
                assert self.manager.current_state == to_state

    def test_state_machine_invalid_transitions(self):
        """Тест недопустимых переходов в конечном автомате."""
        # Тест некоторых недопустимых переходов
        invalid_transitions = [
            (ConsciousnessState.INACTIVE, ConsciousnessState.ACTIVE),
            (ConsciousnessState.INACTIVE, ConsciousnessState.PROCESSING),
            (ConsciousnessState.ACTIVE, ConsciousnessState.INITIALIZING),
            (ConsciousnessState.PROCESSING, ConsciousnessState.INITIALIZING),
            (ConsciousnessState.SHUTDOWN, ConsciousnessState.ACTIVE),
        ]

        for from_state, to_state in invalid_transitions:
            # Сброс состояния
            self.manager = ConsciousnessStateManager()
            self.manager.current_state = from_state

            # Проверка недопустимости перехода
            assert self.manager.transition_to(to_state) is False
            assert self.manager.current_state == from_state

    def test_add_transition_handler_validation(self):
        """Тест валидации добавления обработчиков переходов."""
        def dummy_handler(from_state, to_state):
            pass

        # Добавление обработчика
        self.manager.add_transition_handler(
            ConsciousnessState.ACTIVE,
            ConsciousnessState.PROCESSING,
            dummy_handler
        )

        # Проверка добавления
        key = (ConsciousnessState.ACTIVE, ConsciousnessState.PROCESSING)
        assert key in self.manager.transition_handlers
        assert self.manager.transition_handlers[key] == dummy_handler

    def test_timestamp_ordering(self):
        """Тест упорядоченности временных меток."""
        # Выполнение переходов с задержками
        self.manager.transition_to(ConsciousnessState.INITIALIZING)
        time.sleep(0.001)
        self.manager.transition_to(ConsciousnessState.ACTIVE)
        time.sleep(0.001)
        self.manager.transition_to(ConsciousnessState.PROCESSING)

        timestamps = [item.timestamp for item in self.manager.state_history]

        # Проверка возрастания временных меток
        assert timestamps[0] < timestamps[1] < timestamps[2]

        # Проверка что все временные метки в прошлом
        current_time = time.time()
        assert all(ts <= current_time for ts in timestamps)

    def test_metadata_preservation(self):
        """Тест сохранения метаданных."""
        test_metadata = {
            "component": "consciousness_manager",
            "version": "1.0",
            "configuration": {"debug": True}
        }

        self.manager.transition_to(
            ConsciousnessState.INITIALIZING,
            metadata=test_metadata
        )

        stored_metadata = self.manager.state_history[0].metadata
        assert stored_metadata == test_metadata
        assert stored_metadata is not test_metadata  # Проверка что это копия

    def test_metrics_storage(self):
        """Тест хранения метрик."""
        test_metrics = {
            "processing_efficiency": 0.85,
            "memory_usage": 0.72,
            "stability_score": 0.91
        }

        self.manager.transition_to(
            ConsciousnessState.INITIALIZING,  # Допустимый переход
            metrics=test_metrics
        )

        stored_metrics = self.manager.state_history[0].metrics
        assert stored_metrics == test_metrics

    def test_error_message_storage(self):
        """Тест хранения сообщений об ошибках."""
        error_msg = "Critical system failure: memory overflow"

        # Сначала перейдем в состояние, из которого можно перейти в ERROR
        self.manager.transition_to(ConsciousnessState.INITIALIZING)

        self.manager.transition_to(
            ConsciousnessState.ERROR,
            error_message=error_msg
        )

        stored_error = self.manager.state_history[-1].error_message
        assert stored_error == error_msg

    def test_state_history_independence(self):
        """Тест независимости истории состояний."""
        # Создание переходов
        self.manager.transition_to(ConsciousnessState.INITIALIZING)
        self.manager.transition_to(ConsciousnessState.ACTIVE)

        # Получение истории
        history1 = self.manager.get_state_history()

        # Добавление еще одного перехода
        self.manager.transition_to(ConsciousnessState.PROCESSING)

        # Получение истории снова
        history2 = self.manager.get_state_history()

        # Проверка что первая история не изменилась
        assert len(history1) == 2
        assert len(history2) == 3

        # Проверка что это разные объекты
        assert history1 is not history2

    def test_empty_metadata_defaults(self):
        """Тест значений по умолчанию для пустых метаданных."""
        self.manager.transition_to(ConsciousnessState.INITIALIZING)

        state_data = self.manager.state_history[0]
        assert state_data.metadata == {}
        assert state_data.metrics is None
        assert state_data.error_message is None

    def test_state_persistence_across_calls(self):
        """Тест сохранения состояния между вызовами."""
        # Первый переход
        self.manager.transition_to(ConsciousnessState.INITIALIZING)
        assert self.manager.current_state == ConsciousnessState.INITIALIZING

        # Второй переход
        self.manager.transition_to(ConsciousnessState.ACTIVE)
        assert self.manager.current_state == ConsciousnessState.ACTIVE

        # Проверка что предыдущее состояние сохранилось в истории
        assert len(self.manager.state_history) == 2
        assert self.manager.state_history[0].state == ConsciousnessState.INITIALIZING
        assert self.manager.state_history[1].state == ConsciousnessState.ACTIVE

    def test_handler_storage_limitations(self):
        """Тест ограничений хранения обработчиков."""
        # Добавление множества обработчиков
        handlers = {}
        for i in range(10):
            def make_handler(i=i):
                def handler(from_state, to_state):
                    pass
                return handler

            from_state = ConsciousnessState(list(ConsciousnessState)[i % len(ConsciousnessState)])
            to_state = ConsciousnessState(list(ConsciousnessState)[(i + 1) % len(ConsciousnessState)])

            handler = make_handler()
            self.manager.add_transition_handler(from_state, to_state, handler)
            handlers[(from_state, to_state)] = handler

        # Проверка что все обработчики сохранены
        for key, handler in handlers.items():
            assert key in self.manager.transition_handlers
            assert self.manager.transition_handlers[key] == handler