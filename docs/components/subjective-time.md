# Subjective Time (Субъективное время)

## Обзор

Модуль `subjective_time` реализует модель субъективного времени для системы Life. Субъективное время — это **метрика** (не управляющий цикл), которая обеспечивает детерминированное, монотонное отображение физического времени (`dt`) в субъективное время на основе состояния системы и сигналов.

## Философия

Субъективное время отражает восприятие времени системой:
- **Высокая интенсивность событий** → время течет быстрее (положительный эффект)
- **Низкая стабильность** → время течет медленнее (отрицательный эффект)
- **Высокая энергия** → время течет быстрее (положительный эффект)
- **Экспоненциальное сглаживание** интенсивности создает плавные переходы между состояниями
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
    energy: float,
    intensity_coeff: float,
    stability_coeff: float,
    energy_coeff: float,
    rate_min: float,
    rate_max: float,
) -> float:
```

**Параметры:**
- `base_rate` (float): Базовая скорость субъективного времени (обычно 1.0)
- `intensity` (float): Интенсивность последнего события [0..1]
- `stability` (float): Стабильность системы [0..1]
- `energy` (float): Уровень энергии системы [0..100]
- `intensity_coeff` (float): Коэффициент влияния интенсивности
- `stability_coeff` (float): Коэффициент влияния стабильности
- `energy_coeff` (float): Коэффициент влияния энергии
- `rate_min` (float): Минимальная скорость (обычно 0.1)
- `rate_max` (float): Максимальная скорость (обычно 3.0)

**Возвращает:**
- Множитель скорости субъективного времени в диапазоне [rate_min, rate_max]

**Формула:**
```
intensity_term = intensity_coeff * intensity
stability_term = stability_coeff * (stability - 1.0)
energy_term = energy_coeff * (energy / 100.0)

rate = base_rate + intensity_term + stability_term + energy_term
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
    energy: float,
    intensity_coeff: float,
    stability_coeff: float,
    energy_coeff: float,
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

Модуль интегрирован в `runtime/loop.py` с поддержкой экспоненциального сглаживания интенсивности:

```python
from src.runtime.subjective_time import compute_subjective_dt

# В каждом тике:
# 1. Обновление интенсивности с экспоненциальным сглаживанием
current_max_intensity = max([float(e.intensity) for e in events] + [0.0])
alpha = self_state.subjective_time_intensity_smoothing
self_state.last_event_intensity = (
    alpha * current_max_intensity +
    (1 - alpha) * self_state.last_event_intensity
)

# 2. Вычисление субъективного времени с учетом энергии
subjective_dt = compute_subjective_dt(
    dt=dt,
    base_rate=self_state.subjective_time_base_rate,
    intensity=self_state.last_event_intensity,
    stability=self_state.stability,
    energy=self_state.energy,
    intensity_coeff=self_state.subjective_time_intensity_coeff,
    stability_coeff=self_state.subjective_time_stability_coeff,
    energy_coeff=self_state.subjective_time_energy_coeff,
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
- `subjective_time_energy_coeff` (float): Коэффициент влияния энергии (по умолчанию 0.5)
- `subjective_time_intensity_smoothing` (float): Коэффициент сглаживания интенсивности (по умолчанию 0.3)
- `last_event_intensity` (float): Интенсивность последнего события [0..1], сглаженная экспоненциально

## Примеры использования

### Пример 1: Базовая скорость

```python
from src.runtime.subjective_time import compute_subjective_dt

# Нормальные условия (intensity=0.5, stability=1.0, energy=100.0)
dt = 1.0  # 1 секунда физического времени
subjective_dt = compute_subjective_dt(
    dt=dt,
    base_rate=1.0,
    intensity=0.5,
    stability=1.0,
    energy=100.0,  # Полная энергия
    intensity_coeff=1.0,
    stability_coeff=0.5,
    energy_coeff=0.5,
    rate_min=0.1,
    rate_max=3.0,
)
# Результат: ~2.0 секунды субъективного времени
```

### Пример 2: Высокая интенсивность

```python
# Высокая интенсивность событий (intensity=1.0, stability=1.0, energy=100.0)
subjective_dt = compute_subjective_dt(
    dt=1.0,
    base_rate=1.0,
    intensity=1.0,  # Максимальная интенсивность
    stability=1.0,
    energy=100.0,  # Полная энергия
    intensity_coeff=1.0,
    stability_coeff=0.5,
    energy_coeff=0.5,
    rate_min=0.1,
    rate_max=3.0,
)
# Результат: ~2.5 секунды субъективного времени (время течет быстрее)
```

### Пример 3: Низкая стабильность

```python
# Низкая стабильность (intensity=0.0, stability=0.5, energy=50.0)
subjective_dt = compute_subjective_dt(
    dt=1.0,
    base_rate=1.0,
    intensity=0.0,
    stability=0.5,  # Низкая стабильность
    energy=50.0,    # Средняя энергия
    intensity_coeff=1.0,
    stability_coeff=0.5,
    energy_coeff=0.5,
    rate_min=0.1,
    rate_max=3.0,
)
# Результат: ~0.5 секунды субъективного времени (время течет медленнее)
```

### Пример 4: Интеграция в SelfState

```python
from src.state.self_state import SelfState
from src.runtime.subjective_time import compute_subjective_dt
import time

# Создание состояния с настройками субъективного времени
state = SelfState()
state.subjective_time = 0.0  # Начальное субъективное время
state.last_event_intensity = 0.0  # Начальная интенсивность

# Настройки для быстрого реагирования
state.subjective_time_intensity_coeff = 1.5  # Высокая чувствительность к интенсивности
state.subjective_time_stability_coeff = 0.8  # Средняя чувствительность к стабильности
state.subjective_time_energy_coeff = 0.6    # Чувствительность к энергии
state.subjective_time_intensity_smoothing = 0.4  # Плавное сглаживание

print(f"Начальное субъективное время: {state.subjective_time}")

# Имитация тика runtime loop
dt = 1.0  # Физическая секунда

# Обновление интенсивности (экспоненциальное сглаживание)
current_intensity = 0.8  # Высокая интенсивность события
alpha = state.subjective_time_intensity_smoothing
state.last_event_intensity = (
    alpha * current_intensity +
    (1 - alpha) * state.last_event_intensity
)

# Вычисление субъективного времени
subjective_dt = compute_subjective_dt(
    dt=dt,
    base_rate=state.subjective_time_base_rate,
    intensity=state.last_event_intensity,
    stability=state.stability,
    energy=state.energy,
    intensity_coeff=state.subjective_time_intensity_coeff,
    stability_coeff=state.subjective_time_stability_coeff,
    energy_coeff=state.subjective_time_energy_coeff,
    rate_min=state.subjective_time_rate_min,
    rate_max=state.subjective_time_rate_max,
)

# Применение изменения
state.apply_delta({"subjective_time": subjective_dt})

print(f"Субъективное время после тика: {state.subjective_time:.3f}")
print(f"Физическое время: {dt}, Субъективное время: {subjective_dt:.3f}")
print(f"Отношение: {subjective_dt/dt:.2f}x")
```

### Пример 5: Наблюдение за течением времени при разных состояниях

```python
from src.runtime.subjective_time import compute_subjective_time_rate
from src.state.self_state import SelfState

# Создание тестовых сценариев
scenarios = [
    ("Спокойное состояние", {
        "intensity": 0.1, "stability": 0.9, "energy": 90.0,
        "intensity_coeff": 1.0, "stability_coeff": 0.5, "energy_coeff": 0.5
    }),
    ("Высокая активность", {
        "intensity": 0.9, "stability": 0.8, "energy": 95.0,
        "intensity_coeff": 1.0, "stability_coeff": 0.5, "energy_coeff": 0.5
    }),
    ("Проблемное состояние", {
        "intensity": 0.3, "stability": 0.4, "energy": 30.0,
        "intensity_coeff": 1.0, "stability_coeff": 0.5, "energy_coeff": 0.5
    }),
    ("Кризис", {
        "intensity": 0.1, "stability": 0.2, "energy": 10.0,
        "intensity_coeff": 1.0, "stability_coeff": 0.5, "energy_coeff": 0.5
    })
]

print("Анализ скорости субъективного времени:")
print("-" * 50)

for name, params in scenarios:
    rate = compute_subjective_time_rate(
        base_rate=1.0,
        intensity=params["intensity"],
        stability=params["stability"],
        energy=params["energy"],
        intensity_coeff=params["intensity_coeff"],
        stability_coeff=params["stability_coeff"],
        energy_coeff=params["energy_coeff"],
        rate_min=0.1,
        rate_max=3.0,
    )

    print(f"{name}:")
    print(".2f")
    print(f"  (intensity={params['intensity']}, stability={params['stability']}, energy={params['energy']})")
    print()
```

### Пример 6: Настройка параметров для разных режимов

```python
from src.state.self_state import SelfState
from src.runtime.subjective_time import compute_subjective_dt

# Создание состояния для разных режимов работы
modes = {
    "Разработка": {
        "subjective_time_intensity_coeff": 0.5,  # Меньше реагировать на интенсивность
        "subjective_time_stability_coeff": 0.3,  # Меньше реагировать на стабильность
        "subjective_time_energy_coeff": 0.2,     # Меньше реагировать на энергию
        "subjective_time_intensity_smoothing": 0.6,  # Более плавное сглаживание
    },
    "Боевое состояние": {
        "subjective_time_intensity_coeff": 1.5,  # Высокая чувствительность
        "subjective_time_stability_coeff": 1.0,  # Средняя чувствительность
        "subjective_time_energy_coeff": 0.8,     # Чувствительность к энергии
        "subjective_time_intensity_smoothing": 0.2,  # Быстрое реагирование
    },
    "Медитация": {
        "subjective_time_intensity_coeff": 0.1,  # Минимальная реакция на события
        "subjective_time_stability_coeff": 0.8,  # Высокая чувствительность к стабильности
        "subjective_time_energy_coeff": 0.6,     # Умеренная чувствительность к энергии
        "subjective_time_intensity_smoothing": 0.8,  # Очень плавное сглаживание
    }
}

dt = 1.0  # Физическая секунда

for mode_name, config in modes.items():
    state = SelfState()
    state.last_event_intensity = 0.5
    state.stability = 0.7
    state.energy = 60.0

    # Применение настроек режима
    for param, value in config.items():
        setattr(state, param, value)

    # Вычисление субъективного времени
    subjective_dt = compute_subjective_dt(
        dt=dt,
        base_rate=state.subjective_time_base_rate,
        intensity=state.last_event_intensity,
        stability=state.stability,
        energy=state.energy,
        intensity_coeff=state.subjective_time_intensity_coeff,
        stability_coeff=state.subjective_time_stability_coeff,
        energy_coeff=state.subjective_time_energy_coeff,
        rate_min=state.subjective_time_rate_min,
        rate_max=state.subjective_time_rate_max,
    )

    print(f"{mode_name}:")
    print(".3f")
    print(f"  Конфигурация: {config}")
    print()
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

### Экспоненциальное сглаживание интенсивности

Интенсивность событий сглаживается экспоненциально для создания плавных переходов:

**Формула сглаживания:**
```
smoothed_intensity = alpha * current_intensity + (1 - alpha) * previous_intensity
```

**Параметры:**
- `alpha` (`subjective_time_intensity_smoothing`): Коэффициент сглаживания [0..1]
  - `alpha = 0.0`: Интенсивность не обновляется (статичная)
  - `alpha = 1.0`: Интенсивность мгновенно принимает новое значение (без сглаживания)
  - `alpha = 0.3` (по умолчанию): Плавное сглаживание с небольшим откликом

**Преимущества:**
- Плавные переходы между состояниями вместо резких скачков
- Реалистичное восприятие времени (память о недавних событиях)
- Снижение чувствительности к шумовым пикам интенсивности

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
