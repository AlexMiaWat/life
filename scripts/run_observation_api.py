#!/usr/bin/env python3
"""
Скрипт для запуска API сервера внешнего наблюдения за системой Life.

Использование:
    python run_observation_api.py --host 0.0.0.0 --port 8000
"""

import argparse
import logging
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import uvicorn
    from src.observability.observation_api import app
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что вы находитесь в корневой директории проекта")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Запуск API сервера внешнего наблюдения за системой Life",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Запуск на localhost:8000
  python run_observation_api.py

  # Запуск на всех интерфейсах
  python run_observation_api.py --host 0.0.0.0

  # Запуск на определенном порту
  python run_observation_api.py --port 8080

  # Запуск с отладкой
  python run_observation_api.py --debug
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
        default=8000,
        help='Порт для запуска сервера (default: 8000)'
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

    args = parser.parse_args()

    # Настройка логирования
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Запуск API сервера на {args.host}:{args.port}")

    try:
        uvicorn.run(
            "src.observability.observation_api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="debug" if args.debug else "info"
        )
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска сервера: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()