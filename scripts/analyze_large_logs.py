#!/usr/bin/env python3
"""
Оптимизированный анализ больших файлов логов.

Предоставляет инструменты для эффективного анализа больших JSONL файлов
с поддержкой параллельной обработки, кэширования и потоковой обработки.

Использование:
    python scripts/analyze_large_logs.py stats --log-file data/large_log.jsonl
"""

import argparse
import json
import sys
import time
import pickle
import hashlib
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Iterator, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.observability.log_analysis import _empty_analysis_result


class LargeLogAnalyzer:
    """Анализатор больших файлов логов с оптимизациями."""

    def __init__(self, log_file: str, cache_dir: str = ".log_cache"):
        self.log_file = Path(log_file)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_file_hash(self) -> str:
        """Получить хэш файла для кэширования."""
        hash_md5 = hashlib.md5()
        with open(self.log_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_cache_path(self, analysis_type: str) -> Path:
        """Получить путь к кэш-файлу."""
        file_hash = self.get_file_hash()
        return self.cache_dir / f"{analysis_type}_{file_hash}.pkl"

    def is_cache_valid(self, analysis_type: str) -> bool:
        """Проверить актуальность кэша."""
        cache_path = self.get_cache_path(analysis_type)
        if not cache_path.exists():
            return False

        # Проверяем время модификации
        cache_mtime = cache_path.stat().st_mtime
        log_mtime = self.log_file.stat().st_mtime

        return cache_mtime > log_mtime

    def save_to_cache(self, analysis_type: str, data: Any):
        """Сохранить результат в кэш."""
        cache_path = self.get_cache_path(analysis_type)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"⚠️  Не удалось сохранить кэш: {e}")

    def load_from_cache(self, analysis_type: str) -> Optional[Any]:
        """Загрузить результат из кэша."""
        cache_path = self.get_cache_path(analysis_type)
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"⚠️  Не удалось загрузить кэш: {e}")
            return None

    def stream_entries(self) -> Iterator[Dict[str, Any]]:
        """Потоковое чтение записей из файла."""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Ошибка парсинга строки {line_num}: {e}")
                        continue

        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return

    def analyze_chunk(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ чанка записей."""
        chunk_stats = {
            'total_entries': len(entries),
            'stages': Counter(),
            'event_types': Counter(),
            'errors': Counter(),
            'correlation_ids': set(),
            'tick_numbers': [],
        }

        for entry in entries:
            # Стадии
            stage = entry.get('stage', 'unknown')
            chunk_stats['stages'][stage] += 1

            # Типы событий
            if stage == 'event':
                event_type = entry.get('event_type', 'unknown')
                chunk_stats['event_types'][event_type] += 1

            # Ошибки
            if stage.startswith('error_'):
                error_type = entry.get('error_type', 'unknown')
                chunk_stats['errors'][error_type] += 1

            # Корреляционные ID
            if 'correlation_id' in entry:
                chunk_stats['correlation_ids'].add(entry['correlation_id'])

            # Номера тиков
            if 'tick_number' in entry:
                chunk_stats['tick_numbers'].append(entry['tick_number'])

        return chunk_stats

    def merge_chunk_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Слияние статистики из чанков."""
        merged = {
            'total_entries': 0,
            'stages': Counter(),
            'event_types': Counter(),
            'errors': Counter(),
            'correlation_ids': set(),
            'tick_numbers': [],
        }

        for chunk in chunks:
            merged['total_entries'] += chunk['total_entries']
            merged['stages'].update(chunk['stages'])
            merged['event_types'].update(chunk['event_types'])
            merged['errors'].update(chunk['errors'])
            merged['correlation_ids'].update(chunk['correlation_ids'])
            merged['tick_numbers'].extend(chunk['tick_numbers'])

        return merged

    def analyze_parallel(self, chunk_size: int = 10000, max_workers: Optional[int] = None) -> Dict[str, Any]:
        """Параллельный анализ файла."""
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), 4)  # Не больше 4 процессов

        print(f"🚀 Начинаем параллельный анализ с {max_workers} процессами...")

        # Проверяем кэш
        if self.is_cache_valid('parallel_stats'):
            print("📋 Используем кэшированные результаты")
            cached = self.load_from_cache('parallel_stats')
            if cached:
                return cached

        start_time = time.time()

        # Разделяем файл на чанки
        chunks = []
        current_chunk = []

        for entry in self.stream_entries():
            current_chunk.append(entry)
            if len(current_chunk) >= chunk_size:
                chunks.append(current_chunk)
                current_chunk = []

        if current_chunk:
            chunks.append(current_chunk)

        print(f"📦 Разделено на {len(chunks)} чанков по ~{chunk_size} записей")

        # Параллельная обработка
        chunk_results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.analyze_chunk, chunk) for chunk in chunks]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    chunk_results.append(result)
                except Exception as e:
                    print(f"❌ Ошибка обработки чанка: {e}")

        # Слияние результатов
        merged_stats = self.merge_chunk_stats(chunk_results)

        # Финальная обработка
        total_time = time.time() - start_time
        final_result = {
            'total_entries': merged_stats['total_entries'],
            'stages': dict(merged_stats['stages']),
            'event_types': dict(merged_stats['event_types']),
            'errors': dict(merged_stats['errors']),
            'total_correlations': len(merged_stats['correlation_ids']),
            'analysis_time': total_time,
            'processing_rate': merged_stats['total_entries'] / total_time if total_time > 0 else 0,
            'chunks_processed': len(chunk_results),
            'parallel_workers': max_workers,
        }

        # Сохраняем в кэш
        self.save_to_cache('parallel_stats', final_result)

        return final_result

    def analyze_correlations_parallel(self, chunk_size: int = 50000) -> Dict[str, Any]:
        """Параллельный анализ цепочек корреляций."""
        print("🔗 Анализируем цепочки корреляций...")

        if self.is_cache_valid('correlations'):
            print("📋 Используем кэшированные результаты цепочек")
            cached = self.load_from_cache('correlations')
            if cached:
                return cached

        start_time = time.time()

        # Собираем все цепочки
        correlations = defaultdict(list)

        for entry in self.stream_entries():
            if 'correlation_id' in entry:
                correlations[entry['correlation_id']].append(entry)

        # Обрабатываем цепочки
        chain_stats = []
        for chain_id, entries in correlations.items():
            if len(entries) < 2:  # Пропускаем короткие цепочки
                continue

            # Сортировка по времени
            sorted_entries = sorted(entries, key=lambda x: x['timestamp'])

            # Анализ цепочки
            stages = [e['stage'] for e in sorted_entries]
            duration = sorted_entries[-1]['timestamp'] - sorted_entries[0]['timestamp']
            completeness = len(set(stages) & {'event', 'meaning', 'decision', 'action', 'feedback'}) / 5

            chain_stats.append({
                'chain_id': chain_id,
                'duration': duration,
                'completeness': completeness,
                'stages': stages,
                'entry_count': len(sorted_entries)
            })

        # Статистика цепочек
        if chain_stats:
            durations = [s['duration'] for s in chain_stats]
            completeness_values = [s['completeness'] for s in chain_stats]

            result = {
                'total_chains': len(chain_stats),
                'avg_duration': sum(durations) / len(durations),
                'median_duration': sorted(durations)[len(durations) // 2],
                'min_duration': min(durations),
                'max_duration': max(durations),
                'avg_completeness': sum(completeness_values) / len(completeness_values),
                'complete_chains': sum(1 for s in chain_stats if s['completeness'] >= 0.8),
                'analysis_time': time.time() - start_time
            }
        else:
            result = {
                'total_chains': 0,
                'avg_duration': 0,
                'median_duration': 0,
                'min_duration': 0,
                'max_duration': 0,
                'avg_completeness': 0,
                'complete_chains': 0,
                'analysis_time': time.time() - start_time
            }

        # Сохраняем в кэш
        self.save_to_cache('correlations', result)

        return result

    def stream_filter(self, stage_filter: Optional[str] = None, event_type_filter: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Потоковая фильтрация записей."""
        for entry in self.stream_entries():
            if stage_filter and entry.get('stage') != stage_filter:
                continue
            if event_type_filter and entry.get('event_type') != event_type_filter:
                continue
            yield entry

    def export_filtered(self, output_file: str, **filters):
        """Экспорт отфильтрованных данных."""
        print(f"📤 Экспортируем отфильтрованные данные в {output_file}...")

        count = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in self.stream_filter(**filters):
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                count += 1
                if count % 10000 == 0:
                    print(f"  Обработано {count} записей...")

        print(f"✅ Экспортировано {count} записей")


def main():
    parser = argparse.ArgumentParser(
        description="Оптимизированный анализ больших файлов логов Life",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Базовая статистика с параллельной обработкой
  python scripts/analyze_large_logs.py stats --log-file data/large_log.jsonl

  # Анализ цепочек корреляций
  python scripts/analyze_large_logs.py chains --log-file data/large_log.jsonl

  # Экспорт отфильтрованных данных
  python scripts/analyze_large_logs.py export --filter-stage event --output events.jsonl

  # Очистка кэша
  python scripts/analyze_large_logs.py clear-cache

Оптимизации:
  - Параллельная обработка с использованием процессов
  - Кэширование результатов анализа
  - Потоковое чтение файлов (не загружает в память)
  - Инкрементальная обработка чанками
        """
    )

    parser.add_argument(
        'command',
        choices=['stats', 'chains', 'export', 'clear-cache'],
        help='Команда выполнения'
    )

    parser.add_argument(
        '--log-file',
        required=True,
        help='Путь к файлу логов для анализа'
    )

    parser.add_argument(
        '--chunk-size',
        type=int,
        default=10000,
        help='Размер чанка для параллельной обработки (default: 10000)'
    )

    parser.add_argument(
        '--max-workers',
        type=int,
        help='Максимальное количество процессов (default: auto)'
    )

    parser.add_argument(
        '--filter-stage',
        help='Фильтр по стадии для экспорта'
    )

    parser.add_argument(
        '--filter-event-type',
        help='Фильтр по типу события для экспорта'
    )

    parser.add_argument(
        '--output',
        help='Файл для экспорта результатов'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Не использовать кэширование'
    )

    args = parser.parse_args()

    # Проверяем существование файла
    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"❌ Ошибка: файл логов не найден: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    analyzer = LargeLogAnalyzer(args.log_file)

    try:
        if args.command == 'stats':
            print("📊 Выполняем анализ статистики...")
            result = analyzer.analyze_parallel(args.chunk_size, args.max_workers)

            print(f"📈 РЕЗУЛЬТАТЫ АНАЛИЗА")
            print(f"{'='*50}")
            print(f"Всего записей: {result['total_entries']:,}")
            print(f"Время анализа: {result['analysis_time']:.2f} сек")
            print(f"Скорость обработки: {result['processing_rate']:.0f} записей/сек")
            print(f"Чанков обработано: {result['chunks_processed']}")
            print(f"Параллельных процессов: {result['parallel_workers']}")
            print()

            if result['stages']:
                print("Распределение по стадиям:")
                for stage, count in sorted(result['stages'].items(), key=lambda x: x[1], reverse=True)[:10]:
                    pct = (count / result['total_entries']) * 100
                    print("15")
            print()

            if result['event_types']:
                print("Типы событий:")
                for event_type, count in sorted(result['event_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
                    total = sum(result['event_types'].values())
                    pct = (count / total) * 100
                    print("15")
            print()

            if result['errors']:
                print("Распределение ошибок:")
                for error_type, count in sorted(result['errors'].items(), key=lambda x: x[1], reverse=True)[:5]:
                    total = sum(result['errors'].values())
                    pct = (count / total) * 100
                    print("15")

        elif args.command == 'chains':
            print("🔗 Выполняем анализ цепочек корреляций...")
            result = analyzer.analyze_correlations_parallel(args.chunk_size)

            print(f"🔗 РЕЗУЛЬТАТЫ АНАЛИЗА ЦЕПОЧЕК")
            print(f"{'='*50}")
            print(f"Всего цепочек: {result['total_chains']:,}")
            print(f"Время анализа: {result['analysis_time']:.2f} сек")
            print()

            if result['total_chains'] > 0:
                print("Статистика длительности:")
                print(".3f")
                print(".3f")
                print(".3f")
                print(".3f")
                print()

                print("Статистика полноты:")
                print(".1%")
                print(f"Полных цепочек: {result['complete_chains']}")

        elif args.command == 'export':
            if not args.output:
                print("❌ Ошибка: укажите файл для экспорта с --output", file=sys.stderr)
                sys.exit(1)

            filters = {}
            if args.filter_stage:
                filters['stage_filter'] = args.filter_stage
            if args.filter_event_type:
                filters['event_type_filter'] = args.filter_event_type

            analyzer.export_filtered(args.output, **filters)

        elif args.command == 'clear-cache':
            import shutil
            if analyzer.cache_dir.exists():
                shutil.rmtree(analyzer.cache_dir)
                analyzer.cache_dir.mkdir()
                print("🗑️  Кэш очищен")
            else:
                print("📁 Кэш уже пуст")

    except KeyboardInterrupt:
        print("\n🛑 Анализ прерван пользователем", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()