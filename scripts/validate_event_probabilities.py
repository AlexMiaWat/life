#!/usr/bin/env python3
"""
Валидатор соответствия вероятностей событий между кодом и документацией.

Проверяет:
1. Соответствие вероятностей в EventGenerator заявленным значениям
2. Корректность распределения (сумма = 1.0)
3. Наличие всех документированных типов событий
"""

import sys
import os
import re
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def extract_probabilities_from_code():
    """Извлекает вероятности из кода EventGenerator."""
    generator_path = project_root / "src" / "environment" / "generator.py"

    if not generator_path.exists():
        print(f"❌ Файл {generator_path} не найден")
        return None

    with open(generator_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Ищем массив вероятностей (base_weights)
    pattern = r'base_weights\s*=\s*\[([^\]]+)\]'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        print("❌ Не найден массив probabilities в generator.py")
        return None

    # Парсим вероятности
    probs_text = match.group(1)
    # Извлекаем комментарии и значения
    lines = probs_text.strip().split('\n')
    probabilities = {}
    current_prob = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Ищем комментарий с названием события
        comment_match = re.search(r'#\s*(\w+)\s*', line)
        if comment_match:
            event_type = comment_match.group(1)
            # Ищем значение вероятности в этой же строке
            prob_match = re.search(r'(\d+\.\d+)', line)
            if prob_match:
                probabilities[event_type] = float(prob_match.group(1))

    return probabilities

def extract_probabilities_from_docs():
    """Извлекает вероятности из документации."""
    docs_path = project_root / "docs" / "components" / "event_types_chain_system.md"

    if not docs_path.exists():
        print(f"❌ Файл документации {docs_path} не найден")
        return None

    with open(docs_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Ищем таблицу с вероятностями
    probabilities = {}

    # Ищем паттерн для каждого типа события
    patterns = [
        (r'isolation.*?(\d+\.\d+)%', 'isolation'),
        (r'connection.*?(\d+\.\d+)%', 'connection'),
        (r'insight.*?(\d+\.\d+)%', 'insight'),
        (r'confusion.*?(\d+\.\d+)%', 'confusion'),
        (r'curiosity.*?(\d+\.\d+)%', 'curiosity'),
        (r'meaning_found.*?(\d+\.\d+)%', 'meaning_found'),
        (r'void.*?(\d+\.\d+)%', 'void'),
        (r'acceptance.*?(\d+\.\d+)%', 'acceptance'),
    ]

    for pattern, event_type in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            # Преобразуем проценты в доли
            percent = float(match.group(1))
            probabilities[event_type] = percent / 100.0

    return probabilities

def validate_probabilities():
    """Основная функция валидации."""
    print("🔍 Валидация вероятностей событий...")
    print("=" * 50)

    # Получаем вероятности из кода и документации
    code_probs = extract_probabilities_from_code()
    docs_probs = extract_probabilities_from_docs()

    if code_probs is None or docs_probs is None:
        return False

    print(f"📊 Найдено типов событий в коде: {len(code_probs)}")
    print(f"📋 Задокументировано типов событий: {len(docs_probs)}")
    print()

    # Проверяем соответствие
    all_types = set(code_probs.keys()) | set(docs_probs.keys())
    mismatches = []
    missing_in_docs = []
    missing_in_code = []

    for event_type in sorted(all_types):
        code_prob = code_probs.get(event_type)
        docs_prob = docs_probs.get(event_type)

        if code_prob is None:
            missing_in_code.append(event_type)
            continue
        if docs_prob is None:
            missing_in_docs.append(event_type)
            continue

        # Проверяем соответствие с допустимой погрешностью 0.001
        diff = abs(code_prob - docs_prob)
        if diff > 0.001:
            mismatches.append({
                'type': event_type,
                'code': code_prob,
                'docs': docs_prob,
                'diff': diff
            })

    # Выводим результаты
    success = True

    if missing_in_code:
        print("❌ Типы событий, отсутствующие в коде:")
        for event_type in missing_in_code:
            print(f"   - {event_type}")
        success = False

    if missing_in_docs:
        print("❌ Типы событий, не задокументированные:")
        for event_type in missing_in_docs:
            print(f"   - {event_type}")
        success = False

    if mismatches:
        print("⚠️  Несоответствия вероятностей:")
        for mismatch in mismatches:
            print(f"   - {mismatch['type']}: код={mismatch['code']:.3f}, док={mismatch['docs']:.3f}, разница={mismatch['diff']:.3f}")
        success = False

    # Проверяем сумму вероятностей
    total_code = sum(code_probs.values())
    total_docs = sum(docs_probs.values())

    print()
    print("📈 Суммарные вероятности:")
    print(f"   - В коде: {total_code:.3f}")
    print(f"   - В документации: {total_docs:.3f}")
    # Проверяем, что сумма близка к 1.0
    if abs(total_code - 1.0) > 0.01:
        print(f"❌ Сумма вероятностей в коде сильно отличается от 1.0")
        success = False

    if abs(total_docs - 1.0) > 0.01:
        print(f"❌ Сумма вероятностей в документации сильно отличается от 1.0")
        success = False

    print()
    if success:
        print("✅ Валидация пройдена успешно!")
        return True
    else:
        print("❌ Обнаружены проблемы валидации!")
        return False

if __name__ == "__main__":
    success = validate_probabilities()
    sys.exit(0 if success else 1)