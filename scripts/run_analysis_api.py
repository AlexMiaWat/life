#!/usr/bin/env python3
"""
Скрипт для запуска Analysis API сервера.

Предоставляет REST API для программного анализа структурированных логов Life.

Использование:
    python run_analysis_api.py --host 0.0.0.0 --port 8001
"""

import argparse
import logging
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import uvicorn
    from src.observability.analysis_api import app
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что вы находитесь в корневой директории проекта")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Запуск Analysis API сервера для анализа логов Life",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Запуск на localhost:8001
  python scripts/run_analysis_api.py

  # Запуск на всех интерфейсах
  python scripts/run_analysis_api.py --host 0.0.0.0

  # Запуск на определенном порту
  python scripts/run_analysis_api.py --port 8080

  # Запуск с отладкой
  python scripts/run_analysis_api.py --debug

  # Запуск с автоматической перезагрузкой
  python scripts/run_analysis_api.py --reload

API Endpoints:
  GET  /              - Информация об API
  GET  /stats         - Статистика логов
  GET  /chains        - Анализ цепочек обработки
  GET  /performance   - Метрики производительности
  GET  /errors        - Сводка по ошибкам
  GET  /export        - Экспорт результатов анализа
  POST /analyze       - Произвольный анализ
  GET  /health        - Проверка здоровья API
        """
    )

    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Хост для запуска сервера (default: 127.0.0.1)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8001,
        help='Порт для запуска сервера (default: 8001)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Включить режим отладки'
    )

    parser.add_argument(
        '--reload',
        action='store_true',
        help='Включить автоматическую перезагрузку при изменении кода'
    )

    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error'],
        default='info',
        help='Уровень логирования (default: info)'
    )

    args = parser.parse_args()

    # Настройка логирования
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Запуск Analysis API сервера на {args.host}:{args.port}")

    try:
        uvicorn.run(
            "src.observability.analysis_api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Analysis API сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска Analysis API сервера: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()