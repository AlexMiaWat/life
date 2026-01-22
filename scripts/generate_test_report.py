#!/usr/bin/env python3
"""
Скрипт для генерации итогового отчета по тестированию.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import json

def parse_junit_xml(xml_file):
    """Парсит JUnit XML файл и возвращает статистику."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Общая статистика
        testsuite = root.find('.//testsuite')
        if testsuite is None:
            return None

        stats = {
            'tests': int(testsuite.get('tests', 0)),
            'errors': int(testsuite.get('errors', 0)),
            'failures': int(testsuite.get('failures', 0)),
            'skipped': int(testsuite.get('skipped', 0)),
            'time': float(testsuite.get('time', 0)),
            'testcases': []
        }

        # Детали по тестам
        for testcase in root.findall('.//testcase'):
            tc_info = {
                'classname': testcase.get('classname', ''),
                'name': testcase.get('name', ''),
                'time': float(testcase.get('time', 0)),
                'status': 'passed'
            }

            # Проверяем на ошибки/провалы
            failure = testcase.find('failure')
            error = testcase.find('error')

            if failure is not None:
                tc_info['status'] = 'failed'
                tc_info['message'] = failure.get('message', '')
                tc_info['details'] = failure.text
            elif error is not None:
                tc_info['status'] = 'error'
                tc_info['message'] = error.get('message', '')
                tc_info['details'] = error.text

            stats['testcases'].append(tc_info)

        return stats

    except Exception as e:
        print(f"Ошибка парсинга {xml_file}: {e}")
        return None

def generate_error_report():
    """Генерирует отчет об ошибках."""
    project_root = Path(__file__).parent.parent
    reports_dir = project_root / "docs" / "results"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Собираем все XML файлы отчетов
    xml_files = list(project_root.glob("test_*.xml"))

    all_stats = {
        'summary': {
            'total_tests': 0,
            'total_passed': 0,
            'total_failed': 0,
            'total_errors': 0,
            'total_skipped': 0,
            'total_time': 0.0,
            'test_suites': []
        },
        'errors': [],
        'failures': [],
        'generated_at': datetime.now().isoformat()
    }

    for xml_file in xml_files:
        stats = parse_junit_xml(xml_file)
        if stats:
            suite_name = xml_file.stem.replace('test_', '').replace('_1769089262', '')
            all_stats['summary']['test_suites'].append({
                'name': suite_name,
                'stats': stats
            })

            all_stats['summary']['total_tests'] += stats['tests']
            all_stats['summary']['total_errors'] += stats['errors']
            all_stats['summary']['total_failed'] += stats['failures']
            all_stats['summary']['total_skipped'] += stats['skipped']
            all_stats['summary']['total_time'] += stats['time']

            # Собираем ошибки и провалы
            for tc in stats['testcases']:
                if tc['status'] == 'error':
                    all_stats['errors'].append({
                        'suite': suite_name,
                        'test': f"{tc['classname']}::{tc['name']}",
                        'message': tc.get('message', ''),
                        'details': tc.get('details', '')
                    })
                elif tc['status'] == 'failed':
                    all_stats['failures'].append({
                        'suite': suite_name,
                        'test': f"{tc['classname']}::{tc['name']}",
                        'message': tc.get('message', ''),
                        'details': tc.get('details', '')
                    })

    all_stats['summary']['total_passed'] = (
        all_stats['summary']['total_tests'] -
        all_stats['summary']['total_failed'] -
        all_stats['summary']['total_errors'] -
        all_stats['summary']['total_skipped']
    )

    # Сохраняем JSON отчет
    json_file = reports_dir / "test_errors_report_1769089262.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, indent=2, ensure_ascii=False)

    return all_stats

def generate_markdown_report(stats):
    """Генерирует Markdown отчет."""
    reports_dir = Path(__file__).parent.parent / "docs" / "results"

    report = f"""# Отчет о тестировании - Полная задача 1769089262

**Дата генерации:** {stats['generated_at']}
**Общее время выполнения:** {stats['summary']['total_time']:.2f} сек

## Общая статистика

| Метрика | Значение |
|---------|----------|
| Всего тестов | {stats['summary']['total_tests']} |
| Пройдено | {stats['summary']['total_passed']} |
| Провалено | {stats['summary']['total_failed']} |
| Ошибок | {stats['summary']['total_errors']} |
| Пропущено | {stats['summary']['total_skipped']} |

**Успешность:** {stats['summary']['total_passed']/max(1, stats['summary']['total_tests'])*100:.1f}%

## Результаты по наборам тестов

"""

    for suite in stats['summary']['test_suites']:
        suite_stats = suite['stats']
        passed = suite_stats['tests'] - suite_stats['errors'] - suite_stats['failures'] - suite_stats['skipped']
        success_rate = passed / max(1, suite_stats['tests']) * 100

        report += f"""### {suite['name'].title()} Tests
- **Тестов:** {suite_stats['tests']}
- **Пройдено:** {passed}
- **Провалено:** {suite_stats['failures']}
- **Ошибок:** {suite_stats['errors']}
- **Успешность:** {success_rate:.1f}%
- **Время:** {suite_stats['time']:.2f} сек

"""

    # Ошибки
    if stats['errors']:
        report += f"## Ошибки импорта/инициализации ({len(stats['errors'])})\n\n"
        for error in stats['errors'][:10]:  # Показываем первые 10
            report += f"""### {error['test']}
**Сообщение:** {error['message']}

**Детали:**
```
{error['details'][:500]}...
```

"""

    # Провалы
    if stats['failures']:
        report += f"## Провалы тестов ({len(stats['failures'])})\n\n"
        for failure in stats['failures'][:10]:  # Показываем первые 10
            report += f"""### {failure['test']}
**Сообщение:** {failure['message']}

**Детали:**
```
{failure['details'][:500]}...
```

"""

    # Рекомендации
    report += "## Рекомендации\n\n"

    total_tests = stats['summary']['total_tests']
    total_passed = stats['summary']['total_passed']
    success_rate = total_passed / max(1, total_tests) * 100

    if success_rate >= 90:
        report += "✅ **Отличный результат!** Большинство тестов проходит успешно.\n\n"
    elif success_rate >= 75:
        report += "⚠️ **Хороший результат.** Есть некоторые проблемы, требующие внимания.\n\n"
    else:
        report += "🚨 **Требуется внимание!** Много проваленных тестов.\n\n"

    if stats['errors']:
        report += f"- Исправить {len(stats['errors'])} ошибок импорта/инициализации\n"

    if stats['failures']:
        report += f"- Исправить {len(stats['failures'])} проваленных тестов\n"

    report += "- Рассмотреть возможность рефакторинга проблемных модулей\n"
    report += "- Добавить больше интеграционных тестов\n"

    return report

def main():
    """Основная функция."""
    print("🔍 Генерация отчета о тестировании...")

    # Генерируем отчет об ошибках
    stats = generate_error_report()

    if not stats:
        print("❌ Не удалось сгенерировать статистику тестирования")
        return

    # Генерируем Markdown отчет
    markdown_report = generate_markdown_report(stats)

    # Сохраняем отчет
    reports_dir = Path(__file__).parent.parent / "docs" / "results"
    report_file = reports_dir / "test_full_task_1769089262.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(markdown_report)

    print("📊 Статистика тестирования:")
    print(f"   Всего тестов: {stats['summary']['total_tests']}")
    print(f"   Пройдено: {stats['summary']['total_passed']}")
    print(f"   Провалено: {stats['summary']['total_failed']}")
    print(f"   Ошибок: {stats['summary']['total_errors']}")
    print(f"   Пропущено: {stats['summary']['total_skipped']}")

    success_rate = stats['summary']['total_passed'] / max(1, stats['summary']['total_tests']) * 100
    print(f"   Успешность: {success_rate:.1f}%")
    print(f"\n📄 Отчет сохранен в: {report_file}")

if __name__ == "__main__":
    main()