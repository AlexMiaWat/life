import time
from typing import List, Dict, Any

from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry
from src.state.self_state import SelfState
from src.decision.decision_recorder import DecisionRecorder
from src.decision.decision_analyzer import DecisionAnalyzer
from src.decision.response_selector import ResponseSelector


class DecisionEngine:
    """
    Движок принятия решений для системы Life.

    Декомпозирован на отдельные компоненты с четкой ответственностью:
    - DecisionRecorder: запись истории решений
    - DecisionAnalyzer: анализ паттернов и контекста
    - ResponseSelector: выбор ответа по правилам
    """

    def __init__(self, enable_logging: bool = False, adaptation_manager=None):
        """
        Инициализация движка принятия решений.

        Args:
            enable_logging: Включить логирование решений (feature flag для производительности)
            adaptation_manager: AdaptationManager для анализа адаптаций
        """
        self.recorder = DecisionRecorder(enable_logging=enable_logging)
        self.analyzer = DecisionAnalyzer(adaptation_manager=adaptation_manager)
        self.selector = ResponseSelector()

    def record_decision(self, decision_type: str, context: Dict, outcome: str = None, success: bool = None, execution_time: float = None):
        """
        Записать решение в историю.

        Делегирует запись DecisionRecorder с учетом feature flag.
        """
        # Для совместимости, извлекаем паттерн из контекста если доступен
        pattern = context.get("pattern", "unknown") if context else "unknown"
        self.recorder.record_decision(
            decision_type=decision_type,
            context=context or {},
            pattern=pattern,
            outcome=outcome,
            success=success,
            execution_time=execution_time
        )

    def get_recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получить недавние решения.

        Делегирует запрос DecisionRecorder.
        """
        records = self.recorder.get_recent_decisions(limit)
        # Конвертируем в старый формат для совместимости
        return [
            {
                "timestamp": record.timestamp,
                "type": record.decision_type,
                "context": record.context,
                "outcome": record.outcome,
                "success": record.success,
                "execution_time": record.execution_time,
                "pattern": record.pattern,
            }
            for record in records
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику принятия решений.

        Делегирует запрос DecisionRecorder.
        """
        return self.recorder.get_statistics()

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Анализ паттернов принятия решений.

        Returns:
            Анализ паттернов
        """
        return self.recorder.analyze_patterns()






def decide_response(self_state: SelfState, meaning: Meaning, enable_performance_monitoring: bool = False, adaptation_manager=None) -> str:
    """
    Выбор паттерна реакции на основе комплексного анализа.

    Создает временный экземпляр DecisionEngine для принятия решения.
    Использует декомпозированную архитектуру компонентов.

    Args:
        self_state: Текущее состояние системы
        meaning: Текущий meaning
        enable_performance_monitoring: Включить мониторинг производительности
        adaptation_manager: AdaptationManager для анализа адаптаций (опционально)

    Returns:
        Выбранный паттерн реакции
    """
    import time

    start_time = time.time() if enable_performance_monitoring else None

    # Создаем временный экземпляр DecisionEngine без логирования для производительности
    # Передаем adaptation_manager для анализа адаптаций
    decision_engine = DecisionEngine(enable_logging=False, adaptation_manager=adaptation_manager)

    activated = self_state.activated_memory or []

    # === ФАЗА 1: Анализ активированной памяти ===
    memory_analysis = decision_engine.analyzer.analyze_activated_memory(activated)

    # === ФАЗА 2: Анализ контекста системы ===
    context_analysis = decision_engine.analyzer.analyze_system_context(self_state, meaning)

    # === ФАЗА 3: Выбор паттерна по правилам ===
    pattern = decision_engine.selector.select_pattern(
        memory_analysis, context_analysis, meaning, self_state
    )

    # === ФАЗА 4: Мониторинг производительности ===
    if enable_performance_monitoring and start_time is not None:
        execution_time = time.time() - start_time
        # Можно добавить логирование или метрики здесь
        if execution_time > 0.01:  # Логируем только медленные вызовы
            print(f"DecisionEngine performance: {execution_time:.4f}s")

    return pattern








