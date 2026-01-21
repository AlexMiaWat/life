# Intelligence — Компонент интеллекта

> **Версия:** v1.1
> **Статус:** Реализован и интегрирован
> **Модуль:** `src/intelligence/intelligence.py`
> **Интеграция:** Субъективное время влияет на набор обрабатываемых источников
> **Интеграция:** Субъективное время влияет на набор обрабатываемых источников

---

## Обзор

Intelligence — минимальный компонент обработки информации. Реализует нейтральную фиксацию потенциала обработки из различных источников без интерпретации, оценки или влияния на поведение системы.

**Ключевой принцип:** Intelligence не отвечает на вопрос «что делать», он отвечает только на вопрос «есть ли потенциал обработки информации».

---

## Назначение

Intelligence выполняет следующие функции:
- Фиксирует размеры и значения доступных источников информации
- Записывает метаданные о proxy-источниках (memory, adaptation, learning, planning)
- Записывает данные в `self_state.intelligence` без побочных эффектов

---

## API

### `process_information(self_state: SelfState) -> None`

Минимальная нейтральная обработка информации с учетом субъективного времени.

**Параметры:**
- `self_state` — текущее состояние системы

**Возвращает:**
- `None` — записывает данные напрямую в `self_state.intelligence`

**Новая функциональность (v1.1):**
Функция анализирует восприятие времени и модифицирует набор обрабатываемых источников:

- **Ускоренное восприятие времени** (`time_ratio >= 1.1`): Все доступные источники + расширенные метрики времени
- **Замедленное восприятие времени** (`time_ratio <= 0.9`): Минимальный набор источников + базовые метрики времени
- **Нормальное восприятие времени** (`0.9 < time_ratio < 1.1`): Стандартный набор + базовые метрики времени

**Пример использования:**

```python
from intelligence.intelligence import process_information
from state.self_state import SelfState

state = SelfState()
state.recent_events = ["noise", "decay"]
state.energy = 85.0
state.stability = 0.95
state.planning = {'potential_sequences': [['noise', 'decay']]}

process_information(state)

print(state.intelligence)
# {'processed_sources': {
#     'memory_proxy_size': 2,
#     'adaptation_proxy': 85.0,
#     'learning_proxy': 0.95,
#     'planning_proxy_size': 1
# }}
```

---

## Структура данных

После вызова `process_information()` в `self_state.intelligence` записывается:

```python
{
    'processed_sources': {
        'memory_proxy_size': int,      # количество recent_events
        'adaptation_proxy': float,     # текущая энергия
        'learning_proxy': float,       # текущая стабильность (только при ускоренном/нормальном восприятии)
        'planning_proxy_size': int,    # количество potential_sequences (только при ускоренном/нормальном восприятии)
        'subjective_time_metrics': {   # метрики субъективного времени
            'current_subjective_time': float,  # текущее субъективное время
            'time_ratio': float,               # отношение субъективного к физическому времени
            'time_perception': str,            # "accelerated", "normal", или "slowed"
            'intensity_smoothed': float        # сглаженная интенсивность (только при ускоренном восприятии)
        }
    }
}
```

**Динамическая структура:**
- При **ускоренном восприятии**: Все поля присутствуют
- При **замедленном восприятии**: Только `memory_proxy_size`, `adaptation_proxy` и базовые метрики времени
- При **нормальном восприятии**: Все поля кроме `intensity_smoothed`

### Поля:

| Поле | Тип | Описание |
|------|-----|----------|
| `memory_proxy_size` | `int` | Количество недавних событий |
| `adaptation_proxy` | `float` | Текущий уровень энергии |
| `learning_proxy` | `float` | Текущий уровень стабильности |
| `planning_proxy_size` | `int` | Количество потенциальных последовательностей |

---

## Интеграция в Runtime Loop

Intelligence вызывается в `src/runtime/loop.py` после Planning:

```python
# В методе tick() класса RuntimeLoop
from intelligence.intelligence import process_information

# После Planning
process_information(self.self_state)
```

---

## Архитектурные ограничения

Intelligence соблюдает жёсткие архитектурные ограничения (см. `docs/concepts/intelligence.md`):

### Запрещено:
- Инициировать Decision или Action
- Иметь цели, желания или намерения
- Рассуждать или предсказывать
- Воздействовать на другие слои
- Генерировать "интеллект" или оценки

### Разрешено:
- Существовать как абстрактная способность обработки информации
- Хранить внутренние данные и статистику для наблюдения

---

## Тестирование

Тесты находятся в `src/test/test_intelligence.py`.

```bash
# Запуск тестов Intelligence
pytest src/test/test_intelligence.py -v
```

---

## Связанные документы

- [Концепция Intelligence](../concepts/intelligence.md) — архитектурные ограничения и философия
- [Planning](planning.md) — компонент планирования (вызывается до Intelligence)
- [Self-State](self-state.md) — структура состояния
- [Runtime Loop](runtime-loop.md) — главный цикл интеграции

---

*Документ создан: 2026-01-18*
*Последнее обновление: 2026-01-18*
