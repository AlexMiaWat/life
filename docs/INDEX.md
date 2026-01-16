# Документация проекта Life

Добро пожаловать в документацию проекта **Life**.
Этот проект исследует создание цифровой жизни, которая существует во времени, имеет внутреннее состояние и субъективный опыт, но не обладает сознанием или волей в человеческом понимании.

## Структура документации

Документация разделена на четыре логических уровня:

### 1. Core (Фундамент)
Базовые принципы, видение и архитектура.
- [**BASELINE_STATE.md**](BASELINE_STATE.md) — Базовое состояние проекта. Фиксация отправной точки эволюции.
- [**00_VISION.md**](core/00_VISION.md) — Философия и видение проекта. Что такое Life и чем она не является.
- [**01_ARCHITECTURE.md**](core/01_ARCHITECTURE.md) — Высокоуровневая архитектура системы. Слои и потоки данных.
- [**05_MINIMAL_IMPLEMENTATION.md**](core/05_MINIMAL_IMPLEMENTATION.md) — Описание текущей минимальной реализации (MVP).

### 2. System (Реализованные подсистемы)
Детальное описание уже работающих модулей.
- [**02_RUNTIME_LOOP.md**](system/02_RUNTIME_LOOP.md) — Главный цикл жизни. Время и последовательность тактов.
- [**03_SELF_STATE.md**](system/03_SELF_STATE.md) — Внутреннее состояние (Self-State). Физика существования.
- [**04_MONITOR.md**](system/04_MONITOR.md) — Система наблюдения и логирования.
- [**06_API_SERVER.md**](system/06_API_SERVER.md) — API для управления и наблюдения.
- [**07_ENVIRONMENT.md**](system/07_ENVIRONMENT.md) — Внешняя среда и генерация событий.
- [**08_EVENTS_AND_MEANING.md**](system/08_EVENTS_AND_MEANING.md) — Система интерпретации событий (Meaning Engine).
- [**09.1_Memory_Entry.md**](system/09.1_Memory_Entry.md) — Память и опыт (реализовано v1.0).
- [**10.1_ACTIVATION_Memory.md**](system/10.1_ACTIVATION_Memory.md) — Активация памяти (реализовано v1.0).
- [**11.1_DECISION_Work.md**](system/11.1_DECISION_Work.md) — Принятие решений (реализовано v1.0).
- [**12.1_ACTION_Work.md**](system/12.1_ACTION_Work.md) — Выполнение действий (реализовано v1.0).
- [**13.1_FEEDBACK_Work.md**](system/13.1_FEEDBACK_Work.md) — Обратная связь (архитектурная спецификация, готово к реализации).

### 3. Concepts (Концепции и будущие модули)
Проектирование модулей, которые находятся в разработке или планах.
- [**09_MEMORY.md**](concepts/09_MEMORY.md) — Память и опыт (концепция).
- [**10_ACTIVATION.md**](concepts/10_ACTIVATION.md) — Механизм активации памяти (концепция).
- [**11_DECISION.md**](concepts/11_DECISION.md) — Принятие решений (концепция).
- [**12_ACTION.md**](concepts/12_ACTION.md) — Выполнение действий (концепция).
- [**13_FEEDBACK.md**](concepts/13_FEEDBACK.md) — Обратная связь от среды.
- [**14_LEARNING.md**](concepts/14_LEARNING.md) — Механизмы обучения (без RL).
- [**15_ADAPTATION.md**](concepts/15_ADAPTATION.md) — Адаптация поведения.
- [**16_GOALS.md**](concepts/16_GOALS.md) — Целеполагание (без воли).
- [**17_PLANNING.md**](concepts/17_PLANNING.md) — Планирование действий (реализовано v1.0).
- [**18_INTELLIGENCE.md**](concepts/18_INTELLIGENCE.md) — Роль LLM и интеллекта (реализовано v1.0).

### 4. Meta (Управление проектом)
Инструкции для разработчиков и агентов.
- [**AGENTS_OVERVIEW.md**](meta/AGENTS_OVERVIEW.md) — Роли агентов (Architect, Implementer, Skeptic).
- [**PROJECT_PLAN.md**](meta/PROJECT_PLAN.md) — Общий план развития.
- [**PROJECT_TREE.md**](meta/PROJECT_TREE.md) — Структура файлов проекта.

### 5. Test (Тестирование)
Документация по тестированию проекта.
- [**README.md**](test/README.md) — Обзор тестирования и быстрый старт.
- [**TESTING_INSTRUCTIONS.md**](test/TESTING_INSTRUCTIONS.md) — Подробные инструкции по тестированию.
- [**TESTING_RESULTS.md**](test/TESTING_RESULTS.md) — Результаты тестирования.
- [**COVERAGE_100_COMPLETE.md**](test/COVERAGE_100_COMPLETE.md) — Отчет о достижении максимального покрытия (96%).

### 6. Archive (Архив)
Архивные документы и предыдущие версии концепций.
- [**01.1_runtime_skeleton.md**](archive/01.1_runtime_skeleton.md) — Скелет рантайма.
- [**02.1_interpretations.md**](archive/02.1_interpretations.md) — Интерпретации.
- [**04.0_pre_monitor.md**](archive/04.0_pre_monitor.md) — Предварительный монитор.
- [**07_environment_architecture.md**](archive/07_environment_architecture.md) — Архитектура среды.
- [**11.1_decision_limits.md**](archive/11.1_decision_limits.md) — Лимиты решений.
- [**11.2_decision_minimal_form.md**](archive/11.2_decision_minimal_form.md) — Минимальная форма решений.
- [**12_action_limits.md**](archive/12_action_limits.md) — Лимиты действий.
- [**12.1_action_minimal_form.md**](archive/12.1_action_minimal_form.md) — Минимальная форма действий.
- [**12.3_ACTION_FEEDBACK_INTERFACE.md**](archive/12.3_ACTION_FEEDBACK_INTERFACE.md) — Интерфейс обратной связи действий.
- [**13.1_feedback_minimal_form.md**](archive/13.1_feedback_minimal_form.md) — Минимальная форма обратной связи.
- [**13.2_Feedback_Activation.md**](archive/13.2_Feedback_Activation.md) — Активация обратной связи.
- [**14_ADAPTATION.md**](archive/14_ADAPTATION.md) — Адаптация.
- [**14.1_ADAPTATION_MINIMAL_FORM.md**](archive/14.1_ADAPTATION_MINIMAL_FORM.md) — Минимальная форма адаптации.
- [**14.1_learning_minimal_form.md**](archive/14.1_learning_minimal_form.md) — Минимальная форма обучения.
- [**15.1_adaptation_minimal_form.md**](archive/15.1_adaptation_minimal_form.md) — Минимальная форма адаптации.
- [**16.1_goals_minimal_form.md**](archive/16.1_goals_minimal_form.md) — Минимальная форма целей.
- [**17.1_planning_minimal_form.md**](archive/17.1_planning_minimal_form.md) — Минимальная форма планирования.
- [**18.1_intelligence_minimal_form.md**](archive/18.1_intelligence_minimal_form.md) — Минимальная форма интеллекта.
- [**life_action_diagram.png**](archive/life_action_diagram.png) — Диаграмма действий жизни.

### 7. Skeptic (Скептик)
Документы критического анализа и скептического подхода.
- Директория пока пуста.

---

## С чего начать?

### Для Архитектора
Начните с [**00_VISION.md**](core/00_VISION.md) и [**01_ARCHITECTURE.md**](core/01_ARCHITECTURE.md), чтобы понять ограничения и философию. Затем изучите [**concepts/**](concepts/), чтобы видеть вектор развития.

### Для Разработчика
Изучите [**05_MINIMAL_IMPLEMENTATION.md**](core/05_MINIMAL_IMPLEMENTATION.md) и [**02_RUNTIME_LOOP.md**](system/02_RUNTIME_LOOP.md). Код находится в `src/`.

### Для Новичка
Прочитайте [**00_VISION.md**](core/00_VISION.md), чтобы понять, зачем это всё нужно.
