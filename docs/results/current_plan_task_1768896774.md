# План выполнения: Вынесение индексатора в отдельный модуль с кэшированием

> **Задача:** Вынести индексатор в отдельный модуль (например `mcp_index_engine.py`) и сделать кэш (content_cache + inverted index)
> **Дата создания:** 2026-01-20
> **ID задачи:** task_1768896774

## 1. Обзор задачи

Текущая реализация поиска в `mcp_index.py` выполняет полный обход файловой системы при каждом запросе, что неэффективно. Необходимо:

1. Вынести логику индексации в отдельный модуль `mcp_index_engine.py`
2. Реализовать кэш содержимого файлов (`content_cache`)
3. Реализовать инвертированный индекс (`inverted_index`) для быстрого поиска
4. Интегрировать новый индексатор в `mcp_index.py`

## 2. Текущее состояние

**Файл:** `mcp_index.py`

**Текущая реализация:**
- Функции `search_docs` и `search_todo` обходят все файлы через `os.walk()` при каждом запросе
- Содержимое файлов читается заново при каждом поиске
- Нет кэширования результатов
- Нет индексации для ускорения поиска

**Ограничения:**
- Медленный поиск при большом количестве файлов
- Повторное чтение одних и тех же файлов
- Нет механизма обновления индекса при изменении файлов

## 3. Целевое состояние

После реализации:
- Модуль `mcp_index_engine.py` с классом `IndexEngine`
- Кэш содержимого файлов (`content_cache: dict[str, str]`)
- Инвертированный индекс (`inverted_index: dict[str, set[str]]`)
- Автоматическое обновление индекса при изменении файлов
- Ускорение поиска за счет использования индекса
- Интеграция в `mcp_index.py` без изменения API

## 4. План реализации

### Этап 1: Создание модуля `mcp_index_engine.py`

**Шаг 1.1:** Создать класс `IndexEngine`
- Инициализация с директориями для индексации (docs, todo, src)
- Хранение кэша содержимого (`content_cache`)
- Хранение инвертированного индекса (`inverted_index`)
- Методы для индексации директорий

**Шаг 1.2:** Реализовать `content_cache`
- Структура: `dict[str, str]` где ключ - относительный путь к файлу, значение - содержимое
- Метод `_load_content(file_path: Path) -> str` для чтения и кэширования
- Метод `_get_content(file_path: Path) -> str` для получения из кэша или загрузки

**Шаг 1.3:** Реализовать `inverted_index`
- Структура: `dict[str, set[str]]` где ключ - токен (слово), значение - множество путей к файлам
- Метод `_tokenize_content(content: str) -> set[str]` для извлечения токенов
- Метод `_build_inverted_index()` для построения индекса из кэша
- Метод `_update_index_for_file(file_path: Path, content: str)` для обновления индекса одного файла

### Этап 2: Реализация методов индексации

**Шаг 2.1:** Метод `index_directory(directory: Path, file_pattern: str = "*.md")`
- Рекурсивный обход директории
- Загрузка всех файлов в `content_cache`
- Построение `inverted_index` для всех файлов
- Возврат статистики индексации

**Шаг 2.2:** Метод `reindex()` для полной переиндексации
- Очистка кэша и индекса
- Повторная индексация всех директорий

**Шаг 2.3:** Метод `update_file(file_path: Path)` для обновления одного файла
- Проверка существования файла
- Обновление `content_cache`
- Обновление `inverted_index` (удаление старых токенов, добавление новых)

**Шаг 2.4:** Метод `get_file_content(file_path: Path) -> str | None`
- Получение содержимого из кэша
- Если файл не в кэше - загрузка и кэширование

### Этап 3: Реализация поиска с использованием индекса

**Шаг 3.1:** Метод `search(query: str, mode: str = "AND", limit: int = 10) -> list[dict]`
- Токенизация запроса (используя существующую логику из `mcp_index.py`)
- Для AND mode: пересечение множеств файлов для каждого токена
- Для OR mode: объединение множеств файлов для токенов
- Для PHRASE mode: поиск по `content_cache` (без использования индекса)
- Возврат списка результатов с путями и контекстом

**Шаг 3.2:** Метод `search_in_directory(directory: Path, query: str, mode: str, limit: int) -> list[dict]`
- Поиск только в указанной директории
- Использование индекса для фильтрации файлов
- Применение режима поиска к содержимому

### Этап 4: Интеграция в `mcp_index.py`

**Шаг 4.1:** Импортировать `IndexEngine` из `mcp_index_engine.py`
- Создать глобальный экземпляр `index_engine`
- Инициализировать при первом использовании (lazy initialization)

**Шаг 4.2:** Обновить функции `search_docs` и `search_todo`
- Использовать `index_engine.search_in_directory()` вместо прямого обхода файлов
- Сохранить существующую логику токенизации и режимов поиска
- Сохранить формат возвращаемых результатов

**Шаг 4.3:** Обновить функции `get_doc_content` и `get_todo_content`
- Использовать `index_engine.get_file_content()` вместо прямого чтения файла

**Шаг 4.4:** Добавить функцию для обновления индекса
- Опциональная функция `refresh_index()` для ручного обновления
- Автоматическое обновление при первом запросе (если индекс пуст)

### Этап 5: Оптимизация и обработка изменений файлов

**Шаг 5.1:** Добавить отслеживание изменений файлов
- Хранение времени модификации файлов (`file_mtimes: dict[str, float]`)
- Метод `_is_file_changed(file_path: Path) -> bool` для проверки изменений
- Автоматическое обновление кэша при изменении файла

**Шаг 5.2:** Оптимизация памяти
- Ограничение размера кэша (опционально, для больших проектов)
- Периодическая очистка неиспользуемых файлов из кэша

## 5. Детальная реализация

### 5.1. Структура класса IndexEngine

```python
class IndexEngine:
    def __init__(self, docs_dir: Path, todo_dir: Path, src_dir: Path):
        self.docs_dir = docs_dir
        self.todo_dir = todo_dir
        self.src_dir = src_dir

        # Кэш содержимого файлов: путь -> содержимое
        self.content_cache: dict[str, str] = {}

        # Инвертированный индекс: токен -> множество путей к файлам
        self.inverted_index: dict[str, set[str]] = {}

        # Время модификации файлов: путь -> mtime
        self.file_mtimes: dict[str, float] = {}

        # Флаг инициализации
        self._initialized = False

    def initialize(self):
        """Инициализация индекса (ленивая загрузка)."""
        if not self._initialized:
            self.index_directory(self.docs_dir, "*.md")
            self.index_directory(self.todo_dir, "*.md")
            self._initialized = True

    def _tokenize_content(self, content: str) -> set[str]:
        """Извлекает токены из содержимого файла."""
        import re
        tokens = re.findall(r'\b\w+\b', content.lower())
        return set(tokens)

    def _load_content(self, file_path: Path) -> str:
        """Загружает содержимое файла."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _get_content(self, file_path: Path, base_dir: Path) -> str:
        """Получает содержимое из кэша или загружает."""
        rel_path = str(file_path.relative_to(base_dir))

        # Проверка изменений файла
        current_mtime = file_path.stat().st_mtime
        if rel_path in self.file_mtimes:
            if current_mtime > self.file_mtimes[rel_path]:
                # Файл изменился, обновляем кэш
                self._update_file_in_cache(file_path, base_dir)

        if rel_path not in self.content_cache:
            content = self._load_content(file_path)
            self.content_cache[rel_path] = content
            self.file_mtimes[rel_path] = current_mtime
            self._update_index_for_file(rel_path, content)

        return self.content_cache[rel_path]

    def _update_index_for_file(self, rel_path: str, content: str):
        """Обновляет инвертированный индекс для файла."""
        # Удаляем старые токены для этого файла
        tokens_to_remove = []
        for token, file_set in self.inverted_index.items():
            if rel_path in file_set:
                tokens_to_remove.append((token, rel_path))

        for token, file_path in tokens_to_remove:
            self.inverted_index[token].discard(file_path)
            if not self.inverted_index[token]:
                del self.inverted_index[token]

        # Добавляем новые токены
        tokens = self._tokenize_content(content)
        for token in tokens:
            if token not in self.inverted_index:
                self.inverted_index[token] = set()
            self.inverted_index[token].add(rel_path)

    def index_directory(self, directory: Path, file_pattern: str = "*.md"):
        """Индексирует все файлы в директории."""
        for file_path in directory.rglob(file_pattern):
            if file_path.is_file():
                self._get_content(file_path, directory)

    def search_in_directory(
        self,
        directory: Path,
        query: str,
        mode: str = "AND",
        limit: int = 10
    ) -> list[dict]:
        """Поиск в указанной директории с использованием индекса."""
        # Используем существующую логику токенизации из mcp_index.py
        from mcp_index import _tokenize_query, _search_and, _search_or, _search_phrase

        mode, tokens_or_phrase = _tokenize_query(query, mode, False)

        # Определяем кандидатов из индекса
        candidate_files = set()

        if mode == "PHRASE":
            # Для PHRASE mode используем полный поиск по кэшу
            phrase = str(tokens_or_phrase)
            for rel_path, content in self.content_cache.items():
                full_path = directory / rel_path
                if full_path.exists() and _search_phrase(content, phrase):
                    candidate_files.add(rel_path)
        elif mode == "AND" and isinstance(tokens_or_phrase, list):
            # Пересечение множеств файлов для каждого токена
            if tokens_or_phrase:
                candidate_files = set(self.inverted_index.get(tokens_or_phrase[0].lower(), set()))
                for token in tokens_or_phrase[1:]:
                    candidate_files &= self.inverted_index.get(token.lower(), set())
        elif mode == "OR" and isinstance(tokens_or_phrase, list):
            # Объединение множеств файлов
            for token in tokens_or_phrase:
                candidate_files |= self.inverted_index.get(token.lower(), set())

        # Фильтруем результаты и добавляем контекст
        results = []
        for rel_path in candidate_files:
            if len(results) >= limit:
                break

            full_path = directory / rel_path
            if not full_path.exists():
                continue

            content = self._get_content(full_path, directory)

            # Применяем режим поиска для точной проверки
            match = False
            if mode == "PHRASE":
                match = _search_phrase(content, str(tokens_or_phrase))
            elif mode == "AND" and isinstance(tokens_or_phrase, list):
                match = _search_and(content, tokens_or_phrase)
            elif mode == "OR" and isinstance(tokens_or_phrase, list):
                match = _search_or(content, tokens_or_phrase)

            if match:
                # Находим контекст (используем существующую логику)
                from mcp_index import _find_context_lines
                context_lines = _find_context_lines(content, query, mode, tokens_or_phrase)
                context = "\n".join(context_lines)

                results.append({
                    "path": rel_path,
                    "title": full_path.name,
                    "context": context
                })

        return results

    def get_file_content(self, file_path: Path, base_dir: Path) -> str | None:
        """Получает содержимое файла из кэша."""
        rel_path = str(file_path.relative_to(base_dir))
        return self.content_cache.get(rel_path)
```

### 5.2. Интеграция в mcp_index.py

```python
# В начале файла
from mcp_index_engine import IndexEngine

# После определения директорий
_index_engine: IndexEngine | None = None

def _get_index_engine() -> IndexEngine:
    """Получает или создает экземпляр IndexEngine."""
    global _index_engine
    if _index_engine is None:
        _index_engine = IndexEngine(DOCS_DIR, TODO_DIR, SRC_DIR)
        _index_engine.initialize()
    return _index_engine

# Обновление search_docs
@app.tool()
async def search_docs(query: str, search_mode: str = "AND", limit: int = 10) -> str:
    """Поиск по ключевым словам в документации проекта Life."""
    engine = _get_index_engine()
    results = engine.search_in_directory(DOCS_DIR, query, search_mode, limit)

    # Форматирование результатов (существующая логика)
    # ...
```

## 6. Критерии приемки

✅ **FC1:** Создан модуль `mcp_index_engine.py` с классом `IndexEngine`
✅ **FC2:** Реализован `content_cache` для кэширования содержимого файлов
✅ **FC3:** Реализован `inverted_index` для быстрого поиска
✅ **FC4:** Интегрирован в `mcp_index.py` без изменения API
✅ **FC5:** Поиск работает быстрее за счет использования индекса
✅ **FC6:** Автоматическое обновление кэша при изменении файлов
✅ **FC7:** Обратная совместимость сохранена (все существующие функции работают)
✅ **FC8:** Тесты проходят (если есть)

## 7. Риски и митигация

**Риск 1:** Увеличение потребления памяти из-за кэша
**Митигация:** Кэш хранит только текстовые файлы (.md), размер обычно небольшой. При необходимости можно добавить ограничение размера.

**Риск 2:** Несинхронизированность индекса при изменении файлов
**Митигация:** Отслеживание времени модификации файлов и автоматическое обновление кэша.

**Риск 3:** Регрессии в существующем функционале
**Митигация:** Сохранение существующей логики поиска, использование тех же функций токенизации и режимов поиска.

**Риск 4:** Медленная первичная индексация
**Митигация:** Ленивая инициализация - индекс строится только при первом запросе.

## 8. Оценка времени

- Этап 1 (Создание модуля): 2 часа
- Этап 2 (Методы индексации): 2 часа
- Этап 3 (Поиск с индексом): 1.5 часа
- Этап 4 (Интеграция): 1 час
- Этап 5 (Оптимизация): 1 час

**Итого:** ~7.5 часов

---

**Автор плана:** AI Agent (Project Executor)
**Дата:** 2026-01-20
