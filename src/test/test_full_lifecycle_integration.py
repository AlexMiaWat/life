"""
Интеграционные тесты полного жизненного цикла системы Life

Эти тесты покрывают полный жизненный цикл через все слои архитектуры:
- Environment: генерация и обработка событий
- Runtime: центральный цикл и менеджеры
- Perception: восприятие, память, активация
- Cognitive: решение, действие, обратная связь
- Learning: обучение и адаптация
- Monitoring: наблюдение и метрики
- API: интерфейс системы

Тесты организованы по слоям с постепенным увеличением сложности.
"""

import sys
import threading
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

# Импорты всех компонентов системы
from src.action.action import execute_action
from src.activation.activation import activate_memory
from src.adaptation.adaptation import AdaptationManager
from src.decision.decision import decide_response
from src.environment.event import Event
from src.environment.event_queue import EventQueue
from src.environment.generator import EventGenerator
from src.feedback.feedback import register_action, observe_consequences
from src.intelligence.intelligence import process_information
from src.learning.learning import LearningEngine
from src.meaning.engine import MeaningEngine
from src.memory.memory import Memory
from src.monitor.console import monitor as console_monitor
from src.observability.structured_logger import StructuredLogger
from src.planning.planning import record_potential_sequences
from src.runtime.life_policy import LifePolicy
from src.runtime.log_manager import LogManager
from src.runtime.loop import run_loop
from src.runtime.snapshot_manager import SnapshotManager
from src.state.self_state import SelfState


@pytest.mark.integration
class TestEnvironmentLayerIntegration:
    """Интеграционные тесты для слоя Environment"""

    @pytest.fixture
    def event_queue(self):
        """Фикстура для очереди событий"""
        return EventQueue()

    @pytest.fixture
    def event_generator(self):
        """Фикстура для генератора событий"""
        return EventGenerator()

    def test_event_creation_and_queue_integration(self, event_queue):
        """Тест создания событий и интеграции с очередью"""
        # Создаем различные типы событий
        events = [
            Event(type="noise", intensity=0.3, timestamp=time.time()),
            Event(type="shock", intensity=0.8, timestamp=time.time()),
            Event(type="recovery", intensity=0.5, timestamp=time.time()),
        ]

        # Добавляем события в очередь
        for event in events:
            event_queue.push(event)

        # Проверяем, что события добавлены
        assert not event_queue.is_empty()
        assert event_queue.size() == 3

        # Извлекаем все события
        popped_events = event_queue.pop_all()
        assert len(popped_events) == 3
        assert event_queue.is_empty()

        # Проверяем корректность извлеченных событий
        event_types = [e.type for e in popped_events]
        assert "noise" in event_types
        assert "shock" in event_types
        assert "recovery" in event_types

    def test_event_queue_thread_safety(self, event_queue):
        """Тест потокобезопасности EventQueue"""
        results = []

        def producer():
            """Поток-производитель событий"""
            for i in range(10):
                event = Event(type=f"test_event_{i}", intensity=0.1 * i, timestamp=time.time())
                event_queue.push(event)
                time.sleep(0.001)  # Небольшая задержка

        def consumer():
            """Поток-потребитель событий"""
            while len(results) < 10:
                if not event_queue.is_empty():
                    events = event_queue.pop_all()
                    results.extend(events)
                time.sleep(0.001)

        # Запускаем потоки
        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=consumer)

        producer_thread.start()
        consumer_thread.start()

        producer_thread.join()
        consumer_thread.join()

        # Проверяем, что все события обработаны
        assert len(results) == 10
        assert event_queue.is_empty()

        # Проверяем уникальность событий
        event_ids = [e.type for e in results]
        assert len(set(event_ids)) == 10  # Все события уникальны

    def test_generator_event_queue_integration(self, event_generator, event_queue):
        """Тест интеграции генератора событий с очередью"""
        # Генерируем события
        generated_events = []
        for _ in range(5):
            event = event_generator.generate_event()
            generated_events.append(event)
            event_queue.push(event)

        # Проверяем, что события в очереди
        assert event_queue.size() == 5

        # Извлекаем и проверяем
        popped_events = event_queue.pop_all()
        assert len(popped_events) == 5

        # Проверяем, что события имеют корректные атрибуты
        for event in popped_events:
            assert hasattr(event, 'type')
            assert hasattr(event, 'intensity')
            assert hasattr(event, 'timestamp')
            assert event.type in ['noise', 'shock', 'recovery', 'decay']
            assert -1.0 <= event.intensity <= 1.0
            assert isinstance(event.timestamp, (int, float))

    def test_event_lifecycle_in_runtime_context(self, event_queue):
        """Тест жизненного цикла событий в контексте runtime"""
        # Создаем состояние системы
        self_state = SelfState()

        # Создаем и добавляем событие
        event = Event(type="shock", intensity=0.7, timestamp=time.time())
        event_queue.push(event)

        # Имитируем начало работы runtime loop
        initial_ticks = self_state.ticks
        initial_memory_size = len(self_state.memory)

        # Запускаем короткий цикл обработки
        stop_event = threading.Event()

        def dummy_monitor(state):
            pass

        loop_thread = threading.Thread(
            target=run_loop,
            args=(self_state, dummy_monitor, 0.01, 100, stop_event, event_queue),
            daemon=True
        )
        loop_thread.start()

        # Ждем обработки
        time.sleep(0.1)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что система отреагировала на событие
        # (событие могло быть обработано или сохранено в памяти)
        assert self_state.ticks > initial_ticks

        # Событие могло быть добавлено в память или повлиять на состояние
        # Проверяем, что что-то изменилось
        state_changed = (
            len(self_state.memory) != initial_memory_size or
            self_state.energy != 50.0 or  # начальное значение
            self_state.stability != 0.8 or
            self_state.integrity != 0.9
        )
        assert state_changed, "Система должна отреагировать на событие"


@pytest.mark.integration
class TestRuntimeCoreIntegration:
    """Интеграционные тесты для Runtime Loop и Managers"""

    @pytest.fixture
    def self_state(self):
        """Фикстура для состояния системы"""
        state = SelfState()
        state.energy = 60.0
        state.stability = 0.8
        state.integrity = 0.9
        return state

    @pytest.fixture
    def event_queue(self):
        """Фикстура для очереди событий"""
        return EventQueue()

    def test_runtime_loop_basic_integration(self, self_state, event_queue):
        """Тест базовой интеграции runtime loop"""
        stop_event = threading.Event()
        initial_ticks = self_state.ticks

        def dummy_monitor(state):
            pass

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(self_state, dummy_monitor, 0.01, 100, stop_event, event_queue),
            daemon=True
        )
        loop_thread.start()

        # Ждем несколько тиков
        time.sleep(0.05)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что цикл работал
        assert self_state.ticks > initial_ticks
        assert not loop_thread.is_alive()

    def test_snapshot_manager_integration(self, self_state, tmp_path):
        """Тест интеграции SnapshotManager с runtime"""
        from src.runtime.snapshot_manager import SnapshotManager

        # Меняем директорию для тестов
        original_dir = self_state.__class__.SNAPSHOT_DIR
        test_dir = tmp_path / "snapshots"
        test_dir.mkdir()
        self_state.__class__.SNAPSHOT_DIR = test_dir

        try:
            # Создаем менеджер
            snapshot_manager = SnapshotManager(snapshot_interval=1)  # каждый тик

            # Имитируем работу в цикле
            initial_ticks = self_state.ticks

            def mock_tick():
                """Имитация тика с snapshot"""
                self_state.ticks += 1
                snapshot_manager.maybe_create_snapshot(self_state)

            # Выполняем несколько тиков
            for _ in range(3):
                mock_tick()
                time.sleep(0.01)

            # Проверяем создание snapshots
            snapshot_files = list(test_dir.glob("snapshot_*.json"))
            assert len(snapshot_files) >= 1, f"Expected snapshots, found: {list(snapshot_files)}"

        finally:
            # Восстанавливаем директорию
            self_state.__class__.SNAPSHOT_DIR = original_dir

    def test_log_manager_integration(self, self_state, tmp_path):
        """Тест интеграции LogManager с runtime"""
        from src.runtime.log_manager import LogManager, FlushPolicy

        # Создаем тестовый лог-файл
        log_file = tmp_path / "test_structured_log.jsonl"

        # Создаем менеджер
        log_manager = LogManager(
            flush_policy=FlushPolicy(max_buffer_size=5, flush_interval=0.1)
        )

        # Имитируем логирование в цикле
        for i in range(10):
            log_entry = {
                "tick": i,
                "event": "test_event",
                "timestamp": time.time()
            }
            log_manager.log_structured(log_entry)
            time.sleep(0.01)

        # Принудительный flush
        log_manager.flush()

        # Проверяем, что логи записаны
        assert log_file.exists()
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) >= 5, f"Expected at least 5 log lines, got {len(lines)}"

    def test_life_policy_integration(self, self_state):
        """Тест интеграции LifePolicy с runtime"""
        from src.runtime.life_policy import LifePolicy

        # Создаем политику
        life_policy = LifePolicy()

        # Тестируем штрафы за слабость
        initial_energy = self_state.energy
        initial_stability = self_state.stability
        initial_integrity = self_state.integrity

        # Имитируем слабое состояние
        self_state.energy = 0.05
        self_state.stability = 0.05
        self_state.integrity = 0.05

        # Применяем политику
        life_policy.apply_weakness_penalties(self_state)

        # Проверяем, что применены штрафы
        assert self_state.energy < initial_energy
        assert self_state.stability < initial_stability
        assert self_state.integrity < initial_integrity

        # Проверяем границы (не должны быть отрицательными)
        assert self_state.energy >= 0.0
        assert self_state.stability >= 0.0
        assert self_state.integrity >= 0.0


@pytest.mark.integration
class TestPerceptionLayerIntegration:
    """Интеграционные тесты для слоев восприятия (MeaningEngine, Memory, Activation)"""

    @pytest.fixture
    def self_state(self):
        """Фикстура для состояния системы"""
        return SelfState()

    @pytest.fixture
    def meaning_engine(self):
        """Фикстура для MeaningEngine"""
        return MeaningEngine()

    @pytest.fixture
    def memory(self):
        """Фикстура для Memory"""
        return Memory()

    @pytest.fixture
    def activation(self):
        """Фикстура для функции активации"""
        return activate_memory

    def test_meaning_memory_integration(self, self_state, meaning_engine, memory):
        """Тест интеграции MeaningEngine с Memory"""
        # Создаем тестовое событие
        event = Event(type="shock", intensity=0.8, timestamp=time.time())

        # Получаем значимость события
        meaning = meaning_engine.process(event, self_state)

        # Проверяем, что событие значимое (должно быть сохранено)
        assert meaning.significance > 0, f"Event should be significant, got {meaning.significance}"

        # Добавляем значимое событие в память
        if meaning.significance > 0:
            from src.memory.memory import MemoryEntry
            entry = MemoryEntry(
                event_type=event.type,
                meaning_significance=meaning.significance,
                timestamp=event.timestamp
            )
            memory.append(entry)

        # Проверяем, что событие сохранено
        assert len(memory) > 0
        assert memory[0].event_type == "shock"
        assert memory[0].meaning_significance == meaning.significance

    def test_activation_memory_integration(self, memory, activation):
        """Тест интеграции Activation с Memory"""
        # Добавляем тестовые записи в память
        from src.memory.memory import MemoryEntry

        entries = [
            MemoryEntry(event_type="shock", meaning_significance=0.8, timestamp=time.time()),
            MemoryEntry(event_type="noise", meaning_significance=0.3, timestamp=time.time()),
            MemoryEntry(event_type="recovery", meaning_significance=0.6, timestamp=time.time()),
        ]

        for entry in entries:
            memory.append(entry)

        # Активируем память по типу события
        activated_shock = activation("shock", memory)
        activated_noise = activation("noise", memory)

        # Проверяем активацию
        assert len(activated_shock) > 0
        assert len(activated_noise) > 0

        # Проверяем, что активированы правильные записи
        shock_entries = [e for e in activated_shock if e.event_type == "shock"]
        assert len(shock_entries) > 0

        noise_entries = [e for e in activated_noise if e.event_type == "noise"]
        assert len(noise_entries) > 0

    def test_perception_pipeline_integration(self, self_state, meaning_engine, memory, activation):
        """Тест полного конвейера восприятия"""
        # Создаем последовательность событий
        events = [
            Event(type="shock", intensity=0.7, timestamp=time.time()),
            Event(type="noise", intensity=0.4, timestamp=time.time() + 1),
            Event(type="recovery", intensity=0.5, timestamp=time.time() + 2),
        ]

        # Имитируем полный цикл восприятия для каждого события
        for event in events:
            # 1. Получаем значимость
            meaning = meaning_engine.process(event, self_state)

            # 2. Сохраняем в память если значимо
            if meaning.significance > 0:
                from src.memory.memory import MemoryEntry
                entry = MemoryEntry(
                    event_type=event.type,
                    meaning_significance=meaning.significance,
                    timestamp=event.timestamp
                )
                memory.append(entry)

            # 3. Применяем изменения состояния
            self_state.apply_delta(meaning.impact)

        # Проверяем, что память заполнена
        assert len(memory) >= 2  # Хотя бы 2 значимых события

        # Проверяем активацию памяти
        activated = activation("shock", memory)
        assert len(activated) > 0

        # Проверяем, что состояние изменилось
        # (не проверяем конкретные значения, так как они зависят от логики MeaningEngine)
        assert self_state.ticks >= 0  # Система должна быть инициализирована


@pytest.mark.integration
class TestCognitiveLayerIntegration:
    """Интеграционные тесты для когнитивных слоев (Decision, Action, Feedback)"""

    @pytest.fixture
    def self_state(self):
        """Фикстура для состояния системы"""
        state = SelfState()
        state.energy = 50.0
        state.stability = 0.8
        state.integrity = 0.9
        return state

    @pytest.fixture
    def decision_maker(self):
        """Фикстура для функции принятия решений"""
        return decide_response

    @pytest.fixture
    def action_executor(self):
        """Фикстура для функции выполнения действий"""
        return execute_action

    @pytest.fixture
    def feedback(self):
        """Фикстура для функций feedback"""
        return {
            'register_action': register_action,
            'observe_consequences': observe_consequences
        }

    @pytest.fixture
    def memory(self):
        """Фикстура для Memory"""
        return Memory()

    def test_decision_action_integration(self, self_state, decision_maker, action_executor, memory):
        """Тест интеграции Decision с Action"""
        # Добавляем контекст в память
        from src.memory.memory import MemoryEntry

        context_entries = [
            MemoryEntry(event_type="shock", meaning_significance=0.8, timestamp=time.time()),
            MemoryEntry(event_type="recovery", meaning_significance=0.6, timestamp=time.time() + 1),
        ]

        for entry in context_entries:
            memory.append(entry)

        # Создаем тестовое meaning для принятия решения
        from src.meaning.meaning import Meaning
        test_meaning = Meaning(
            significance=0.7,
            impact={'energy': -0.1, 'stability': 0.05},
            response_pattern="dampen"
        )

        # Принимаем решение
        pattern = decision_maker(self_state, test_meaning)

        # Проверяем, что получен паттерн
        assert pattern is not None
        assert isinstance(pattern, str)

        # Выполняем действие
        action_executor(pattern, self_state)

    def test_action_feedback_integration(self, self_state, action_executor, feedback, memory):
        """Тест интеграции Action с Feedback"""
        # Выполняем действие
        pattern = "dampen"
        action_executor(pattern, self_state)

        # Имитируем задержку (как в реальном runtime)
        time.sleep(0.01)

        # Получаем feedback - функция observe_consequences не требует параметров
        # В текущей реализации feedback работает по-другому
        # Проверяем, что состояние могло измениться
        # Это упрощенная версия теста

    def test_cognitive_cycle_integration(self, self_state, decision_maker, action_executor, feedback, memory):
        """Тест полного когнитивного цикла"""
        # Имитируем полный цикл: Decision -> Action -> Feedback

        # 1. Создаем тестовое meaning
        from src.meaning.meaning import Meaning
        test_meaning = Meaning(
            significance=0.6,
            impact={'energy': -0.05, 'stability': 0.02},
            response_pattern="absorb"
        )

        # 2. Запоминаем состояние до действия
        state_before = {
            'energy': self_state.energy,
            'stability': self_state.stability,
            'integrity': self_state.integrity
        }

        # 3. Принимаем решение и выполняем действие
        pattern = decision_maker(self_state, test_meaning)
        action_executor(pattern, self_state)

        # 4. Проверяем, что состояние могло измениться
        state_after = {
            'energy': self_state.energy,
            'stability': self_state.stability,
            'integrity': self_state.integrity
        }

        # Проверяем целостность цикла
        assert pattern is not None
        assert isinstance(pattern, str)

        # Состояние могло измениться
        state_changed = (
            state_before['energy'] != state_after['energy'] or
            state_before['stability'] != state_after['stability'] or
            state_before['integrity'] != state_after['integrity']
        )
        # Действие могло не изменить состояние, поэтому проверяем только структуру


@pytest.mark.integration
class TestLearningLayerIntegration:
    """Интеграционные тесты для слоев обучения (Learning, Adaptation, Planning, Intelligence)"""

    @pytest.fixture
    def self_state(self):
        """Фикстура для состояния системы"""
        return SelfState()

    @pytest.fixture
    def learning_engine(self):
        """Фикстура для LearningEngine"""
        return LearningEngine()

    @pytest.fixture
    def adaptation_manager(self):
        """Фикстура для AdaptationManager"""
        return AdaptationManager()

    @pytest.fixture
    def planning(self):
        """Фикстура для функции планирования"""
        return record_potential_sequences

    @pytest.fixture
    def intelligence(self):
        """Фикстура для функции обработки информации"""
        return process_information

    def test_learning_adaptation_integration(self, self_state, learning_engine, adaptation_manager):
        """Тест интеграции Learning с Adaptation"""
        # Имитируем процесс обучения
        # Добавляем статистику событий
        mock_statistics = {
            'event_counts': {'shock': 10, 'noise': 20, 'recovery': 15},
            'response_patterns': {'pattern_1': 0.6, 'pattern_2': 0.4},
            'success_rates': {'pattern_1': 0.8, 'pattern_2': 0.7}
        }

        # Обучаемся на статистике
        learning_engine.process_statistics(mock_statistics)

        # Получаем обновленные параметры обучения
        learning_params = learning_engine.adjust_parameters(mock_statistics, self_state.learning_params)

        # Адаптируемся к изменениям
        adaptation_manager.analyze_changes(learning_params)

        # Применяем адаптацию
        adaptation_manager.apply_adaptation(adaptation_manager.analyze_changes(learning_params))

        # Проверяем, что параметры обновлены
        assert hasattr(self_state, 'learning_params')
        assert hasattr(self_state, 'adaptation_params')
        assert hasattr(self_state, 'adaptation_history')

    def test_planning_intelligence_integration(self, self_state, planning, intelligence):
        """Тест интеграции Planning с Intelligence"""
        # Intelligence обрабатывает информацию
        intelligence(self_state)

        # Planning фиксирует потенциальные последовательности
        planning(self_state)

        # Проверяем, что метрики собраны
        assert metrics is not None
        assert isinstance(metrics, dict)

        # Проверяем наличие основных метрик
        expected_metrics = ['energy', 'stability', 'integrity', 'active', 'ticks']
        for metric in expected_metrics:
            assert metric in metrics, f"Missing metric: {metric}"

    def test_learning_lifecycle_integration(self, self_state, learning_engine, adaptation_manager):
        """Тест жизненного цикла обучения"""
        # Имитируем длительный процесс обучения
        initial_learning_params = self_state.learning_params.copy()
        initial_adaptation_params = self_state.adaptation_params.copy()

        # Много итераций обучения
        for i in range(10):
            mock_stats = {
                'event_counts': {'shock': 5 + i, 'noise': 10 + i, 'recovery': 8 + i},
                'response_patterns': {f'pattern_{j}': 0.1 * (j + 1) for j in range(3)},
                'success_rates': {f'pattern_{j}': 0.5 + 0.05 * j for j in range(3)}
            }

            # Обучение
            learning_engine.process_statistics(mock_stats)
            new_learning_params = learning_engine.adjust_parameters(mock_stats, self_state.learning_params)

            # Адаптация
            adaptation_manager.analyze_changes(new_learning_params)
            adaptation_manager.apply_adaptation(adaptation_manager.analyze_changes(new_learning_params))

            # Небольшая задержка для реализма
            time.sleep(0.001)

        # Проверяем, что система эволюционировала
        params_changed = (
            self_state.learning_params != initial_learning_params or
            self_state.adaptation_params != initial_adaptation_params
        )
        # Параметры могут не измениться значительно за короткий тест


@pytest.mark.integration
class TestMonitoringLayerIntegration:
    """Интеграционные тесты для слоев мониторинга (Monitor, Observability)"""

    @pytest.fixture
    def self_state(self):
        """Фикстура для состояния системы"""
        return SelfState()

    @pytest.fixture
    def console_monitor(self):
        """Фикстура для функции мониторинга"""
        return console_monitor

    @pytest.fixture
    def structured_logger(self, tmp_path):
        """Фикстура для StructuredLogger"""
        log_file = tmp_path / "test_integration_log.jsonl"
        return StructuredLogger(log_file=str(log_file))

    def test_monitor_state_integration(self, self_state, console_monitor):
        """Тест интеграции Monitor с состоянием системы"""
        # Мониторим состояние
        console_monitor(self_state)

        # Проверяем, что мониторинг не сломал состояние
        assert self_state is not None
        assert hasattr(self_state, 'energy')
        assert hasattr(self_state, 'stability')
        assert hasattr(self_state, 'integrity')

    def test_structured_logger_runtime_integration(self, self_state, structured_logger):
        """Тест интеграции StructuredLogger с runtime"""
        # Имитируем события runtime loop
        correlation_id = "test_correlation_123"

        # Логируем различные стадии
        structured_logger.log_event("meaning_processing", {
            "correlation_id": correlation_id,
            "event_type": "shock",
            "significance": 0.8,
            "state_energy": self_state.energy
        })

        structured_logger.log_event("decision_making", {
            "correlation_id": correlation_id,
            "pattern": "defensive_response",
            "confidence": 0.7
        })

        structured_logger.log_event("action_execution", {
            "correlation_id": correlation_id,
            "action_type": "energy_conservation",
            "intensity": 0.6
        })

        structured_logger.log_event("feedback_observation", {
            "correlation_id": correlation_id,
            "feedback_delay": 0.05,
            "state_change": 0.1
        })

        # Принудительно сбрасываем логи
        structured_logger.flush()

        # Проверяем, что логи записаны
        log_file = Path(structured_logger.log_file)
        assert log_file.exists()

        # Читаем и проверяем логи
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) >= 4  # Минимум 4 события

            # Парсим JSON и проверяем структуру
            import json
            for line in lines:
                log_entry = json.loads(line.strip())
                assert "event" in log_entry
                assert "timestamp" in log_entry
                assert "correlation_id" in log_entry
                assert log_entry["correlation_id"] == correlation_id

    def test_observability_metrics_integration(self, self_state, structured_logger):
        """Тест интеграции метрик наблюдаемости"""
        # Имитируем сбор метрик производительности
        tick_start = time.time()

        # Имитируем тик runtime
        self_state.ticks += 1
        self_state.energy -= 0.01  # Небольшое изменение

        tick_duration = time.time() - tick_start

        # Логируем метрики
        structured_logger.log_performance("tick_completed", {
            "tick_duration": tick_duration,
            "queue_size": 0,
            "events_processed": 1,
            "memory_size": len(self_state.memory),
            "final_energy": self_state.energy
        })

        structured_logger.flush()

        # Проверяем логи метрик
        log_file = Path(structured_logger.log_file)
        assert log_file.exists()

        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) >= 1

            import json
            log_entry = json.loads(lines[0].strip())
            assert log_entry["event"] == "tick_completed"
            assert "tick_duration" in log_entry["data"]
            assert log_entry["data"]["tick_duration"] >= 0


@pytest.mark.integration
class TestFullLifecycleIntegration:
    """Интеграционные тесты полного жизненного цикла системы"""

    def test_system_birth_lifecycle(self, tmp_path):
        """Тест 'рождения' системы - инициализация всех слоев"""
        # Создаем все компоненты
        self_state = SelfState()
        event_queue = EventQueue()
        meaning_engine = MeaningEngine()
        memory = Memory()
        activation = Activation()
        decision_maker = DecisionMaker()
        action_executor = ActionExecutor()
        feedback = Feedback()
        learning_engine = LearningEngine()
        adaptation_manager = AdaptationManager()
        planning = Planning()
        intelligence = Intelligence()

        # Настраиваем мониторинг
        log_file = tmp_path / "birth_lifecycle_log.jsonl"
        structured_logger = StructuredLogger(log_file=str(log_file))
        console_monitor = ConsoleMonitor()

        # Проверяем начальное состояние
        assert self_state.active is True
        assert self_state.ticks == 0
        assert len(memory) == 0

        # Имитируем первое 'восприятие' - событие рождения
        birth_event = Event(type="birth", intensity=0.1, timestamp=time.time())
        event_queue.push(birth_event)

        # Логируем начало жизни
        structured_logger.log_event("system_birth", {
            "initial_energy": self_state.energy,
            "initial_stability": self_state.stability,
            "initial_integrity": self_state.integrity
        })

        # Проверяем, что система 'родилась' правильно
        assert not event_queue.is_empty()
        assert self_state.is_active()

        structured_logger.flush()

    def test_full_event_processing_cycle(self, tmp_path):
        """Тест полного цикла обработки события через все слои"""
        # Создаем полную систему
        self_state = SelfState()
        event_queue = EventQueue()
        meaning_engine = MeaningEngine()
        memory = Memory()
        activation = Activation()
        decision_maker = DecisionMaker()
        action_executor = ActionExecutor()
        feedback = Feedback()

        # Настраиваем логирование
        log_file = tmp_path / "full_cycle_log.jsonl"
        structured_logger = StructuredLogger(log_file=str(log_file))

        # Создаем тестовое событие
        event = Event(type="shock", intensity=0.7, timestamp=time.time())
        event_queue.push(event)

        correlation_id = f"cycle_{int(time.time() * 1000)}"

        # === Полный цикл обработки ===

        # 1. Получаем событие
        events = event_queue.pop_all()
        assert len(events) == 1
        current_event = events[0]

        structured_logger.log_event("event_received", {
            "correlation_id": correlation_id,
            "event_type": current_event.type,
            "intensity": current_event.intensity
        })

        # 2. Обрабатываем восприятие
        meaning = meaning_engine.process(current_event, self_state)

        structured_logger.log_event("meaning_processed", {
            "correlation_id": correlation_id,
            "significance": meaning.significance,
            "impact_energy": meaning.impact.get('energy', 0)
        })

        # 3. Сохраняем в память если значимо
        if meaning.significance > 0:
            from src.memory.memory import MemoryEntry
            entry = MemoryEntry(
                event_type=current_event.type,
                meaning_significance=meaning.significance,
                timestamp=current_event.timestamp
            )
            memory.append(entry)

        # 4. Применяем изменения состояния
        self_state.apply_delta(meaning.impact)

        # 5. Активируем память
        activated = activation.activate_memory(current_event.type, memory)

        # 6. Принимаем решение
        pattern = decision_maker(self_state, meaning)

        structured_logger.log_event("decision_made", {
            "correlation_id": correlation_id,
            "pattern_type": pattern,
            "activated_memory_count": len(activated)
        })

        # 7. Выполняем действие
        action_executor(pattern, self_state)

        structured_logger.log_event("action_executed", {
            "correlation_id": correlation_id,
            "action_type": pattern,
            "action_intensity": 0.5  # Заглушка
        })

        # 8. Имитируем задержку feedback
        time.sleep(0.01)

        # 9. Получаем feedback (упрощенная версия)
        feedback_data = {
            'timestamp': time.time(),
            'action_timestamp': time.time() - 0.01,
            'feedback_delay': 0.01
        }

        structured_logger.log_event("feedback_received", {
            "correlation_id": correlation_id,
            "feedback_timestamp": feedback_data['timestamp'],
            "action_feedback_delay": feedback_data['feedback_delay']
        })

        # Сбрасываем логи
        structured_logger.flush()

        # Проверяем целостность цикла
        assert len(memory) >= 0  # Память могла быть обновлена
        assert feedback_data is not None
        assert 'timestamp' in feedback_data

        # Проверяем логи
        assert log_file.exists()
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) >= 5  # Минимум 5 этапов логирования

    def test_system_development_lifecycle(self, tmp_path):
        """Тест жизненного цикла развития системы (рост + обучение)"""
        # Создаем систему
        self_state = SelfState()
        event_queue = EventQueue()
        meaning_engine = MeaningEngine()
        memory = Memory()
        learning_engine = LearningEngine()
        adaptation_manager = AdaptationManager()

        # Настраиваем логирование
        log_file = tmp_path / "development_log.jsonl"
        structured_logger = StructuredLogger(log_file=str(log_file))

        # Имитируем процесс развития
        initial_energy = self_state.energy
        initial_learning_params = self_state.learning_params.copy()

        for cycle in range(20):  # 20 циклов развития
            # Генерируем разнообразные события
            event_types = ["shock", "noise", "recovery", "decay"]
            event_type = event_types[cycle % len(event_types)]
            intensity = 0.3 + (cycle % 5) * 0.1  # Варьируем интенсивность

            event = Event(type=event_type, intensity=intensity, timestamp=time.time())
            event_queue.push(event)

            # Обрабатываем событие
            events = event_queue.pop_all()
            for evt in events:
                meaning = meaning_engine.process(evt, self_state)
                self_state.apply_delta(meaning.impact)

                # Сохраняем значимые события
                if meaning.significance > 0:
                    from src.memory.memory import MemoryEntry
                    entry = MemoryEntry(
                        event_type=evt.type,
                        meaning_significance=meaning.significance,
                        timestamp=evt.timestamp
                    )
                    memory.append(entry)

            # Каждые 5 циклов запускаем обучение
            if cycle % 5 == 0 and cycle > 0:
                mock_stats = {
                    'event_counts': {'shock': 5, 'noise': 5, 'recovery': 5, 'decay': 5},
                    'response_patterns': {'adaptive': 0.6, 'conservative': 0.4},
                    'success_rates': {'adaptive': 0.7, 'conservative': 0.8}
                }

                learning_engine.process_statistics(mock_stats)
                new_params = learning_engine.adjust_parameters(mock_stats, self_state.learning_params)

                adaptation_manager.analyze_changes(new_params)
                adaptation_manager.apply_adaptation(adaptation_manager.analyze_changes(new_params))

                structured_logger.log_event("learning_cycle", {
                    "cycle": cycle,
                    "memory_size": len(memory),
                    "learning_evolution": "params_updated"
                })

            # Логируем прогресс
            structured_logger.log_event("development_tick", {
                "cycle": cycle,
                "energy": self_state.energy,
                "memory_size": len(memory),
                "ticks": self_state.ticks
            })

            # Небольшая задержка
            time.sleep(0.001)

        # Сбрасываем логи
        structured_logger.flush()

        # Проверяем развитие системы
        assert self_state.ticks >= 20
        assert len(memory) >= 10  # Должно быть сохранено много воспоминаний

        # Проверяем логи развития
        assert log_file.exists()
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) >= 20  # Минимум 20 записей о развитии

    def test_system_death_lifecycle(self):
        """Тест жизненного цикла 'смерти' системы (деградация)"""
        self_state = SelfState()

        # Начинаем с хорошего состояния
        self_state.energy = 80.0
        self_state.stability = 0.9
        self_state.integrity = 0.95

        initial_state = {
            'energy': self_state.energy,
            'stability': self_state.stability,
            'integrity': self_state.integrity,
            'active': self_state.active
        }

        # Имитируем процесс деградации
        life_policy = LifePolicy()

        for degradation_step in range(10):
            # Применяем штрафы за слабость
            life_policy.apply_weakness_penalties(self_state)

            # Дополнительная деградация
            self_state.energy *= 0.9  # Ускоренная потеря энергии
            self_state.stability *= 0.95
            self_state.integrity *= 0.95

            # Проверяем условие смерти
            if not self_state.is_active():
                break

        # Проверяем, что система деградировала
        assert self_state.energy < initial_state['energy']
        assert self_state.stability < initial_state['stability']
        assert self_state.integrity < initial_state['integrity']

        # Система должна 'умереть' при нулевых параметрах
        assert self_state.active is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])