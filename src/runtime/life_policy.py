"""
LifePolicy: единая политика "weakness/penalties" для Life.

Инкапсулирует логику определения слабости и расчета штрафов,
делая политику явной, конфигурируемой и тестируемой.
"""
from src.state.self_state import SelfState


class LifePolicy:
    """
    Политика "слабости" и штрафов для Life.
    
    Определяет пороги слабости и коэффициенты штрафов,
    применяемых когда система находится в состоянии слабости.
    """
    
    def __init__(
        self,
        weakness_threshold: float = 0.05,
        penalty_k: float = 0.02,
        stability_multiplier: float = 2.0,
        integrity_multiplier: float = 2.0,
    ):
        """
        Инициализация политики слабости.
        
        Args:
            weakness_threshold: Порог для определения слабости (по умолчанию 0.05)
            penalty_k: Коэффициент штрафа за слабость (по умолчанию 0.02)
            stability_multiplier: Множитель штрафа для stability (по умолчанию 2.0)
            integrity_multiplier: Множитель штрафа для integrity (по умолчанию 2.0)
            
        Raises:
            ValueError: Если параметры имеют некорректные значения (отрицательные или нулевые где недопустимо)
        """
        if weakness_threshold < 0:
            raise ValueError("weakness_threshold must be non-negative")
        if penalty_k < 0:
            raise ValueError("penalty_k must be non-negative")
        if stability_multiplier < 0:
            raise ValueError("stability_multiplier must be non-negative")
        if integrity_multiplier < 0:
            raise ValueError("integrity_multiplier must be non-negative")
        
        self.weakness_threshold = weakness_threshold
        self.penalty_k = penalty_k
        self.stability_multiplier = stability_multiplier
        self.integrity_multiplier = integrity_multiplier
    
    def is_weak(self, self_state: SelfState) -> bool:
        """
        Проверяет, находится ли система в состоянии слабости.
        
        Система считается слабой, если хотя бы один из параметров
        (energy/integrity/stability) <= threshold.
        
        Args:
            self_state: Состояние Life для проверки
            
        Returns:
            True если система в состоянии слабости, False иначе
        """
        return (
            self_state.energy <= self.weakness_threshold
            or self_state.integrity <= self.weakness_threshold
            or self_state.stability <= self.weakness_threshold
        )
    
    def weakness_penalty(self, dt: float) -> dict[str, float]:
        """
        Вычисляет штрафы за слабость как функцию от dt.
        
        Чистая функция без side effects, возвращает дельты для apply_delta.
        
        Args:
            dt: Прошедшее время с последнего тика (секунды)
            
        Returns:
            Словарь с дельтами для apply_delta:
            {
                "energy": -penalty,
                "stability": -penalty * stability_multiplier,
                "integrity": -penalty * integrity_multiplier,
            }
        """
        penalty = self.penalty_k * dt
        return {
            "energy": -penalty,
            "stability": -penalty * self.stability_multiplier,
            "integrity": -penalty * self.integrity_multiplier,
        }
