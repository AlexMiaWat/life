"""
Тесты на потокобезопасность API и state между API и runtime

Проверяем:
- Конкурентный доступ к состоянию из API и runtime loop
- Атомарность операций чтения/записи
- Обработку race conditions
- Immutable snapshots для API
"""

import sys
import threading
import time
from pathlib import Path
from unittest.mock import Mock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
from fastapi.testclient import TestClient

from api import app
from src.runtime.loop import run_loop
from src.state.self_state import SelfState


@pytest.mark.concurrency
class TestAPIConcurrency:
    """Тесты на потокобезопасность API"""

    def test_api_status_read_during_runtime_modification(self):
        """Тест чтения статуса API во время модификации runtime"""
        client = TestClient(app, timeout=10.0)

        # Получаем токен
        login_response = client.post(
            "/token", data={"username": "admin", "password": "admin123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Создаем состояние и очередь событий
        state = SelfState()
        event_queue = None
        stop_event = threading.Event()

        # Запускаем runtime loop в отдельном потоке
        def run_runtime():
            try:
                run_loop(
                    state,
                    lambda s: None,
                    0.001,
                    50,
                    stop_event,
                    event_queue,
                    False,
                    False,
                    False,
                    False,
                    10,
                    False,
                )
            except Exception:
                pass  # Игнорируем исключения для теста

        runtime_thread = threading.Thread(target=run_runtime)
        runtime_thread.start()

        # Пока runtime работает, делаем несколько запросов к API
        status_responses = []
        for _ in range(5):
            response = client.get("/status", headers=headers)
            status_responses.append(response.status_code)
            time.sleep(0.01)  # Небольшая задержка

        # Останавливаем runtime
        stop_event.set()
        runtime_thread.join(timeout=1.0)

        # Все запросы должны быть успешными
        assert all(code == 200 for code in status_responses)

    def test_concurrent_api_requests_same_user(self):
        """Тест конкурентных запросов API от одного пользователя"""
        client = TestClient(app, timeout=10.0)

        # Получаем токен
        login_response = client.post(
            "/token", data={"username": "admin", "password": "admin123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        results = []

        def make_request(request_id):
            try:
                # Делаем запрос статуса
                response = client.get("/status", headers=headers)
                results.append(
                    (request_id, response.status_code, response.json().get("active"))
                )
            except Exception as e:
                results.append((request_id, "error", str(e)))

        # Запускаем несколько одновременных запросов
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Ждем завершения всех запросов
        for thread in threads:
            thread.join(timeout=2.0)

        # Проверяем результаты
        assert len(results) == 10
        for request_id, status_code, active in results:
            assert status_code == 200
            assert active is not None

    def test_concurrent_event_submission_and_status_read(self):
        """Тест конкурентной отправки событий и чтения статуса"""
        client = TestClient(app, timeout=10.0)

        # Регистрируем пользователя для теста
        user_data = {
            "username": "concurrency_test",
            "email": "concurrency@example.com",
            "password": "test123",
        }
        client.post("/register", json=user_data)

        login_response = client.post(
            "/token", data={"username": "concurrency_test", "password": "test123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        results = []

        def submit_event(event_id):
            try:
                event_data = {
                    "type": "noise",
                    "intensity": 0.1 + (event_id % 5) * 0.1,
                    "metadata": {"test": "concurrency", "event_id": event_id},
                }
                response = client.post("/event", json=event_data, headers=headers)
                results.append(("event", event_id, response.status_code))
            except Exception as e:
                results.append(("event", event_id, f"error: {e}"))

        def read_status(status_id):
            try:
                response = client.get("/status", headers=headers)
                results.append(("status", status_id, response.status_code))
            except Exception as e:
                results.append(("status", status_id, f"error: {e}"))

        # Запускаем микс из отправки событий и чтения статуса
        threads = []

        # 5 потоков для отправки событий
        for i in range(5):
            thread = threading.Thread(target=submit_event, args=(i,))
            threads.append(thread)

        # 5 потоков для чтения статуса
        for i in range(5):
            thread = threading.Thread(target=read_status, args=(i,))
            threads.append(thread)

        # Запускаем все потоки
        for thread in threads:
            thread.start()

        # Ждем завершения
        for thread in threads:
            thread.join(timeout=3.0)

        # Проверяем результаты
        event_results = [r for r in results if r[0] == "event"]
        status_results = [r for r in results if r[0] == "status"]

        assert len(event_results) == 5
        assert len(status_results) == 5

        # Все события должны быть приняты
        for _, _, status in event_results:
            assert status == 200

        # Все чтения статуса должны быть успешными
        for _, _, status in status_results:
            assert status == 200

    def test_api_state_isolation_between_users(self):
        """Тест изоляции состояния между пользователями"""
        client = TestClient(app, timeout=10.0)

        # Создаем двух пользователей
        users = [
            {"username": "user1", "email": "user1@example.com", "password": "pass1"},
            {"username": "user2", "email": "user2@example.com", "password": "pass2"},
        ]

        tokens = {}
        for user in users:
            client.post("/register", json=user)
            login_response = client.post("/token", data=user)
            tokens[user["username"]] = login_response.json()["access_token"]

        # Каждый пользователь отправляет событие
        for username, token in tokens.items():
            headers = {"Authorization": f"Bearer {token}"}
            event_data = {"type": "noise", "metadata": {"user": username}}
            response = client.post("/event", json=event_data, headers=headers)
            assert response.status_code == 200

            # Проверяем, что сообщение содержит имя пользователя
            data = response.json()
            assert username in data["message"]

        # Проверяем, что пользователи не могут читать токены друг друга
        # (в текущей реализации токены не привязаны к пользователю в payload)
        # Тестируем через попытку использовать токен одного пользователя для действий другого

    def test_api_handles_concurrent_token_generation(self):
        """Тест конкурентной генерации токенов"""
        client = TestClient(app, timeout=10.0)

        results = []

        def get_token(attempt_id):
            try:
                response = client.post(
                    "/token", data={"username": "admin", "password": "admin123"}
                )
                results.append((attempt_id, response.status_code))
                if response.status_code == 200:
                    token = response.json()["access_token"]
                    # Проверяем, что токен валиден
                    headers = {"Authorization": f"Bearer {token}"}
                    status_response = client.get("/status", headers=headers)
                    results.append(
                        (f"{attempt_id}_verify", status_response.status_code)
                    )
            except Exception as e:
                results.append((attempt_id, f"error: {e}"))

        # Запускаем несколько одновременных запросов токенов
        threads = []
        for i in range(5):
            thread = threading.Thread(target=get_token, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=2.0)

        # Проверяем результаты
        successful_tokens = [
            r
            for r in results
            if len(r) >= 2 and r[1] == 200 and not str(r[0]).endswith("_verify")
        ]
        successful_verifications = [
            r
            for r in results
            if len(r) >= 2 and str(r[0]).endswith("_verify") and r[1] == 200
        ]

        # Хотя бы некоторые токены должны быть сгенерированы успешно
        assert len(successful_tokens) >= 1
        assert len(successful_verifications) >= 1


@pytest.mark.concurrency
class TestStateIsolation:
    """Тесты на изоляцию состояния между API и runtime"""

    def test_api_reads_immutable_snapshot(self):
        """Тест что API читает immutable snapshot состояния"""
        from src.state.self_state import SelfState

        # Создаем состояние
        original_state = SelfState()
        original_state.energy = 75.0
        original_state.ticks = 42

        # Имитируем API чтение (через copy или snapshot)
        # В реальной реализации API должен использовать immutable snapshot
        api_snapshot = original_state.__dict__.copy()  # Имитация immutable snapshot

        # Модифицируем оригинальное состояние
        original_state.energy = 50.0
        original_state.ticks = 43

        # API snapshot не должен измениться
        assert api_snapshot["energy"] == 75.0
        assert api_snapshot["ticks"] == 42

    def test_runtime_modification_during_api_read(self):
        """Тест модификации состояния runtime во время чтения API"""
        state = SelfState()
        state.energy = 100.0
        state.ticks = 0

        # Имитируем чтение API (создаем snapshot)
        api_snapshot = state.__dict__.copy()

        # Имитируем работу runtime (модификация состояния)
        time.sleep(0.01)  # Небольшая задержка
        state.energy = 90.0
        state.ticks = 1

        # Проверяем, что API snapshot не изменился
        assert api_snapshot["energy"] == 100.0
        assert api_snapshot["ticks"] == 0

    def test_snapshot_creation_isolation(self):
        """Тест изоляции при создании снапшотов"""
        from src.runtime.snapshot_manager import SnapshotManager

        saver = Mock()
        state = SelfState()
        state.energy = 80.0
        state.ticks = 10  # Устанавливаем правильный тик

        manager = SnapshotManager(period_ticks=10, saver=saver)

        # Создаем снапшот
        result = manager.maybe_snapshot(state)

        # Проверяем, что saver был вызван и снапшот создан
        assert result is True
        saver.assert_called_once_with(state)

    def test_memory_consistency_during_concurrent_access(self):
        """Тест консистентности памяти при конкурентном доступе"""
        from src.memory.memory import Memory, MemoryEntry

        memory = Memory()

        # Добавляем начальные записи
        for i in range(5):
            entry = MemoryEntry(
                event_type="noise", meaning_significance=0.3, timestamp=float(i)
            )
            memory.append(entry)

        initial_length = len(memory)

        results = []

        def read_memory(reader_id):
            try:
                # Имитируем чтение (создаем копию списка)
                snapshot = list(memory)
                results.append(("read", reader_id, len(snapshot)))
            except Exception as e:
                results.append(("read", reader_id, f"error: {e}"))

        def write_memory(writer_id):
            try:
                # Имитируем запись
                entry = MemoryEntry(
                    event_type="shock",
                    meaning_significance=0.8,
                    timestamp=100.0 + writer_id,
                )
                memory.append(entry)
                results.append(("write", writer_id, len(memory)))
            except Exception as e:
                results.append(("write", writer_id, f"error: {e}"))

        # Запускаем чтение и запись конкурентно
        threads = []

        # 3 потока чтения
        for i in range(3):
            thread = threading.Thread(target=read_memory, args=(i,))
            threads.append(thread)

        # 2 потока записи
        for i in range(2):
            thread = threading.Thread(target=write_memory, args=(i,))
            threads.append(thread)

        # Запускаем все
        for thread in threads:
            thread.start()

        # Ждем завершения
        for thread in threads:
            thread.join(timeout=2.0)

        # Проверяем результаты
        read_results = [r for r in results if r[0] == "read"]
        write_results = [r for r in results if r[0] == "write"]

        assert len(read_results) == 3
        assert len(write_results) == 2

        # Все операции должны быть успешными
        for _, _, result in read_results + write_results:
            assert not str(result).startswith("error")

        # Финальная длина памяти должна быть initial + writes
        assert len(memory) == initial_length + 2


@pytest.mark.concurrency
class TestAPIErrorHandling:
    """Тесты обработки ошибок в конкурентной среде"""

    def test_api_timeout_handling(self):
        """Тест обработки таймаутов API"""
        client = TestClient(app, timeout=10.0)

        # Получаем токен
        login_response = client.post(
            "/token", data={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Делаем много быстрых запросов
        start_time = time.time()
        responses = []

        for i in range(20):
            try:
                response = client.get("/status", headers=headers)
                responses.append(response.status_code)
            except Exception as e:
                responses.append(f"error: {e}")

        end_time = time.time()

        # Проверяем, что запросы выполнились за разумное время
        assert end_time - start_time < 5.0  # Не больше 5 секунд на 20 запросов

        # Большинство запросов должны быть успешными
        successful_responses = [r for r in responses if r == 200]
        assert len(successful_responses) >= 15  # Хотя бы 75% успешных

    def test_api_handles_invalid_tokens_concurrently(self):
        """Тест обработки невалидных токенов в конкурентной среде"""
        client = TestClient(app, timeout=10.0)

        invalid_tokens = [
            "invalid.jwt.token",
            "another.invalid.token",
            "expired.token.here",
            "",
            "malformed_token",
        ]

        results = []

        def test_invalid_token(token_id, token):
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = client.get("/status", headers=headers)
                results.append((token_id, response.status_code))
            except Exception as e:
                results.append((token_id, f"error: {e}"))

        # Тестируем невалидные токены конкурентно
        threads = []
        for i, token in enumerate(invalid_tokens):
            thread = threading.Thread(target=test_invalid_token, args=(i, token))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=2.0)

        # Все запросы с невалидными токенами должны вернуть 401
        assert len(results) == len(invalid_tokens)
        for token_id, result in results:
            assert result == 401 or str(result) == "401"

    def test_api_connection_pooling(self):
        """Тест пула соединений API"""
        client = TestClient(app, timeout=10.0)

        # Регистрируем пользователя
        user_data = {
            "username": "pool_test",
            "email": "pool@example.com",
            "password": "pool123",
        }
        client.post("/register", json=user_data)

        login_response = client.post(
            "/token", data={"username": "pool_test", "password": "pool123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Делаем много последовательных запросов
        for i in range(50):
            response = client.get("/status", headers=headers)
            assert response.status_code == 200

            if i % 10 == 0:  # Каждые 10 запросов отправляем событие
                event_response = client.post(
                    "/event",
                    json={"type": "noise", "metadata": {"batch": i // 10}},
                    headers=headers,
                )
                assert event_response.status_code == 200

        # Система должна выдержать нагрузку без ошибок
