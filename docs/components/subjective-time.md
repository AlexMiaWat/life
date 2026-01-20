# Subjective Time (Субъективное время)

## Обзор

Модуль `subjective_time` реализует модель субъективного времени для системы Life. Субъективное время — это **метрика** (не управляющий цикл), которая обеспечивает детерминированное, монотонное отображение физического времени (`dt`) в субъективное время на основе состояния системы и сигналов.

## Философия

Субъективное время отражает восприятие времени системой:
- **Высокая интенсивность событий** → время течет быстрее (положительный эффект)
- **Низкая стабильность** → время течет медленнее (отрицательный эффект)
- Субъективное время всегда **монотонно** и **неотрицательно**

## API

### `compute_subjective_time_rate()`

Вычисляет множитель скорости субъективного времени.

```python
def compute_subjective_time_rate(
    *,
    base_rate: float,
    intensity: float,
    stability: float,
    intensity_coeff: float,
    stability_coeff: float,
    rate_min: float,
    rate_max: float,
) -> float:
```

**Параметры:**
- `base_rate` (float): Базовая скорость субъективного времени (обычно 1.0)
- `intensity` (float): Интенсивность последнего события [0..1]
- `stability` (float): Стабильность системы [0..1]
- `intensity_coeff` (float): Коэффициент влияния интенсивности
- `stability_coeff` (float): Коэффициент влияния стабильности
- `rate_min` (float): Минимальная скорость (обычно 0.1)
- `rate_max` (float): Максимальная скорость (обычно 3.0)

**Возвращает:**
- Множитель скорости субъективного времени в диапазоне [rate_min, rate_max]

**Формула:**
```
rate = base_rate + intensity_coeff * intensity + stability_coeff * (stability - 1.0)
rate = clamp(rate, rate_min, rate_max)
```

### `compute_subjective_dt()`

Вычисляет приращение субъективного времени для физического интервала времени.

```python
def compute_subjective_dt(
    *,
    dt: float,
    base_rate: float,
    intensity: float,
    stability: float,
    intensity_coeff: float,
    stability_coeff: float,
    rate_min: float,
    rate_max: float,
) -> float:
```

**Параметры:**
- `dt` (float): Физический интервал времени в секундах (≥ 0)
- Остальные параметры аналогичны `compute_subjective_time_rate()`

**Возвращает:**
- Приращение субъективного времени в секундах

**Формула:**
```
rate = compute_subjective_time_rate(...)
subjective_dt = dt * rate
```

## Интеграция в Runtime Loop

Модуль интегрирован в `runtime/loop.py`:

```python
from src.runtime.subjective_time import compute_subjective_dt

# В каждом тике:
subjective_dt = compute_subjective_dt(
    dt=dt,
    base_rate=self_state.subjective_time_base_rate,
    intensity=self_state.last_event_intensity,
    stability=self_state.stability,
    intensity_coeff=self_state.subjective_time_intensity_coeff,
    stability_coeff=self_state.subjective_time_stability_coeff,
    rate_min=self_state.subjective_time_rate_min,
    rate_max=self_state.subjective_time_rate_max,
)
self_state.apply_delta({"subjective_time": subjective_dt})
```

## Параметры в SelfState

Модуль использует следующие параметры из `SelfState`:

- `subjective_time` (float): Текущее значение субъективного времени
- `subjective_time_base_rate` (float): Базовая скорость (по умолчанию 1.0)
- `subjective_time_rate_min` (float): Минимальная скорость (по умолчанию 0.1)
- `subjective_time_rate_max` (float): Максимальная скорость (по умолчанию 3.0)
- `subjective_time_intensity_coeff` (float): Коэффициент интенсивности (по умолчанию 1.0)
- `subjective_time_stability_coeff` (float): Коэффициент стабильности (по умолчанию 0.5)
- `last_event_intensity` (float): Интенсивность последнего события [0..1]

## Примеры использования

### Пример 1: Базовая скорость

```python
from src.runtime.subjective_time import compute_subjective_dt

# Нормальные условия (intensity=0.5, stability=1.0)
dt = 1.0  # 1 секунда физического времени
subjective_dt = compute_subjective_dt(
    dt=dt,
    base_rate=1.0,
    intensity=0.5,
    stability=1.0,
    intensity_coeff=1.0,
    stability_coeff=0.5,
    rate_min=0.1,
    rate_max=3.0,
)
# Результат: ~1.5 секунды субъективного времени
```

### Пример 2: Высокая интенсивность

```python
# Высокая интенсивность событий (intensity=1.0, stability=1.0)
subjective_dt = compute_subjective_dt(
    dt=1.0,
    base_rate=1.0,
    intensity=1.0,  # Максимальная интенсивность
    stability=1.0,
    intensity_coeff=1.0,
    stability_coeff=0.5,
    rate_min=0.1,
    rate_max=3.0,
)
# Результат: ~2.0 секунды субъективного времени (время течет быстрее)
```

### Пример 3: Низкая стабильность

```python
# Низкая стабильность (intensity=0.0, stability=0.5)
subjective_dt = compute_subjective_dt(
    dt=1.0,
    base_rate=1.0,
    intensity=0.0,
    stability=0.5,  # Низкая стабильность
    intensity_coeff=1.0,
    stability_coeff=0.5,
    rate_min=0.1,
    rate_max=3.0,
)
# Результат: ~0.75 секунды субъективного времени (время течет медленнее)
```

## Свойства

### Детерминированность

Функции детерминированы: одинаковые входные параметры всегда дают одинаковый результат.

### Монотонность

Субъективное время всегда монотонно возрастает:
- `subjective_dt ≥ 0` для любого `dt ≥ 0`
- Если `dt1 < dt2`, то `subjective_dt1 < subjective_dt2` (при одинаковых параметрах)

### Ограниченность

Скорость субъективного времени всегда ограничена:
- `rate_min ≤ rate ≤ rate_max`
- Это гарантирует, что субъективное время не может течь слишком быстро или слишком медленно

## Тестирование

Модуль покрыт тестами в `src/test/test_subjective_time.py`:
- ✅ Проверка диапазонов скорости
- ✅ Проверка монотонности
- ✅ Проверка влияния интенсивности
- ✅ Проверка влияния стабильности

## Связанные документы

- [docs/components/runtime-loop.md](./runtime-loop.md) — интеграция в runtime loop
- [docs/components/self-state.md](./self-state.md) — параметры состояния
- [docs/concepts/](../concepts/) — концептуальные документы
