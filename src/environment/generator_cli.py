"""
CLI для генерации событий и отправки их на API сервера.

Пример:
    python -m environment.generator_cli --interval 5 --host localhost --port 8000
"""

import argparse
import time

import requests

from src.environment.generator import EventGenerator
from src.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


def send_event(host: str, port: int, payload: dict) -> tuple[bool, int | None, str, str]:
    url = f"http://{host}:{port}/event"
    try:
        resp = requests.post(url, json=payload, timeout=5)
        code = resp.status_code
        body = resp.text
        return True, code, "", body
    except requests.exceptions.RequestException as e:
        return False, 0, str(e), ""
    except Exception as e:
        return False, None, str(e), ""


def main():
    parser = argparse.ArgumentParser(description="Environment Event Generator CLI")
    parser.add_argument(
        "--host", default="localhost", help="Хост API сервера (по умолчанию localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Порт API сервера (по умолчанию 8000)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Интервал генерации событий, сек (по умолчанию 5)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Включить подробное логирование (debug уровень)",
    )
    args = parser.parse_args()

    # Настройка логирования
    setup_logging(verbose=args.verbose)

    generator = EventGenerator()

    logger.info(
        f"[GeneratorCLI] start: host={args.host} port={args.port} interval={args.interval}s"
    )
    logger.info("[GeneratorCLI] Нажмите Ctrl+C для остановки")

    try:
        while True:
            event = generator.generate()
            payload = {
                "type": event.type,
                "intensity": event.intensity,
                "timestamp": event.timestamp,
                "metadata": event.metadata,
            }
            success, code, reason, body = send_event(args.host, args.port, payload)
            if success:
                logger.debug(
                    f"[GeneratorCLI] Sent event: {payload} | Code: {code} | Body: '{body}'"
                )
            else:
                logger.warning(
                    f"[GeneratorCLI] Failed: code={code} reason='{reason}' body='{body}'"
                )

            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("\n[GeneratorCLI] Stopped")


if __name__ == "__main__":  # pragma: no cover
    main()
