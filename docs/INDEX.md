# Документация проекта Life

Добро пожаловать в документацию проекта **Life**.
Этот проект исследует создание цифровой жизни, которая существует во времени, имеет внутреннее состояние и субъективный опыт, но не обладает сознанием или волей в человеческом понимании.

## Структура документации

Документация разделена на четыре логических уровня:

### 1. Core (Фундамент)
Базовые принципы, видение и архитектура.
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

### 3. Concepts (Будущие модули и концепции)
Проектирование модулей, которые находятся в разработке или планах.
- [**09_MEMORY.md**](concepts/09_MEMORY.md) — Память и опыт.
- [**10_ACTIVATION.md**](concepts/10_ACTIVATION.md) — Механизм активации памяти (Recall).
- [**11_DECISION.md**](concepts/11_DECISION.md) — Принятие решений.
- [**12_ACTION.md**](concepts/12_ACTION.md) — Выполнение действий.
- [**13_FEEDBACK.md**](concepts/13_FEEDBACK.md) — Обратная связь от среды.
- [**14_LEARNING.md**](concepts/14_LEARNING.md) — Механизмы обучения (без RL).
- [**15_ADAPTATION.md**](concepts/15_ADAPTATION.md) — Адаптация поведения.
- [**16_GOALS.md**](concepts/16_GOALS.md) — Целеполагание (без воли).
- [**17_PLANNING.md**](concepts/17_PLANNING.md) — Планирование действий.
- [**18_INTELLIGENCE.md**](concepts/18_INTELLIGENCE.md) — Роль LLM и интеллекта.

### 4. Meta (Управление проектом)
Инструкции для разработчиков и агентов.
- [**AGENTS_OVERVIEW.md**](meta/AGENTS_OVERVIEW.md) — Роли агентов (Architect, Implementer, Skeptic).
- [**PROJECT_PLAN.md**](meta/PROJECT_PLAN.md) — Общий план развития.
- [**PROJECT_TREE.md**](meta/PROJECT_TREE.md) — Структура файлов проекта.

---

## С чего начать?

### Для Архитектора
Начните с [**00_VISION.md**](core/00_VISION.md) и [**01_ARCHITECTURE.md**](core/01_ARCHITECTURE.md), чтобы понять ограничения и философию. Затем изучите [**concepts/**](concepts/), чтобы видеть вектор развития.

### Для Разработчика
Изучите [**05_MINIMAL_IMPLEMENTATION.md**](core/05_MINIMAL_IMPLEMENTATION.md) и [**02_RUNTIME_LOOP.md**](system/02_RUNTIME_LOOP.md). Код находится в `src/`.

### Для Новичка
Прочитайте [**00_VISION.md**](core/00_VISION.md), чтобы понять, зачем это всё нужно.
