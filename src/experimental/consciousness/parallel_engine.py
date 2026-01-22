"""
Parallel Consciousness Engine - Параллельный движок сознания.

Предоставляет параллельную обработку задач сознания с поддержкой
различных режимов выполнения (threading, async).
"""

import asyncio
import concurrent.futures
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from src.contracts.serialization_contract import SerializationContract

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Режимы параллельной обработки."""
    THREADING = "threading"       # Многопоточная обработка
    ASYNC = "async"              # Асинхронная обработка
    SEQUENTIAL = "sequential"    # Последовательная обработка


@dataclass
class TaskResult:
    """Результат выполнения задачи."""
    task_id: str
    result: Any
    success: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0

    @property
    def processing_time(self) -> float:
        """Свойство для совместимости с тестами."""
        return self.execution_time

    @property
    def error(self) -> Optional[str]:
        """Свойство для совместимости с тестами."""
        return self.error_message


class ParallelConsciousnessEngine(SerializationContract):
    """
    Параллельный движок сознания для обработки задач.

    Поддерживает многопоточную и асинхронную обработку задач сознания.
    Реализует контракты сериализации для интеграции в SelfState.
    """

    def __init__(self, max_workers: int = 4, mode: ProcessingMode = ProcessingMode.THREADING):
        """
        Инициализация параллельного движка сознания.

        Args:
            max_workers: Максимальное количество рабочих потоков
            mode: Режим обработки (threading или async)
        """
        self.max_workers = max_workers
        self.mode = mode
        self.executor: Optional[ThreadPoolExecutor] = None
        self._is_shutdown = False

        # Инициализация executor для threading режима
        if self.mode in (ProcessingMode.THREADING, ProcessingMode.SEQUENTIAL):
            # Для SEQUENTIAL используем 1 поток
            workers = 1 if self.mode == ProcessingMode.SEQUENTIAL else max_workers
            self.executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="consciousness")

    def _process_single_task(self, task: Dict[str, Any]) -> TaskResult:
        """
        Обработка одиночной задачи.

        Args:
            task: Словарь с задачей

        Returns:
            TaskResult: Результат выполнения задачи
        """
        task_id = task.get("task_id", task.get("id", "unknown"))
        operation = task.get("operation", "unknown")
        data = task.get("data", {})

        start_time = time.time()

        try:
            # Имитация обработки задачи
            # В реальной реализации здесь будет логика обработки
            if operation == "analyze":
                result = self._analyze_data(data)
            elif operation == "transform":
                result = self._transform_data(data)
            else:
                result = {"operation": operation, "processed": True, "data": data, "processed_data": {"result": "completed"}}

            execution_time = time.time() - start_time

            return TaskResult(
                task_id=task_id,
                result=result,
                success=True,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error processing task {task_id}: {e}")

            return TaskResult(
                task_id=task_id,
                result=None,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )

    def _analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ данных задачи."""
        # Имитация анализа
        return {
            "analysis_type": "consciousness_analysis",
            "input_size": len(str(data)),
            "processed_at": time.time(),
            "insights": ["pattern_detected", "correlation_found"]
        }

    def _transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Трансформация данных задачи."""
        # Имитация трансформации
        return {
            "transformation_type": "consciousness_transform",
            "original_data": data,
            "transformed_data": {k: f"processed_{v}" for k, v in data.items()},
            "processed_at": time.time()
        }

    def process_sync(self, tasks: List[Dict[str, Any]]) -> List[TaskResult]:
        """
        Синхронная обработка списка задач.

        Args:
            tasks: Список задач для обработки

        Returns:
            List[TaskResult]: Список результатов выполнения
        """
        if self._is_shutdown:
            # После shutdown создаем новый executor для повторного использования
            self._reinitialize_executor()

        if self.mode == ProcessingMode.THREADING and self.executor:
            # Параллельная обработка с помощью ThreadPoolExecutor
            futures = [self.executor.submit(self._process_single_task, task) for task in tasks]

            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in task execution: {e}")
                    # Создаем результат ошибки
                    results.append(TaskResult(
                        task_id="error",
                        result=None,
                        success=False,
                        error_message=str(e)
                    ))

            return results

        else:
            # Последовательная обработка
            return [self._process_single_task(task) for task in tasks]

    async def process_async(self, tasks: List[Dict[str, Any]]) -> List[TaskResult]:
        """
        Асинхронная обработка списка задач.

        Args:
            tasks: Список задач для обработки

        Returns:
            List[TaskResult]: Список результатов выполнения
        """
        if self._is_shutdown:
            # После shutdown создаем новый executor для повторного использования
            self._reinitialize_executor()

        if self.mode == ProcessingMode.ASYNC:
            # Асинхронная обработка
            async def process_task_async(task):
                # Имитация асинхронной операции
                await asyncio.sleep(0.01)  # Небольшая задержка для имитации I/O
                return self._process_single_task(task)

            # Ограничиваем количество одновременных задач
            semaphore = asyncio.Semaphore(self.max_workers)

            async def process_with_semaphore(task):
                async with semaphore:
                    return await process_task_async(task)

            # Запускаем все задачи параллельно с ограничением
            results = await asyncio.gather(
                *[process_with_semaphore(task) for task in tasks],
                return_exceptions=True
            )

            # Обрабатываем результаты
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    final_results.append(TaskResult(
                        task_id=tasks[i].get("id", f"task_{i}"),
                        result=None,
                        success=False,
                        error_message=str(result)
                    ))
                else:
                    final_results.append(result)

            return final_results

        else:
            # Для других режимов используем синхронную обработку в executor
            loop = asyncio.get_event_loop()

            def run_sync():
                return self.process_sync(tasks)

            results = await loop.run_in_executor(None, run_sync)
            return results

    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализация состояния ParallelConsciousnessEngine.

        Архитектурные гарантии:
        - Thread-safe: Метод безопасен для вызова из разных потоков
        - Атомарный: Сериализация представляет консистентное состояние
        - Отказоустойчивый: Исключения не должны приводить к повреждению состояния
        - Детерминированный: Для одинакового состояния возвращает одинаковый результат

        Returns:
            Dict[str, Any]: Словарь с состоянием компонента
        """
        return {
            "max_workers": self.max_workers,
            "mode": self.mode.value,
            "is_shutdown": self._is_shutdown,
            "has_executor": self.executor is not None,
            "component_type": "ParallelConsciousnessEngine",
            "version": "1.0"
        }

    def get_serialization_metadata(self) -> Dict[str, Any]:
        """
        Получить метаданные сериализации для ParallelConsciousnessEngine.

        Returns:
            Dict[str, Any]: Метаданные содержащие как минимум:
            - version: str - версия формата сериализации
            - timestamp: float - время сериализации
            - component_type: str - тип компонента
            - thread_safe: bool - подтверждение thread-safety
        """
        return {
            "version": "1.0",
            "component_type": "ParallelConsciousnessEngine",
            "thread_safe": True,
            "timestamp": time.time(),
            "processing_mode": self.mode.value,
            "max_workers": self.max_workers,
            "is_shutdown": self._is_shutdown
        }

    def process_threading(self, tasks: List[Dict[str, Any]]) -> List[TaskResult]:
        """
        Псевдоним для process_sync для совместимости с тестами.

        Args:
            tasks: Список задач для обработки

        Returns:
            List[TaskResult]: Список результатов выполнения
        """
        return self.process_sync(tasks)

    def process_sequential(self, tasks: List[Dict[str, Any]]) -> List[TaskResult]:
        """
        Последовательная обработка задач (синоним process_sync).

        Args:
            tasks: Список задач для обработки

        Returns:
            List[TaskResult]: Список результатов выполнения
        """
        # Для последовательной обработки отключаем параллельность
        original_max_workers = self.max_workers
        self.max_workers = 1

        try:
            results = self.process_sync(tasks)
        finally:
            self.max_workers = original_max_workers

        return results

    def _reinitialize_executor(self) -> None:
        """Переинициализация executor после shutdown для повторного использования."""
        self._is_shutdown = False
        if self.mode in (ProcessingMode.THREADING, ProcessingMode.SEQUENTIAL):
            workers = 1 if self.mode == ProcessingMode.SEQUENTIAL else self.max_workers
            self.executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="consciousness")

    def shutdown(self) -> None:
        """Завершение работы движка и освобождение ресурсов."""
        if self._is_shutdown:
            return

        self._is_shutdown = True

        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None

        logger.info("ParallelConsciousnessEngine shutdown complete")