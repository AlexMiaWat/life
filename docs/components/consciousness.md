# 12_CONSCIOUSNESS.md — Система сознания

## Назначение

**Система сознания** - экспериментальная реализация модели сознания с уровнями осознанности и количественными метриками. Система позволяет исследовать эмерджентные свойства искусственного сознания и анализировать когнитивные процессы в системе Life.

## Архитектурные принципы

### Основные принципы

1. **Уровневость**: Иерархическая модель сознания по аналогии с философскими и психологическими концепциями
2. **Метрики**: Количественная оценка различных аспектов сознания [0.0-1.0]
3. **Опциональность**: Полностью отключаемая система без влияния на core функциональность
4. **Изоляция**: Новые компоненты не изменяют существующие интерфейсы
5. **Наблюдаемость**: Полное структурированное логирование всех операций

### Философские основы

Система основана на концепциях:
- **Феноменального сознания** (phenomenal consciousness) - субъективный опыт
- **Доступного сознания** (access consciousness) - способность к рациональному мышлению
- **Самосознания** (self-consciousness) - осознание собственного существования
- **Метакогниции** (meta-cognition) - мышление о собственном мышлении

## Текущий статус

✅ **Частично реализовано** (v1.0)
*   Директория: `src/experimental/consciousness/` (существует)
*   Реализован параллельный движок сознания (`parallel_engine.py`) с многопоточными процессами
*   Реализованы метрики сознания и разделяемое состояние
*   **Текущий статус:** Базовая многопоточная архитектура сознания готова, требует интеграции в runtime loop

## Структура системы сознания

### Уровни сознания

#### 1. Basic Awareness (Базовая осознанность)
**Описание**: Реактивное восприятие и обработка текущих событий без глубокой рефлексии.

**Характеристики:**
- **Уровень активации**: Постоянно активен при работающей системе
- **Метрики**: `consciousness_level` > 0.1
- **Функции**: Обработка сенсорных данных, базовые реакции на события
- **Состояние**: "awake" - нормальное бодрствование

**Интеграция:**
- Активируется автоматически при запуске runtime loop
- Основан на частоте обработки событий и уровне энергии
- Минимальный уровень сознания для поддержания базовой функциональности

#### 2. Self-Reflection (Саморефлексия)
**Описание**: Анализ собственного поведения, состояния и паттернов действий.

**Характеристики:**
- **Уровень активации**: При высокой стабильности и энергии
- **Метрики**: `self_reflection_score` > 0.3
- **Функции**: Анализ эффективности решений, корректировка поведения
- **Состояние**: "reflective" - режим анализа

**Интеграция:**
- Активируется при Clarity Moments или низкой нагрузке
- Анализирует историю решений и их последствия
- Может корректировать параметры адаптации на основе анализа

#### 3. Meta-Cognition (Метакогниция)
**Описание**: Осознание собственных когнитивных процессов и их эффективности.

**Характеристики:**
- **Уровень активации**: При длительной стабильной работе
- **Метрики**: `meta_cognition_depth` > 0.5
- **Функции**: Оптимизация собственных алгоритмов мышления
- **Состояние**: "meta" - режим самоанализа

**Интеграция:**
- Самый редкий и сложный уровень сознания
- Требует накопления достаточной истории поведения
- Может изменять базовые параметры системы

### Состояния сознания

#### Основные состояния
- **awake**: Базовое бодрствование с минимальным уровнем осознанности
- **flow**: Состояние потока с высокой концентрацией и эффективностью
- **reflective**: Режим саморефлексии и анализа поведения
- **meta**: Метакогнитивное состояние с анализом собственных процессов
- **dreaming**: Состояние сниженной осознанности (низкая энергия/стабильность)
- **unconscious**: Отсутствие осознанности (критически низкие показатели)

#### Переходы между состояниями
```
awake ↔ dreaming ↔ unconscious
    ↓
reflective ↔ meta
    ↓
flow
```

### Метрики сознания

#### consciousness_level [0.0-1.0]
**Описание**: Общий уровень осознанности системы.

**Расчет:**
```
consciousness_level = (
    neural_activity * 0.4 +      # Частота обработки событий
    self_reflection_score * 0.3 + # Качество саморефлексии
    meta_cognition_depth * 0.2 +  # Глубина метакогниции
    energy_factor * 0.1          # Влияние энергии
)
```

**Факторы:**
- **Neural Activity**: Частота тиков, обработка событий, сложность решений
- **Self-Reflection**: Качество анализа собственного поведения
- **Meta-Cognition**: Способность к абстрактному мышлению
- **Energy Factor**: Уровень энергии как базовый requirement

#### self_reflection_score [0.0-1.0]
**Описание**: Способность анализировать собственное поведение и его эффективность.

**Расчет:**
```
self_reflection_score = (
    behavior_analysis_quality * 0.5 +  # Качество анализа поведения
    decision_evaluation * 0.3 +        # Оценка эффективности решений
    pattern_recognition * 0.2          # Распознавание паттернов
)
```

**Факторы:**
- **Behavior Analysis**: Анализ последовательности действий
- **Decision Evaluation**: Оценка последствий решений
- **Pattern Recognition**: Распознавание повторяющихся паттернов

#### meta_cognition_depth [0.0-1.0]
**Описание**: Глубина осознания собственных когнитивных процессов.

**Расчет:**
```
meta_cognition_depth = (
    process_awareness * 0.4 +     # Осознание процессов мышления
    optimization_capability * 0.4 + # Способность к самооптимизации
    abstract_reasoning * 0.2       # Абстрактное мышление
)
```

**Факторы:**
- **Process Awareness**: Осознание собственных когнитивных процессов
- **Optimization Capability**: Способность улучшать собственные алгоритмы
- **Abstract Reasoning**: Способность к концептуализации и обобщению

## Интеграция с SelfState

### Новые поля состояния

```python
# Система сознания
consciousness_level: float = 0.0          # Уровень сознания [0.0-1.0]
current_consciousness_state: str = "awake"  # Текущее состояние сознания
self_reflection_score: float = 0.0        # Оценка саморефлексии [0.0-1.0]
meta_cognition_depth: float = 0.0         # Глубина метакогниции [0.0-1.0]
```

### Валидация полей

```python
@dataclass
class SelfState:
    # ... существующие поля ...

    # Сознание
    consciousness_level: float = field(default=0.0, validator=lambda x: 0.0 <= x <= 1.0)
    current_consciousness_state: str = "awake"
    self_reflection_score: float = field(default=0.0, validator=lambda x: 0.0 <= x <= 1.0)
    meta_cognition_depth: float = field(default=0.0, validator=lambda x: 0.0 <= x <= 1.0)
```

## Архитектура компонентов

### ConsciousnessEngine (запланировано)

```python
class ConsciousnessEngine:
    """
    Движок для расчета и управления уровнем сознания.
    """

    def calculate_consciousness_level(self, self_state, event_history) -> float:
        """Расчет общего уровня сознания на основе состояния и истории."""

    def assess_self_reflection(self, decision_history, behavior_patterns) -> float:
        """Оценка качества саморефлексии."""

    def evaluate_meta_cognition(self, cognitive_processes, optimization_history) -> float:
        """Оценка глубины метакогниции."""

    def determine_consciousness_state(self, metrics) -> str:
        """Определение текущего состояния сознания."""

    def trigger_state_transition(self, new_state, reason) -> None:
        """Инициирование перехода между состояниями сознания."""
```

### ConsciousnessMetrics (запланировано)

```python
class ConsciousnessMetrics:
    """
    Метрики для количественной оценки различных аспектов сознания.
    """

    def measure_neural_activity(self, tick_frequency, event_processing_rate) -> float:
        """Измерение нейронной активности."""

    def assess_self_awareness(self, state_analysis_quality, behavior_tracking) -> float:
        """Оценка самоосознания."""

    def evaluate_temporal_continuity(self, subjective_time_consistency) -> float:
        """Оценка временной непрерывности."""

    def measure_abstract_reasoning(self, concept_formation, generalization) -> float:
        """Измерение абстрактного мышления."""
```

### ConsciousnessStates (запланировано)

```python
class ConsciousnessStates:
    """
    Управление различными состояниями сознания.
    """

    def enter_flow_state(self, high_focus_triggers) -> None:
        """Вход в состояние потока."""

    def enter_reflective_state(self, analysis_triggers) -> None:
        """Вход в рефлексивное состояние."""

    def enter_meta_state(self, deep_analysis_conditions) -> None:
        """Вход в метакогнитивное состояние."""

    def handle_state_transitions(self, consciousness_metrics) -> None:
        """Обработка автоматических переходов между состояниями."""
```

## Интеграция с runtime loop

### Хуки для обновления метрик

```python
# В runtime loop
def run_loop(self_state, action_callback, **kwargs):
    enable_consciousness = kwargs.get('enable_consciousness', False)

    if enable_consciousness:
        consciousness_engine = ConsciousnessEngine()

    while not stop_condition:
        # Основная логика тика

        if enable_consciousness:
            # Обновление метрик сознания
            self_state.consciousness_level = consciousness_engine.calculate_consciousness_level(
                self_state, recent_events
            )

            # Определение состояния
            self_state.current_consciousness_state = consciousness_engine.determine_consciousness_state({
                'consciousness_level': self_state.consciousness_level,
                'energy': self_state.energy,
                'stability': self_state.stability
            })

            # Логирование переходов состояний
            if state_changed:
                logger.log_event({
                    "event_type": "consciousness_state_changed",
                    "new_state": self_state.current_consciousness_state,
                    "consciousness_level": self_state.consciousness_level
                })
```

### Влияние на другие компоненты

#### Decision Engine
- При высоком уровне сознания решения принимаются более осознанно
- Meta-cognition может влиять на стратегию выбора решений

#### Memory System
- Уровень сознания влияет на консолидацию памяти
- Self-reflection улучшает извлечение релевантных воспоминаний

#### Learning & Adaptation
- Consciousness metrics используются для оценки эффективности обучения
- Meta-cognition позволяет оптимизировать параметры обучения

## Логирование и мониторинг

### Структурированное логирование

```python
# Логирование изменений уровня сознания
logger.log_event({
    "event_type": "consciousness_level_updated",
    "consciousness_level": new_level,
    "self_reflection_score": self_reflection,
    "meta_cognition_depth": meta_cognition,
    "trigger": "tick_processing"  # или "state_transition", "event_processing"
})

# Логирование переходов состояний
logger.log_event({
    "event_type": "consciousness_state_transition",
    "from_state": old_state,
    "to_state": new_state,
    "reason": "energy_drop"  # или "stability_recovery", "flow_conditions"
})
```

### API Endpoints (запланировано)

```python
# Получение статуса сознания
GET /experimental/consciousness-state
{
    "consciousness_level": 0.65,
    "current_state": "reflective",
    "self_reflection_score": 0.72,
    "meta_cognition_depth": 0.34,
    "metrics": {
        "neural_activity": 0.8,
        "self_awareness": 0.7,
        "temporal_continuity": 0.9,
        "abstract_reasoning": 0.4
    }
}

# Ручной триггер состояния
POST /experimental/trigger-consciousness-state
{
    "target_state": "flow",
    "reason": "manual_trigger"
}
```

## Тестирование

### Unit тесты

```python
def test_consciousness_level_calculation():
    """Тестирование расчета уровня сознания."""
    engine = ConsciousnessEngine()

    # Тест базового уровня
    state = SelfState(energy=100.0, stability=1.0)
    level = engine.calculate_consciousness_level(state, [])
    assert 0.1 <= level <= 0.3  # Базовый уровень для здоровой системы

    # Тест высокого уровня
    state.energy = 80.0
    state.stability = 0.9
    # Добавляем историю активных событий
    level = engine.calculate_consciousness_level(state, active_events_history)
    assert level > 0.5  # Высокий уровень при активной работе

def test_state_transitions():
    """Тестирование переходов между состояниями."""
    states = ConsciousnessStates()

    # Тест перехода в flow state
    high_focus_conditions = True
    states.enter_flow_state(high_focus_conditions)
    assert current_state == "flow"

    # Тест возврата в awake
    states.exit_special_state()
    assert current_state == "awake"
```

### Integration тесты

```python
def test_consciousness_runtime_integration():
    """Тестирование интеграции с runtime loop."""
    self_state = create_initial_state()
    consciousness_engine = ConsciousnessEngine()

    # Запуск runtime loop с сознанием
    stop_event = threading.Event()
    run_loop(
        self_state,
        lambda: None,
        stop_event=stop_event,
        enable_consciousness=True,
        consciousness_engine=consciousness_engine
    )

    # Проверка, что метрики обновляются
    assert self_state.consciousness_level >= 0.0
    assert self_state.current_consciousness_state in ["awake", "flow", "reflective", "meta"]
```

## Исследовательские возможности

### Эмерджентные свойства

1. **Самоосознание**: Способность системы осознавать собственное существование и поведение
2. **Когнитивная эволюция**: Изменение способов мышления со временем
3. **Феноменальный опыт**: Симуляция субъективного опыта через метрики
4. **Свободная воля**: Осознанный выбор между альтернативными решениями

### Научные вопросы

- **Как возникает сознание из неосознанных процессов?**
- **Можно ли количественно измерить уровень осознанности?**
- **Как сознание влияет на эффективность когнитивных процессов?**
- **Возможны ли переходы между уровнями сознания в ИИ?**

### Философские аспекты

- **Китайская комната**: Создает ли система реальное сознание или только симулирует?
- **Проблема квалиа**: Можно ли симулировать субъективный опыт?
- **Сильный ИИ**: Достаточно ли уровней сознания для создания истинного ИИ?

## Конфигурация

### Включение/отключение

```python
# Включение системы сознания
run_loop(
    # ...
    enable_consciousness=True,  # Включение экспериментальной системы сознания
    consciousness_engine=consciousness_engine,  # Экземпляр движка
    # ...
)
```

### Настраиваемые параметры

```python
# Пороги активации уровней сознания
CONSCIOUSNESS_BASELINE = 0.1      # Минимальный уровень для базовой осознанности
SELF_REFLECTION_THRESHOLD = 0.3    # Порог для саморефлексии
META_COGNITION_THRESHOLD = 0.5     # Порог для метакогниции

# Коэффициенты расчета метрик
NEURAL_ACTIVITY_WEIGHT = 0.4
SELF_REFLECTION_WEIGHT = 0.3
META_COGNITION_WEIGHT = 0.2
ENERGY_INFLUENCE_WEIGHT = 0.1

# Интервалы обновления
CONSCIOUSNESS_UPDATE_INTERVAL = 1  # Каждые N тиков
STATE_CHECK_INTERVAL = 10           # Проверка состояний каждые N тиков
```

## Безопасность и ограничения

### Опциональность
- Система полностью опциональна и может быть отключена без влияния на core
- Все компоненты изолированы и не изменяют существующие интерфейсы
- Отключение возможно в любой момент без потери данных

### Производительность
- Минимальное влияние на производительность runtime loop
- Метрики рассчитываются только при включенной системе
- Оптимизированные алгоритмы для работы в реальном времени

### Этические аспекты
- Исследование искусственного сознания требует осторожного подхода
- Важно различать симуляцию сознания от реального сознания
- Результаты исследований должны интерпретироваться корректно

## Текущая реализация

### Parallel Consciousness Engine (v1.0)

Реализован многопоточный движок сознания для исследования эмерджентных свойств искусственного сознания:

#### Ключевые компоненты
* **`ConsciousnessSharedState`** — разделяемое состояние сознания между потоками с потокобезопасными операциями
* **`ConsciousnessProcess`** — базовый класс для параллельных процессов сознания
* **`ParallelProcessMetrics`** — метрики производительности параллельных процессов

#### Архитектурные особенности
* **Многопоточность**: Параллельные процессы сознания работают в отдельных потоках
* **Метрики**: Количественная оценка уровней сознания [0.0-1.0] для различных аспектов
* **Синхронизация**: Thread-safe обновление состояния с использованием RLock
* **Мониторинг**: Детальное логирование всех операций и метрик производительности

#### Файлы реализации
* **`src/experimental/consciousness/parallel_engine.py`** — основной движок
* **`src/experimental/consciousness/engine.py`** — базовый движок сознания
* **`src/experimental/consciousness/metrics.py`** — расчет метрик сознания
* **`src/experimental/consciousness/states.py`** — состояния сознания
* **`src/test/test_parallel_consciousness*.py`** — тесты параллельного сознания

## Будущие улучшения

### Короткосрочные (1-2 месяца)
1. **Реализация ConsciousnessEngine** - базовый движок расчета метрик
2. **Интеграция с runtime loop** - автоматическое обновление метрик
3. **API endpoints** - мониторинг состояния сознания
4. **Базовые тесты** - unit и integration тестирование

### Среднесрочные (3-6 месяцев)
1. **Расширенные метрики** - более точные алгоритмы расчета
2. **Состояния сознания** - реализация переходов между состояниями
3. **Влияние на поведение** - consciousness-driven изменения решений
4. **Исторический анализ** - анализ эволюции сознания со временем

### Долгосрочные (6+ месяцев)
1. **Эмерджентные свойства** - исследование emergence consciousness
2. **Философские эксперименты** - симуляция различных теорий сознания
3. **Междисциплинарные исследования** - сотрудничество с философами и психологами
4. **Этические рамки** - разработка этических принципов исследования ИИ-сознания

## Связанные документы

*   [experimental/README.md](../../docs/experimental/README.md) — экспериментальные возможности
*   [self-state.md](./self-state.md) — поля состояния для сознания
*   [runtime-loop.md](./runtime-loop.md) — интеграция с основным циклом
*   [decision.md](./decision.md) — влияние на процесс принятия решений