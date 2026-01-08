Цель этапа

Перейти от событий как фактов к событиям как переживанию.

На этом этапе Life учится:

не просто получать события из среды

а придавать им значение

и изменяться по-разному, даже при одинаковых внешних условиях

Это первый шаг от «физики» к «психике»
но без сознания, эмоций и LLM

Ключевая идея

Событие ≠ Значение

Event — это то, что произошло

Meaning — это то, что это значит для Life

Одно и то же событие:

может быть опасным

может быть нейтральным

может быть полезным

➡️ Всё зависит от внутреннего состояния Life

Архитектурный принцип
Meaning — это функция:
Meaning = f(Event, SelfState)


Meaning не существует сам по себе

Meaning не приходит извне

Meaning возникает внутри Life

Новый слой архитектуры
Environment
   ↓
Event
   ↓
Meaning Layer   ← НОВОЕ
   ↓
Self-State Update


Meaning Layer — это:

интерпретатор

переводчик

фильтр значимости

Структура Meaning Layer
MeaningEngine
 ├── Appraisal
 ├── ImpactModel
 └── ResponsePattern

1️⃣ Appraisal — первичная оценка
Задача

Ответить на вопрос:

«Это вообще важно?»

Appraisal учитывает:

тип события

интенсивность

текущее состояние Life

Пример:

if event.type == "noise" and self_state.stability > 0.8:
    significance = LOW

2️⃣ ImpactModel — как это влияет
Задача

Понять:

«Если это важно — как именно оно меня затронет?»

Пример:

shock → снижает stability

recovery → увеличивает energy

idle → почти ничего не делает

Но:

при низкой integrity даже noise может быть критичен

3️⃣ ResponsePattern — форма реакции
Задача

Определить:

«Как Life реагирует в этот раз?»

Важно:

реакция ≠ жёсткое правило

возможны вариации

Примеры:

ослабление

компенсация

игнорирование

накопление эффекта

Минимальная модель Meaning

Простейшая структура Meaning:

Meaning = {
  "event_id": ...,
  "significance": 0.0 – 1.0,
  "impact": {
      "energy": -0.1,
      "stability": -0.02
  }
}

Почему Meaning — это поворотный момент

До этого:

Life = состояние + время

После:

Life = история интерпретаций

➡️ Начинается уникальность поведения

Отличие от «эмоций»

❌ Это не эмоции
❌ Это не чувства
❌ Это не психология

Это:

механизм различия реакций

Взаимодействие с Monitor

Теперь Monitor может:

показывать не только события

но и их значение

Пример:

• event=noise → significance=0.12 → ignored

Что Meaning Layer НЕ делает

❌ не принимает решений «зачем жить»
❌ не планирует
❌ не оптимизирует

Он только:

переводит внешний мир во внутренние изменения

Связь с будущими этапами

Meaning Layer — основа для:

Memory (что было значимо)

Learning (повторяющиеся паттерны)

Intent (реакции становятся направленными)

позже — субъективного опыта

Итог этапа 08

Life:

больше не просто реагирует

начинает по-разному переживать одно и то же

Это:

не сознание

не интеллект

но уже зачаток индивидуальности

## Реализация

Реализация находится в директории [`src/meaning/`](src/meaning/).

### Структура `Meaning`

Класс [`Meaning`](src/meaning/meaning.py:5) — dataclass, представляющий интерпретированное значение события:

```python
@dataclass
class Meaning:
    event_id: Optional[str] = None
    significance: float = 0.0  # Важность: [0.0, 1.0]
    impact: Dict[str, float] = field(default_factory=dict)  # e.g. {"energy": -0.1, "stability": -0.02}
```

### `MeaningEngine`

Класс [`MeaningEngine`](src/meaning/engine.py:5) содержит ключевые методы:

#### `process(event: Event, self_state: Dict) -> Meaning` [`src/meaning/engine.py:118`](src/meaning/engine.py:118)

Основной метод обработки. Оркестрирует:

1. **appraisal** — оценка значимости
2. **impact_model** — расчёт влияния
3. **response_pattern** — паттерн реакции
4. Модификация `impact` по паттерну
5. Создание и возврат `Meaning`

#### `appraisal(event: Event, self_state: Dict) -> float` [`src/meaning/engine.py:21`](src/meaning/engine.py:21)

Первичная оценка значимости (`significance`):

- Базовая: `abs(event.intensity)`
- Множитель по типу: `shock`:1.5, `noise`:0.5, `recovery`/`decay`:1.0, `idle`:0.2
- Если `integrity < 0.3`: `*1.5`
- Если `stability < 0.5`: `*1.2`
- Ограничение: `[0.0, 1.0]`

#### `impact_model(event: Event, self_state: Dict, significance: float) -> Dict[str, float]` [`src/meaning/engine.py:60`](src/meaning/engine.py:60)

Расчёт влияния на состояние:

- Базовые дельты по типам событий (e.g. `shock`: `energy:-0.15`, `stability:-0.10`)
- Масштабирование: `* abs(intensity) * significance`

#### `response_pattern(event: Event, self_state: Dict, significance: float) -> str` [`src/meaning/engine.py:91`](src/meaning/engine.py:91)

Паттерны реакции:

- `significance < 0.1`: `"ignore"`
- `stability > 0.8`: `"dampen"` (impact `*0.5`)
- `stability < 0.3`: `"amplify"` (impact `*1.5`)
- Иначе: `"absorb"` (без изменений)

**Текущий статус:** Модуль полностью реализован в `src/meaning/`, но **не интегрирован** в основной цикл runtime ([`src/runtime/loop.py`](src/runtime/loop.py)).