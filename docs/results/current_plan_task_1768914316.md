# План выполнения задачи: Fallback стратегия без LLM и multi-provider для LLM

**Задача:** Спроектировать и реализовать fallback стратегию без LLM (и опционально — multi-provider для LLM, если появится)

**Дата создания:** 2026-01-20  
**ID задачи:** 1768914096

## Анализ текущей ситуации

### Текущая реализация поиска

В проекте используется MCP (Model Context Protocol) engine для поиска по документации:

1. **`mcp_index_engine.py`** — модуль индексации с:
   - Инвертированным индексом (`inverted_index`)
   - Кэшем содержимого файлов (`content_cache`)
   - Методом `search_in_directory()` для поиска

2. **`mcp_index.py`** — MCP сервер, который:
   - Использует `IndexEngine` для поиска
   - Предоставляет инструменты `search_docs` и `search_todo`
   - Поддерживает режимы поиска: AND, OR, PHRASE

### Проблемы текущей реализации

1. **Отсутствие fallback механизмов:**
   - Если индекс не построен, поиск может не работать
   - Нет резервных методов поиска при сбое индекса
   - Нет обработки ошибок при недоступности индекса

2. **Отсутствие multi-provider поддержки:**
   - Нет возможности использовать LLM для улучшения поиска
   - Нет архитектуры для добавления новых провайдеров поиска
   - Нет абстракции для переключения между провайдерами

## Цели задачи

1. **Реализовать fallback стратегию без LLM:**
   - Уровень 1: Инвертированный индекс (основной метод) — уже реализован
   - Уровень 2: Линейный поиск по кэшу (если индекс не построен)
   - Уровень 3: Простой grep-подобный поиск (последний резерв)

2. **Опционально: Спроектировать multi-provider архитектуру:**
   - Абстракция для провайдеров поиска
   - Поддержка LLM-based поиска как дополнительного провайдера
   - Механизм переключения между провайдерами

## Архитектура решения

### Fallback стратегия (обязательная часть)

```
┌─────────────────────────────────────┐
│   Поисковый запрос                  │
└──────────────┬──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Проверка индекса     │
    │  (inverted_index)     │
    └──────────┬────────────┘
               │
       ┌───────┴────────┐
       │                │
   [Доступен]      [Недоступен]
       │                │
       ▼                ▼
┌─────────────┐  ┌──────────────────┐
│ Уровень 1:  │  │ Уровень 2:       │
│ Инвертир.   │  │ Линейный поиск   │
│ индекс      │  │ по кэшу          │
└─────────────┘  └────────┬─────────┘
                          │
                    [Недоступен]
                          │
                          ▼
                   ┌──────────────┐
                   │ Уровень 3:   │
                   │ Grep-поиск   │
                   │ по файлам    │
                   └──────────────┘
```

### Multi-provider архитектура (опциональная часть)

```
┌─────────────────────────────────────┐
│   SearchProvider (абстракция)      │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│ IndexSearch │  │ LLMSearch   │
│ Provider    │  │ Provider    │
│ (текущий)   │  │ (опционально)│
└─────────────┘  └─────────────┘
```

## План реализации

### Этап 1: Fallback стратегия (обязательная часть)

#### Шаг 1.1: Проверка доступности индекса

**Файл:** `mcp_index_engine.py`

**Добавить метод:**
```python
def _is_index_available(self) -> bool:
    """Проверяет, доступен ли инвертированный индекс для поиска."""
    return (
        self._initialized 
        and len(self.inverted_index) > 0 
        and len(self.content_cache) > 0
    )
```

#### Шаг 1.2: Линейный поиск по кэшу (Уровень 2)

**Добавить метод:**
```python
def _linear_search_in_cache(
    self,
    directory: Path,
    query: str,
    mode: str,
    tokens_or_phrase: list[str] | str,
    limit: int,
    search_and_func,
    search_or_func,
    search_phrase_func,
    find_context_func,
) -> list[dict]:
    """
    Линейный поиск по кэшированному содержимому файлов.
    Используется как fallback, если индекс недоступен.
    """
    results = []
    query_lower = query.lower()
    
    for rel_path, content in self.content_cache.items():
        if len(results) >= limit:
            break
            
        full_path = directory / rel_path
        if not full_path.exists():
            continue
            
        # Применяем режим поиска
        match = False
        if mode == "PHRASE":
            match = search_phrase_func(content, str(tokens_or_phrase))
        elif mode == "AND" and isinstance(tokens_or_phrase, list):
            match = search_and_func(content, tokens_or_phrase)
        elif mode == "OR" and isinstance(tokens_or_phrase, list):
            match = search_or_func(content, tokens_or_phrase)
            
        if match:
            context_lines = find_context_func(
                content, query, mode, tokens_or_phrase
            )
            context = "\n".join(context_lines)
            score = self._calculate_document_score(rel_path)
            
            results.append({
                "path": rel_path,
                "title": full_path.name,
                "context": context,
                "score": score,
            })
    
    # Сортируем по score
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results
```

#### Шаг 1.3: Grep-поиск по файлам (Уровень 3)

**Добавить метод:**
```python
def _grep_search_in_files(
    self,
    directory: Path,
    query: str,
    mode: str,
    tokens_or_phrase: list[str] | str,
    limit: int,
    search_and_func,
    search_or_func,
    search_phrase_func,
    find_context_func,
) -> list[dict]:
    """
    Простой grep-подобный поиск по файлам.
    Используется как последний резерв, если кэш недоступен.
    """
    results = []
    query_lower = query.lower()
    
    # Ищем все .md файлы в директории
    for file_path in directory.rglob("*.md"):
        if len(results) >= limit:
            break
            
        if not file_path.is_file():
            continue
            
        try:
            # Загружаем файл
            content = self._load_content(file_path)
            rel_path = self._get_relative_path(file_path, directory)
            
            # Применяем режим поиска
            match = False
            if mode == "PHRASE":
                match = search_phrase_func(content, str(tokens_or_phrase))
            elif mode == "AND" and isinstance(tokens_or_phrase, list):
                match = search_and_func(content, tokens_or_phrase)
            elif mode == "OR" and isinstance(tokens_or_phrase, list):
                match = search_or_func(content, tokens_or_phrase)
                
            if match:
                context_lines = find_context_func(
                    content, query, mode, tokens_or_phrase
                )
                context = "\n".join(context_lines)
                score = self._calculate_document_score(rel_path)
                
                results.append({
                    "path": rel_path,
                    "title": file_path.name,
                    "context": context,
                    "score": score,
                })
                
                # Обновляем кэш для будущих запросов
                self._evict_cache_if_needed()
                self.content_cache[rel_path] = content
                self.file_mtimes[rel_path] = file_path.stat().st_mtime
                self._update_index_for_file(rel_path, content)
                
        except Exception as e:
            logger.warning(f"Ошибка при grep-поиске в {file_path}: {e}")
            continue
    
    # Сортируем по score
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results
```

#### Шаг 1.4: Интеграция fallback в `search_in_directory()`

**Модифицировать метод `search_in_directory()`:**

```python
def search_in_directory(...) -> list[dict]:
    # ... существующий код токенизации ...
    
    # Уровень 1: Попытка использовать инвертированный индекс
    if self._is_index_available():
        try:
            # Существующая логика поиска через индекс
            candidate_files = set()
            # ... код поиска через индекс ...
            
            # Формируем результаты
            results = []
            for rel_path in candidate_files:
                # ... существующий код ...
            
            if results:
                return results
        except Exception as e:
            logger.warning(f"Ошибка при поиске через индекс: {e}")
    
    # Уровень 2: Линейный поиск по кэшу
    if len(self.content_cache) > 0:
        try:
            results = self._linear_search_in_cache(
                directory, query, search_mode, tokens_or_phrase,
                limit, search_and_func, search_or_func,
                search_phrase_func, find_context_func
            )
            if results:
                logger.info(f"Использован fallback уровень 2 (линейный поиск)")
                return results
        except Exception as e:
            logger.warning(f"Ошибка при линейном поиске: {e}")
    
    # Уровень 3: Grep-поиск по файлам
    try:
        results = self._grep_search_in_files(
            directory, query, search_mode, tokens_or_phrase,
            limit, search_and_func, search_or_func,
            search_phrase_func, find_context_func
        )
        if results:
            logger.info(f"Использован fallback уровень 3 (grep-поиск)")
            return results
    except Exception as e:
        logger.error(f"Ошибка при grep-поиске: {e}")
    
    # Если все уровни не дали результатов
    return []
```

### Этап 2: Multi-provider архитектура (опциональная часть)

#### Шаг 2.1: Создать абстракцию провайдера

**Создать файл:** `mcp_search_provider.py`

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

class SearchProvider(ABC):
    """Абстракция для провайдеров поиска."""
    
    @abstractmethod
    def search(
        self,
        directory: Path,
        query: str,
        mode: str,
        limit: int,
        **kwargs
    ) -> list[dict]:
        """
        Выполняет поиск в указанной директории.
        
        Returns:
            Список результатов поиска с полями: path, title, context, score
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверяет, доступен ли провайдер."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Возвращает имя провайдера."""
        pass
```

#### Шаг 2.2: Реализовать IndexSearchProvider

```python
from mcp_search_provider import SearchProvider
from mcp_index_engine import IndexEngine

class IndexSearchProvider(SearchProvider):
    """Провайдер поиска на основе инвертированного индекса."""
    
    def __init__(self, engine: IndexEngine):
        self.engine = engine
    
    def search(self, directory, query, mode, limit, **kwargs) -> list[dict]:
        return self.engine.search_in_directory(
            directory, query, mode, limit, **kwargs
        )
    
    def is_available(self) -> bool:
        return self.engine._is_index_available()
    
    def get_name(self) -> str:
        return "IndexSearch"
```

#### Шаг 2.3: Реализовать LLMSearchProvider (опционально)

```python
class LLMSearchProvider(SearchProvider):
    """Провайдер поиска на основе LLM (опционально)."""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.enabled = llm_client is not None
    
    def search(self, directory, query, mode, limit, **kwargs) -> list[dict]:
        if not self.is_available():
            raise RuntimeError("LLM провайдер недоступен")
        
        # Здесь будет логика LLM-based поиска
        # Пока заглушка
        return []
    
    def is_available(self) -> bool:
        return self.enabled and self.llm_client is not None
    
    def get_name(self) -> str:
        return "LLMSearch"
```

#### Шаг 2.4: Создать SearchManager для управления провайдерами

```python
class SearchManager:
    """Менеджер для управления несколькими провайдерами поиска."""
    
    def __init__(self):
        self.providers: list[SearchProvider] = []
        self.fallback_providers: list[SearchProvider] = []
    
    def add_provider(self, provider: SearchProvider, is_fallback: bool = False):
        """Добавляет провайдер в список."""
        if is_fallback:
            self.fallback_providers.append(provider)
        else:
            self.providers.append(provider)
    
    def search(
        self,
        directory: Path,
        query: str,
        mode: str = "AND",
        limit: int = 10,
        **kwargs
    ) -> list[dict]:
        """
        Выполняет поиск, пробуя провайдеры по порядку.
        Использует fallback провайдеры, если основные недоступны.
        """
        # Пробуем основные провайдеры
        for provider in self.providers:
            if provider.is_available():
                try:
                    results = provider.search(directory, query, mode, limit, **kwargs)
                    if results:
                        logger.info(f"Использован провайдер: {provider.get_name()}")
                        return results
                except Exception as e:
                    logger.warning(f"Ошибка в провайдере {provider.get_name()}: {e}")
                    continue
        
        # Пробуем fallback провайдеры
        for provider in self.fallback_providers:
            if provider.is_available():
                try:
                    results = provider.search(directory, query, mode, limit, **kwargs)
                    if results:
                        logger.info(f"Использован fallback провайдер: {provider.get_name()}")
                        return results
                except Exception as e:
                    logger.warning(f"Ошибка в fallback провайдере {provider.get_name()}: {e}")
                    continue
        
        return []
```

#### Шаг 2.5: Интеграция в mcp_index.py

```python
# В начале файла
from mcp_search_provider import SearchManager, IndexSearchProvider

# Глобальный менеджер поиска
_search_manager = None

def _get_search_manager():
    """Получает или создает SearchManager."""
    global _search_manager
    if _search_manager is None:
        engine = _get_index_engine()
        _search_manager = SearchManager()
        _search_manager.add_provider(IndexSearchProvider(engine))
        # Опционально: добавить LLM провайдер
        # if llm_client:
        #     _search_manager.add_provider(LLMSearchProvider(llm_client))
    return _search_manager

# В функциях search_docs и search_todo
async def search_docs(query: str, search_mode: str = "AND", limit: int = 10) -> str:
    # ... валидация ...
    
    manager = _get_search_manager()
    results = manager.search(DOCS_DIR, query, search_mode, limit, ...)
    
    # ... форматирование результатов ...
```

## Тестирование

### Тесты для fallback стратегии

1. **Тест уровня 1 (индекс):**
   - Проверить, что поиск работает через индекс при его доступности

2. **Тест уровня 2 (линейный поиск):**
   - Очистить индекс, но оставить кэш
   - Проверить, что поиск работает через линейный поиск по кэшу

3. **Тест уровня 3 (grep):**
   - Очистить индекс и кэш
   - Проверить, что поиск работает через grep по файлам

4. **Тест последовательности fallback:**
   - Симулировать сбой индекса
   - Проверить, что система переключается на следующий уровень

### Тесты для multi-provider (опционально)

1. **Тест переключения провайдеров:**
   - Проверить, что система переключается между провайдерами

2. **Тест fallback провайдеров:**
   - Проверить, что fallback провайдеры используются при недоступности основных

## Критерии приемки

### Обязательные (fallback стратегия)

- ✅ Поиск работает через инвертированный индекс (уровень 1)
- ✅ Поиск работает через линейный поиск по кэшу (уровень 2)
- ✅ Поиск работает через grep по файлам (уровень 3)
- ✅ Система автоматически переключается между уровнями
- ✅ Логирование используемого уровня fallback
- ✅ Тесты покрывают все уровни fallback

### Опциональные (multi-provider)

- ✅ Создана абстракция SearchProvider
- ✅ Реализован IndexSearchProvider
- ✅ Реализован SearchManager
- ✅ Архитектура позволяет добавить LLM провайдер
- ✅ Тесты для multi-provider архитектуры

## Выводы

Реализация fallback стратегии обеспечит:

1. **Надежность:** Система будет работать даже при сбоях индекса
2. **Гибкость:** Возможность использовать разные методы поиска
3. **Расширяемость:** Архитектура готова для добавления новых провайдеров

Multi-provider архитектура (опционально) обеспечит:

1. **Модульность:** Разделение логики поиска по провайдерам
2. **Расширяемость:** Легкое добавление новых провайдеров (LLM, векторный поиск и т.д.)
3. **Гибкость:** Возможность комбинировать разные провайдеры
