# 01_ARCHITECTURE.md — Архитектура системы

## Обзор

Архитектура Life построена по принципу **слоеного пирога**, где каждый следующий слой опирается на предыдущий, но не управляет им напрямую.

```mermaid
graph TD
    Env[Environment] -->|Events| Loop[Runtime Loop]
    Loop -->|Update| State[Self-State]
    Loop -->|Interpret| Meaning[Meaning Engine]
    Meaning -->|Impact| State
    Meaning -->|Trigger| Activation[Activation]
    Activation -->|Activated| Memory[Memory]
    Memory -->|Context| Decision[Decision Maker]
    State -->|Context| Decision
    Decision -->|Command| Action[Action Executor]
    Action -->|Effect| State
    Action -->|Record| Memory
    Action -.->|Observe| Feedback[Feedback]
    Feedback -->|Record| Memory
    Loop -->|Metrics| Planning[Planning]
    Loop -->|Metrics| Intelligence[Intelligence]

    subgraph "Core System"
        Loop
        State
    end

    subgraph "Perception & Memory"
        Meaning
        Activation
        Memory
    end

    subgraph "Cognitive Layers"
        Decision
        Action
        Feedback
    end

    subgraph "Higher Layers"
        Planning
        Intelligence
    end
```

## Слои системы

### 1. Runtime Loop (Сердцебиение)
Центральный цикл, который обеспечивает течение времени.
*   **Роль:** Оркестрация всех процессов.
*   **Документация:** [02_RUNTIME_LOOP.md](../system/02_RUNTIME_LOOP.md)

### 2. Self-State (Тело)
Хранилище текущего состояния системы.
*   **Роль:** Поддержание гомеостаза, накопление усталости, энергии, возраста.
*   **Документация:** [03_SELF_STATE.md](../system/03_SELF_STATE.md)

### 3. Environment (Среда)
Источник внешних событий и неопределенности.
*   **Роль:** Генерация стимулов (шум, шок, восстановление).
*   **Документация:** [07_ENVIRONMENT.md](../system/07_ENVIRONMENT.md)

### 4. Meaning Engine (Восприятие)
Интерпретатор событий. Переводит объективные факты в субъективный опыт.
*   **Роль:** Оценка значимости событий для конкретного состояния Life.
*   **Документация:** [08_EVENTS_AND_MEANING.md](../system/08_EVENTS_AND_MEANING.md)

### 5. Memory (Память)
Накопление опыта и эпизодических воспоминаний.
*   **Роль:** Хранение событий, состояний и действий для будущего использования.
*   **Документация:** [09_MEMORY.md](../concepts/09_MEMORY.md)

### 6. Activation (Активация)
Активация релевантной памяти по типу события.
*   **Роль:** Выбор подходящих воспоминаний для текущего контекста.
*   **Документация:** [10_ACTIVATION.md](../concepts/10_ACTIVATION.md)

### 7. Decision (Решение)
Выбор паттерна реакции на основе состояния и памяти.
*   **Роль:** Минимальный выбор следующего шага без планирования или оптимизации.
*   **Документация:** [11_DECISION.md](../concepts/11_DECISION.md)

### 8. Action (Действие)
Выполнение выбранного решения.
*   **Роль:** Атомарное выполнение действий с записью в память.
*   **Документация:** [12_ACTION.md](../concepts/12_ACTION.md)

### 9. Feedback (Обратная связь)
Фиксация последствий действий без оценки.
*   **Роль:** Наблюдение изменений состояния после действий и запись фактов для будущего использования.
*   **Документация:** [13.1_FEEDBACK_Work.md](../system/13.1_FEEDBACK_Work.md)

### 10. Planning (Планирование)
Фиксация потенциальных последовательностей событий.
*   **Роль:** Пассивная запись статистики без оценки или выполнения.
*   **Документация:** [17_PLANNING.md](../concepts/17_PLANNING.md)

### 11. Intelligence (Интеллект)
Сбор метрик и информации о системе.
*   **Роль:** Прокси-слой для измерения состояния без интерпретации.
*   **Документация:** [18_INTELLIGENCE.md](../concepts/18_INTELLIGENCE.md)

### 12. Monitor (Наблюдатель)
Инструмент для внешнего наблюдения за системой.
*   **Роль:** Визуализация состояния без вмешательства.
*   **Документация:** [04_MONITOR.md](../system/04_MONITOR.md)

### 13. API Server (Интерфейс)
Точка входа для управления и интеграции.
*   **Роль:** Запуск, остановка, подача внешних сигналов.
*   **Документация:** [06_API_SERVER.md](../system/06_API_SERVER.md)

## Потоки данных

1.  **Входящий поток:** Environment -> Event Queue -> Runtime Loop -> Meaning Engine -> Activation -> Memory -> Decision -> Action -> Self-State Update.
2.  **Поток памяти:** Events -> Memory (через Activation) -> Decision (как контекст).
3.  **Поток обратной связи:** Action -> Feedback (наблюдение через 3-10 тиков) -> Memory (запись фактов).
4.  **Поток метрик:** Runtime Loop -> Planning / Intelligence (пассивный сбор).
5.  **Поток наблюдения:** Self-State -> Monitor -> Logs / Console.

## Принципы взаимодействия

*   **Асинхронность:** Среда живет своей жизнью, Life — своей.
*   **Изоляция:** Слои знают только о соседях. Decision не знает о деталях реализации Loop.
*   **Необратимость:** Изменения в Self-State нельзя отменить, только компенсировать новыми изменениями.
