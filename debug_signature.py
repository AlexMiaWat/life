#!/usr/bin/env python3
"""
Проверка сигнатуры метода process_statistics
"""

import inspect
import sys
from pathlib import Path

# Добавляем src в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.learning.learning import LearningEngine


def check_signature():
    engine = LearningEngine()
    sig = inspect.signature(engine.process_statistics)
    print(f"Signature: {sig}")
    print(f"Parameters: {sig.parameters}")
    print(f"Number of parameters: {len(sig.parameters)}")

    # Проверим, является ли метод bound
    print(f"Method: {engine.process_statistics}")
    print(f"Type: {type(engine.process_statistics)}")

    # Проверим unbound метод
    unbound_sig = inspect.signature(LearningEngine.process_statistics)
    print(f"Unbound signature: {unbound_sig}")
    print(f"Unbound parameters: {unbound_sig.parameters}")


if __name__ == "__main__":
    check_signature()
