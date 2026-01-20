# План выполнения: Реализация search_mode (AND/OR/PHRASE) для search_docs/search_todo

> **Задача:** Реализовать `search_mode` (AND/OR/PHRASE) для `search_docs`/`search_todo`
> **Источник:** План `mcp_engine_redesign_ab76d85d`, подзадача #1 из задачи #1
> **Дата создания:** 2026-01-20
> **ID задачи:** task_1768893889

## 1. Обзор задачи

Текущая реализация `search_docs` и `search_todo` в `mcp_index.py` использует простой поиск подстроки без поддержки различных режимов поиска. Необходимо добавить поддержку трех режимов:

- **AND mode** (по умолчанию): все слова запроса должны присутствовать в документе
- **OR mode**: хотя бы одно слово запроса должно присутствовать
- **PHRASE mode**: точная фраза должна присутствовать в документе (определяется кавычками)

## 2. Текущее состояние

**Файл:** `mcp_index.py`

**Текущая реализация:**
- `search_docs(query: str, limit: int = 10)` - простой поиск подстроки
- `search_todo(query: str, limit: int = 10)` - простой поиск подстроки
- Поиск выполняется через `query_lower in content.lower()`

**Ограничения:**
- Нет поддержки многословных запросов
- Нет режимов поиска (AND/OR/PHRASE)
- Нет токенизации запроса

## 3. Целевое состояние

После реализации:
- `search_docs(query: str, search_mode: str = "AND", limit: int = 10)` - с поддержкой режимов
- `search_todo(query: str, search_mode: str = "AND", limit: int = 10)` - с поддержкой режимов
- Три режима поиска работают корректно
- Обратная совместимость сохранена (по умолчанию AND mode)

## 4. План реализации

### Этап 1: Токенизация запроса

**Шаг 1.1:** Создать функцию `_tokenize_query(query: str) -> tuple[str, list[str]]`
- Определяет режим поиска по наличию кавычек (PHRASE) или возвращает указанный режим
- Для PHRASE: извлекает фразу из кавычек
- Для AND/OR: разбивает запрос на слова, нормализует (lowercase, удаление пунктуации)
- Возвращает: `(mode, tokens_or_phrase)`

**Примеры:**
- `"test query"` → `("PHRASE", "test query")`
- `"test query"` (mode="OR") → `("OR", ["test", "query"])`
- `test query` → `("AND", ["test", "query"])` (по умолчанию)

### Этап 2: Реализация режимов поиска

**Шаг 2.1:** Реализовать AND mode
- Функция `_search_and(content: str, tokens: list[str]) -> bool`
- Проверяет, что все токены присутствуют в контенте
- Возвращает True, если все токены найдены

**Шаг 2.2:** Реализовать OR mode
- Функция `_search_or(content: str, tokens: list[str]) -> bool`
- Проверяет, что хотя бы один токен присутствует в контенте
- Возвращает True, если хотя бы один токен найден

**Шаг 2.3:** Реализовать PHRASE mode
- Функция `_search_phrase(content: str, phrase: str) -> bool`
- Ищет точную фразу в контенте (case-insensitive)
- Возвращает True, если фраза найдена

### Этап 3: Интеграция в существующие функции

**Шаг 3.1:** Обновить `search_docs`
- Добавить параметр `search_mode: str = "AND"`
- Использовать `_tokenize_query` для определения режима
- Применить соответствующий режим поиска вместо простого `in`

**Шаг 3.2:** Обновить `search_todo`
- Добавить параметр `search_mode: str = "AND"`
- Использовать ту же логику, что и в `search_docs`

**Шаг 3.3:** Сохранить обратную совместимость
- По умолчанию используется AND mode
- Старые вызовы без `search_mode` работают как раньше (но с улучшенной логикой)

### Этап 4: Тестирование

**Шаг 4.1:** Обновить существующие тесты
- Убедиться, что старые тесты проходят с новым кодом

**Шаг 4.2:** Добавить тесты для режимов
- Тест AND mode: запрос "test query" должен находить только документы с обоими словами
- Тест OR mode: запрос "test query" должен находить документы с любым из слов
- Тест PHRASE mode: запрос "test query" должен находить только документы с точной фразой

## 5. Детальная реализация

### 5.1. Функция токенизации

```python
def _tokenize_query(query: str, default_mode: str = "AND") -> tuple[str, list[str] | str]:
    """
    Токенизирует запрос и определяет режим поиска.

    Args:
        query: Поисковый запрос
        default_mode: Режим по умолчанию (AND/OR)

    Returns:
        Tuple (mode, tokens_or_phrase):
        - mode: "AND", "OR", или "PHRASE"
        - tokens_or_phrase: список токенов для AND/OR или строка для PHRASE
    """
    query = query.strip()

    # Проверка на PHRASE mode (кавычки)
    if query.startswith('"') and query.endswith('"') and len(query) > 2:
        phrase = query[1:-1].strip()
        return ("PHRASE", phrase)

    # Токенизация для AND/OR
    import re
    # Разбиваем на слова, удаляем пунктуацию
    tokens = re.findall(r'\b\w+\b', query.lower())
    return (default_mode, tokens)
```

### 5.2. Функции поиска по режимам

```python
def _search_and(content: str, tokens: list[str]) -> bool:
    """Проверяет, что все токены присутствуют в контенте."""
    content_lower = content.lower()
    return all(token in content_lower for token in tokens)

def _search_or(content: str, tokens: list[str]) -> bool:
    """Проверяет, что хотя бы один токен присутствует в контенте."""
    content_lower = content.lower()
    return any(token in content_lower for token in tokens)

def _search_phrase(content: str, phrase: str) -> bool:
    """Ищет точную фразу в контенте (case-insensitive)."""
    return phrase.lower() in content.lower()
```

### 5.3. Обновление search_docs и search_todo

```python
async def search_docs(query: str, search_mode: str = "AND", limit: int = 10) -> str:
    """Поиск по ключевым словам в документации проекта Life.

    Args:
        query: Ключевые слова для поиска
        search_mode: Режим поиска ("AND", "OR", "PHRASE")
        limit: Максимальное количество результатов (по умолчанию 10)
    """
    mode, tokens_or_phrase = _tokenize_query(query, search_mode)
    results = []

    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith(".md"):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(DOCS_DIR)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Применяем соответствующий режим поиска
                    match = False
                    if mode == "PHRASE":
                        match = _search_phrase(content, tokens_or_phrase)
                    elif mode == "AND":
                        match = _search_and(content, tokens_or_phrase)
                    elif mode == "OR":
                        match = _search_or(content, tokens_or_phrase)

                    if match:
                        # Найти контекст вокруг найденного текста
                        # ... существующая логика ...
```

## 6. Критерии приемки

✅ **FC1:** Реализованы все три режима поиска (AND/OR/PHRASE)
✅ **FC2:** Параметр `search_mode` добавлен в `search_docs` и `search_todo`
✅ **FC3:** PHRASE mode определяется автоматически по кавычкам
✅ **FC4:** Обратная совместимость сохранена (по умолчанию AND mode)
✅ **FC5:** Тесты для всех режимов проходят
✅ **FC6:** Документация обновлена (docstrings)

## 7. Риски и митигация

**Риск 1:** Регрессии в существующем функционале
**Митигация:** Сохранение обратной совместимости, обновление существующих тестов

**Риск 2:** Неправильная обработка кавычек
**Митигация:** Тесты для различных вариантов кавычек

**Риск 3:** Производительность при большом количестве токенов
**Митигация:** Текущая реализация достаточно эффективна для типичных запросов

## 8. Оценка времени

- Этап 1 (Токенизация): 30 минут
- Этап 2 (Режимы поиска): 1 час
- Этап 3 (Интеграция): 1 час
- Этап 4 (Тестирование): 30 минут

**Итого:** ~3 часа

---

**Автор плана:** AI Agent (Project Executor)
**Дата:** 2026-01-20
