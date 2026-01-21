import argparse
import glob
import importlib
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from colorama import Fore, Style, init

from src.environment import Event, EventQueue
from src.environment.scenario_manager import ScenarioManager
from src.environment.impact_analyzer import ImpactAnalyzer
from src.environment.environment_config import EnvironmentConfigManager
from src.logging_config import get_logger, setup_logging
from src.monitor.console import monitor
from src.runtime.loop import run_loop
from src.state.self_state import SelfState

init()

from typing import Any

# Настройка логирования
logger = get_logger(__name__)

HOST = "localhost"
PORT = 8000



class StoppableHTTPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self_state больше не нужен - API читает из snapshots
        self.event_queue: EventQueue | None = None
        self.stopped = False
        self.dev_mode = False

        # Новые компоненты для расширенного API среды
        self.scenario_manager: ScenarioManager | None = None
        self.impact_analyzer: ImpactAnalyzer | None = None
        self.environment_config_manager: EnvironmentConfigManager | None = None

    def serve_forever(self, poll_interval=0.5):
        self.timeout = poll_interval
        while not self.stopped:
            self.handle_request()

    def shutdown(self):
        self.stopped = True
        self.server_close()


class LifeHandler(BaseHTTPRequestHandler):
    server: Any  # Добавляем, чтобы IDE знала, что у server могут быть кастомные атрибуты

    def do_GET(self):
        if self.path.startswith("/status"):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            # Парсим query-параметры для ограничения больших полей
            from urllib.parse import parse_qs, urlparse

            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            # Извлекаем лимиты из query-параметров
            limits = {}
            if "memory_limit" in query_params:
                try:
                    limits["memory_limit"] = int(query_params["memory_limit"][0])
                except (ValueError, IndexError):
                    pass
            if "events_limit" in query_params:
                try:
                    limits["events_limit"] = int(query_params["events_limit"][0])
                except (ValueError, IndexError):
                    pass
            if "energy_history_limit" in query_params:
                try:
                    limits["energy_history_limit"] = int(query_params["energy_history_limit"][0])
                except (ValueError, IndexError):
                    pass
            if "stability_history_limit" in query_params:
                try:
                    limits["stability_history_limit"] = int(
                        query_params["stability_history_limit"][0]
                    )
                except (ValueError, IndexError):
                    pass
            if "adaptation_history_limit" in query_params:
                try:
                    limits["adaptation_history_limit"] = int(
                        query_params["adaptation_history_limit"][0]
                    )
                except (ValueError, IndexError):
                    pass

            # Получаем текущее состояние
            # Сначала пробуем взять из сервера (для тестов), иначе из snapshot
            if hasattr(self.server, "self_state") and self.server.self_state is not None:
                self_state = self.server.self_state
            else:
                try:
                    self_state = SelfState().load_latest_snapshot()
                except FileNotFoundError:
                    self_state = SelfState()

            safe_status = self_state.get_safe_status_dict(limits=limits)
            self.wfile.write(json.dumps(safe_status).encode())
        elif self.path == "/refresh-cache":
            # В текущей реализации состояние читается из snapshots при каждом запросе,
            # поэтому кэширование не требуется. Просто возвращаем успех.
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"message": "Cache refreshed (no-op in current implementation)"}')
        elif self.path == "/clear-data":
            os.makedirs("data/snapshots", exist_ok=True)
            log_file = "data/tick_log.jsonl"
            snapshots = glob.glob("data/snapshots/*.json")
            if os.path.exists(log_file):
                os.remove(log_file)
            for f in snapshots:
                if os.path.exists(f):
                    os.remove(f)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Data cleared")
        elif self.path == "/scenarios":
            # GET /scenarios - список доступных сценариев
            if not self.server.scenario_manager:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"error": "Scenario manager not initialized"}')
                return

            scenarios = self.server.scenario_manager.get_available_scenarios()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"scenarios": scenarios}).encode())
        elif self.path.startswith("/scenarios/") and "/status" in self.path:
            # GET /scenarios/{id}/status - статус выполнения сценария
            scenario_id = self.path.split("/scenarios/")[1].split("/status")[0]
            if not self.server.scenario_manager:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"error": "Scenario manager not initialized"}')
                return

            status = self.server.scenario_manager.get_scenario_status(scenario_id)
            self.send_response(200 if status.get("success", False) else 404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        elif self.path == "/scenarios/status":
            # GET /scenarios/status - статус всех сценариев
            if not self.server.scenario_manager:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"error": "Scenario manager not initialized"}')
                return

            all_status = self.server.scenario_manager.get_all_statuses()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(all_status).encode())
        elif self.path == "/environment/config":
            # GET /environment/config - текущая конфигурация среды
            if not self.server.environment_config_manager:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"error": "Environment config manager not initialized"}')
                return

            config_summary = self.server.environment_config_manager.get_config_summary()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"config": config_summary}).encode())
        elif self.path == "/analysis/sensitivity":
            # GET /analysis/sensitivity - анализ чувствительности к типам событий
            if not self.server.impact_analyzer:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"error": "Impact analyzer not initialized"}')
                return

            # Получаем текущее состояние
            try:
                self_state = SelfState().load_latest_snapshot()
            except FileNotFoundError:
                self_state = SelfState()

            sensitivity = self.server.impact_analyzer.get_sensitivity_analysis(self_state)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(sensitivity).encode())
        elif self.path.startswith("/adaptation/rollback/options"):
            # GET /adaptation/rollback/options — получить доступные варианты отката
            try:
                from src.adaptation.adaptation import AdaptationManager

                adaptation_manager = AdaptationManager()

                # Загружаем состояние
                try:
                    self_state = SelfState().load_latest_snapshot()
                except FileNotFoundError:
                    self_state = SelfState()

                # Получаем варианты отката
                options = adaptation_manager.get_rollback_options(self_state)

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"options": options, "total_options": len(options)}).encode()
                )

            except Exception as e:
                logger.error(f"Error getting rollback options: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif self.path.startswith("/adaptation/history"):
            # GET /adaptation/history — получить историю адаптаций
            try:
                # Загружаем состояние
                try:
                    self_state = SelfState().load_latest_snapshot()
                except FileNotFoundError:
                    self_state = SelfState()

                # Получаем историю адаптаций
                history = getattr(self_state, "adaptation_history", [])

                # Ограничиваем размер ответа (последние 20 записей)
                recent_history = history[-20:] if len(history) > 20 else history

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {
                            "history": recent_history,
                            "total_entries": len(history),
                            "returned_entries": len(recent_history),
                        }
                    ).encode()
                )

            except Exception as e:
                logger.error(f"Error getting adaptation history: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())


        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Unknown endpoint")

    def do_POST(self):
        """
        Поддерживаемые эндпоинты:
        /event — добавить одиночное событие
        /events — добавить пакет событий
        /scenarios/{id}/start — запустить сценарий
        /scenarios/{id}/stop — остановить сценарий
        /scenarios/stop-all — остановить все сценарии
        /state — частичное обновление состояния
        /state/reset — сброс состояния
        /environment/config — обновить конфигурацию среды
        /environment/config/reset — сброс конфигурации среды
        /environment/mode/{mode} — установить режим активности
        /analysis/impact — анализ одиночного события
        /analysis/impact-batch — анализ пакета событий
        """
        # POST /event — одиночное событие (существующий эндпоинт)
        if self.path == "/event":
            self._handle_single_event()
        # POST /events — пакет событий
        elif self.path == "/events":
            self._handle_batch_events()
        # POST /scenarios/{id}/start — запуск сценария
        elif self.path.startswith("/scenarios/") and self.path.endswith("/start"):
            scenario_id = self.path.split("/scenarios/")[1].split("/start")[0]
            self._handle_scenario_start(scenario_id)
        # POST /scenarios/{id}/stop — остановка сценария
        elif self.path.startswith("/scenarios/") and self.path.endswith("/stop"):
            scenario_id = self.path.split("/scenarios/")[1].split("/stop")[0]
            self._handle_scenario_stop(scenario_id)
        # POST /scenarios/stop-all — остановка всех сценариев
        elif self.path == "/scenarios/stop-all":
            self._handle_stop_all_scenarios()
        # POST /state — обновление состояния
        elif self.path == "/state":
            self._handle_state_update()
        # POST /state/reset — сброс состояния
        elif self.path == "/state/reset":
            self._handle_state_reset()
        # POST /environment/config — обновление конфигурации среды
        elif self.path == "/environment/config":
            self._handle_environment_config_update()
        # POST /environment/config/reset — сброс конфигурации среды
        elif self.path == "/environment/config/reset":
            self._handle_environment_config_reset()
        # POST /environment/mode/{mode} — установка режима
        elif self.path.startswith("/environment/mode/"):
            mode = self.path.split("/environment/mode/")[1]
            self._handle_environment_mode_set(mode)
        # POST /analysis/impact — анализ одиночного события
        elif self.path == "/analysis/impact":
            self._handle_impact_analysis()
        # POST /analysis/impact-batch — анализ пакета событий
        elif self.path == "/analysis/impact-batch":
            self._handle_batch_impact_analysis()
        # POST /adaptation/rollback — выполнить откат адаптаций
        elif self.path == "/adaptation/rollback":
            self._handle_adaptation_rollback()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Unknown endpoint")

    def _handle_single_event(self):
        """Обработка POST /event"""
        if not self.server.event_queue:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"No event queue configured")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        event_type = payload.get("type")
        if not isinstance(event_type, str):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"'type' is required")
            return

        intensity = float(payload.get("intensity", 0.0))
        timestamp = float(payload.get("timestamp", time.time()))
        metadata = payload.get("metadata") or {}

        try:
            logger.debug(f"Получен POST /event: type='{event_type}', intensity={intensity}")
            event = Event(
                type=event_type,
                intensity=intensity,
                timestamp=timestamp,
                metadata=metadata,
            )
            self.server.event_queue.push(event)
            logger.debug(f"Event PUSHED to queue. Size now: {self.server.event_queue.size()}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Event accepted")
        except Exception as exc:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"Invalid event: {exc}".encode("utf-8"))

    def _handle_batch_events(self):
        """Обработка POST /events"""
        if not self.server.event_queue:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"No event queue configured")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"[]"
        try:
            events_data = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        if not isinstance(events_data, list):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Expected array of events")
            return

        accepted_count = 0
        errors = []

        for i, event_data in enumerate(events_data):
            try:
                event_type = event_data.get("type")
                if not isinstance(event_type, str):
                    errors.append(f"Event {i}: 'type' is required")
                    continue

                intensity = float(event_data.get("intensity", 0.0))
                timestamp = float(event_data.get("timestamp", time.time()))
                metadata = event_data.get("metadata") or {}

                event = Event(
                    type=event_type,
                    intensity=intensity,
                    timestamp=timestamp,
                    metadata=metadata,
                )
                self.server.event_queue.push(event)
                accepted_count += 1

            except Exception as exc:
                errors.append(f"Event {i}: {exc}")

        response = {
            "accepted_count": accepted_count,
            "total_count": len(events_data),
            "errors": errors,
        }

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def _handle_scenario_start(self, scenario_id: str):
        """Обработка запуска сценария"""
        if not self.server.scenario_manager:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Scenario manager not initialized"}')
            return

        result = self.server.scenario_manager.start_scenario(scenario_id)
        status_code = 200 if result.get("success", False) else 400
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _handle_scenario_stop(self, scenario_id: str):
        """Обработка остановки сценария"""
        if not self.server.scenario_manager:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Scenario manager not initialized"}')
            return

        result = self.server.scenario_manager.stop_scenario(scenario_id)
        status_code = 200 if result.get("success", False) else 400
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _handle_stop_all_scenarios(self):
        """Обработка остановки всех сценариев"""
        if not self.server.scenario_manager:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Scenario manager not initialized"}')
            return

        result = self.server.scenario_manager.stop_all_scenarios()
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _handle_state_update(self):
        """Обработка обновления состояния"""
        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            updates = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        # Получаем текущее состояние
        try:
            self_state = SelfState().load_latest_snapshot()
        except FileNotFoundError:
            self_state = SelfState()

        # Применяем контролируемые обновления
        updated_fields = []
        errors = []

        # Контролируемые параметры для обновления
        allowed_updates = {
            "energy": lambda x: max(0.0, min(100.0, float(x))),  # Ограничение диапазона
            "stability": lambda x: max(0.0, min(1.0, float(x))),
            "integrity": lambda x: max(0.0, min(1.0, float(x))),  # Только снижение
        }

        for field, value in updates.items():
            if field in allowed_updates:
                try:
                    new_value = allowed_updates[field](value)
                    old_value = getattr(self_state, field)

                    # Дополнительные ограничения
                    if field == "integrity" and new_value > old_value:
                        errors.append(f"Cannot increase integrity (current: {old_value})")
                        continue

                    setattr(self_state, field, new_value)
                    updated_fields.append(
                        {"field": field, "old_value": old_value, "new_value": new_value}
                    )
                except Exception as e:
                    errors.append(f"Invalid value for {field}: {e}")
            else:
                errors.append(f"Field '{field}' not allowed for update")

        if updated_fields:
            # Сохраняем обновленное состояние
            self_state.save_snapshot()
            logger.info(f"State updated via API: {updated_fields}")

        response = {"updated_fields": updated_fields, "errors": errors}

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def _handle_state_reset(self):
        """Обработка сброса состояния"""
        try:
            # Создаем новое состояние со значениями по умолчанию
            reset_state = SelfState()

            # Сохраняем его как новый snapshot
            reset_state.save_snapshot()

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "message": "State reset to defaults",
                        "new_state": {
                            "energy": reset_state.energy,
                            "stability": reset_state.stability,
                            "integrity": reset_state.integrity,
                            "ticks": reset_state.ticks,
                        },
                    }
                ).encode()
            )
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Reset failed: {e}".encode())

    def _handle_environment_config_update(self):
        """Обработка обновления конфигурации среды"""
        if not self.server.environment_config_manager:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Environment config manager not initialized"}')
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            updates = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        result = self.server.environment_config_manager.update_config(updates)
        status_code = 200 if result.get("success", False) else 400
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _handle_environment_config_reset(self):
        """Обработка сброса конфигурации среды"""
        if not self.server.environment_config_manager:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Environment config manager not initialized"}')
            return

        result = self.server.environment_config_manager.reset_config()
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _handle_environment_mode_set(self, mode: str):
        """Обработка установки режима активности среды"""
        if not self.server.environment_config_manager:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Environment config manager not initialized"}')
            return

        available_modes = self.server.environment_config_manager.get_available_modes()
        if mode not in available_modes:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {"error": f"Unknown mode '{mode}'", "available_modes": available_modes}
                ).encode()
            )
            return

        result = self.server.environment_config_manager.update_config({"activity_mode": mode})
        status_code = 200 if result.get("success", False) else 500
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _handle_impact_analysis(self):
        """Обработка анализа одиночного события"""
        if not self.server.impact_analyzer:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Impact analyzer not initialized"}')
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            event_data = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        # Получаем текущее состояние
        try:
            self_state = SelfState().load_latest_snapshot()
        except FileNotFoundError:
            self_state = SelfState()

        # Создаем событие для анализа
        try:
            event = Event(
                type=event_data.get("type", "noise"),
                intensity=float(event_data.get("intensity", 0.0)),
                timestamp=float(event_data.get("timestamp", time.time())),
                metadata=event_data.get("metadata", {}),
            )
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"Invalid event data: {e}".encode())
            return

        # Анализируем воздействие
        prediction = self.server.impact_analyzer.analyze_single_event(event, self_state)

        response = {
            "event": {"type": prediction.event.type, "intensity": prediction.event.intensity},
            "prediction": {
                "meaning_significance": prediction.meaning_significance,
                "impact": prediction.meaning_impact,
                "final_energy": prediction.final_energy,
                "final_stability": prediction.final_stability,
                "final_integrity": prediction.final_integrity,
                "response_pattern": prediction.response_pattern,
                "confidence": prediction.confidence,
            },
        }

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def _handle_batch_impact_analysis(self):
        """Обработка анализа пакета событий"""
        if not self.server.impact_analyzer:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Impact analyzer not initialized"}')
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"[]"
        try:
            events_data = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        if not isinstance(events_data, list):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Expected array of events")
            return

        # Получаем текущее состояние
        try:
            self_state = SelfState().load_latest_snapshot()
        except FileNotFoundError:
            self_state = SelfState()

        # Создаем события для анализа
        events = []
        for event_data in events_data:
            try:
                event = Event(
                    type=event_data.get("type", "noise"),
                    intensity=float(event_data.get("intensity", 0.0)),
                    timestamp=float(event_data.get("timestamp", time.time())),
                    metadata=event_data.get("metadata", {}),
                )
                events.append(event)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f"Invalid event in batch: {e}".encode())
                return

        # Анализируем воздействие пакета
        analysis = self.server.impact_analyzer.analyze_batch_events(events, self_state)

        response = {
            "batch_info": {
                "event_count": len(events),
                "cumulative_impact": analysis.cumulative_impact,
                "final_state": analysis.final_state,
                "risk_assessment": analysis.risk_assessment,
            },
            "recommendations": analysis.recommendations,
            "predictions": [
                {
                    "event": {"type": pred.event.type, "intensity": pred.event.intensity},
                    "meaning_significance": pred.meaning_significance,
                    "impact": pred.meaning_impact,
                    "final_state": {
                        "energy": pred.final_energy,
                        "stability": pred.final_stability,
                        "integrity": pred.final_integrity,
                    },
                    "response_pattern": pred.response_pattern,
                    "confidence": pred.confidence,
                }
                for pred in analysis.predictions
            ],
        }

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def _handle_adaptation_rollback(self):
        """Обработка POST /adaptation/rollback — откат адаптаций"""
        from src.adaptation.adaptation import AdaptationManager
        from src.observability.structured_logger import StructuredLogger

        # Получаем тело запроса
        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            request_data = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        # Валидируем параметры запроса
        rollback_type = request_data.get("type")  # "timestamp" или "steps"
        if rollback_type not in ["timestamp", "steps"]:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "type must be 'timestamp' or 'steps'"}).encode())
            return

        # Загружаем состояние
        try:
            self_state = SelfState().load_latest_snapshot()
        except FileNotFoundError:
            self_state = SelfState()

        # Создаем менеджеры
        adaptation_manager = AdaptationManager()
        structured_logger = StructuredLogger()

        try:
            if rollback_type == "timestamp":
                # Откат к timestamp
                timestamp = request_data.get("timestamp")
                if not isinstance(timestamp, (int, float)):
                    raise ValueError("timestamp must be a number")

                result = adaptation_manager.rollback_to_timestamp(
                    timestamp, self_state, structured_logger
                )

            elif rollback_type == "steps":
                # Откат на N шагов
                steps = request_data.get("steps")
                if not isinstance(steps, int) or steps <= 0:
                    raise ValueError("steps must be a positive integer")

                result = adaptation_manager.rollback_steps(steps, self_state, structured_logger)

            if result["success"]:
                # Сохраняем измененное состояние
                self_state.save_snapshot()

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())

        except ValueError as e:
            logger.error(f"Validation error in adaptation rollback: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

        except Exception as e:
            logger.error(f"Error in adaptation rollback: {e}")
            structured_logger.log_error("adaptation_rollback", e)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_request(self, code, size=-1):  # pragma: no cover
        if self.server.dev_mode:
            try:
                logger.debug(Fore.CYAN + "=" * 80 + Style.RESET_ALL)
                logger.debug(Fore.GREEN + "ВХОДЯЩИЙ HTTP-ЗАПРОС" + Style.RESET_ALL)
                logger.debug(
                    Fore.YELLOW + f"Время: {self.log_date_time_string()}" + Style.RESET_ALL
                )
                logger.debug(Fore.YELLOW + f"Клиент IP: {self.client_address[0]}" + Style.RESET_ALL)
                logger.debug(Fore.YELLOW + f"Запрос: {self.requestline}" + Style.RESET_ALL)
                logger.debug(Fore.MAGENTA + f"Статус ответа: {code}" + Style.RESET_ALL)
                if isinstance(size, (int, float)) and size > 0:
                    logger.debug(Fore.MAGENTA + f"Размер ответа: {size} байт" + Style.RESET_ALL)
                logger.debug(Fore.CYAN + "=" * 80 + Style.RESET_ALL)
            except UnicodeEncodeError:
                # Fallback to plain text if color output fails
                logger.debug("=" * 80)
                logger.debug("ВХОДЯЩИЙ HTTP-ЗАПРОС")
                logger.debug(f"Время: {self.log_date_time_string()}")
                logger.debug(f"Клиент IP: {self.client_address[0]}")
                logger.debug(f"Запрос: {self.requestline}")
                logger.debug(f"Статус ответа: {code}")
                if isinstance(size, (int, float)) and size > 0:
                    logger.debug(f"Размер ответа: {size} байт")
                logger.debug("=" * 80)
            sys.stdout.flush()


def start_api_server(event_queue, dev_mode):
    global server
    server = StoppableHTTPServer((HOST, PORT), LifeHandler)
    # self_state больше не передается - API читает из snapshots
    server.event_queue = event_queue
    server.dev_mode = dev_mode

    # Инициализация компонентов расширенного API среды
    try:
        server.scenario_manager = ScenarioManager(event_queue)
        server.impact_analyzer = ImpactAnalyzer()
        server.environment_config_manager = EnvironmentConfigManager()
        logger.info("Extended environment API components initialized")
    except Exception as e:
        logger.error(f"Failed to initialize extended API components: {e}")
        logger.warning("Extended API features will not be available")

    logger.info(f"API server running on http://{HOST}:{PORT}")
    server.serve_forever()


def reloader_thread():  # pragma: no cover
    """
    Отслеживает изменения в исходных файлах проекта и перезагружает их "горячо".
    Перезапускает API сервер при изменении модулей.
    """
    global self_state, server, api_thread, monitor, log, loop_thread, loop_stop, config, event_queue

    # Файлы для отслеживания
    files_to_watch = [
        "src/main_server_api.py",
        "src/monitor/console.py",
        "src/runtime/loop.py",
        "src/state/self_state.py",
        "src/environment/event.py",
        "src/environment/event_queue.py",
        "src/environment/generator.py",
    ]
    mtime_dict = {}

    # Инициализация времени модификации файлов
    for f in files_to_watch:
        try:
            mtime_dict[f] = os.stat(f).st_mtime
            logger.debug(f"Watching {f}")
        except Exception as e:
            logger.error(f"Error watching {f}: {e}")

    logger.info("Reloader initialized, starting poll loop")

    while True:
        time.sleep(1)
        changed = False

        # Проверка изменений
        for f in files_to_watch:
            try:
                if os.stat(f).st_mtime != mtime_dict[f]:
                    changed = True
                    mtime_dict[f] = os.stat(f).st_mtime
            except FileNotFoundError:
                continue

        if changed:
            logger.info("Detected change, reloading modules...")

            # Остановка API сервера
            if server:
                server.shutdown()
                if api_thread:
                    api_thread.join(timeout=5.0)
                    if api_thread.is_alive():
                        logger.warning(
                            "[RELOAD] api_thread не завершился за 5 секунд, продолжается перезагрузка"
                        )

            # Перезагрузка модулей
            import environment.event as event_module
            import environment.event_queue as event_queue_module
            import environment.generator as generator_module
            import monitor.console as console_module
            import runtime.loop as loop_module
            import state.self_state as state_module

            importlib.reload(console_module)
            importlib.reload(loop_module)
            importlib.reload(state_module)
            importlib.reload(event_module)
            importlib.reload(event_queue_module)
            importlib.reload(generator_module)

            logger.debug(
                f"Reloaded loop_module.run_loop: firstlineno={loop_module.run_loop.__code__.co_firstlineno}, argcount={loop_module.run_loop.__code__.co_argcount}"
            )
            logger.debug(f"New run_loop code file: {loop_module.run_loop.__code__.co_filename}")

            # Обновляем ссылки на функции
            monitor = console_module.monitor
            log = console_module.log
            run_loop = loop_module.run_loop
            try:
                self_state = state_module.SelfState().load_latest_snapshot()
            except FileNotFoundError:
                self_state = state_module.SelfState()

            # Перезапуск API сервера
            api_thread = threading.Thread(
                target=start_api_server,
                args=(event_queue, True),
                daemon=True,
            )
            api_thread.start()

            logger.info("Modules reloaded and server restarted")

            # Restart runtime loop
            if loop_thread and loop_thread.is_alive():
                loop_stop.set()
                loop_thread.join(timeout=5.0)
                logger.info("[RELOAD] Old loop stopped")

            loop_stop = threading.Event()
            loop_thread = threading.Thread(
                target=run_loop,
                args=(
                    self_state,
                    monitor,
                    config["tick_interval"],
                    config["snapshot_period"],
                    loop_stop,
                    event_queue,
                    False,  # disable_weakness_penalty
                    False,  # disable_structured_logging
                    False,  # disable_learning
                    False,  # disable_adaptation
                    10,  # log_flush_period_ticks
                    config["enable_profiling"],
                ),
                daemon=True,
            )
            loop_thread.start()
            logger.info("[RELOAD] New loop started")


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear-data", type=str, default="no")
    parser.add_argument("--tick-interval", type=float, default=1.0)
    parser.add_argument("--snapshot-period", type=int, default=10)
    parser.add_argument(
        "--dev", action="store_true", help="Enable development mode with auto-reload"
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable runtime loop profiling with cProfile",
    )
    args = parser.parse_args()
    dev_mode = args.dev

    # Настройка уровня логирования в зависимости от режима
    setup_logging(verbose=dev_mode)

    config = {
        "tick_interval": args.tick_interval,
        "snapshot_period": args.snapshot_period,
        "enable_profiling": args.profile,
    }

    if args.clear_data.lower() == "yes":
        logger.info("Очистка данных при старте...")
        log_file = "data/tick_log.jsonl"
        snapshots = glob.glob("data/snapshots/*.json")
        if os.path.exists(log_file):
            os.remove(log_file)
        for f in snapshots:
            if os.path.exists(f):
                os.remove(f)

    try:
        self_state = SelfState().load_latest_snapshot()
    except FileNotFoundError:
        self_state = SelfState()

    server = None
    api_thread = None

    # Инициализация Environment
    event_queue = EventQueue()

    if args.dev:
        logger.info("--dev mode enabled, starting reloader")
        threading.Thread(target=reloader_thread, daemon=True).start()

    # Start API thread
    api_thread = threading.Thread(
        target=start_api_server, args=(event_queue, dev_mode), daemon=True
    )
    api_thread.start()

    # Start loop thread
    loop_stop = threading.Event()
    loop_thread = threading.Thread(
        target=run_loop,
        args=(
            self_state,
            monitor,
            config["tick_interval"],
            config["snapshot_period"],
            loop_stop,
            event_queue,
            False,  # disable_weakness_penalty
            False,  # disable_structured_logging
            False,  # disable_learning
            False,  # disable_adaptation
            False,  # disable_clarity_moments
            True,  # enable_memory_hierarchy
            True,  # enable_silence_detection
            10,  # log_flush_period_ticks
            config["enable_profiling"],
        ),
        daemon=True,
    )
    loop_thread.start()

    loop_thread.join()
    logger.info("Loop ended. Server still running. Press Enter to stop.")
    input()
    logger.info("\nЖизнь завершена. Финальное состояние:")
    logger.info(str(self_state))
