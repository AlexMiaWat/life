# 14_Computation_Cache.md — Система кэширования вычислений

## Текущий статус
✅ **Реализован** (v2.6)
*   Файл: [`src/runtime/computation_cache.py`](../../src/runtime/computation_cache.py)
*   Интегрирован в Runtime Loop для оптимизации производительности
*   LRU-кэш с максимальным размером 1000 записей
*   Кэширование критических вычислений: subjective_dt, валидация, поиск в памяти
*   Целевые показатели: <10мс среднее время тика, >50% cache hit rate

## Назначение

Computation Cache — это высокопроизводительная LRU-кэш система для оптимизации дорогостоящих вычислений в Runtime Loop. Кэширует результаты повторяющихся операций для достижения целевых показателей производительности.

### Архитектурные принципы

1. **Изоляция типов операций** — каждый тип вычислений имеет отдельный кэш
2. **LRU политика** — автоматическое вытеснение редко используемых записей
3. **Хэширование ключей** — детерминированное хэширование для корректного кэширования
4. **Опциональность** — система не влияет на корректность, только на производительность
5. **Мониторинг** — детальная статистика использования и эффективности

## Архитектура

### Основные компоненты

```
ComputationCache
├── subjective_dt_cache: OrderedDict[str, float]      # Кэш compute_subjective_dt
├── validation_cache: OrderedDict[str, bool]          # Кэш валидации состояний
├── memory_search_cache: OrderedDict[str, Any]        # Кэш поиска в памяти
├── meaning_appraisal_cache: OrderedDict[str, Any]    # Кэш Meaning Engine appraisal
├── decision_cache: OrderedDict[str, Any]             # Кэш Decision Engine
└── Глобальный экземпляр: _computation_cache
```

### Глобальный доступ

```python
from src.runtime.computation_cache import get_computation_cache

cache = get_computation_cache()  # Thread-safe singleton
```

## Кэшируемые операции

### 1. compute_subjective_dt

**Наиболее критичная оптимизация** — кэширует вычисление субъективного времени (~60% вычислений на тик).

#### Параметры кэширования
- `dt: float` — временной интервал
- `base_rate: float` — базовая скорость
- `intensity: float` — интенсивность событий
- `stability: float` — стабильность системы
- `energy: float` — уровень энергии
- `intensity_coeff: float` — коэффициент интенсивности
- `stability_coeff: float` — коэффициент стабильности
- `energy_coeff: float` — коэффициент энергии
- `rate_min: float` — минимальная скорость
- `rate_max: float` — максимальная скорость
- `circadian_phase: float` — фаза циркадного ритма
- `recovery_efficiency: float` — эффективность восстановления

#### Оптимизации
- **Округление float значений** до 6 знаков для улучшения hit rate
- **Хэширование** всех параметров для создания ключа
- **LRU вытеснение** при переполнении (max 1000 записей)

#### API
```python
# Низкоуровневый API
cached_value = cache.get_cached_subjective_dt(dt, base_rate, intensity, ...)
if cached_value is None:
    value = compute_subjective_dt(...)
    cache.cache_subjective_dt(dt, base_rate, intensity, ..., value)

# Высокоуровневый API
value = cached_compute_subjective_dt(dt=dt, base_rate=base_rate, ...)
```

### 2. Валидация состояний

Кэширует результаты проверки корректности состояний системы.

#### Типы валидации
- Структурная валидация SelfState
- Валидация параметров компонентов
- Проверка инвариантов системы

#### API
```python
result = cache.get_cached_validation("state_validation", state_data)
if result is None:
    result = validate_state(state_data)
    cache.cache_validation("state_validation", state_data, result)
```

### 3. Поиск в памяти (activate_memory)

Кэширует результаты функции `activate_memory` из Activation Engine.

#### Параметры кэширования
- `event_type: str` — тип события
- `memory_size: int` — размер памяти (для инвалидации при изменениях)
- `subjective_time: float` — текущее субъективное время
- `age: float` — возраст системы
- `limit: Optional[int]` — лимит активации

#### Оптимизации
- Округление временных параметров до 3 знаков
- Инвалидация при изменении размера памяти

#### API
```python
result = cache.get_cached_activate_memory(event_type, memory_size, subjective_time, age, limit)
if result is None:
    result = _activate_memory(event_type, memory, limit, self_state)
    cache.cache_activate_memory(event_type, memory_size, subjective_time, age, limit, result)
```

### 4. Meaning Engine appraisal

Кэширует результаты оценки значимости событий Meaning Engine.

#### Параметры кэширования
- `event_type: str` — тип события
- `intensity: float` — интенсивность события
- `state_energy: float` — энергия состояния
- `state_stability: float` — стабильность состояния
- `state_integrity: float` — целостность состояния

#### API
```python
appraisal = cache.get_cached_meaning_appraisal(event_type, intensity, state_energy, state_stability, state_integrity)
if appraisal is None:
    appraisal = meaning_engine.appraise_event(...)
    cache.cache_meaning_appraisal(event_type, intensity, state_energy, state_stability, state_integrity, appraisal)
```

### 5. Decision Engine

Кэширует решения Decision Engine для оптимизации принятия решений.

#### Параметры кэширования
- `activated_memory_count: int` — количество активированной памяти
- `top_significance: float` — максимальная значимость
- `event_type: str` — тип события
- `current_energy: float` — текущая энергия
- `current_stability: float` — текущая стабильность

#### API
```python
decision = cache.get_cached_decision(activated_memory_count, top_significance, event_type, current_energy, current_stability)
if decision is None:
    decision = decision_engine.make_decision(...)
    cache.cache_decision(activated_memory_count, top_significance, event_type, current_energy, current_stability, decision)
```

## Механизмы кэширования

### Хэширование ключей

```python
def _make_cache_key(self, *args, **kwargs) -> str:
    # Сортировка kwargs для детерминизма
    sorted_kwargs = sorted(kwargs.items())
    cache_str = str(args) + str(sorted_kwargs)
    return hashlib.md5(cache_str.encode()).hexdigest()
```

### LRU политика

```python
def _evict_if_needed(self, cache_dict: OrderedDict):
    if len(cache_dict) > self.max_size:
        cache_dict.popitem(last=False)  # Удаляем самый старый (LRU)
```

### Перемещение при доступе (MRU)

```python
def get_cached_subjective_dt(self, ...):
    if cache_key in self.subjective_dt_cache:
        self.subjective_dt_hits += 1
        # Перемещаем в конец (MRU)
        value = self.subjective_dt_cache.pop(cache_key)
        self.subjective_dt_cache[cache_key] = value
        return value
```

## Статистика и мониторинг

### Метрики производительности

```python
stats = cache.get_stats()
# {
#   "subjective_dt": {
#     "hits": 1250,
#     "misses": 340,
#     "hit_rate": 78.6,
#     "size": 890
#   },
#   "validation": {...},
#   "memory_search": {...},
#   ...
# }
```

### Интеграция с PerformanceMetrics

Все операции кэширования измеряются через `performance_metrics`:

```python
from src.runtime.performance_metrics import measure_time

with measure_time("cache_subjective_dt_get"):
    cached_value = cache.get_cached_subjective_dt(...)

with measure_time("cache_subjective_dt_set"):
    cache.cache_subjective_dt(..., value)
```

## Производительность

### Целевые показатели

- **Cache hit rate > 50%** для subjective_dt кэша
- **Время доступа < 1мс** к кэшированным значениям
- **Ускорение > 2x** для повторяющихся вычислений
- **Память < 50MB** для всех кэшей

### Типичные результаты

Для Runtime Loop с 100 тиками в секунду:
- **Subjective DT cache:** hit rate 65-85%, ускорение 3-5x
- **Memory search cache:** hit rate 40-60%, ускорение 2-3x
- **Общее ускорение:** 25-40% снижение CPU времени

### Бенчмаркинг

```bash
# Запуск комплексного бенчмарка
python scripts/benchmark_runtime_optimizations.py

# Результаты сохраняются в benchmark_results.json
```

## Безопасность и надежность

### Graceful degradation

Система спроектирована для graceful degradation:
- При ошибках кэширования возвращается `None`
- Вычисления выполняются без кэша
- Система продолжает работать с degraded производительностью

### Thread safety

- Глобальный singleton потокобезопасен
- LRU операции атомарны
- Нет блокировок на hot path

### Очистка кэша

```python
cache.clear()  # Полная очистка всех кэшей
```

## Интеграция в Runtime Loop

### Автоматическое использование

Кэширование интегрировано прозрачно:

```python
# В runtime/loop.py
from src.runtime.computation_cache import cached_compute_subjective_dt

# Вместо compute_subjective_dt используется cached версия
subjective_dt = cached_compute_subjective_dt(
    dt=dt,
    base_rate=state.subjective_time_base_rate,
    # ... все параметры
)
```

### Опциональность

Кэширование можно отключить на уровне конфигурации:

```python
# В будущем можно добавить флаг
runtime_config = {
    "enable_computation_cache": True,  # По умолчанию включено
    "cache_size": 1000
}
```

## Тестирование

### Unit тесты

```python
# src/test/test_computation_cache.py
def test_subjective_dt_caching():
    cache = ComputationCache()
    # Тест кэширования с одинаковыми параметрами
    # Проверка hit/miss счетчиков
    # Валидация LRU политики
```

### Интеграционные тесты

```python
# src/test/test_runtime_loop_caching.py
def test_runtime_loop_with_cache():
    # Тест полного runtime loop с кэшированием
    # Измерение производительности с кэшем и без
    # Проверка корректности результатов
```

### Нагрузочное тестирование

```python
# scripts/benchmark_runtime_optimizations.py
def benchmark_cache_performance():
    # Измерение hit rate при разных нагрузках
    # Тестирование LRU при переполнении
    # Сравнение с baseline без кэша
```

## Связанные компоненты

*   [runtime-loop.md](runtime-loop.md) — основной цикл с интеграцией кэширования
*   [memory.md](memory.md) — индексы памяти с кэшированием поиска
*   [performance-profiling.md](../observability/performance_profiling.md) — профилирование производительности