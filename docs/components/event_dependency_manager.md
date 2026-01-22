# EventDependencyManager — Менеджер зависимостей событий

## Назначение
EventDependencyManager — это компонент для управления зависимостями между событиями в системе Life. Он отслеживает паттерны событий и модифицирует вероятности генерации новых событий на основе недавней истории, создавая естественные "цепочки" и "паттерны" в потоке событий.

## Текущий статус
✅ **Реализован** (v1.0)
*   Файлы: [`src/environment/event_dependency_manager.py`](../../src/environment/event_dependency_manager.py)
*   Интегрирован: `EventGenerator`

## Компоненты

### 1. EventDependencyManager класс

Основной класс, управляющий зависимостями между событиями.

#### Основные паттерны зависимостей

1. **Confusion → Insight** (Путаница приводит к озарению)
2. **Isolation → Connection** (Одиночество приводит к поиску связи)
3. **Curiosity → Insight или Confusion** (Любопытство приводит к пониманию или путанице)
4. **Void → Meaning_found или Acceptance** (Пустота приводит к поиску смысла или принятию)
5. **Insight → Curiosity** (Озарение стимулирует дальнейшее любопытство)

#### Матрица зависимостей

```python
dependency_matrix = {
    # Confusion часто приводит к Insight или Curiosity
    "confusion": {
        "insight": 2.5,      # Путаница часто разрешается озарением
        "curiosity": 1.8,    # Путаница стимулирует любопытство
        "confusion": 0.3,    # Меньше шансов на повторную путаницу
        "acceptance": 1.2,   # Или приводит к принятию
    },

    # Insight стимулирует дальнейшее исследование
    "insight": {
        "curiosity": 2.2,    # Озарение рождает любопытство
        "insight": 0.4,      # Меньше шансов на повторное озарение подряд
        "meaning_found": 1.6, # Может привести к нахождению смысла
        "confusion": 0.6,    # Но иногда вызывает новую путаницу
    },

    # Isolation мотивирует поиск связи
    "isolation": {
        "connection": 2.8,   # Одиночество сильно мотивирует поиск связи
        "isolation": 0.2,    # Меньше шансов на повторное одиночество
        "void": 1.4,         # Может привести к чувству пустоты
        "curiosity": 1.3,    # Или к любопытству о других
    },

    # И другие зависимости...
}
```

## Использование

### Базовая инициализация

```python
from src.environment.event_dependency_manager import EventDependencyManager

# Создание менеджера зависимостей
dependency_manager = EventDependencyManager(
    history_size=10,      # Размер истории событий
    decay_factor=0.9      # Фактор затухания влияния старых событий
)
```

### Регистрация событий

```python
from src.environment.event import Event

# Создание события
event = Event(type="confusion", intensity=0.7, timestamp=time.time())

# Регистрация события в менеджере зависимостей
dependency_manager.record_event(event)
```

### Получение модификаторов вероятностей

```python
# Получение модификаторов для всех типов событий
modifiers = dependency_manager.get_probability_modifiers()

print("Модификаторы вероятностей:")
for event_type, modifier in modifiers.items():
    print(f"  {event_type}: {modifier:.2f}x")
```

### Обнаружение паттернов

```python
# Получение последних событий
recent_events = [event1, event2, event3]

# Обнаружение паттерна
pattern = dependency_manager.detect_pattern(recent_events)
if pattern:
    print(f"Обнаружен паттерн: {pattern}")
```

### Расчет вероятности цепочки

```python
# Расчет вероятности последовательности событий
event_types = ["confusion", "curiosity", "insight"]
probability = dependency_manager.get_chain_probability(event_types)
print(f"Вероятность цепочки: {probability:.3f}")
```

### Получение статистики

```python
# Получение статистики работы системы зависимостей
stats = dependency_manager.get_dependency_stats()
print(f"Создано цепочек: {stats['chains_created']}")
print(f"Обнаружено паттернов: {stats['patterns_detected']}")
print(f"Всего модификаций: {stats['total_modifications']}")

# Сброс статистики
dependency_manager.reset_stats()
```

## Интеграция с EventGenerator

EventDependencyManager интегрирован в EventGenerator для создания естественных паттернов событий:

```python
from src.environment.generator import EventGenerator

# Создание генератора с системой зависимостей
generator = EventGenerator()

# Генератор автоматически использует dependency_manager
# для модификации вероятностей генерации событий

# Получение статистики зависимостей
dependency_stats = generator.get_dependency_stats()
print(f"Статистика зависимостей: {dependency_stats}")

# Сброс статистики
generator.reset_dependency_stats()
```

## Архитектурные принципы

### Затухание по времени и позиции

Влияние событий затухает со временем и по позиции в истории:

```python
# Для каждого события в истории:
time_decay = decay_factor ** (current_time - event_time)      # Затухание по времени
position_decay = decay_factor ** i                            # Затухание по позиции
combined_decay = time_decay * position_decay

# Применение к модификатору
final_modifier = 1.0 + (base_modifier - 1.0) * combined_decay
```

### Ограничение модификаторов

Модификаторы вероятностей ограничиваются разумными пределами:

```python
# Ограничение диапазона [0.1, 3.0]
modifiers[event_type] = max(0.1, min(3.0, modifiers[event_type]))
```

## Примеры паттернов

### Паттерн "Обучение через путаницу"

```
Confusion (путаница) → Curiosity (любопытство) → Insight (озарение)
```

Этот паттерн моделирует процесс обучения через преодоление трудностей.

### Паттерн "Социальная изоляция"

```
Isolation (одиночество) → Connection (связь) → Acceptance (принятие)
```

Моделирует поиск социальной связи и последующее принятие.

### Паттерн "Экзистенциальный кризис"

```
Void (пустота) → Confusion (путаница) → Meaning_found (нахождение смысла)
```

Отражает глубокие экзистенциальные переживания.

## Тестирование

### Unit тесты

```bash
# Запуск тестов для EventDependencyManager
python -m pytest src/test/test_event_dependency_manager.py -v
```

### Integration тесты

```bash
# Запуск интеграционных тестов с EventGenerator
python -m pytest src/test/test_event_dependency_integration.py -v
```

## Будущие улучшения

1. **Адаптивная матрица зависимостей** — динамическое обучение зависимостей на основе реального поведения системы
2. **Контекстуальные модификаторы** — учет состояния системы Life при расчете зависимостей
3. **Многоуровневые паттерны** — поддержка более сложных паттернов с несколькими ветвями
4. **Статистический анализ** — детальный анализ эффективности паттернов и их влияния на поведение системы