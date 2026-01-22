#!/usr/bin/env python3
"""
Валидация группировки параметров в Computation Cache.

Проверяет эффективность группировки параметров для activate_memory кэширования:
- Сравнивает hit rate с группировкой и без группировки
- Оценивает влияние группировки на точность кэширования
- Измеряет производительность кэширования

Использование:
    python scripts/validate_computation_cache_grouping.py [--test-size 1000] [--iterations 100]
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.runtime.computation_cache import ComputationCache
from src.memory.memory import Memory
from src.memory.memory_types import MemoryEntry

logger = logging.getLogger(__name__)


class CacheGroupingValidator:
    """
    Валидатор группировки параметров в Computation Cache.
    """

    def __init__(self, test_size: int = 1000, iterations: int = 100):
        """
        Инициализация валидатора.

        Args:
            test_size: Размер тестовой памяти
            iterations: Количество итераций тестирования
        """
        self.test_size = test_size
        self.iterations = iterations
        self.test_memory = self._create_test_memory()
        self.results = {}

        # Создаем директорию для результатов
        self.output_dir = Path("data/validation/cache_grouping")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Cache Grouping Validator initialized with test_size={test_size}, iterations={iterations}")

    def _create_test_memory(self) -> Memory:
        """Создает тестовую память для экспериментов."""
        memory = Memory()
        current_time = time.time()

        for i in range(self.test_size):
            # Создаем записи с различными характеристиками
            weight = 0.1 + (i / self.test_size) * 0.9
            age_seconds = (i / self.test_size) * 7 * 24 * 3600  # От 0 до 7 дней
            timestamp = current_time - age_seconds

            entry = MemoryEntry(
                event_type=f"test_event_{i % 10}",
                meaning_significance=0.1 + (i % 9) * 0.1,
                timestamp=timestamp,
                weight=weight,
                subjective_timestamp=timestamp - age_seconds * 0.1
            )

            memory.append(entry)

        logger.info(f"Created test memory with {len(memory)} entries")
        return memory

    def test_cache_with_grouping(self) -> Dict[str, Any]:
        """
        Тестирует кэш с группировкой параметров.

        Returns:
            Dict с результатами тестирования
        """
        logger.info("Testing cache WITH parameter grouping")

        cache = ComputationCache(max_size=2000)
        results = {
            "grouping_enabled": True,
            "hits": 0,
            "misses": 0,
            "total_requests": 0,
            "processing_time": 0.0,
            "memory_size_variations": [],
            "time_variations": [],
            "age_variations": []
        }

        start_time = time.perf_counter()

        # Генерируем различные параметры для тестирования
        for i in range(self.iterations):
            # Варьируем параметры
            memory_size = len(self.test_memory) + (i % 50 - 25)  # ±25 от базового размера
            subjective_time = time.time() + (i % 200 - 100)  # ±100 секунд от текущего времени
            age = (i % 100) * 864  # Возраст от 0 до ~100 дней

            # Проверяем кэш
            cached_result = cache.get_cached_activate_memory(
                "test_event", memory_size, subjective_time, age, limit=50
            )

            if cached_result is None:
                # Cache miss - симулируем результат
                result = [entry for entry in self.test_memory[:50]]  # Первые 50 записей
                cache.cache_activate_memory(
                    "test_event", memory_size, subjective_time, age, limit=50, result=result
                )
                results["misses"] += 1
            else:
                results["hits"] += 1

            results["total_requests"] += 1

            # Записываем вариации параметров для анализа
            results["memory_size_variations"].append(memory_size)
            results["time_variations"].append(subjective_time)
            results["age_variations"].append(age)

        results["processing_time"] = time.perf_counter() - start_time
        results["hit_rate"] = results["hits"] / max(1, results["total_requests"]) * 100

        # Статистика кэша
        cache_stats = cache.get_stats()
        results["cache_stats"] = cache_stats.get("memory_search", {})

        logger.info(f"Grouping test complete: {results['hits']} hits, {results['misses']} misses, "
                   f"hit rate: {results['hit_rate']:.1f}%")

        return results

    def test_cache_without_grouping(self) -> Dict[str, Any]:
        """
        Тестирует кэш без группировки параметров.

        Returns:
            Dict с результатами тестирования
        """
        logger.info("Testing cache WITHOUT parameter grouping")

        # Создаем модифицированную версию кэша без группировки
        cache = ComputationCache(max_size=2000)

        # Переопределяем методы для тестирования без группировки
        def get_cached_activate_memory_no_grouping(event_type: str, memory_size: int,
                                                  subjective_time: float, age: float,
                                                  limit: int = None) -> Any:
            """Версия без группировки параметров."""
            rounded_args = (
                event_type,
                memory_size,  # Без группировки
                subjective_time,  # Без группировки
                age,  # Без группировки
                limit
            )

            cache_key = cache._make_cache_key("activate_memory", rounded_args)
            if cache_key in cache.memory_search_cache:
                cache.memory_search_hits += 1
                value = cache.memory_search_cache.pop(cache_key)
                cache.memory_search_cache[cache_key] = value
                return value
            else:
                cache.memory_search_misses += 1
                return None

        def cache_activate_memory_no_grouping(event_type: str, memory_size: int,
                                            subjective_time: float, age: float,
                                            limit: int, result: Any) -> None:
            """Версия без группировки параметров."""
            rounded_args = (
                event_type,
                memory_size,  # Без группировки
                subjective_time,  # Без группировки
                age,  # Без группировки
                limit
            )

            cache_key = cache._make_cache_key("activate_memory", rounded_args)
            cache.memory_search_cache[cache_key] = result
            cache._evict_if_needed(cache.memory_search_cache)

        results = {
            "grouping_enabled": False,
            "hits": 0,
            "misses": 0,
            "total_requests": 0,
            "processing_time": 0.0,
            "memory_size_variations": [],
            "time_variations": [],
            "age_variations": []
        }

        start_time = time.perf_counter()

        # Генерируем те же параметры для сравнения
        for i in range(self.iterations):
            memory_size = len(self.test_memory) + (i % 50 - 25)
            subjective_time = time.time() + (i % 200 - 100)
            age = (i % 100) * 864

            # Проверяем кэш без группировки
            cached_result = get_cached_activate_memory_no_grouping(
                "test_event", memory_size, subjective_time, age, limit=50
            )

            if cached_result is None:
                result = [entry for entry in self.test_memory[:50]]
                cache_activate_memory_no_grouping(
                    "test_event", memory_size, subjective_time, age, limit=50, result=result
                )
                results["misses"] += 1
            else:
                results["hits"] += 1

            results["total_requests"] += 1

            results["memory_size_variations"].append(memory_size)
            results["time_variations"].append(subjective_time)
            results["age_variations"].append(age)

        results["processing_time"] = time.perf_counter() - start_time
        results["hit_rate"] = results["hits"] / max(1, results["total_requests"]) * 100

        # Статистика кэша
        cache_stats = cache.get_stats()
        results["cache_stats"] = cache_stats.get("memory_search", {})

        logger.info(f"No-grouping test complete: {results['hits']} hits, {results['misses']} misses, "
                   f"hit rate: {results['hit_rate']:.1f}%")

        return results

    def run_validation(self) -> Dict[str, Any]:
        """
        Запускает полную валидацию группировки параметров.

        Returns:
            Dict с результатами валидации
        """
        logger.info("Starting cache grouping validation")

        # Тестируем обе версии
        with_grouping = self.test_cache_with_grouping()
        without_grouping = self.test_cache_without_grouping()

        # Анализируем результаты
        analysis = self._analyze_results(with_grouping, without_grouping)

        results = {
            "timestamp": time.time(),
            "validator": "CacheGroupingValidator",
            "test_size": self.test_size,
            "iterations": self.iterations,
            "with_grouping": with_grouping,
            "without_grouping": without_grouping,
            "analysis": analysis
        }

        # Сохраняем результаты
        self.save_results(results)

        logger.info("Cache grouping validation complete")
        return results

    def _analyze_results(self, with_grouping: Dict, without_grouping: Dict) -> Dict[str, Any]:
        """
        Анализирует результаты сравнения.

        Args:
            with_grouping: Результаты с группировкой
            without_grouping: Результаты без группировки

        Returns:
            Dict с анализом
        """
        analysis = {
            "hit_rate_difference": with_grouping["hit_rate"] - without_grouping["hit_rate"],
            "time_difference": with_grouping["processing_time"] - without_grouping["processing_time"],
            "cache_efficiency_with_grouping": with_grouping["cache_stats"].get("efficiency", 0),
            "cache_efficiency_without_grouping": without_grouping["cache_stats"].get("efficiency", 0),
            "recommendation": "",
            "grouping_benefit": "unknown"
        }

        # Определяем пользу группировки
        hit_rate_diff = analysis["hit_rate_difference"]
        if hit_rate_diff > 5:
            analysis["grouping_benefit"] = "beneficial"
            analysis["recommendation"] = "Группировка параметров улучшает hit rate кэша"
        elif hit_rate_diff < -5:
            analysis["grouping_benefit"] = "detrimental"
            analysis["recommendation"] = "Группировка параметров снижает hit rate кэша"
        else:
            analysis["grouping_benefit"] = "neutral"
            analysis["recommendation"] = "Группировка параметров не оказывает значительного влияния"

        # Анализируем вариативность параметров
        memory_variation = len(set(with_grouping["memory_size_variations"]))
        time_variation = len(set(with_grouping["time_variations"]))
        age_variation = len(set(with_grouping["age_variations"]))

        analysis["parameter_variations"] = {
            "memory_size_unique_values": memory_variation,
            "time_unique_values": time_variation,
            "age_unique_values": age_variation,
            "total_unique_combinations": memory_variation * time_variation * age_variation
        }

        return analysis

    def save_results(self, results: Dict[str, Any]) -> None:
        """
        Сохраняет результаты валидации.

        Args:
            results: Результаты для сохранения
        """
        import json

        timestamp = int(results["timestamp"])
        filename = f"cache_grouping_validation_{timestamp}.json"

        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Results saved to {output_path}")

        # Генерируем отчет
        self.generate_validation_report(results)

    def generate_validation_report(self, results: Dict[str, Any]) -> None:
        """
        Генерирует отчет о валидации.

        Args:
            results: Результаты валидации
        """
        report_lines = [
            "# Cache Parameter Grouping Validation Report",
            f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}",
            f"**Test Size:** {results['test_size']} memory entries",
            f"**Iterations:** {results['iterations']}",
            "",
            "## Results Summary",
            "",
            "### With Parameter Grouping",
            f"- **Hit Rate:** {results['with_grouping']['hit_rate']:.1f}%",
            f"- **Hits:** {results['with_grouping']['hits']}",
            f"- **Misses:** {results['with_grouping']['misses']}",
            f"- **Processing Time:** {results['with_grouping']['processing_time']:.4f}s",
            "",
            "### Without Parameter Grouping",
            f"- **Hit Rate:** {results['without_grouping']['hit_rate']:.1f}%",
            f"- **Hits:** {results['without_grouping']['hits']}",
            f"- **Misses:** {results['without_grouping']['misses']}",
            f"- **Processing Time:** {results['without_grouping']['processing_time']:.4f}s",
            "",
            "## Analysis",
            "",
            f"### Hit Rate Difference: {results['analysis']['hit_rate_difference']:.1f}%",
            f"### Time Difference: {results['analysis']['time_difference']:.4f}s",
            f"### Grouping Benefit: {results['analysis']['grouping_benefit']}",
            "",
            f"**Recommendation:** {results['analysis']['recommendation']}",
            "",
            "### Parameter Variations",
            f"- Memory Size Unique Values: {results['analysis']['parameter_variations']['memory_size_unique_values']}",
            f"- Time Unique Values: {results['analysis']['parameter_variations']['time_unique_values']}",
            f"- Age Unique Values: {results['analysis']['parameter_variations']['age_unique_values']}",
            f"- Total Unique Combinations: {results['analysis']['parameter_variations']['total_unique_combinations']}",
            "",
            "## Conclusion",
        ]

        # Заключение на основе анализа
        if results['analysis']['grouping_benefit'] == 'beneficial':
            report_lines.extend([
                "Группировка параметров в Computation Cache показала положительный эффект на производительность.",
                "Рекомендуется сохранить текущую реализацию группировки."
            ])
        elif results['analysis']['grouping_benefit'] == 'detrimental':
            report_lines.extend([
                "Группировка параметров снижает эффективность кэширования.",
                "Рекомендуется рассмотреть альтернативные стратегии группировки или отказаться от неё."
            ])
        else:
            report_lines.extend([
                "Группировка параметров не оказывает значительного влияния на производительность кэша.",
                "Текущее решение приемлемо, но можно рассмотреть упрощение реализации."
            ])

        # Сохраняем отчет
        timestamp = int(results["timestamp"])
        report_path = self.output_dir / f"cache_grouping_report_{timestamp}.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        logger.info(f"Validation report saved to {report_path}")


def main():
    """Основная функция для запуска валидации."""
    parser = argparse.ArgumentParser(description="Cache Parameter Grouping Validator")
    parser.add_argument("--test-size", type=int, default=1000,
                       help="Size of test memory (default: 1000)")
    parser.add_argument("--iterations", type=int, default=100,
                       help="Number of test iterations (default: 100)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    # Настройка логирования
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Запуск валидации
    validator = CacheGroupingValidator(
        test_size=args.test_size,
        iterations=args.iterations
    )

    try:
        results = validator.run_validation()
        logger.info("Cache grouping validation completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())