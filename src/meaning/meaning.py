from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Meaning:
    """
    Интерпретированное значение события.

    Структура:
    - event_id: связь с исходным событием (опционально)
    - significance: субъективная важность [0.0, 1.0]
    - impact: дельты изменений для параметров состояния
    """

    event_id: Optional[str] = None
    significance: float = 0.0  # Важность: 0.0 (игнорируется) до 1.0 (критично)
    impact: Dict[str, float] = field(
        default_factory=dict
    )  # {"energy": -0.1, "stability": -0.02, "integrity": 0.0}

    def __post_init__(self):
        # Валидация significance
        if not 0.0 <= self.significance <= 1.0:
            raise ValueError(
                f"significance должен быть в диапазоне [0.0, 1.0], получено: {self.significance}"
            )
