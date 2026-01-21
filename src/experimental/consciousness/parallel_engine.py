"""
Parallel Consciousness Engine - Compatibility Layer

Backward compatibility layer for the old consciousness API
using the new AdaptiveProcessingManager.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

from src.experimental.adaptive_processing_manager import (
    AdaptiveProcessingManager,
    ProcessingMode,
    ProcessingResult
)


class ProcessingMode(Enum):
    """Processing modes for consciousness engine."""
    SEQUENTIAL = "sequential"
    THREADING = "threading"
    ASYNC = "async"
    MULTIPROCESS = "multiprocess"


@dataclass
class ProcessingResult:
    """Result of a processing operation."""
    task_id: str
    result: Any
    processing_time: float
    success: bool
    error: Optional[str] = None


class ParallelConsciousnessEngine:
    """Engine for parallel consciousness processing."""

    def __init__(self, max_workers: int = 4, mode: ProcessingMode = ProcessingMode.THREADING):
        self.max_workers = max_workers
        self.mode = mode
        self.adaptive_manager = AdaptiveProcessingManager()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers) if mode == ProcessingMode.THREADING else None

    async def process_async(self, tasks: List[Dict[str, Any]]) -> List[ProcessingResult]:
        """Process tasks asynchronously."""
        if self.mode != ProcessingMode.ASYNC:
            return await self._process_with_executor(tasks)

        results = []
        start_time = time.time()

        # Process tasks concurrently using adaptive manager
        for task in tasks:
            try:
                result = await self._process_single_task_async(task)
                processing_time = time.time() - start_time

                results.append(ProcessingResult(
                    task_id=task.get('id', f'task_{len(results)}'),
                    result=result,
                    processing_time=processing_time,
                    success=True
                ))
            except Exception as e:
                processing_time = time.time() - start_time
                results.append(ProcessingResult(
                    task_id=task.get('id', f'task_{len(results)}'),
                    result=None,
                    processing_time=processing_time,
                    success=False,
                    error=str(e)
                ))

        return results

    def process_sync(self, tasks: List[Dict[str, Any]]) -> List[ProcessingResult]:
        """Process tasks synchronously."""
        results = []

        for task in tasks:
            start_time = time.time()
            task_id = task.get('id', f'task_{len(results)}')

            try:
                result = self._process_single_task_sync(task)
                processing_time = time.time() - start_time

                results.append(ProcessingResult(
                    task_id=task_id,
                    result=result,
                    processing_time=processing_time,
                    success=True
                ))
            except Exception as e:
                processing_time = time.time() - start_time
                results.append(ProcessingResult(
                    task_id=task_id,
                    result=None,
                    processing_time=processing_time,
                    success=False,
                    error=str(e)
                ))

        return results

    async def _process_with_executor(self, tasks: List[Dict[str, Any]]) -> List[ProcessingResult]:
        """Process tasks using thread/process executor."""
        if not self.executor:
            return self.process_sync(tasks)

        loop = asyncio.get_event_loop()
        results = []

        # Submit all tasks to executor
        futures = [
            loop.run_in_executor(self.executor, self._process_single_task_sync, task)
            for task in tasks
        ]

        # Wait for all results
        task_results = await asyncio.gather(*futures, return_exceptions=True)

        for i, result in enumerate(task_results):
            task_id = tasks[i].get('id', f'task_{i}')

            if isinstance(result, Exception):
                results.append(ProcessingResult(
                    task_id=task_id,
                    result=None,
                    processing_time=0.0,
                    success=False,
                    error=str(result)
                ))
            else:
                results.append(ProcessingResult(
                    task_id=task_id,
                    result=result,
                    processing_time=0.0,
                    success=True
                ))

        return results

    def _process_single_task_sync(self, task: Dict[str, Any]) -> Any:
        """Process a single task synchronously."""
        # Simulate some processing time
        time.sleep(0.01)

        # Extract task parameters
        operation = task.get('operation', 'default')
        data = task.get('data', {})

        # Perform mock processing based on operation
        if operation == 'analyze':
            return self._mock_analysis(data)
        elif operation == 'transform':
            return self._mock_transformation(data)
        else:
            return {'result': 'processed', 'input': data}

    async def _process_single_task_async(self, task: Dict[str, Any]) -> Any:
        """Process a single task asynchronously."""
        # Simulate async processing
        await asyncio.sleep(0.01)

        return self._process_single_task_sync(task)

    def _mock_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock analysis operation."""
        # Use adaptive manager for analysis
        self.adaptive_manager.analyze_system_conditions()

        return {
            'analysis_type': 'consciousness_metrics',
            'input_size': len(str(data)),
            'confidence': 0.85,
            'patterns_found': ['pattern_1', 'pattern_2'],
            'adaptive_state': self.adaptive_manager.get_current_state().value
        }

    def _mock_transformation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock transformation operation."""
        return {
            'transformation_type': 'data_normalization',
            'original_keys': list(data.keys()),
            'processed_keys': [f'processed_{k}' for k in data.keys()],
            'quality_score': 0.92
        }

    def shutdown(self):
        """Shutdown the engine and cleanup resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None


# Global instance
engine = ParallelConsciousnessEngine()</contents>
</xai:function_call=FileWrite>