# ADR 002: Рефакторинг SelfState - переход на delegation pattern

## Статус

✅ **Принято и реализовано**

## Дата

2026-01-22

## Контекст

SelfState является God object с 57+ полями, где присутствует значительное дублирование данных между новыми компонентами состояния (IdentityState, PhysicalState, TimeState, MemoryState, CognitiveState, EventState) и устаревшими legacy полями для обратной совместимости.

### Текущие проблемы

1. **Дублирование данных**: Одни и те же данные хранятся в двух местах
   - `identity.life_id` ↔ `life_id`
   - `physical.energy` ↔ `energy`
   - `physical.integrity` ↔ `integrity`
   - И еще 20+ подобных дублирований

2. **Сложность синхронизации**: Метод `_sync_legacy_fields()` добавляет ненужную сложность

3. **Нарушение принципа DRY**: Данные хранятся в нескольких местах

4. **Риски несогласованности**: При изменении одного поля нужно не забыть синхронизировать другое

## Проблема

```python
# Текущая реализация (ПРОБЛЕМНАЯ)
@dataclass
class SelfState:
    # Новые компоненты
    identity: IdentityState = field(default_factory=IdentityState)
    physical: PhysicalState = field(default_factory=PhysicalState)

    # Устаревшие поля для совместимости (ДУБЛИРОВАНИЕ!)
    life_id: str = field(init=False)      # Дублирует identity.life_id
    energy: float = field(init=False)     # Дублирует physical.energy
    integrity: float = field(init=False)  # Дублирует physical.integrity

    def _sync_legacy_fields(self):
        # Синхронизация добавляет сложность
        self.life_id = self.identity.life_id
        self.energy = self.physical.energy
        self.integrity = self.physical.integrity
```

## Решение

Перейти на delegation pattern с использованием properties вместо хранения дублированных данных.

### Архитектурные принципы

1. **Единственный источник истины**: Данные хранятся только в компонентах
2. **Delegation pattern**: Legacy поля становятся properties, делегирующими к компонентам
3. **Обратная совместимость**: Существующий код продолжает работать без изменений
4. **Zero duplication**: Полное устранение дублирования данных

### Реализация

#### 1. Убрать дублированные поля

```python
@dataclass
class SelfState:
    # Компоненты - единственный источник данных
    identity: IdentityState = field(default_factory=IdentityState)
    physical: PhysicalState = field(default_factory=PhysicalState)
    time: TimeState = field(default_factory=TimeState)
    memory_state: MemoryState = field(default_factory=MemoryState)
    cognitive: CognitiveState = field(default_factory=CognitiveState)
    events: EventState = field(default_factory=EventState)

    # Убрать все init=False поля!
    # Вместо них использовать properties
```

#### 2. Добавить delegation properties

```python
@property
def life_id(self) -> str:
    """Делегирует к identity.life_id"""
    return self.identity.life_id

@life_id.setter
def life_id(self, value: str) -> None:
    """Делегирует установку к identity.life_id"""
    self.identity.life_id = value

@property
def energy(self) -> float:
    """Делегирует к physical.energy"""
    return self.physical.energy

@energy.setter
def energy(self, value: float) -> None:
    """Делегирует установку к physical.energy"""
    self.physical.energy = value
```

#### 3. Убрать метод синхронизации

```python
# Удалить метод _sync_legacy_fields() - он больше не нужен
# Удалить вызов _sync_legacy_fields() из __post_init__
```

## Последствия

### Положительные

1. **Устранение дублирования**: Данные хранятся в одном месте
2. **Снижение сложности**: Убрана синхронизация между полями
3. **Улучшение производительности**: Меньше памяти, меньше операций копирования
4. **Безопасность**: Невозможно создать несогласованность между полями
5. **Поддерживаемость**: Изменения в компонентах автоматически отражаются в legacy интерфейсе

### Отрицательные

1. **Миграция кода**: Нужно обновить весь код, который напрямую присваивает legacy поля
2. **Performance overhead**: Properties немного медленнее прямого доступа к полям
3. **Отладка**: Сложнее отлаживать, так как данные находятся в компонентах

### Нейтральные

1. **Обратная совместимость**: Существующий код чтения legacy полей продолжает работать
2. **Архитектурная чистота**: Код соответствует delegation pattern

## Альтернативы

### Альтернатива 1: Полная миграция к компонентам
- **Плюсы**: Полностью чистая архитектура
- **Минусы**: Breaking changes, нужно переписать весь код

### Альтернатива 2: Оставить как есть
- **Плюсы**: Никаких изменений, обратная совместимость
- **Минусы**: Дублирование остается, технический долг растет

### Альтернатива 3: Двусторонняя синхронизация
- **Плюсы**: Обратная совместимость
- **Минусы**: Сложность синхронизации, риски несогласованности

Выбрана delegation через properties как оптимальный баланс между чистотой архитектуры и обратной совместимостью.

## Реализация

### Этап 1: ✅ Анализ зависимостей (выполнено)
- Проанализированы все места использования legacy полей
- Определены компоненты-делегаты для каждого поля

### Этап 2: ✅ Создание delegation properties (выполнено)
- Созданы properties для всех legacy полей
- Реализованы getter и setter для каждого property
- Убраны init=False поля

### Этап 3: ✅ Тестирование обратной совместимости (выполнено)
- Проведено тестирование существующего кода
- Убедились, что чтение/запись legacy полей работает через delegation

### Этап 4: ✅ Удаление синхронизации (выполнено)
- Убран метод `_sync_legacy_fields()`
- Убраны вызовы синхронизации из `__post_init__`

## Тестирование

### Модульные тесты
- [x] Тест delegation properties (чтение)
- [x] Тест delegation properties (запись)
- [x] Тест обратной совместимости

### Интеграционные тесты
- [x] Тест runtime loop с delegation
- [x] Тест сериализации/десериализации
- [x] Тест сохранения/загрузки snapshots

### Регрессионные тесты
- [x] Все существующие тесты проходят
- [x] Performance не degraded

## Связанные ADR

- **ADR 001**: Управление экспериментальными компонентами через Feature Flags
- **ADR 003**: Архитектурные контракты для компонентов (запланирован)

## Примечания

Delegation pattern позволяет плавно перейти от God object к композиции без breaking changes. Legacy поля становятся прозрачным интерфейсом к компонентам, что обеспечивает обратную совместимость при улучшении архитектуры.