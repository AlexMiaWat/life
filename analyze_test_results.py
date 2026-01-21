#!/usr/bin/env python3

import os
import glob
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def analyze_single_xml_file(xml_file):
    """Analyze single pytest XML results file and return summary"""
    try:
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
    except Exception as e:
        print(f"Error analyzing {xml_file}: {e}")
        return None


def analyze_all_test_results(results_dir="artifacts"):
    """Analyze all test results from CI artifacts and return comprehensive summary"""
    print("🔍 Анализ результатов тестирования...")

    # Define test categories and their expected XML files
    categories = {
        "unit": "test-results-unit.xml",
        "static": "test-results-static.xml",
        "smoke": "test-results-smoke.xml",
        "integration": "test-results-integration.xml",
        "performance": "test-results-performance.xml",
        "concurrency": "test-results-concurrency.xml"
    }

    overall_summary = {
        "categories": {},
        "total": {
            "tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "time": 0.0
        },
        "failed_tests": [],
        "missing_categories": []
    }

    # Analyze each category
    for category_name, xml_filename in categories.items():
        xml_path = os.path.join(results_dir, xml_filename)

        if os.path.exists(xml_path):
            print(f"📄 Анализ {category_name} тестов...")
            result = analyze_single_xml_file(xml_path)

            if result:
                overall_summary["categories"][category_name] = result

                # Add to overall totals
                overall_summary["total"]["tests"] += result["total"]
                overall_summary["total"]["passed"] += result["passed"]
                overall_summary["total"]["failed"] += result["failed"]
                overall_summary["total"]["errors"] += result["errors"]
                overall_summary["total"]["skipped"] += result["skipped"]
                overall_summary["total"]["time"] += result["time"]

                # Collect failed tests with category
                for failed_test in result["failed_tests"]:
                    failed_test["category"] = category_name
                    overall_summary["failed_tests"].append(failed_test)
            else:
                print(f"⚠️  Не удалось проанализировать {xml_filename}")
                overall_summary["missing_categories"].append(category_name)
        else:
            print(f"⚠️  Файл {xml_filename} не найден")
            overall_summary["missing_categories"].append(category_name)

    # Try to find any other XML files
    xml_pattern = os.path.join(results_dir, "*.xml")
    found_xmls = glob.glob(xml_pattern)

    for xml_file in found_xmls:
        filename = os.path.basename(xml_file)
        if filename not in categories.values():
            print(f"📄 Найден дополнительный файл результатов: {filename}")
            result = analyze_single_xml_file(xml_file)
            if result:
                category_name = filename.replace("test-results-", "").replace(".xml", "")
                overall_summary["categories"][category_name] = result

                # Add to overall totals
                overall_summary["total"]["tests"] += result["total"]
                overall_summary["total"]["passed"] += result["passed"]
                overall_summary["total"]["failed"] += result["failed"]
                overall_summary["total"]["errors"] += result["errors"]
                overall_summary["total"]["skipped"] += result["skipped"]
                overall_summary["total"]["time"] += result["time"]

    return overall_summary


def create_comprehensive_report(results, output_file):
    """Create a comprehensive test report for CI pipeline"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# Комплексный отчет о тестировании - {timestamp}

## 📊 Общая статистика по всем категориям

- **Всего тестов:** {results['total']['tests']}
- **Пройдено:** {results['total']['passed']}
- **Провалено:** {results['total']['failed']}
- **Ошибки:** {results['total']['errors']}
- **Пропущено:** {results['total']['skipped']}
- **Общее время выполнения:** {results['total']['time']:.2f} секунд
- **Категорий тестов:** {len(results['categories'])}

## 🎯 Статус тестирования

"""

    # Overall status
    total_failed = results['total']['failed'] + results['total']['errors']
    if total_failed == 0:
        report += "✅ **ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!**\n\n"
        success_rate = 100.0
    else:
        report += f"❌ **ОБНАРУЖЕНЫ ПРОБЛЕМЫ:** {total_failed} тестов не прошли\n\n"
        success_rate = (results['total']['passed'] / results['total']['tests']) * 100 if results['total']['tests'] > 0 else 0

    report += f"**Уровень успешности:** {success_rate:.1f}%\n\n"

    # Category breakdown
    report += "## 📈 Статистика по категориям\n\n"
    report += "| Категория | Всего | Пройдено | Провалено | Ошибки | Пропущено | Время |\n"
    report += "|-----------|-------|----------|-----------|--------|-----------|-------|\n"

    for category_name, category_results in results['categories'].items():
        report += f"| {category_name} | {category_results['total']} | {category_results['passed']} | {category_results['failed']} | {category_results['errors']} | {category_results['skipped']} | {category_results['time']:.1f}s |\n"

    report += "\n"

    # Missing categories
    if results['missing_categories']:
        report += "## ⚠️  Отсутствующие категории тестов\n\n"
        for category in results['missing_categories']:
            report += f"- {category}\n"
        report += "\n"

    # Failed tests details
    if results['failed_tests']:
        report += "## ❌ Детали проваленных тестов\n\n"
        for i, test in enumerate(results["failed_tests"], 1):
            report += f"### {i}. {test['name']} ({test.get('category', 'unknown')})\n\n"
            report += f"**Время выполнения:** {test['time']:.3f} сек\n\n"
            report += "**Ошибка:**\n\n```\n"
            report += test["message"]
            report += "\n```\n\n"

    # Skipped tests
    if results['total']['skipped'] > 0:
        report += "## ⏭️  Пропущенные тесты\n\n"
        report += f"**Общее количество пропущенных тестов:** {results['total']['skipped']}\n\n"
        report += "Пропущенные тесты обычно требуют специальных условий выполнения.\n\n"

    # Recommendations
    report += "## 💡 Рекомендации\n\n"

    if results['total']['failed'] > 0:
        report += "- 🔧 Необходимо исправить проваленные тесты\n"
        report += "- 🔍 Проверить логику и реализации соответствующих функций\n"
        report += "- 📦 Возможно, требуется обновление зависимостей или конфигурации\n"

    if results['total']['errors'] > 0:
        report += "- 🐛 Исправить ошибки в коде тестов или зависимостях\n"
        report += "- 🔗 Проверить импорты и структуру проекта\n"

    if results['missing_categories']:
        report += "- ⚠️  Проверить почему отсутствуют результаты некоторых категорий тестов\n"
        report += "- 🔄 Возможно, требуется настройка CI pipeline\n"

    if success_rate >= 95:
        report += "- 🎉 Отличный результат! Тестовое покрытие стабильное\n"
    elif success_rate >= 90:
        report += "- 👍 Хороший результат, но есть место для улучшений\n"
    else:
        report += "- ⚠️  Требуется внимание к качеству тестирования\n"

    report += "\n---\n*Отчет создан автоматически CI pipeline*"

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"📄 Комплексный отчет создан: {output_file}")
    print(f"📊 Общий статус: {'✅ УСПЕХ' if total_failed == 0 else '❌ ПРОБЛЕМЫ'}")
    print(f"📈 Уровень успешности: {success_rate:.1f}%")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Анализ результатов тестирования CI pipeline")
    parser.add_argument("--results-dir", default="artifacts", help="Директория с результатами тестов")
    parser.add_argument("--output", default="docs/results/ci_test_summary.md", help="Файл выходного отчета")

    args = parser.parse_args()

    print(f"🔍 Поиск результатов тестирования в: {args.results_dir}")

    if not os.path.exists(args.results_dir):
        print(f"⚠️  Директория {args.results_dir} не существует, создаем пустой отчет")
        # Create minimal report for missing results
        results = {
            "categories": {},
            "total": {"tests": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0, "time": 0.0},
            "failed_tests": [],
            "missing_categories": ["unit", "static", "smoke", "integration", "performance", "concurrency"]
        }
    else:
        results = analyze_all_test_results(args.results_dir)

    if results:
        create_comprehensive_report(results, args.output)
        print("✅ Отчет успешно создан!")

        # Return appropriate exit code
        total_failed = results['total']['failed'] + results['total']['errors']
        if total_failed > 0:
            print(f"❌ Обнаружено {total_failed} проваленных тестов")
            return 1
        else:
            print("✅ Все тесты прошли успешно")
            return 0
    else:
        print("❌ Не удалось проанализировать результаты тестов")
        return 1


if __name__ == "__main__":
    exit(main())
