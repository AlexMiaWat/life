#!/usr/bin/env python3
"""
Инструмент мониторинга логов в реальном времени.

Следит за структурированными логами Life и показывает алерты,
статистику и метрики производительности в реальном времени.

Использование:
    python scripts/monitor_logs.py --log-file data/structured_log.jsonl
"""

import argparse
import json
import sys
import time
import threading
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))


class LogMonitor:
    """Монитор логов в реальном времени."""

    def __init__(self, log_file: str, alert_thresholds: Optional[Dict[str, Any]] = None):
        self.log_file = Path(log_file)
        self.alert_thresholds = alert_thresholds or self._default_thresholds()
        self.stats = self._init_stats()
        self.last_position = 0
        self.running = False
        self.lock = threading.Lock()

    def _default_thresholds(self) -> Dict[str, Any]:
        """Стандартные пороги для алертов."""
        return {
            'slow_tick_ms': 50.0,      # Медленный тик > 50мс
            'very_slow_tick_ms': 100.0, # Очень медленный тик > 100мс
            'error_rate_threshold': 0.1, # Доля ошибок > 10%
            'max_queue_size': 50,       # Большая очередь > 50
        }

    def _init_stats(self) -> Dict[str, Any]:
        """Инициализация статистики."""
        return {
            'total_entries': 0,
            'stages': defaultdict(int),
            'event_types': defaultdict(int),
            'errors': defaultdict(int),
            'tick_durations': deque(maxlen=100),  # Последние 100 тиков
            'queue_sizes': deque(maxlen=100),     # Последние 100 размеров очереди
            'recent_entries': deque(maxlen=10),   # Последние 10 записей
            'alerts': [],
            'start_time': time.time()
        }

    def start_monitoring(self):
        """Запуск мониторинга."""
        if not self.log_file.exists():
            print(f"Ошибка: файл логов не найден: {self.log_file}")
            return

        self.running = True
        print(f"🚀 Начинаем мониторинг файла: {self.log_file}")
        print(f"📊 Пороги алертов: {self.alert_thresholds}")
        print("=" * 60)

        try:
            while self.running:
                self._check_new_entries()
                self._display_stats()
                time.sleep(1)  # Проверяем каждую секунду

        except KeyboardInterrupt:
            print("\n🛑 Мониторинг остановлен пользователем")
        except Exception as e:
            print(f"\n❌ Ошибка мониторинга: {e}")
        finally:
            self._print_final_summary()

    def stop_monitoring(self):
        """Остановка мониторинга."""
        self.running = False

    def _check_new_entries(self):
        """Проверка новых записей в файле логов."""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()

            for line in new_lines:
                try:
                    entry = json.loads(line.strip())
                    self._process_entry(entry)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Ошибка парсинга: {e}")

        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")

    def _process_entry(self, entry: Dict[str, Any]):
        """Обработка новой записи лога."""
        with self.lock:
            self.stats['total_entries'] += 1

            # Анализ стадии
            stage = entry.get('stage', 'unknown')
            self.stats['stages'][stage] += 1

            # Анализ событий
            if stage == 'event':
                event_type = entry.get('event_type', 'unknown')
                self.stats['event_types'][event_type] += 1

            # Анализ ошибок
            if stage.startswith('error_'):
                error_type = entry.get('error_type', 'unknown')
                self.stats['errors'][error_type] += 1

                # Алерт на ошибки
                self._check_error_alert(entry)

            # Анализ производительности
            if stage == 'tick_start':
                queue_size = entry.get('queue_size', 0)
                self.stats['queue_sizes'].append(queue_size)

                if queue_size > self.alert_thresholds['max_queue_size']:
                    self._add_alert(f"Большая очередь: {queue_size} элементов", "warning")

            elif stage == 'tick_end':
                # Для простоты предполагаем, что tick_end следует за tick_start
                # В реальности нужно связывать их по tick_number
                pass

            # Сохраняем недавние записи
            self.stats['recent_entries'].append(entry)

            # Проверяем алерты
            self._check_alerts()

    def _check_error_alert(self, entry: Dict[str, Any]):
        """Проверка алертов по ошибкам."""
        total_entries = self.stats['total_entries']
        total_errors = sum(self.stats['errors'].values())

        if total_entries > 0:
            error_rate = total_errors / total_entries
            if error_rate > self.alert_thresholds['error_rate_threshold']:
                self._add_alert(".1%", "error")

    def _check_alerts(self):
        """Проверка различных алертов."""
        # Алерт на высокую частоту ошибок
        total_errors = sum(self.stats['errors'].values())
        if total_errors > 0 and self.stats['total_entries'] > 100:
            error_rate = total_errors / self.stats['total_entries']
            if error_rate > 0.05:  # > 5% ошибок
                self._add_alert(".1%", "warning")

    def _add_alert(self, message: str, level: str = "info"):
        """Добавление алерта."""
        alert = {
            'timestamp': time.time(),
            'message': message,
            'level': level
        }
        self.stats['alerts'].append(alert)

        # Ограничиваем количество алертов
        if len(self.stats['alerts']) > 50:
            self.stats['alerts'] = self.stats['alerts'][-50:]

        # Выводим алерт
        emoji = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}.get(level, 'ℹ️')
        print(f"{emoji} {message}")

    def _display_stats(self):
        """Отображение текущей статистики."""
        with self.lock:
            runtime = time.time() - self.stats['start_time']

            print(f"\r{'='*60}")
            print("📊 СТАТИСТИКА МОНИТОРИНГА")
            print(f"{'='*60}")
            print(f"⏱️  Время работы: {runtime:.1f} сек")
            print(f"📝 Всего записей: {self.stats['total_entries']:,}")
            print(f"🔄 Записей/сек: {self.stats['total_entries'] / runtime:.1f}" if runtime > 0 else "🔄 Записей/сек: 0.0")

            if self.stats['stages']:
                print(f"\n🎭 Стадии обработки:")
                for stage, count in sorted(self.stats['stages'].items(), key=lambda x: x[1], reverse=True)[:5]:
                    pct = (count / self.stats['total_entries']) * 100 if self.stats['total_entries'] > 0 else 0
                    print("15")

            if self.stats['event_types']:
                print(f"\n🎯 Типы событий:")
                for event_type, count in sorted(self.stats['event_types'].items(), key=lambda x: x[1], reverse=True)[:5]:
                    total_events = sum(self.stats['event_types'].values())
                    pct = (count / total_events) * 100 if total_events > 0 else 0
                    print("15")

            if self.stats['errors']:
                print(f"\n❌ Ошибки:")
                total_errors = sum(self.stats['errors'].values())
                for error_type, count in sorted(self.stats['errors'].items(), key=lambda x: x[1], reverse=True)[:3]:
                    pct = (count / total_errors) * 100 if total_errors > 0 else 0
                    print("15")

            # Показываем недавние алерты
            recent_alerts = [a for a in self.stats['alerts'][-5:] if time.time() - a['timestamp'] < 60]
            if recent_alerts:
                print(f"\n🚨 Недавние алерты:")
                for alert in recent_alerts:
                    emoji = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}.get(alert['level'], 'ℹ️')
                    print(f"  {emoji} {alert['message']}")

            # Очистка экрана (для обновления)
            print("\033[2J\033[H", end="")  # Очистка экрана и курсор в начало

    def _print_final_summary(self):
        """Вывод итоговой сводки при завершении."""
        with self.lock:
            print(f"\n{'='*60}")
            print("📋 ИТОГОВАЯ СВОДКА МОНИТОРИНГА")
            print(f"{'='*60}")

            runtime = time.time() - self.stats['start_time']
            print(f"⏱️  Общее время мониторинга: {runtime:.1f} сек")
            print(f"📝 Всего обработано записей: {self.stats['total_entries']:,}")
            print(f"🔄 Средняя скорость: {self.stats['total_entries'] / runtime:.1f} записей/сек" if runtime > 0 else "🔄 Средняя скорость: 0.0 записей/сек")

            if self.stats['alerts']:
                print(f"\n🚨 Всего алертов: {len(self.stats['alerts'])}")
                error_alerts = [a for a in self.stats['alerts'] if a['level'] == 'error']
                warning_alerts = [a for a in self.stats['alerts'] if a['level'] == 'warning']
                print(f"❌ Критических алертов: {len(error_alerts)}")
                print(f"⚠️  Предупреждений: {len(warning_alerts)}")

            print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Мониторинг структурированных логов Life в реальном времени",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Мониторинг стандартного файла логов
  python scripts/monitor_logs.py

  # Мониторинг конкретного файла
  python scripts/monitor_logs.py --log-file data/custom_log.jsonl

  # Мониторинг с кастомными порогами
  python scripts/monitor_logs.py --slow-tick-threshold 100 --error-rate-threshold 0.05

  # Тихий режим (без постоянного обновления статистики)
  python scripts/monitor_logs.py --quiet

Алерты:
  - Медленные тики (> 50мс по умолчанию)
  - Высокая частота ошибок (> 10% по умолчанию)
  - Большая очередь событий (> 50 по умолчанию)
        """
    )

    parser.add_argument(
        '--log-file',
        default='data/structured_log.jsonl',
        help='Путь к файлу логов для мониторинга (default: data/structured_log.jsonl)'
    )

    parser.add_argument(
        '--slow-tick-threshold',
        type=float,
        default=50.0,
        help='Порог для алерта медленных тиков в мс (default: 50.0)'
    )

    parser.add_argument(
        '--error-rate-threshold',
        type=float,
        default=0.1,
        help='Порог частоты ошибок для алерта (default: 0.1)'
    )

    parser.add_argument(
        '--max-queue-size',
        type=int,
        default=50,
        help='Максимальный размер очереди для алерта (default: 50)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Тихий режим - показывать только алерты'
    )

    args = parser.parse_args()

    # Настройка порогов алертов
    alert_thresholds = {
        'slow_tick_ms': args.slow_tick_threshold,
        'error_rate_threshold': args.error_rate_threshold,
        'max_queue_size': args.max_queue_size,
    }

    # Создание и запуск монитора
    monitor = LogMonitor(args.log_file, alert_thresholds)

    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("\n🛑 Мониторинг завершен")


if __name__ == '__main__':
    main()