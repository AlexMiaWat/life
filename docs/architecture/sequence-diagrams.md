# Диаграммы последовательности основных потоков

> **Назначение:** Визуализация основных потоков данных и взаимодействия компонентов в системе Life

## 1. Runtime Loop - главный цикл жизни

```mermaid
sequenceDiagram
    participant RL as RuntimeLoop
    participant SS as SelfState
    participant EQ as EventQueue
    participant ME as MeaningEngine
    participant AM as Activation
    participant DM as Decision
    participant AC as Action
    participant FB as Feedback
    participant PL as Planning
    participant IN as Intelligence
    participant LE as Learning
    participant AD as Adaptation
    participant MO as Monitor

    loop Каждый тик
        RL->>SS: Проверить is_active()
        alt Активен
            RL->>EQ: Получить события (pop_all())
            RL->>ME: Обработать события
            ME->>SS: Записать meaning
            RL->>AM: Активировать память
            AM->>SS: Записать activated_memory
            RL->>DM: Принять решение
            DM->>SS: Записать last_pattern
            RL->>SS: Применить impact (apply_delta)
            RL->>AC: Выполнить действие
            RL->>FB: Зарегистрировать действие
            RL->>PL: Записать последовательности
            RL->>IN: Обработать информацию
            RL->>LE: Обучить (каждые 50 тиков)
            LE->>SS: Обновить learning_params
            RL->>AD: Адаптировать (после Learning)
            AD->>SS: Обновить adaptation_params
            RL->>MO: Мониторить состояние
        end
    end
```

## 2. Event Processing - обработка событий

```mermaid
sequenceDiagram
    participant API as API Server
    participant EQ as EventQueue
    participant RL as RuntimeLoop
    participant ME as MeaningEngine
    participant AM as Activation
    participant DM as Decision
    participant SS as SelfState

    API->>EQ: POST /event (событие)
    EQ->>RL: tick() - pop_all()
    RL->>ME: process(event, self_state)
    ME->>ME: appraisal() - вычислить significance
    ME->>ME: impact_model() - рассчитать deltas
    ME->>ME: response_pattern() - выбрать паттерн
    ME->>RL: return Meaning
    RL->>AM: activate_memory(event.type, memory)
    AM->>RL: return activated_entries[]
    RL->>DM: decide_response(activated, meaning)
    DM->>RL: return pattern
    RL->>SS: apply_delta(meaning.impact)
    Note over RL,SS: Применить изменения к energy/stability/integrity
```

## 3. Learning Cycle - цикл обучения

```mermaid
sequenceDiagram
    participant RL as RuntimeLoop
    participant LE as LearningEngine
    participant SS as SelfState

    RL->>LE: process_statistics(memory)
    LE->>LE: Анализ паттернов событий
    LE->>LE: Извлечение частот и корреляций
    LE->>LE: adjust_parameters(stats, current_params)
    LE->>LE: Медленное изменение параметров (<=0.01)
    LE->>SS: record_changes(old, new, self_state)
    SS->>SS: Обновить learning_params
    Note over LE,SS: Параметры: event_type_sensitivity,<br/>significance_thresholds,<br/>response_coefficients
```

## 4. Adaptation Cycle - цикл адаптации

```mermaid
sequenceDiagram
    participant RL as RuntimeLoop
    participant AD as AdaptationManager
    participant LE as LearningEngine
    participant SS as SelfState

    RL->>AD: analyze_changes(learning_params)
    AD->>AD: Сравнить с текущими adaptation_params
    AD->>AD: Вычислить разницу (delta)
    AD->>AD: apply_adaptation(delta)
    AD->>AD: Медленное приближение (<=0.01)
    AD->>SS: Обновить adaptation_params
    AD->>SS: Сохранить в adaptation_history
    Note over AD,SS: Параметры: behavior_sensitivity,<br/>behavior_coefficients,<br/>adaptation_history
```

## 5. API Request Flow - обработка API запросов

```mermaid
sequenceDiagram
    participant Client as HTTP Client
    participant API as API Server
    participant SS as SelfState
    participant RL as RuntimeLoop

    Client->>API: GET /status
    API->>SS: Получить текущее состояние
    SS->>API: Вернуть данные
    API->>Client: JSON response

    Client->>API: POST /event
    API->>API: Валидация данных
    API->>RL: Отправить событие в очередь
    RL->>API: Подтверждение
    API->>Client: "Event accepted"

    Client->>API: GET /clear-data
    API->>SS: Очистить данные
    API->>API: Очистить логи и snapshots
    API->>Client: "Data cleared"
```

## 6. Memory Operations - операции с памятью

```mermaid
sequenceDiagram
    participant RL as RuntimeLoop
    participant ME as MeaningEngine
    participant MM as Memory
    participant FB as Feedback
    participant SS as SelfState

    ME->>MM: Добавить значимое событие (significance > 0)
    MM->>MM: append(MemoryEntry)
    MM->>MM: clamp_size() - ограничить размер

    RL->>MM: decay_weights() каждые 10 тиков
    MM->>MM: Уменьшить веса записей

    RL->>MM: archive_old_entries() каждые 50 тиков
    MM->>MM: Перенести старые записи в ArchiveMemory

    FB->>MM: Добавить запись о действии
    MM->>MM: append(FeedbackRecord)

    RL->>MM: activate_memory() при событии
    MM->>RL: Вернуть релевантные записи
```

## Легенда диаграмм

- **RuntimeLoop**: Главный цикл жизни системы
- **SelfState**: Внутреннее состояние системы
- **EventQueue**: Очередь событий из внешней среды
- **MeaningEngine**: Интерпретация значимости событий
- **Activation**: Активация релевантной памяти
- **Decision**: Принятие решений о паттернах реакции
- **Action**: Выполнение внутренних действий
- **Feedback**: Обратная связь и наблюдение последствий
- **Planning**: Фиксация потенциальных последовательностей
- **Intelligence**: Обработка информации
- **Learning**: Медленное обучение на статистике
- **Adaptation**: Медленная адаптация поведения
- **Monitor**: Система наблюдения и логирования

---

*Диаграммы созданы в формате Mermaid для интеграции в документацию.*