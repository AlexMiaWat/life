"""
Unit-тесты для MCP команды refresh_index()
"""

import asyncio
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_index import refresh_index


@pytest.mark.unit
class TestRefreshIndexBasic:
    """Базовые тесты для refresh_index()"""

    def test_refresh_index_success(self):
        """Тест успешного выполнения refresh_index()"""
        result = asyncio.run(refresh_index())
        
        assert "Индекс успешно обновлен" in result or "Ошибка" in result
        assert "Проиндексировано файлов:" in result
        assert "Уникальных токенов в индексе:" in result
        assert "Время выполнения:" in result

    def test_refresh_index_contains_statistics(self):
        """Тест наличия статистики в результате"""
        result = asyncio.run(refresh_index())
        
        if "Индекс успешно обновлен" in result:
            import re
            file_count_match = re.search(r"Проиндексировано файлов: (\d+)", result)
            token_count_match = re.search(r"Уникальных токенов в индексе: (\d+)", result)
            time_match = re.search(r"Время выполнения: ([\d.]+) сек\.", result)
            
            assert file_count_match is not None, "Не найдено количество файлов"
            assert token_count_match is not None, "Не найдено количество токенов"
            assert time_match is not None, "Не найдено время выполнения"
            
            file_count = int(file_count_match.group(1))
            token_count = int(token_count_match.group(1))
            elapsed_time = float(time_match.group(1))
            
            assert file_count >= 0
            assert token_count >= 0
            assert elapsed_time >= 0

    def test_refresh_index_timing_accuracy(self):
        """Тест точности измерения времени выполнения"""
        start = time.time()
        result = asyncio.run(refresh_index())
        actual_elapsed = time.time() - start
        
        if "Индекс успешно обновлен" in result:
            import re
            time_match = re.search(r"Время выполнения: ([\d.]+) сек\.", result)
            
            if time_match:
                reported_time = float(time_match.group(1))
                # Проверяем, что заявленное время близко к реальному (с допуском 1 сек)
                assert abs(reported_time - actual_elapsed) < 1.0, \
                    f"Заявленное время ({reported_time:.2f}) сильно отличается от реального ({actual_elapsed:.2f})"


@pytest.mark.unit
class TestRefreshIndexErrorHandling:
    """Тесты обработки ошибок в refresh_index()"""

    def test_refresh_index_handles_engine_init_error(self):
        """Тест обработки ошибки инициализации движка"""
        with patch('mcp_index._get_index_engine') as mock_get_engine:
            mock_get_engine.side_effect = RuntimeError("Ошибка инициализации")
            
            result = asyncio.run(refresh_index())
            
            assert "Ошибка" in result
            assert "инициализации" in result.lower() or "движок" in result.lower()
            assert "Время до ошибки:" in result

    def test_refresh_index_handles_reindex_error(self):
        """Тест обработки ошибки при переиндексации"""
        with patch('mcp_index._get_index_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.reindex.side_effect = RuntimeError("Ошибка переиндексации")
            mock_get_engine.return_value = mock_engine
            
            result = asyncio.run(refresh_index())
            
            assert "Ошибка" in result
            assert "переиндексации" in result.lower() or "обновлении индекса" in result.lower()
            assert "Время до ошибки:" in result

    def test_refresh_index_handles_statistics_error(self):
        """Тест обработки ошибки при подсчете статистики"""
        with patch('mcp_index._get_index_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.reindex.return_value = None
            # Симулируем ошибку при обращении к content_cache
            type(mock_engine).content_cache = property(
                lambda self: (_ for _ in ()).throw(ValueError("Ошибка доступа к кэшу"))
            )
            mock_get_engine.return_value = mock_engine
            
            result = asyncio.run(refresh_index())
            
            assert "Ошибка" in result
            assert "статистики" in result.lower() or "подсчете" in result.lower()
            assert "Время до ошибки:" in result

    def test_refresh_index_handles_os_error(self):
        """Тест обработки ошибок файловой системы"""
        with patch('mcp_index._get_index_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.reindex.side_effect = OSError("Permission denied")
            mock_get_engine.return_value = mock_engine
            
            result = asyncio.run(refresh_index())
            
            assert "Ошибка" in result
            assert "файловой системе" in result.lower() or "доступа" in result.lower()
            assert "Время до ошибки:" in result

    def test_refresh_index_handles_unexpected_error(self):
        """Тест обработки неожиданных ошибок"""
        with patch('mcp_index._get_index_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.reindex.side_effect = KeyError("Неожиданная ошибка")
            mock_get_engine.return_value = mock_engine
            
            result = asyncio.run(refresh_index())
            
            assert "Ошибка" in result
            assert "Неожиданная ошибка" in result or "KeyError" in result
            assert "Время до ошибки:" in result


@pytest.mark.unit
class TestRefreshIndexValidation:
    """Тесты валидации статистики в refresh_index()"""

    def test_refresh_index_warns_on_zero_files(self):
        """Тест предупреждения при нулевом количестве файлов"""
        # Этот тест может не сработать, если в проекте есть файлы
        # Но мы проверяем, что предупреждение появляется в соответствующем случае
        result = asyncio.run(refresh_index())
        
        # Если файлов 0, должно быть предупреждение
        import re
        file_count_match = re.search(r"Проиндексировано файлов: (\d+)", result)
        
        if file_count_match:
            file_count = int(file_count_match.group(1))
            if file_count == 0:
                assert "⚠️" in result or "Предупреждение" in result
                assert "не проиндексировано ни одного файла" in result.lower() or \
                       "файлов пусты" in result.lower()

    def test_refresh_index_warns_on_zero_tokens(self):
        """Тест предупреждения при нулевом количестве токенов"""
        result = asyncio.run(refresh_index())
        
        import re
        token_count_match = re.search(r"Уникальных токенов в индексе: (\d+)", result)
        
        if token_count_match:
            token_count = int(token_count_match.group(1))
            if token_count == 0:
                assert "⚠️" in result or "Предупреждение" in result
                assert "не содержит токенов" in result.lower() or \
                       "файлы пусты" in result.lower()


@pytest.mark.integration
class TestRefreshIndexIntegration:
    """Интеграционные тесты для refresh_index()"""

    def test_refresh_index_integration_with_search(self):
        """Тест интеграции refresh_index() с поиском"""
        # Выполняем переиндексацию
        refresh_result = asyncio.run(refresh_index())
        assert "Индекс успешно обновлен" in refresh_result or "Ошибка" not in refresh_result
        
        # Проверяем, что после переиндексации поиск работает
        from mcp_index import search_docs
        search_result = asyncio.run(search_docs("test", limit=1))
        
        # Поиск должен работать (даже если ничего не найдено)
        assert isinstance(search_result, str)
        assert len(search_result) > 0

    def test_refresh_index_multiple_calls(self):
        """Тест множественных вызовов refresh_index()"""
        # Первый вызов
        result1 = asyncio.run(refresh_index())
        assert "Индекс успешно обновлен" in result1 or "Ошибка" not in result1
        
        # Второй вызов (должен работать корректно)
        result2 = asyncio.run(refresh_index())
        assert "Индекс успешно обновлен" in result2 or "Ошибка" not in result2
        
        # Статистика должна быть согласованной
        import re
        file_count_match1 = re.search(r"Проиндексировано файлов: (\d+)", result1)
        file_count_match2 = re.search(r"Проиндексировано файлов: (\d+)", result2)
        
        if file_count_match1 and file_count_match2:
            file_count1 = int(file_count_match1.group(1))
            file_count2 = int(file_count_match2.group(1))
            # Количество файлов должно быть одинаковым при повторных вызовах
            assert file_count1 == file_count2, \
                f"Количество файлов изменилось между вызовами: {file_count1} -> {file_count2}"
