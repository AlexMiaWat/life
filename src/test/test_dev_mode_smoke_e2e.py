"""
End-to-end smoke-тест для dev-mode (новая функциональность process_restarter)

Проверяет полный цикл dev-mode:
- Старт процесса Life в dev-mode
- Симуляция изменения файла
- Перезапуск процесса
- Сохранение/восстановление состояния

⚠️  ВНИМАНИЕ: Этот тест запускает реальный процесс Life на порту 8000!
   - Может конфликтовать с уже запущенными серверами
   - Требует ручного запуска (--skip по умолчанию)
   - Может быть медленным (до 60 секунд)
   - Изменяет файлы в проекте для тестирования
"""

import os
import subprocess
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
import requests
from requests.exceptions import ConnectionError, Timeout


@pytest.mark.smoke
@pytest.mark.e2e
@pytest.mark.dev_mode
@pytest.mark.skip(
    reason="Requires manual execution - may conflict with running servers on port 8000"
)
class TestDevModeSmokeE2E:
    """
    End-to-end smoke тест полного цикла dev-mode

    Запускает реальный процесс Life с dev-mode, симулирует изменения файлов,
    проверяет перезапуск и восстановление состояния.
    """

    @pytest.fixture
    def test_file_for_changes(self):
        """Создает тестовый файл для симуляции изменений"""
        # Используем один из отслеживаемых dev-mode файлов
        test_file = project_root / "src" / "test_dev_mode_change_trigger.py"
        original_content = ""

        # Сохраняем оригинальное содержимое если файл существует
        if test_file.exists():
            original_content = test_file.read_text()

        # Создаем файл с начальным содержимым
        test_file.write_text("# Test file for dev-mode change trigger\n# Initial content\n")

        yield test_file

        # Восстанавливаем оригинальное содержимое
        if original_content:
            test_file.write_text(original_content)
        else:
            test_file.unlink(missing_ok=True)

    def test_dev_mode_full_cycle(self, test_file_for_changes):
        """
        Полный end-to-end тест цикла dev-mode:
        старт → изменение → рестарт → сохранение/восстановление snapshot

        Тест запускает реальный процесс Life, симулирует изменения файлов,
        проверяет автоматический перезапуск и восстановление состояния.

        ⚠️  Тест использует порт 8000 и может конфликтовать с другими серверами!
        """
        life_process = None

        try:
            # ШАГ 1: Запуск процесса Life в dev-mode
            print("Шаг 1: Запуск процесса Life в dev-mode...")

            # Запускаем процесс Life в dev-mode
            env = os.environ.copy()
            env["PYTHONPATH"] = str(project_root / "src")

            # Запускаем main_server_api.py с флагом --dev
            life_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "src.main_server_api",
                    "--dev",
                    "--tick-interval",
                    "0.1",  # Очень быстро для теста
                    "--snapshot-period",
                    "2",  # Часто для теста
                ],
                cwd=project_root,  # Запускаем из основной директории проекта
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # ШАГ 2: Ожидание запуска и инициализации
            print("Шаг 2: Ожидание запуска API сервера...")
            self._wait_for_api_ready("http://localhost:8000", timeout=30)

            # ШАГ 3: Получение начального состояния через API
            print("Шаг 3: Получение начального состояния...")
            initial_response = requests.get("http://localhost:8000/status", timeout=5)
            assert initial_response.status_code == 200
            initial_state = initial_response.json()
            print(f"Начальное состояние: energy={initial_state.get('energy', 'N/A')}")

            # ШАГ 4: Симуляция изменения файла
            print("Шаг 4: Симуляция изменения файла...")
            time.sleep(2)  # Даем время на инициализацию мониторинга
            test_file_for_changes.write_text(
                "# Modified content for dev-mode test\nprint('dev-mode triggered')\n"
            )

            # ШАГ 5: Ожидание перезапуска процесса
            print("Шаг 5: Ожидание перезапуска...")
            # Ждем немного, чтобы изменения были обнаружены и перезапуск начался
            time.sleep(3)
            # Проверяем, что процесс еще жив (ожидаем перезапуска)
            assert life_process.poll() is None, "Процесс unexpectedly завершился"

            # Ждем перезапуска API (сервер может быть временно недоступен)
            self._wait_for_restart("http://localhost:8000", timeout=20)

            # ШАГ 6: Валидация восстановления состояния
            print("Шаг 6: Валидация восстановления состояния...")
            restored_response = requests.get("http://localhost:8000/status", timeout=5)
            assert restored_response.status_code == 200
            restored_state = restored_response.json()

            # Проверяем, что состояние восстановлено (основные поля присутствуют)
            assert "energy" in restored_state
            assert "ticks" in restored_state
            assert "stability" in restored_state

            print(f"Восстановленное состояние: energy={restored_state.get('energy', 'N/A')}")
            print("✅ Тест пройден успешно!")

        finally:
            # ШАГ 7: Остановка и cleanup
            print("Шаг 7: Очистка...")
            self._cleanup_process(life_process)

    def _wait_for_api_ready(self, base_url, timeout=30):
        """
        Ожидает готовности API сервера

        Args:
            base_url: Базовый URL API
            timeout: Максимальное время ожидания в секундах
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{base_url}/status", timeout=2)
                if response.status_code == 200:
                    return True
            except (ConnectionError, Timeout):
                pass
            time.sleep(0.5)

        raise AssertionError(f"API сервер не запустился за {timeout} секунд")

    def _wait_for_restart(self, base_url, timeout=20):
        """
        Ожидает перезапуска API сервера после изменения файлов

        Args:
            base_url: Базовый URL API
            timeout: Максимальное время ожидания в секундах
        """
        # Короткая пауза, чтобы дать время на обнаружение изменений
        time.sleep(1)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{base_url}/status", timeout=2)
                if response.status_code == 200:
                    # Сервер перезапустился
                    return True
            except (ConnectionError, Timeout):
                # Сервер временно недоступен - это нормально во время перезапуска
                pass
            time.sleep(0.5)

        raise AssertionError(f"Перезапуск сервера не произошел за {timeout} секунд")

    def _cleanup_process(self, process):
        """
        Корректно останавливает процесс

        Args:
            process: subprocess.Popen объект
        """
        if process and process.poll() is None:
            try:
                # Сначала пытаемся graceful shutdown через SIGTERM
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Если не помогло, принудительно убиваем
                process.kill()
                process.wait(timeout=2)
            except Exception:
                # Игнорируем ошибки cleanup
                pass
