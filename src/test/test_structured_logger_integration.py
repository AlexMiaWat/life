"""
Интеграционные тесты для StructuredLogger (новая функциональность наблюдаемости)

Проверяем:
- Взаимодействие StructuredLogger с runtime loop
- Полные циклы обработки событий с логированием
- Корреляцию событий в цепочках
- Работа в многопоточной среде runtime loop
- Сохранение и анализ логов
"""

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.environment.event import Event
from src.environment.event_queue import EventQueue
from src.observability.structured_logger import StructuredLogger
from src.runtime.loop import run_loop
from src.state.self_state import SelfState


@pytest.mark.integration
class TestStructuredLoggerIntegration:
    """Интеграционные тесты StructuredLogger"""

    # ============================================================================
    # Runtime Loop Integration
    # ============================================================================

    def test_structured_logger_full_chain_simulation(self):
        """Интеграционный тест StructuredLogger с runtime loop"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            log_file = f.name

        try:
            # Создаем StructuredLogger
            logger = StructuredLogger(log_file=log_file, enabled=True)

            # Создаем состояние и очередь
            self_state = SelfState()
            event_queue = EventQueue()
            stop_event = threading.Event()

            # Добавляем события в очередь
            events = [
                Event(type="noise", intensity=0.3, timestamp=1.0),
                Event(type="shock", intensity=-0.7, timestamp=2.0),
                Event(type="recovery", intensity=0.5, timestamp=3.0),
            ]

            for event in events:
                event_queue.push(event)

            # Модифицируем run_loop для использования StructuredLogger
            # (в реальном коде это должно быть интегрировано в runtime loop)

            def monitor_with_structured_logging(state):
                """Монитор, который логирует через StructuredLogger"""
                # Имитируем логирование стадий
                if hasattr(state, "_current_event") and state._current_event:
                    event = state._current_event
                    correlation_id = logger.log_event(event)

                    # Имитируем meaning processing
                    class MockMeaning:
                        def __init__(self):
                            self.significance = abs(event.intensity)
                            self.impact = {"energy": -event.intensity * 10}

                    meaning = MockMeaning()
                    logger.log_meaning(event, meaning, correlation_id)

                    # Имитируем decision
                    if event.intensity > 0.5:
                        pattern = "absorb"
                    elif event.intensity < -0.5:
                        pattern = "dampen"
                    else:
                        pattern = "ignore"

                    logger.log_decision(pattern, correlation_id)

                    # Имитируем action
                    action_id = f"action_{hash(correlation_id) % 1000}"
                    logger.log_action(action_id, pattern, correlation_id)

                    # Имитируем feedback
                    class MockFeedback:
                        def __init__(self, action_id):
                            self.action_id = action_id
                            self.delay_ticks = 1
                            self.state_delta = {"energy": -2.0}
                            self.associated_events = [getattr(event, "id", "unknown")]

                    feedback = MockFeedback(action_id)
                    logger.log_feedback(feedback, correlation_id)

            # Запускаем runtime loop на короткое время
            thread = threading.Thread(
                target=run_loop,
                args=(
                    self_state,
                    monitor_with_structured_logging,
                    0.01,
                    1000,
                    stop_event,
                    event_queue,
                ),
            )
            thread.start()

            # Ждем обработки событий
            time.sleep(0.3)
            stop_event.set()
            thread.join(timeout=1.0)

            # Проверяем логи
            assert os.path.exists(log_file)

            with open(log_file, "r") as f:
                content = f.read().strip()
                lines = [line for line in content.split("\n") if line.strip()]
                assert len(lines) >= 1  # Минимум по событию

                entries = [json.loads(line) for line in lines if line.strip()]

                # Группируем по correlation_id
                correlation_chains = {}
                for entry in entries:
                    corr_id = entry["correlation_id"]
                    if corr_id not in correlation_chains:
                        correlation_chains[corr_id] = []
                    correlation_chains[corr_id].append(entry)

                # Проверяем, что есть полные цепочки
                complete_chains = 0
                for chain in correlation_chains.values():
                    stages = [entry["stage"] for entry in chain]
                    if (
                        "event" in stages
                        and "meaning" in stages
                        and "decision" in stages
                    ):
                        complete_chains += 1

                assert complete_chains >= 1  # Хотя бы одна полная цепочка

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_structured_logger_correlation_tracking(self):
        """Тест отслеживания корреляции событий"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            log_file = f.name

        try:
            logger = StructuredLogger(log_file=log_file, enabled=True)

            # Создаем цепочку событий
            event1 = Event(type="noise", intensity=0.4, timestamp=1.0)
            corr1 = logger.log_event(event1)

            # Meaning для первого события
            class MockMeaning:
                def __init__(self):
                    self.significance = 0.6
                    self.impact = {"stability": -0.1}

            meaning1 = MockMeaning()
            logger.log_meaning(event1, meaning1, corr1)

            # Decision и Action
            logger.log_decision("absorb", corr1)
            logger.log_action("action_001", "absorb", corr1)

            # Feedback
            class MockFeedback:
                def __init__(self):
                    self.action_id = "action_001"
                    self.delay_ticks = 2
                    self.state_delta = {"energy": -5.0}

            feedback1 = MockFeedback()
            logger.log_feedback(feedback1, corr1)

            # Аналогично для второго события
            event2 = Event(type="shock", intensity=-0.8, timestamp=2.0)
            corr2 = logger.log_event(event2)

            meaning2 = MockMeaning()
            logger.log_meaning(event2, meaning2, corr2)
            logger.log_decision("dampen", corr2)
            logger.log_action("action_002", "dampen", corr2)

            feedback2 = MockFeedback()
            feedback2.action_id = "action_002"
            logger.log_feedback(feedback2, corr2)

            # Анализируем логи
            with open(log_file, "r") as f:
                entries = [json.loads(line) for line in f.read().strip().split("\n")]

            # Группируем по correlation_id
            chains = {}
            for entry in entries:
                corr_id = entry["correlation_id"]
                if corr_id not in chains:
                    chains[corr_id] = []
                chains[corr_id].append(entry)

            # Проверяем, что correlation_id разные
            assert len(chains) == 2
            assert corr1 in chains
            assert corr2 in chains

            # Проверяем полные цепочки для каждого correlation_id
            for corr_id, chain in chains.items():
                stages = [entry["stage"] for entry in chain]
                expected_stages = ["event", "meaning", "decision", "action", "feedback"]

                for stage in expected_stages:
                    assert (
                        stage in stages
                    ), f"Стадия {stage} отсутствует в цепочке {corr_id}"

                # Проверяем временную последовательность
                timestamps = [entry["timestamp"] for entry in chain]
                assert timestamps == sorted(
                    timestamps
                ), f"Нарушен порядок времени в цепочке {corr_id}"

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_structured_logger_performance_monitoring(self):
        """Тест мониторинга производительности с tick логированием"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            log_file = f.name

        try:
            logger = StructuredLogger(log_file=log_file, enabled=True)

            # Имитируем несколько тиков
            for tick in range(1, 4):
                # Начало тика
                queue_size = tick * 2  # Имитируем рост очереди
                logger.log_tick_start(tick, queue_size)

                # Имитируем обработку
                time.sleep(0.01)  # Маленькая задержка

                # Конец тика
                duration_ms = 10.5 + tick  # Имитируем время обработки
                events_processed = tick  # Имитируем количество обработанных событий
                logger.log_tick_end(tick, duration_ms, events_processed)

            # Проверяем логи производительности
            with open(log_file, "r") as f:
                entries = [json.loads(line) for line in f.read().strip().split("\n")]

            tick_starts = [e for e in entries if e["stage"] == "tick_start"]
            tick_ends = [e for e in entries if e["stage"] == "tick_end"]

            assert len(tick_starts) == 3
            assert len(tick_ends) == 3

            # Проверяем соответствие tick номеров
            start_ticks = sorted([e["tick_number"] for e in tick_starts])
            end_ticks = sorted([e["tick_number"] for e in tick_ends])

            assert start_ticks == end_ticks == [1, 2, 3]

            # Проверяем метрики
            for end_entry in tick_ends:
                assert "duration_ms" in end_entry
                assert "events_processed" in end_entry
                assert isinstance(end_entry["duration_ms"], (int, float))
                assert isinstance(end_entry["events_processed"], int)

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_structured_logger_error_handling(self):
        """Тест обработки ошибок в логировании"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            log_file = f.name

        try:
            logger = StructuredLogger(log_file=log_file, enabled=True)

            # Создаем нормальную цепочку
            event = Event(type="noise", intensity=0.5, timestamp=1.0)
            corr_id = logger.log_event(event)
            logger.log_meaning(
                event, type("Mock", (), {"significance": 0.5, "impact": {}})(), corr_id
            )

            # Имитируем ошибку на стадии decision
            try:
                raise ValueError("Decision processing failed")
            except ValueError as e:
                logger.log_error("decision", e, corr_id)

            # Продолжаем цепочку несмотря на ошибку
            logger.log_decision("ignore", corr_id)

            # Проверяем логи
            with open(log_file, "r") as f:
                entries = [json.loads(line) for line in f.read().strip().split("\n")]

            # Находим ошибку
            error_entries = [e for e in entries if e["stage"].startswith("error_")]
            assert len(error_entries) == 1

            error_entry = error_entries[0]
            assert error_entry["stage"] == "error_decision"
            assert error_entry["correlation_id"] == corr_id
            assert error_entry["error_type"] == "ValueError"
            assert "Decision processing failed" in error_entry["error_message"]

            # Проверяем, что цепочка продолжилась после ошибки
            decision_entries = [e for e in entries if e["stage"] == "decision"]
            assert len(decision_entries) == 1

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_structured_logger_multithreaded_integration(self):
        """Интеграционный тест многопоточной работы StructuredLogger"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            log_file = f.name

        try:
            logger = StructuredLogger(log_file=log_file, enabled=True)

            results = []

            def worker(thread_id):
                """Рабочий поток, имитирующий обработку событий"""
                thread_results = []

                for i in range(5):
                    # Создаем цепочку обработки
                    event = Event(
                        type=f"event_{thread_id}_{i}",
                        intensity=0.1 * (i + 1),
                        timestamp=float(i + 1),
                    )
                    corr_id = logger.log_event(event)
                    thread_results.append(corr_id)

                    # Имитируем полный цикл
                    class MockMeaning:
                        def __init__(self, sig):
                            self.significance = sig
                            self.impact = {"energy": -sig * 5}

                    meaning = MockMeaning(abs(event.intensity))
                    logger.log_meaning(event, meaning, corr_id)
                    logger.log_decision("absorb", corr_id)
                    logger.log_action(f"action_{thread_id}_{i}", "absorb", corr_id)

                    class MockFeedback:
                        def __init__(self, action_id):
                            self.action_id = action_id
                            self.delay_ticks = 1
                            self.state_delta = {"stability": -0.1}

                    feedback = MockFeedback(f"action_{thread_id}_{i}")
                    logger.log_feedback(feedback, corr_id)

                    time.sleep(0.001)  # Имитация работы

                results.append(thread_results)

            # Запускаем несколько потоков
            threads = []
            for thread_id in range(3):
                t = threading.Thread(target=worker, args=(thread_id,))
                threads.append(t)
                t.start()

            # Ждем завершения
            for t in threads:
                t.join()

            # Проверяем результаты
            assert len(results) == 3
            all_correlation_ids = []
            for thread_results in results:
                all_correlation_ids.extend(thread_results)

            # Все correlation_id должны быть уникальными
            assert len(set(all_correlation_ids)) == len(all_correlation_ids)

            # Проверяем логи
            with open(log_file, "r") as f:
                lines = f.read().strip().split("\n")
                entries = [json.loads(line) for line in lines]

                # Должно быть 3 потока * 5 событий * 5 стадий = 75 записей
                assert len(entries) == 75

                # Группируем по correlation_id
                chains = {}
                for entry in entries:
                    corr_id = entry["correlation_id"]
                    if corr_id not in chains:
                        chains[corr_id] = []
                    chains[corr_id].append(entry)

                # Каждая цепочка должна иметь все стадии
                for corr_id, chain in chains.items():
                    stages = [entry["stage"] for entry in chain]
                    required_stages = [
                        "event",
                        "meaning",
                        "decision",
                        "action",
                        "feedback",
                    ]

                    for stage in required_stages:
                        assert (
                            stage in stages
                        ), f"Стадия {stage} отсутствует в цепочке {corr_id}"

                    # Проверяем, что записи одной цепочки имеют одинаковый correlation_id
                    chain_corr_ids = [entry["correlation_id"] for entry in chain]
                    assert all(cid == corr_id for cid in chain_corr_ids)

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_structured_logger_log_analysis(self):
        """Тест анализа логов для выявления паттернов"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            log_file = f.name

        try:
            logger = StructuredLogger(log_file=log_file, enabled=True)

            # Создаем разнообразные события для анализа
            test_events = [
                ("noise", 0.2, "absorb"),
                ("shock", -0.8, "dampen"),
                ("recovery", 0.6, "absorb"),
                ("noise", 0.1, "ignore"),
                ("decay", -0.3, "dampen"),
            ]

            for event_type, intensity, expected_pattern in test_events:
                event = Event(
                    type=event_type, intensity=intensity, timestamp=time.time()
                )
                corr_id = logger.log_event(event)

                # Имитируем meaning и decision на основе типа события
                significance = abs(intensity)
                logger.log_meaning(
                    event,
                    type("Mock", (), {"significance": significance, "impact": {}})(),
                    corr_id,
                )
                logger.log_decision(expected_pattern, corr_id)

            # Анализируем логи
            with open(log_file, "r") as f:
                entries = [json.loads(line) for line in f.read().strip().split("\n")]

            # Группируем по correlation_id
            chains = {}
            for entry in entries:
                corr_id = entry["correlation_id"]
                if corr_id not in chains:
                    chains[corr_id] = []
                chains[corr_id].append(entry)

            # Анализируем паттерны
            pattern_stats = {}
            for chain in chains.values():
                # Находим decision стадию
                decision_entries = [e for e in chain if e["stage"] == "decision"]
                if decision_entries:
                    pattern = decision_entries[0]["pattern"]
                    if pattern not in pattern_stats:
                        pattern_stats[pattern] = 0
                    pattern_stats[pattern] += 1

            # Проверяем статистику
            assert "absorb" in pattern_stats
            assert "dampen" in pattern_stats
            assert "ignore" in pattern_stats

            # Проверяем соответствие ожидаемым паттернам
            assert pattern_stats["absorb"] >= 2  # noise 0.2 и recovery 0.6
            assert pattern_stats["dampen"] >= 2  # shock -0.8 и decay -0.3
            assert pattern_stats["ignore"] >= 1  # noise 0.1

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_structured_logger_disabled_integration(self):
        """Тест интеграции с отключенным логированием"""
        # Используем уникальный файл для теста
        test_file = "data/test_disabled_integration_log.jsonl"
        if os.path.exists(test_file):
            os.unlink(test_file)

        logger = StructuredLogger(log_file=test_file, enabled=False)

        # Создаем полную цепочку обработки
        event = Event(type="noise", intensity=0.5, timestamp=1.0)
        corr_id = logger.log_event(event)

        logger.log_meaning(
            event, type("Mock", (), {"significance": 0.5, "impact": {}})(), corr_id
        )
        logger.log_decision("absorb", corr_id)
        logger.log_action("action_001", "absorb", corr_id)
        logger.log_feedback(
            type("Mock", (), {"action_id": "action_001", "delay_ticks": 1})(), corr_id
        )
        logger.log_tick_start(1, 5)
        logger.log_tick_end(1, 12.5, 2)

        # Файл не должен быть создан
        assert not os.path.exists(test_file)

        # Все операции должны выполняться без ошибок
        # (проверяем, что не было исключений)
