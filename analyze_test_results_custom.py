#!/usr/bin/env python3

import os
import xml.etree.ElementTree as ET
from datetime import datetime


def analyze_test_results(xml_file):
    """Analyze pytest XML results and return summary"""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Get overall statistics
    testsuite = root.find("testsuite")
    if testsuite is None:
        return None

    total_tests = int(testsuite.get("tests", 0))
    failures = int(testsuite.get("failures", 0))
    errors = int(testsuite.get("errors", 0))
    skipped = int(testsuite.get("skipped", 0))
    time_taken = float(testsuite.get("time", 0))

    passed = total_tests - failures - errors - skipped

    # Collect failed test details
    failed_tests = []
    for testcase in testsuite.findall("testcase"):
        failure = testcase.find("failure")
        error = testcase.find("error")
        if failure is not None or error is not None:
            test_name = f"{testcase.get('classname')}::{testcase.get('name')}"
            message = ""
            if failure is not None:
                message = failure.get("message", "") + "\n" + failure.text
            elif error is not None:
                message = error.get("message", "") + "\n" + error.text

            failed_tests.append(
                {
                    "name": test_name,
                    "message": message.strip(),
                    "time": float(testcase.get("time", 0)),
                }
            )

    return {
        "total": total_tests,
        "passed": passed,
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
        "time": time_taken,
        "failed_tests": failed_tests,
    }


def create_report(results, output_file):
    """Create a detailed test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# Отчет о тестировании - {timestamp}

## Общая статистика

- **Всего тестов:** {results['total']}
- **Пройдено:** {results['passed']}
- **Провалено:** {results['failed']}
- **Ошибки:** {results['errors']}
- **Пропущено:** {results['skipped']}
- **Время выполнения:** {results['time']:.2f} секунд

## Статус тестирования

"""

    if results["failed"] == 0 and results["errors"] == 0:
        report += "✅ **ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!**\n\n"
    else:
        report += f"❌ **ОБНАРУЖЕНЫ ПРОБЛЕМЫ:** {results['failed'] + results['errors']} тестов не прошли\n\n"

    if results["failed_tests"]:
        report += "## Детали проваленных тестов\n\n"
        for i, test in enumerate(results["failed_tests"], 1):
            report += f"### {i}. {test['name']}\n\n"
            report += f"**Время выполнения:** {test['time']:.3f} сек\n\n"
            report += "**Ошибка:**\n\n```\n"
            report += test["message"]
            report += "\n```\n\n"

    if results["skipped"] > 0:
        report += "## Пропущенные тесты\n\n"
        report += f"Количество пропущенных тестов: {results['skipped']}\n\n"
        report += "Пропущенные тесты обычно требуют специальных условий выполнения (например, реального сервера).\n\n"

    # Summary by test files
    test_files = {}
    for testcase in (
        ET.parse("test_results.xml").getroot().find("testsuite").findall("testcase")
    ):
        classname = testcase.get("classname", "")
        if classname:
            file_name = classname.split(".")[1] if "." in classname else classname
            if file_name not in test_files:
                test_files[file_name] = {"total": 0, "passed": 0, "failed": 0}

            test_files[file_name]["total"] += 1
            if (
                testcase.find("failure") is not None
                or testcase.find("error") is not None
            ):
                test_files[file_name]["failed"] += 1
            else:
                test_files[file_name]["passed"] += 1

    report += "## Статистика по файлам тестов\n\n"
    report += "| Файл | Всего | Пройдено | Провалено |\n"
    report += "|------|-------|----------|-----------|\n"

    for file_name, stats in sorted(test_files.items()):
        report += f"| {file_name} | {stats['total']} | {stats['passed']} | {stats['failed']} |\n"

    report += "\n## Рекомендации\n\n"

    if results["failed"] > 0:
        report += "- Необходимо исправить проваленные тесты\n"
        report += "- Проверить логику и реализации соответствующих функций\n"
        report += "- Возможно, требуется обновление зависимостей или конфигурации\n"

    if results["errors"] > 0:
        report += "- Исправить ошибки в коде тестов или зависимостях\n"
        report += "- Проверить импорты и структуру проекта\n"

    if results["skipped"] > 0:
        report += f"- {results['skipped']} тестов пропущено - возможно, требуется запуск с дополнительными опциями\n"

    report += "\n---\n*Отчет создан автоматически*"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Отчет создан: {output_file}")


def main():
    xml_file = "test_results_observability.xml"
    output_file = "docs/results/test_full_task_1769013311.md"

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    if not os.path.exists(xml_file):
        print(f"Файл {xml_file} не найден!")
        return

    results = analyze_test_results(xml_file)
    if results:
        create_report(results, output_file)
        print("Отчет успешно создан!")
    else:
        print("Не удалось проанализировать результаты тестов")


if __name__ == "__main__":
    main()
