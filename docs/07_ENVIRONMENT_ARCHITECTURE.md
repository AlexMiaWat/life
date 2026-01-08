# Архитектура слоя Environment (этап 07)

## Общая концепция

**Environment** — это внешний мир, который существует независимо от Life и влияет на неё через события.

### Ключевые принципы:

1. **Независимость**: Environment не знает о внутренностях Life
2. **Асинхронность**: События генерируются независимо от тиков Life
3. **Разделение ответственности**: Environment только порождает события, Life их интерпретирует

---

## Архитектура слоя

```
┌─────────────────────────────────────────────────────────┐
│                    Environment Layer                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐      ┌──────────────┐                 │
│  │ EventGenerator│─────▶│ EventQueue   │                 │
│  │              │      │              │                 │
│  │ - generate() │      │ - push()     │                 │
│  │              │      │ - pop()      │                 │
│  │              │      │ - pop_all()  │                 │
│  └──────────────┘      └──────┬───────┘                 │
│                                │                          │
│                                ▼                          │
│                        ┌──────────────┐                  │
│                        │    Event     │                  │
│                        │              │                  │
│                        │ - type       │                  │
│                        │ - intensity │                  │
│                        │ - timestamp │                  │
│                        │ - metadata  │                  │
│                        └──────────────┘                  │
│                                                           │
└───────────────────────────────────────────────────────────┘
                                │
                                │ события
                                ▼
┌───────────────────────────────────────────────────────────┐
│                    Runtime Loop                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 1. pop_all() - получить все события                │  │
│  │ 2. _interpret_event() - интерпретировать каждое     │  │
│  │ 3. обновить self_state                             │  │
│  └────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

---

## Поток данных

```
Время →
│
├─ [Фоновый поток] EventGenerator.generate()
│  └─▶ Event(type='noise', intensity=0.2, ...)
│      └─▶ EventQueue.push(event)
│
├─ [Фоновый поток] EventGenerator.generate()
│  └─▶ Event(type='decay', intensity=-0.3, ...)
│      └─▶ EventQueue.push(event)
│
├─ [Тик Life] Runtime Loop
│  ├─▶ EventQueue.pop_all() → [event1, event2, ...]
│  ├─▶ _interpret_event(event1, self_state)
│  ├─▶ _interpret_event(event2, self_state)
│  └─▶ self_state обновлен
│
└─ [Следующий тик] ...
```

---

## Модули Environment

### 1. Event (`event.py`)

**Назначение**: Структура данных для представления события из среды.

**Реализация**:
```python
@dataclass
class Event:
    type: str           # Тип события
    intensity: float   # Интенсивность [-1.0, 1.0]
    timestamp: float    # Время создания
    metadata: Dict     # Дополнительные данные
```

**Типы событий**:
- `noise` - случайное воздействие
- `decay` - естественный износ
- `recovery` - восстановление
- `shock` - резкое воздействие
- `idle` - отсутствие событий

**Особенности**:
- Immutable структура (dataclass)
- Всегда имеет timestamp
- metadata может содержать контекстную информацию

**Пример**:
```python
event = Event(
    type='shock',
    intensity=-0.8,
    timestamp=1704739200.5,
    metadata={'source': 'external'}
)
```

---

### 2. EventQueue (`event_queue.py`)

**Назначение**: Thread-safe очередь событий (FIFO) с ограниченным размером.

**Реализация**:
```python
class EventQueue:
    def __init__(self):
        self._queue = queue.Queue(maxsize=100)  # Thread-safe очередь
```

**Методы**:

1. **`push(event: Event) -> None`**
   - Добавляет событие в очередь
   - Если очередь полна (100 событий), событие **тихо игнорируется**
   - Thread-safe операция

2. **`pop() -> Event | None`**
   - Извлекает одно событие (FIFO)
   - Возвращает `None` если очередь пуста
   - Thread-safe операция

3. **`pop_all() -> list[Event]`**
   - Извлекает **все** события из очереди
   - Возвращает список в порядке FIFO
   - Используется в Runtime Loop для обработки всех накопленных событий за тик

4. **`is_empty() -> bool`**
   - Проверяет, пуста ли очередь

5. **`size() -> int`**
   - Возвращает количество событий в очереди

**Особенности**:
- Использует `queue.Queue` из стандартной библиотеки (thread-safe)
- Максимальный размер: 100 событий
- При переполнении новые события теряются (silent drop)
- FIFO порядок (первый пришел - первый ушел)

**Пример использования**:
```python
queue = EventQueue()

# Добавление событий
queue.push(Event(type='noise', intensity=0.1, ...))
queue.push(Event(type='decay', intensity=-0.2, ...))

# Извлечение всех событий
events = queue.pop_all()  # [Event(noise), Event(decay)]
```

---

### 3. EventGenerator (`generator.py`)

**Назначение**: Генератор событий, создающий события согласно вероятностям и спецификации.

**Реализация**:
```python
class EventGenerator:
    def generate(self) -> Event:
        # 1. Выбор типа события по весам
        # 2. Генерация интенсивности для типа
        # 3. Создание Event с timestamp
```

**Вероятности типов событий**:
- `noise`: 40% (0.4)
- `decay`: 30% (0.3)
- `recovery`: 20% (0.2)
- `shock`: 5% (0.05)
- `idle`: 5% (0.05)

**Диапазоны интенсивности** (согласно спецификации этапа 07):
- `noise`: `[-0.3, 0.3]` - небольшое случайное воздействие
- `decay`: `[-0.5, 0.0]` - отрицательное (износ)
- `recovery`: `[0.0, 0.5]` - положительное (восстановление)
- `shock`: `[-1.0, 1.0]` - полный диапазон (резкое воздействие)
- `idle`: `0.0` - отсутствие воздействия

**Алгоритм работы**:
1. Использует `random.choices()` с весами для выбора типа
2. Генерирует интенсивность в диапазоне для выбранного типа
3. Создает `Event` с текущим timestamp

**Пример**:
```python
generator = EventGenerator()

# Генерация события
event = generator.generate()
# Может быть: Event(type='noise', intensity=0.15, ...)
# Или: Event(type='shock', intensity=-0.9, ...)
```

**Особенности**:
- Детерминированная логика (нет состояния)
- Каждый вызов `generate()` создает новое событие
- Timestamp всегда текущее время

---

## Интеграция с Runtime Loop

### Инициализация (в `main.py`)

```python
# 1. Создание очереди
event_queue = EventQueue()

# 2. Создание генератора
generator = EventGenerator()

# 3. Фоновый поток для генерации событий
def background_event_generation(queue, generator, stop_event):
    while not stop_event.is_set():
        event = generator.generate()
        queue.push(event)
        time.sleep(1.0)  # Генерация каждую секунду

generator_thread = threading.Thread(
    target=background_event_generation,
    args=(event_queue, generator, stop_event)
)
generator_thread.daemon = True
generator_thread.start()

# 4. Передача очереди в Runtime Loop
run_loop(self_state, monitor, event_queue=event_queue)
```

### Обработка в Runtime Loop (`loop.py`)

```python
def run_loop(..., event_queue=None):
    while self_state['alive']:
        # ...
        
        # ШАГ 1: Получить все события из среды
        if event_queue and not event_queue.is_empty():
            events = event_queue.pop_all()  # Извлекаем все события
            
            # ШАГ 2: Интерпретировать каждое событие
            for event in events:
                _interpret_event(event, self_state)
        
        # ...
```

### Интерпретация событий (`_interpret_event()`)

```python
def _interpret_event(event: Event, self_state: dict) -> None:
    event_type = event.type
    intensity = event.intensity
    
    if event_type == 'noise':
        self_state['stability'] += intensity * 0.01
    elif event_type == 'decay':
        self_state['energy'] += intensity  # отрицательная
    elif event_type == 'recovery':
        self_state['energy'] += intensity  # положительная
    elif event_type == 'shock':
        self_state['integrity'] += intensity * 0.1
        self_state['stability'] += intensity * 0.05
    # idle - ничего не делает
    
    # Ограничение значений
    self_state['energy'] = max(0.0, min(100.0, self_state['energy']))
    self_state['stability'] = max(0.0, min(1.0, self_state['stability']))
    self_state['integrity'] = max(0.0, min(1.0, self_state['integrity']))
```

---

## Временная диаграмма

```
Время →
│
├─ t=0.0s: [Генератор] generate() → Event(noise, 0.2) → Queue.push()
├─ t=0.5s: [Генератор] generate() → Event(decay, -0.3) → Queue.push()
├─ t=1.0s: [Runtime Loop] Тик #1
│          ├─ pop_all() → [Event(noise), Event(decay)]
│          ├─ _interpret_event(noise) → stability += 0.002
│          ├─ _interpret_event(decay) → energy -= 0.3
│          └─ self_state обновлен
│
├─ t=1.5s: [Генератор] generate() → Event(recovery, 0.4) → Queue.push()
├─ t=2.0s: [Runtime Loop] Тик #2
│          ├─ pop_all() → [Event(recovery)]
│          ├─ _interpret_event(recovery) → energy += 0.4
│          └─ self_state обновлен
│
└─ ...
```

---

## Ключевые особенности архитектуры

### 1. Асинхронность

- **Генератор** работает в отдельном потоке
- События накапливаются в очереди между тиками
- Life обрабатывает все накопленные события за один тик

### 2. Thread-safety

- `EventQueue` использует `queue.Queue` (thread-safe)
- Генератор может добавлять события, пока Life их читает
- Нет race conditions

### 3. Ограничение размера

- Максимум 100 событий в очереди
- При переполнении новые события теряются
- Защита от переполнения памяти

### 4. Разделение ответственности

- **Environment** (Generator) - только генерирует события
- **EventQueue** - только хранит события
- **Life** (Runtime Loop) - интерпретирует события

### 5. Независимость

- Environment не знает о `self_state`
- Environment не знает о логике интерпретации
- Environment только порождает "сырые" события

---

## Пример полного цикла

```python
# === ИНИЦИАЛИЗАЦИЯ ===
queue = EventQueue()
generator = EventGenerator()

# === ГЕНЕРАЦИЯ (фоновый поток) ===
event1 = generator.generate()  # Event(type='noise', intensity=0.15)
queue.push(event1)

event2 = generator.generate()  # Event(type='decay', intensity=-0.25)
queue.push(event2)

# === ОБРАБОТКА (Runtime Loop) ===
events = queue.pop_all()  # [event1, event2]

for event in events:
    _interpret_event(event, self_state)
    # noise: stability += 0.15 * 0.01 = 0.0015
    # decay: energy += (-0.25) = -0.25

# self_state обновлен
```

---

## Расширяемость

Архитектура позволяет легко:

1. **Добавить новые типы событий**:
   - Добавить тип в `EventGenerator.generate()`
   - Добавить обработку в `_interpret_event()`

2. **Изменить логику генерации**:
   - Модифицировать вероятности в `EventGenerator`
   - Добавить паттерны (волны, циклы)

3. **Изменить интерпретацию**:
   - Модифицировать `_interpret_event()`
   - Добавить контекстную логику

4. **Добавить источники событий**:
   - Создать новые генераторы
   - Подключить внешние источники (API, файлы)

---

## Итог

**Environment** — это простой, но мощный слой, который:
- ✅ Существует независимо от Life
- ✅ Генерирует события асинхронно
- ✅ Обеспечивает thread-safety
- ✅ Легко расширяется
- ✅ Соответствует принципам этапа 07

**Life** получает события из Environment и сама решает, как их интерпретировать, создавая субъективную реакцию на внешний мир.
