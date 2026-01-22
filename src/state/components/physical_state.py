from dataclasses import dataclass, field
from typing import List


@dataclass
class PhysicalState:
    """
    Компонент состояния, отвечающий за физические параметры системы Life.

    Включает энергию, целостность, стабильность и связанные метрики.
    """

    # Основные физические параметры
    energy: float = 100.0      # Уровень энергии [0, 100]
    integrity: float = 1.0     # Целостность системы [0, 1]
    stability: float = 1.0     # Стабильность системы [0, 2]

    # Параметры нагрузки и стресса
    fatigue: float = 0.0       # Уровень усталости [0, 100]
    tension: float = 0.0       # Уровень напряжения [0, 100]

    # История для анализа трендов
    energy_history: List[float] = field(default_factory=list)
    stability_history: List[float] = field(default_factory=list)

    # Константы для валидации
    ENERGY_MIN = 0.0
    ENERGY_MAX = 100.0
    INTEGRITY_MIN = 0.0
    INTEGRITY_MAX = 1.0
    STABILITY_MIN = 0.0
    STABILITY_MAX = 2.0
    FATIGUE_MIN = 0.0
    FATIGUE_MAX = 100.0
    TENSION_MIN = 0.0
    TENSION_MAX = 100.0

    def update_energy(self, delta: float) -> None:
        """Обновляет уровень энергии с валидацией."""
        self.energy = max(self.ENERGY_MIN, min(self.ENERGY_MAX, self.energy + delta))
        self._update_history()

    def update_stability(self, delta: float) -> None:
        """Обновляет уровень стабильности с валидацией."""
        self.stability = max(self.STABILITY_MIN, min(self.STABILITY_MAX, self.stability + delta))
        self._update_stability_history()

    def _update_history(self) -> None:
        """Обновляет историю энергии (оптимизировано, хранит последние 100 значений)."""
        self.energy_history.append(self.energy)
        if len(self.energy_history) > 100:
            self.energy_history.pop(0)

    def _update_stability_history(self) -> None:
        """Обновляет историю стабильности (оптимизировано, хранит последние 100 значений)."""
        self.stability_history.append(self.stability)
        if len(self.stability_history) > 100:
            self.stability_history.pop(0)

    def get_energy_trend(self) -> float:
        """Возвращает тренд изменения энергии (положительный - рост, отрицательный - падение)."""
        if len(self.energy_history) < 2:
            return 0.0
        return self.energy_history[-1] - self.energy_history[-2]

    def get_stability_trend(self) -> float:
        """Возвращает тренд изменения стабильности."""
        if len(self.stability_history) < 2:
            return 0.0
        return self.stability_history[-1] - self.stability_history[-2]

    def is_critical_energy(self) -> bool:
        """Проверяет, находится ли энергия в критическом состоянии."""
        return self.energy < 20.0

    def is_high_stress(self) -> bool:
        """Проверяет, находится ли система в состоянии высокого стресса."""
        return self.fatigue > 70.0 or self.tension > 70.0