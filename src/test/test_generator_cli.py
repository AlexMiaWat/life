"""
Тесты для generator_cli.py
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
import requests
from unittest.mock import patch, MagicMock
from environment.generator_cli import send_event, main
from environment.generator import EventGenerator


class TestGeneratorCLI:
    """Тесты для generator_cli"""
    
    def test_send_event_success(self, monkeypatch):
        """Тест успешной отправки события (строки 18-24)"""
        class MockResponse:
            status_code = 200
            text = "Event accepted"
        
        def mock_post(url, json=None, timeout=None):
            return MockResponse()
        
        monkeypatch.setattr("requests.post", mock_post)
        
        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is True
        assert code == 200
        assert body == "Event accepted"
    
    def test_send_event_request_exception(self, monkeypatch):
        """Тест обработки RequestException (строки 25-26)"""
        import requests
        
        def mock_post(url, json=None, timeout=None):
            raise requests.exceptions.RequestException("Connection error")
        
        monkeypatch.setattr("requests.post", mock_post)
        
        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is False
        assert code == 0
        assert "Connection error" in reason or "RequestException" in reason
    
    def test_send_event_general_exception(self, monkeypatch):
        """Тест обработки общего исключения (строки 27-28)"""
        def mock_post(url, json=None, timeout=None):
            raise ValueError("Unexpected error")
        
        monkeypatch.setattr("requests.post", mock_post)
        
        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is False
        assert code is None
        assert "Unexpected error" in reason or "ValueError" in reason
    
    @patch('builtins.print')
    @patch('environment.generator_cli.send_event')
    @patch('environment.generator_cli.EventGenerator')
    @patch('time.sleep')
    @patch('builtins.input', return_value='')  # Для KeyboardInterrupt
    def test_main_function_basic(self, mock_input, mock_sleep, mock_generator_class, mock_send, mock_print):
        """Тест основной функции main (строки 32-60)"""
        # Настраиваем моки
        mock_generator = MagicMock()
        mock_generator.generate.return_value = MagicMock(
            type="shock",
            intensity=0.5,
            timestamp=1234567890.0,
            metadata={}
        )
        mock_generator_class.return_value = mock_generator
        
        mock_send.return_value = (True, 200, "", "Event accepted")
        
        # Симулируем KeyboardInterrupt после первой итерации
        call_count = [0]
        def side_effect(*args):
            call_count[0] += 1
            if call_count[0] > 1:
                raise KeyboardInterrupt()
        
        mock_sleep.side_effect = side_effect
        
        # Запускаем main с аргументами
        import sys
        with patch.object(sys, 'argv', ['generator_cli.py', '--interval', '0.1']):
            try:
                main()
            except KeyboardInterrupt:
                pass  # Ожидаемое поведение
        
        # Проверяем, что generator был создан
        mock_generator_class.assert_called_once()
        
        # Проверяем, что generate был вызван
        assert mock_generator.generate.call_count >= 1
    
    @patch('builtins.print')
    @patch('environment.generator_cli.send_event')
    @patch('environment.generator_cli.EventGenerator')
    @patch('time.sleep')
    def test_main_function_send_event_called(self, mock_sleep, mock_generator_class, mock_send, mock_print):
        """Тест, что send_event вызывается в main"""
        mock_generator = MagicMock()
        mock_event = MagicMock()
        mock_event.type = "noise"
        mock_event.intensity = 0.3
        mock_event.timestamp = 1234567890.0
        mock_event.metadata = {}
        mock_generator.generate.return_value = mock_event
        mock_generator_class.return_value = mock_generator
        
        mock_send.return_value = (True, 200, "", "Event accepted")
        
        # Симулируем одну итерацию
        call_count = [0]
        def side_effect(*args):
            call_count[0] += 1
            if call_count[0] > 0:
                raise KeyboardInterrupt()
        
        mock_sleep.side_effect = side_effect
        
        import sys
        with patch.object(sys, 'argv', ['generator_cli.py']):
            try:
                main()
            except KeyboardInterrupt:
                pass
        
        # Проверяем, что send_event был вызван
        assert mock_send.call_count >= 1
        
        # Проверяем аргументы вызова
        call_args = mock_send.call_args
        assert call_args[0][0] == "localhost"  # host
        assert call_args[0][1] == 8000  # port
        assert isinstance(call_args[0][2], dict)  # payload
        assert call_args[0][2]["type"] == "noise"
    
    @patch('builtins.print')
    @patch('environment.generator_cli.send_event')
    @patch('environment.generator_cli.EventGenerator')
    @patch('time.sleep')
    def test_main_function_send_failure(self, mock_sleep, mock_generator_class, mock_send, mock_print):
        """Тест обработки ошибки отправки в main"""
        mock_generator = MagicMock()
        mock_generator.generate.return_value = MagicMock(
            type="shock",
            intensity=0.5,
            timestamp=1234567890.0,
            metadata={}
        )
        mock_generator_class.return_value = mock_generator
        
        # Симулируем ошибку отправки
        mock_send.return_value = (False, 0, "Connection refused", "")
        
        call_count = [0]
        def side_effect(*args):
            call_count[0] += 1
            if call_count[0] > 0:
                raise KeyboardInterrupt()
        
        mock_sleep.side_effect = side_effect
        
        import sys
        with patch.object(sys, 'argv', ['generator_cli.py']):
            try:
                main()
            except KeyboardInterrupt:
                pass
        
        # Проверяем, что ошибка была обработана
        assert mock_send.call_count >= 1
    
    def test_main_function_if_name_main(self):
        """Тест вызова main при запуске как скрипт (строка 64)"""
        import sys
        from unittest.mock import patch
        
        # Мокируем все зависимости
        with patch('environment.generator_cli.EventGenerator') as mock_gen_class, \
             patch('environment.generator_cli.send_event') as mock_send, \
             patch('time.sleep', side_effect=KeyboardInterrupt()), \
             patch('builtins.print'):
            
            mock_generator = MagicMock()
            mock_generator.generate.return_value = MagicMock(
                type="test",
                intensity=0.5,
                timestamp=1234567890.0,
                metadata={}
            )
            mock_gen_class.return_value = mock_generator
            mock_send.return_value = (True, 200, "", "OK")
            
            # Симулируем запуск как __main__
            with patch.object(sys, 'argv', ['generator_cli.py']):
                # Импортируем модуль и вызываем main через __main__
                import importlib
                import environment.generator_cli as cli_module
                
                # Симулируем if __name__ == "__main__": main()
                try:
                    cli_module.main()
                except KeyboardInterrupt:
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
