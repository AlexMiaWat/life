#!/usr/bin/env python3
"""
Модуль для multi-provider архитектуры поиска.
Предоставляет абстракцию для различных провайдеров поиска (индекс, LLM и т.д.).
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

# Настройка логирования
logger = logging.getLogger(__name__)


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

        Args:
            directory: Директория для поиска
            query: Поисковый запрос
            mode: Режим поиска ("AND", "OR", "PHRASE")
            limit: Максимальное количество результатов
            **kwargs: Дополнительные параметры

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


class IndexSearchProvider(SearchProvider):
    """Провайдер поиска на основе инвертированного индекса."""

    def __init__(self, engine):
        """
        Инициализация провайдера.

        Args:
            engine: Экземпляр IndexEngine
        """
        self.engine = engine

    def search(
        self, directory: Path, query: str, mode: str = "AND", limit: int = 10, **kwargs
    ) -> list[dict]:
        """Выполняет поиск через IndexEngine."""
        return self.engine.search_in_directory(
            directory, query, mode, limit, **kwargs
        )

    def is_available(self) -> bool:
        """Проверяет доступность индекса."""
        return self.engine._is_index_available()

    def get_name(self) -> str:
        """Возвращает имя провайдера."""
        return "IndexSearch"


class LLMSearchProvider(SearchProvider):
    """Провайдер поиска на основе LLM (опционально)."""

    def __init__(self, llm_client=None):
        """
        Инициализация LLM провайдера.

        Args:
            llm_client: Клиент LLM (если None, провайдер отключен)
        """
        self.llm_client = llm_client
        self.enabled = llm_client is not None

    def search(
        self, directory: Path, query: str, mode: str = "AND", limit: int = 10, **kwargs
    ) -> list[dict]:
        """Выполняет поиск через LLM."""
        if not self.is_available():
            raise RuntimeError("LLM провайдер недоступен")

        # Здесь будет логика LLM-based поиска
        # Пока заглушка
        logger.warning("LLMSearchProvider.search() - заглушка, LLM поиск не реализован")
        return []

    def is_available(self) -> bool:
        """Проверяет доступность LLM провайдера."""
        return self.enabled and self.llm_client is not None

    def get_name(self) -> str:
        """Возвращает имя провайдера."""
        return "LLMSearch"


class SearchManager:
    """Менеджер для управления несколькими провайдерами поиска."""

    def __init__(self):
        """Инициализация менеджера."""
        self.providers: list[SearchProvider] = []
        self.fallback_providers: list[SearchProvider] = []

    def add_provider(self, provider: SearchProvider, is_fallback: bool = False):
        """
        Добавляет провайдер в список.

        Args:
            provider: Провайдер поиска
            is_fallback: True если это fallback провайдер
        """
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

        Args:
            directory: Директория для поиска
            query: Поисковый запрос
            mode: Режим поиска ("AND", "OR", "PHRASE")
            limit: Максимальное количество результатов
            **kwargs: Дополнительные параметры

        Returns:
            Список результатов поиска
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
                    logger.warning(
                        f"Ошибка в провайдере {provider.get_name()}: {e}"
                    )
                    continue

        # Пробуем fallback провайдеры
        for provider in self.fallback_providers:
            if provider.is_available():
                try:
                    results = provider.search(directory, query, mode, limit, **kwargs)
                    if results:
                        logger.info(
                            f"Использован fallback провайдер: {provider.get_name()}"
                        )
                        return results
                except Exception as e:
                    logger.warning(
                        f"Ошибка в fallback провайдере {provider.get_name()}: {e}"
                    )
                    continue

        return []
