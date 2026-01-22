"""
Интеграционные тесты для генератора событий с API сервером
Поддерживают работу с реальным сервером (--real-server) или тестовым сервером
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.environment.generator import EventGenerator
from src.environment.generator_cli import send_event


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
class TestGeneratorServerIntegration:
    """Интеграционные тесты генератора с сервером"""

    def test_generator_send_to_server(self, server_setup):
        """Тест отправки сгенерированного события на сервер"""
        generator = EventGenerator()
        event = generator.generate()

        payload = {
            "type": event.type,
            "intensity": event.intensity,
            "timestamp": event.timestamp,
            "metadata": event.metadata,
        }

        success, code, reason, body = send_event("localhost", server_setup["port"], payload)

        assert success is True
        assert code == 200

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            assert server_setup["event_queue"].size() == 1

            queued_event = server_setup["event_queue"].pop()
            assert queued_event.type == event.type
            assert abs(queued_event.intensity - event.intensity) < 0.001

    def test_generator_multiple_events_to_server(self, server_setup):
        """Тест отправки нескольких сгенерированных событий"""
        generator = EventGenerator()
        events = [generator.generate() for _ in range(5)]

        for event in events:
            payload = {
                "type": event.type,
                "intensity": event.intensity,
                "timestamp": event.timestamp,
                "metadata": event.metadata,
            }

            success, code, reason, body = send_event("localhost", server_setup["port"], payload)
            assert success is True
            assert code == 200

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            assert server_setup["event_queue"].size() == 5

    def test_generator_all_event_types_to_server(self, server_setup):
        """Тест отправки всех типов событий на сервер"""
        generator = EventGenerator()
        event_types = set()

        # Генерируем события до тех пор, пока не получим все типы
        for _ in range(100):
            event = generator.generate()
            event_types.add(event.type)

            payload = {
                "type": event.type,
                "intensity": event.intensity,
                "timestamp": event.timestamp,
                "metadata": event.metadata,
            }

            success, code, reason, body = send_event("localhost", server_setup["port"], payload)
            assert success is True

            if len(event_types) == 5:  # Все типы получены
                break

        assert len(event_types) == 5

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            assert server_setup["event_queue"].size() > 0

    def test_generator_event_intensity_ranges(self, server_setup):
        """Тест, что интенсивности событий соответствуют спецификации"""
        generator = EventGenerator()

        intensity_ranges = {
            "noise": (-0.3, 0.3),
            "decay": (-0.5, 0.0),
            "recovery": (0.0, 0.5),
            "shock": (-1.0, 1.0),
            "idle": (0.0, 0.0),
            "cognitive_doubt": (-0.5, 0.0),
            "curiosity": (-0.3, 0.4),
            "social_presence": (-0.4, 0.4),
            "social_conflict": (-0.6, 0.0),
            "social_harmony": (0.0, 0.6),
            "cognitive_clarity": (0.0, 0.5),
            "cognitive_confusion": (-0.4, 0.0),
            "existential_void": (-0.7, 0.0),
            "existential_purpose": (0.0, 0.7),
            "existential_finitude": (-0.6, 0.0),
            "connection": (0.0, 0.8),
            "isolation": (-0.7, 0.0),
            "insight": (0.0, 0.6),
            "confusion": (-0.5, 0.0),
            "meaning_found": (0.0, 0.9),
            "void": (-0.8, 0.0),
            "acceptance": (0.0, 0.5),
            "joy": (0.0, 0.8),
            "sadness": (-0.7, 0.0),
            "fear": (-0.8, 0.0),
            "calm": (0.0, 0.6),
            "discomfort": (-0.6, 0.0),
            "comfort": (0.0, 0.7),
            "fatigue": (-0.5, 0.0),
            "anticipation": (-0.3, 0.5),
            "boredom": (-0.4, 0.0),
            "inspiration": (0.0, 0.9),
            "creative_dissonance": (-0.5, 0.0),
        }

        # Генерируем события и проверяем диапазоны
        for _ in range(200):
            event = generator.generate()
            min_intensity, max_intensity = intensity_ranges[event.type]

            if event.type == "idle":
                assert event.intensity == 0.0
            else:
                assert min_intensity <= event.intensity <= max_intensity

    def test_generator_server_full_cycle(self, server_setup):
        """Тест полного цикла: генерация -> отправка -> получение"""
        generator = EventGenerator()

        # Генерируем и отправляем событие
        event = generator.generate()
        payload = {
            "type": event.type,
            "intensity": event.intensity,
            "timestamp": event.timestamp,
            "metadata": event.metadata,
        }

        success, code, reason, body = send_event("localhost", server_setup["port"], payload)

        assert success is True

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            # Получаем событие из очереди
            assert server_setup["event_queue"].size() == 1
            queued_event = server_setup["event_queue"].pop()

            # Проверяем целостность данных
            assert queued_event.type == event.type
            assert abs(queued_event.intensity - event.intensity) < 0.001
            assert abs(queued_event.timestamp - event.timestamp) < 0.001
            assert queued_event.metadata == event.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
