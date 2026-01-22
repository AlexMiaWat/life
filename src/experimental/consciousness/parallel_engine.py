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
import threading

from src.experimental.adaptive_processing_manager import (
    AdaptiveProcessingManager,
    ProcessingMode
)


class ConsciousnessState(Enum):
    """Enumeration of consciousness states for backward compatibility."""
    BASIC_AWARENESS = "basic_awareness"
    SELF_REFLECTION = "self_reflection"
    META_COGNITION = "meta_cognition"
    FLOW_STATE = "flow_state"
    DEEP_REFLECTION = "deep_reflection"
    META_AWARENESS = "meta_awareness"
    ENLIGHTENMENT = "enlightenment"


@dataclass
class ConsciousnessMetrics:
    """Consciousness metrics for backward compatibility."""
    level: float = 0.0
    self_reflection_score: float = 0.0
    meta_cognition_depth: float = 0.0
    state_duration: int = 0
    transitions_count: int = 0
    last_transition_time: Optional[float] = None


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
    """Engine for parallel consciousness processing with backward compatibility."""

    def __init__(self,
                 initial_state: ConsciousnessState = ConsciousnessState.BASIC_AWARENESS,
                 initial_metrics: Optional[ConsciousnessMetrics] = None,
                 max_workers: int = 4,
                 mode: ProcessingMode = ProcessingMode.THREADING):
        # Backward compatibility attributes
        self.current_state = initial_state
        self.metrics = initial_metrics or ConsciousnessMetrics()
        self._transition_history = []
        self._lock = threading.Lock()

        # New processing capabilities
        self.max_workers = max_workers
        self.mode = mode
        # Create a dummy self_state_provider for compatibility
        def dummy_self_state_provider():
            return None
        self.adaptive_manager = AdaptiveProcessingManager(dummy_self_state_provider)
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

    # Backward compatibility methods for old consciousness API

    def transition_to_state(self, new_state: ConsciousnessState) -> None:
        """Transition to a new consciousness state."""
        with self._lock:
            old_state = self.current_state
            self.current_state = new_state
            self.metrics.transitions_count += 1
            self.metrics.last_transition_time = time.time()

            # Reset state duration for new state
            self.metrics.state_duration = 0

            # Record transition
            transition_record = {
                "from_state": old_state.name if old_state else None,
                "to_state": new_state.name,
                "timestamp": self.metrics.last_transition_time,
                "transition_id": self.metrics.transitions_count
            }
            self._transition_history.append(transition_record)

    def evaluate_consciousness_level(self) -> ConsciousnessState:
        """Evaluate current consciousness level based on metrics."""
        # Use adaptive manager's state to determine consciousness level
        adaptive_state = self.adaptive_manager.get_current_state()

        # Map adaptive states to consciousness states
        state_mapping = {
            "idle": ConsciousnessState.BASIC_AWARENESS,
            "processing": ConsciousnessState.SELF_REFLECTION,
            "analyzing": ConsciousnessState.META_COGNITION,
            "optimizing": ConsciousnessState.FLOW_STATE,
            "error": ConsciousnessState.BASIC_AWARENESS
        }

        # Use metrics to determine more advanced states
        if self.metrics.level >= 0.9 and self.metrics.meta_cognition_depth >= 0.8:
            return ConsciousnessState.ENLIGHTENMENT
        elif self.metrics.level >= 0.8 and self.metrics.meta_cognition_depth >= 0.7:
            return ConsciousnessState.META_AWARENESS
        elif self.metrics.level >= 0.7 and self.metrics.self_reflection_score >= 0.6:
            return ConsciousnessState.DEEP_REFLECTION
        elif self.metrics.level >= 0.6:
            return ConsciousnessState.FLOW_STATE
        elif self.metrics.level >= 0.4:
            return ConsciousnessState.META_COGNITION
        elif self.metrics.level >= 0.2:
            return ConsciousnessState.SELF_REFLECTION
        else:
            return ConsciousnessState.BASIC_AWARENESS

    def update_metrics(self, level: Optional[float] = None,
                      self_reflection_score: Optional[float] = None,
                      meta_cognition_depth: Optional[float] = None) -> None:
        """Update consciousness metrics."""
        with self._lock:
            if level is not None:
                self.metrics.level = level
            if self_reflection_score is not None:
                self.metrics.self_reflection_score = self_reflection_score
            if meta_cognition_depth is not None:
                self.metrics.meta_cognition_depth = meta_cognition_depth

    def increment_state_duration(self) -> None:
        """Increment the duration counter for current state."""
        with self._lock:
            self.metrics.state_duration += 1

    def get_transition_history(self) -> List[Dict[str, Any]]:
        """Get the history of state transitions."""
        with self._lock:
            return self._transition_history.copy()

    @property
    def transition_history(self) -> List[Dict[str, Any]]:
        """Get the history of state transitions (property for backward compatibility)."""
        return self.get_transition_history()

    def get_consciousness_report(self) -> Dict[str, Any]:
        """Get a comprehensive consciousness report."""
        with self._lock:
            return {
                "current_state": self.current_state.name,
                "metrics": {
                    "level": self.metrics.level,
                    "self_reflection_score": self.metrics.self_reflection_score,
                    "meta_cognition_depth": self.metrics.meta_cognition_depth,
                    "state_duration_ticks": self.metrics.state_duration,
                    "transitions_count": self.metrics.transitions_count,
                    "last_transition_time": self.metrics.last_transition_time
                },
                "transition_history": self.get_transition_history(),
                "adaptive_state": self.adaptive_manager.get_current_state().value,
                "processing_stats": self.adaptive_manager.get_processing_statistics()
            }

    def analyze_consciousness_conditions(self) -> Dict[str, Any]:
        """
        Анализировать условия сознания на основе текущих метрик и состояния.

        Returns:
            Dict с анализом условий сознания
        """
        with self._lock:
            # Анализируем текущие метрики для определения условий
            analysis = {
                "current_state": self.current_state.name,
                "level_assessment": "low" if self.metrics.level < 0.3 else "medium" if self.metrics.level < 0.7 else "high",
                "reflection_capability": "limited" if self.metrics.self_reflection_score < 0.4 else "developing" if self.metrics.self_reflection_score < 0.7 else "advanced",
                "meta_cognition_depth": "shallow" if self.metrics.meta_cognition_depth < 0.3 else "moderate" if self.metrics.meta_cognition_depth < 0.7 else "deep",
                "stability_indicators": {
                    "state_duration_ok": self.metrics.state_duration > 10,
                    "transitions_reasonable": self.metrics.transitions_count < 100,
                    "recent_transition_recent": time.time() - (self.metrics.last_transition_time or 0) < 300  # 5 minutes
                },
                "recommendations": []
            }

            # Формируем рекомендации на основе анализа
            if self.metrics.level < 0.3:
                analysis["recommendations"].append("Increase consciousness level through focused activities")
            if self.metrics.self_reflection_score < 0.4:
                analysis["recommendations"].append("Enhance self-reflection through journaling or meditation")
            if self.metrics.meta_cognition_depth < 0.3:
                analysis["recommendations"].append("Deepen meta-cognition through analytical thinking exercises")

            return analysis

    def get_current_state(self) -> ConsciousnessState:
        """
        Получить текущее состояние сознания.

        Returns:
            Текущее состояние сознания
        """
        with self._lock:
            return self.current_state