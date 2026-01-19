# Проверка соответствия документации структуре проекта

**Дата:** 2026-01-26
**Статус:** ✅ Исправлено

---

## Проблемы, которые были найдены и исправлены

### 1. ✅ Ссылки на старую структуру в development/

**Проблема:** Документы ссылались на несуществующие директории:
- `docs/core/` → должно быть `docs/getting-started/` и `docs/architecture/`
- `docs/system/` → должно быть `docs/components/`
- `docs/meta/` → должно быть `docs/development/`
- `docs/skeptic/` → должно быть `docs/reviews/`

**Исправлено в:**
- `docs/development/llm-instructions.md` ✅
- `docs/development/agents-overview.md` ✅
- `docs/development/agent-architect.md` ✅
- `docs/development/agent-implementer.md` ✅
- `docs/development/agent-skeptic.md` ✅
- `docs/development/IMPLEMENTATION_TASK_FEEDBACK.md` ✅

### 2. ✅ Ссылки на старые имена файлов

**Проблема:** Ссылки на файлы со старыми именами:
- `AGENTS_OVERVIEW.md` → `agents-overview.md`
- `AGENT_ARCHITECT.md` → `agent-architect.md`
- `PROJECT_STATUS.md` → `status.md`
- `13.1_FEEDBACK_Work.md` → `feedback.md`

**Исправлено:** Все ссылки обновлены на новые имена.

### 3. ✅ Устаревшие ссылки в reviews/

**Проблема:** `docs/reviews/conflicts.md` ссылался на несуществующие файлы:
- `docs/meta/PROJECT_TREE.md`
- `docs/meta/PROJECT_PLAN.md`
- `docs/meta/NOW.md`

**Исправлено:** Все ссылки обновлены на `docs/development/status.md`.

---

## Текущая структура документации

```
docs/
├── getting-started/      # Для новичков
│   ├── introduction.md
│   ├── vision.md
│   ├── setup.md
│   └── baseline.md
│
├── architecture/         # Архитектура
│   ├── overview.md
│   └── minimal-implementation.md
│
├── components/           # Компоненты
│   ├── runtime-loop.md
│   ├── self-state.md
│   ├── memory.md
│   ├── decision.md
│   ├── action.md
│   └── feedback.md
│
├── concepts/            # Концепции
│   ├── memory-concept.md
│   ├── decision-concept.md
│   └── ...
│
├── development/         # Для разработчиков
│   ├── status.md          # Единый источник истины
│   ├── agents-overview.md
│   ├── agent-architect.md
│   ├── agent-implementer.md
│   └── llm-instructions.md
│
├── testing/            # Тестирование
├── reviews/            # Критический анализ
└── archive/            # Архив
```

---

## Проверка соответствия

### ✅ Ссылки обновлены

Все документы теперь ссылаются на новую структуру:
- `docs/core/` → `docs/getting-started/` или `docs/architecture/`
- `docs/system/` → `docs/components/`
- `docs/meta/` → `docs/development/`
- `docs/skeptic/` → `docs/reviews/`

### ✅ Имена файлов обновлены

Все ссылки используют kebab-case:
- `AGENTS_OVERVIEW.md` → `agents-overview.md`
- `PROJECT_STATUS.md` → `status.md`
- `13.1_FEEDBACK_Work.md` → `feedback.md`

### ✅ Пути к коду актуальны

Ссылки на `src/` остались актуальными, так как структура кода не менялась.

---

## Рекомендации

1. ✅ **Регулярно проверять ссылки** — при изменении структуры обновлять ссылки
2. ✅ **Использовать относительные пути** — для переносимости
3. ✅ **Проверять ссылки автоматически** — можно использовать скрипты или CI

---

*Документация теперь полностью соответствует новой структуре проекта.*
