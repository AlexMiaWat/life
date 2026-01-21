"""
Менеджер сценариев внешних воздействий для API.

Предоставляет возможность запуска предопределенных сценариев воздействий на систему Life,
таких как кризисы, фазы восстановления, стресс-тестирование и т.д.
"""

import json
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.environment.event import Event
from src.environment.event_queue import EventQueue
from src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ScenarioStep:
    """Шаг сценария воздействия"""

    delay: float  # Задержка перед выполнением в секундах
    event: Event  # Событие для отправки
    repeat_count: int = 1  # Количество повторений события
    repeat_interval: float = 0.0  # Интервал между повторениями


@dataclass
class Scenario:
    """Сценарий внешних воздействий"""

    id: str
    name: str
    description: str
    steps: List[ScenarioStep]
    duration: Optional[float] = None  # Общая длительность сценария (None = до остановки)
    auto_stop: bool = True  # Автоматическая остановка по завершению


class ScenarioExecution:
    """Выполнение сценария"""

    def __init__(self, scenario: Scenario, event_queue: EventQueue):
        self.scenario = scenario
        self.event_queue = event_queue
        self.start_time = time.time()
        self.stop_time: Optional[float] = None
        self.is_running = False
        self.current_step_index = 0
        self.executed_steps = 0
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

    def start(self) -> bool:
        """Запустить выполнение сценария"""
        if self.is_running:
            return False

        self.is_running = True
        self.thread = threading.Thread(target=self._execute_scenario, daemon=True)
        self.thread.start()
        logger.info(f"Started scenario '{self.scenario.name}' (ID: {self.scenario.id})")
        return True

    def stop(self) -> bool:
        """Остановить выполнение сценария"""
        if not self.is_running:
            return False

        self.is_running = False
        self.stop_event.set()
        self.stop_time = time.time()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

        logger.info(f"Stopped scenario '{self.scenario.name}' (ID: {self.scenario.id})")
        return True

    def get_status(self) -> Dict[str, Any]:
        """Получить статус выполнения сценария"""
        elapsed = time.time() - self.start_time
        return {
            "scenario_id": self.scenario.id,
            "scenario_name": self.scenario.name,
            "is_running": self.is_running,
            "start_time": self.start_time,
            "elapsed_time": elapsed,
            "current_step": self.current_step_index,
            "executed_steps": self.executed_steps,
            "total_steps": len(self.scenario.steps),
            "progress": (
                self.current_step_index / len(self.scenario.steps) if self.scenario.steps else 0.0
            ),
            "auto_stop": self.scenario.auto_stop,
            "duration_limit": self.scenario.duration,
        }

    def _execute_scenario(self):
        """Выполнить сценарий в отдельном потоке"""
        try:
            step_start_time = time.time()

            for step_index, step in enumerate(self.scenario.steps):
                if self.stop_event.is_set():
                    break

                self.current_step_index = step_index

                # Ждем задержку перед выполнением шага
                if step.delay > 0:
                    if self.stop_event.wait(step.delay):
                        break  # Прервано

                # Выполняем шаг (повторения)
                for repeat in range(step.repeat_count):
                    if self.stop_event.is_set():
                        break

                    # Отправляем событие в очередь
                    try:
                        self.event_queue.push(step.event)
                        self.executed_steps += 1
                        logger.debug(
                            f"Scenario '{self.scenario.name}': executed step {step_index + 1}/{len(self.scenario.steps)}, repeat {repeat + 1}/{step.repeat_count}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to execute scenario step: {e}")
                        continue

                    # Ждем интервал между повторениями
                    if repeat < step.repeat_count - 1 and step.repeat_interval > 0:
                        if self.stop_event.wait(step.repeat_interval):
                            break

                # Проверяем ограничение по длительности
                if (
                    self.scenario.duration
                    and (time.time() - self.start_time) >= self.scenario.duration
                ):
                    logger.info(f"Scenario '{self.scenario.name}' reached duration limit")
                    break

            # Автоматическая остановка если включена
            if self.scenario.auto_stop:
                self.is_running = False
                self.stop_time = time.time()
                logger.info(f"Scenario '{self.scenario.name}' completed automatically")

        except Exception as e:
            logger.error(f"Error executing scenario '{self.scenario.name}': {e}")
            self.is_running = False
        finally:
            self.is_running = False


class ScenarioManager:
    """Менеджер сценариев воздействий"""

    def __init__(self, event_queue: EventQueue):
        self.event_queue = event_queue
        self.scenarios: Dict[str, Scenario] = {}
        self.executions: Dict[str, ScenarioExecution] = {}
        self.lock = threading.RLock()

        # Загружаем встроенные сценарии
        self._load_builtin_scenarios()

    def _load_builtin_scenarios(self):
        """Загрузить встроенные сценарии"""
        self.scenarios = {
            "crisis_simulation": Scenario(
                id="crisis_simulation",
                name="Симуляция кризиса",
                description="Интенсивные негативные события для тестирования устойчивости системы",
                steps=[
                    ScenarioStep(
                        delay=0.0, event=Event(type="shock", intensity=0.8, timestamp=time.time())
                    ),
                    ScenarioStep(
                        delay=1.0, event=Event(type="decay", intensity=0.6, timestamp=time.time())
                    ),
                    ScenarioStep(
                        delay=2.0,
                        event=Event(type="social_conflict", intensity=0.7, timestamp=time.time()),
                    ),
                    ScenarioStep(
                        delay=3.0,
                        event=Event(type="existential_void", intensity=0.5, timestamp=time.time()),
                    ),
                ],
                duration=30.0,  # 30 секунд
                auto_stop=True,
            ),
            "recovery_phase": Scenario(
                id="recovery_phase",
                name="Фаза восстановления",
                description="Позитивные события для восстановления системы",
                steps=[
                    ScenarioStep(
                        delay=0.0,
                        event=Event(type="recovery", intensity=0.7, timestamp=time.time()),
                    ),
                    ScenarioStep(
                        delay=2.0,
                        event=Event(type="social_harmony", intensity=0.6, timestamp=time.time()),
                    ),
                    ScenarioStep(
                        delay=4.0,
                        event=Event(type="cognitive_clarity", intensity=0.5, timestamp=time.time()),
                    ),
                    ScenarioStep(
                        delay=6.0,
                        event=Event(type="meaning_found", intensity=0.8, timestamp=time.time()),
                    ),
                ],
                duration=20.0,
                auto_stop=True,
            ),
            "stress_test": Scenario(
                id="stress_test",
                name="Стресс-тестирование",
                description="Высокая частота разнообразных событий для нагрузочного тестирования",
                steps=[
                    ScenarioStep(
                        delay=0.0,
                        event=Event(type="noise", intensity=0.3, timestamp=time.time()),
                        repeat_count=10,
                        repeat_interval=0.1,
                    ),
                    ScenarioStep(
                        delay=2.0,
                        event=Event(type="shock", intensity=0.5, timestamp=time.time()),
                        repeat_count=5,
                        repeat_interval=0.2,
                    ),
                ],
                duration=15.0,
                auto_stop=True,
            ),
            "gentle_stimulation": Scenario(
                id="gentle_stimulation",
                name="Мягкая стимуляция",
                description="Легкие позитивные воздействия для поддержания активности",
                steps=[
                    ScenarioStep(
                        delay=0.0,
                        event=Event(type="social_presence", intensity=0.4, timestamp=time.time()),
                    ),
                    ScenarioStep(
                        delay=5.0,
                        event=Event(type="curiosity", intensity=0.3, timestamp=time.time()),
                    ),
                    ScenarioStep(
                        delay=10.0,
                        event=Event(type="insight", intensity=0.4, timestamp=time.time()),
                    ),
                    ScenarioStep(
                        delay=15.0,
                        event=Event(type="acceptance", intensity=0.3, timestamp=time.time()),
                    ),
                ],
                duration=None,  # Бесконечный до остановки
                auto_stop=False,
            ),
        }

    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """Получить список доступных сценариев"""
        with self.lock:
            return [
                {
                    "id": scenario.id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "step_count": len(scenario.steps),
                    "duration": scenario.duration,
                    "auto_stop": scenario.auto_stop,
                }
                for scenario in self.scenarios.values()
            ]

    def start_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Запустить сценарий"""
        with self.lock:
            if scenario_id not in self.scenarios:
                return {"success": False, "error": f"Scenario '{scenario_id}' not found"}

            if scenario_id in self.executions and self.executions[scenario_id].is_running:
                return {"success": False, "error": f"Scenario '{scenario_id}' is already running"}

            scenario = self.scenarios[scenario_id]
            execution = ScenarioExecution(scenario, self.event_queue)

            if execution.start():
                self.executions[scenario_id] = execution
                return {
                    "success": True,
                    "scenario_id": scenario_id,
                    "message": f"Scenario '{scenario.name}' started",
                }
            else:
                return {"success": False, "error": "Failed to start scenario"}

    def stop_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Остановить сценарий"""
        with self.lock:
            if scenario_id not in self.executions:
                return {"success": False, "error": f"Scenario '{scenario_id}' is not running"}

            execution = self.executions[scenario_id]
            if execution.stop():
                return {
                    "success": True,
                    "scenario_id": scenario_id,
                    "message": f"Scenario '{execution.scenario.name}' stopped",
                }
            else:
                return {"success": False, "error": "Failed to stop scenario"}

    def get_scenario_status(self, scenario_id: str) -> Dict[str, Any]:
        """Получить статус сценария"""
        with self.lock:
            if scenario_id not in self.executions:
                return {"success": False, "error": f"Scenario '{scenario_id}' is not running"}

            execution = self.executions[scenario_id]
            status = execution.get_status()
            status["success"] = True
            return status

    def get_all_statuses(self) -> Dict[str, Any]:
        """Получить статусы всех выполняющихся сценариев"""
        with self.lock:
            running_scenarios = {
                scenario_id: execution.get_status()
                for scenario_id, execution in self.executions.items()
                if execution.is_running
            }
            return {"running_scenarios": running_scenarios, "count": len(running_scenarios)}

    def stop_all_scenarios(self) -> Dict[str, Any]:
        """Остановить все выполняющиеся сценарии"""
        with self.lock:
            stopped_count = 0
            for execution in self.executions.values():
                if execution.is_running:
                    execution.stop()
                    stopped_count += 1

            return {
                "success": True,
                "stopped_count": stopped_count,
                "message": f"Stopped {stopped_count} scenarios",
            }
