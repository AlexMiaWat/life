#!/usr/bin/env python3
"""
Скрипт для запуска performance тестов с проверкой на регрессии.

Использование:
    python run_performance_tests.py [--update-baseline] [--report-only]

Опции:
    --update-baseline: Обновить baseline значения
    --report-only: Только показать отчет, не запускать тесты
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Добавляем src в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def run_performance_tests(update_baseline: bool = False):
    """Запустить performance тесты."""
    print("🚀 Запуск performance тестов...")

    # Формируем команду pytest
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "src/test/test_performance.py",
        "-v",
        "--tb=short",
        "-m",
        "performance",
    ]

    if update_baseline:
        # Устанавливаем переменную окружения для обновления baseline
        env = dict(os.environ)
        env["PERFORMANCE_UPDATE_BASELINE"] = "1"
    else:
        env = None

    # Запускаем тесты
    result = subprocess.run(
        cmd, cwd=project_root, env=env, capture_output=True, text=True
    )

    print("📊 Результаты выполнения тестов:")
    print(result.stdout)

    if result.stderr:
        print("⚠️  Ошибки:")
        print(result.stderr)

    return result.returncode == 0, result.stdout, result.stderr


def generate_regression_report(stdout: str = "", stderr: str = ""):
    """Генерировать отчет о регрессиях производительности на основе вывода тестов."""
    print("📈 Генерация отчета о регрессиях...")

    # Анализируем вывод тестов
    full_output = stdout + stderr

    # Ищем результаты тестов и сообщения о регрессиях
    lines = full_output.split("\n")

    report = {
        "summary": {"total_tests": 0, "passed": 0, "failed": 0, "regressions": []},
        "details": [],
    }

    current_test = None
    test_output = []

    for line in lines:
        # Ищем начало теста
        if line.startswith("src/test/test_performance.py::TestPerformanceBenchmarks::"):
            if current_test:
                # Сохраняем предыдущий тест
                _process_test_output(current_test, test_output, report)

            # Начинаем новый тест
            test_name = line.split("::")[-1]
            current_test = test_name
            test_output = [line]
        elif current_test:
            test_output.append(line)

    # Обрабатываем последний тест
    if current_test:
        _process_test_output(current_test, test_output, report)

    # Если не нашли структурированных результатов, ищем сообщения о регрессиях в общем выводе
    if report["summary"]["total_tests"] == 0:
        regression_lines = [
            line for line in lines if "🚨 РЕГРЕССИЯ" in line or "✅ OK" in line
        ]
        if regression_lines:
            report["summary"]["total_tests"] = len(regression_lines)
            report["summary"]["passed"] = len(
                [line for line in regression_lines if "✅" in line]
            )
            report["summary"]["failed"] = 0
            report["summary"]["regressions"] = [
                line.split()[2].split(".")[0]
                for line in regression_lines
                if "🚨" in line
            ]

            for line in regression_lines:
                has_regression = "🚨" in line
                test_name = (
                    line.split()[2].split(".")[0]
                    if len(line.split()) > 2
                    else "unknown"
                )
                report["details"].append(
                    {
                        "test_name": test_name,
                        "status": "✅ ПРОЙДЕН" if not has_regression else "❌ ПРОВАЛЕН",
                        "has_regression": has_regression,
                        "duration": 0.0,
                        "stdout": line,
                    }
                )

    return report


def _process_test_output(test_name: str, output_lines: list, report: dict):
    """Обработать вывод одного теста."""
    output_text = "\n".join(output_lines)

    # Определяем статус теста
    if "PASSED" in output_text or "passed" in output_text.lower():
        status = "✅ ПРОЙДЕН"
        report["summary"]["passed"] += 1
    elif "FAILED" in output_text or "failed" in output_text.lower():
        status = "❌ ПРОВАЛЕН"
        report["summary"]["failed"] += 1
    else:
        status = "❓ НЕИЗВЕСТНО"
        report["summary"]["passed"] += 1  # Считаем passed по умолчанию

    report["summary"]["total_tests"] += 1

    # Ищем сообщения о регрессиях
    has_regression = "🚨 РЕГРЕССИЯ" in output_text

    if has_regression:
        report["summary"]["regressions"].append(test_name)

    # Ищем время выполнения (примерно)
    duration = 0.0
    for line in output_lines:
        if "in " in line and "s" in line:
            try:
                # Ищем паттерн вроде "0.123s"
                import re

                match = re.search(r"(\d+\.\d+)s", line)
                if match:
                    duration = float(match.group(1))
                    break
            except Exception:
                pass

    report["details"].append(
        {
            "test_name": test_name,
            "status": status,
            "has_regression": has_regression,
            "duration": duration,
            "stdout": output_text,
        }
    )


def print_report(report):
    """Вывести отчет в консоль."""
    print("\n" + "=" * 60)
    print("📊 ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 60)

    summary = report["summary"]
    print("\nОбщая статистика:")
    print(f"  Всего тестов: {summary['total_tests']}")
    print(f"  Пройдено: {summary['passed']}")
    print(f"  Провалено: {summary['failed']}")
    print(f"  Регрессий: {len(summary['regressions'])}")

    if summary["regressions"]:
        print("\n🚨 ОБНАРУЖЕНЫ РЕГРЕССИИ:")
        for regression in summary["regressions"]:
            print(f"  - {regression}")
    else:
        print("\n✅ РЕГРЕССИЙ НЕ ОБНАРУЖЕНО")

    print("\nДетали по тестам:")
    for detail in report["details"]:
        regression_marker = " 🚨" if detail["has_regression"] else ""
        print(
            f"  {detail['status']} {detail['test_name']} ({detail['duration']:.3f}s){regression_marker}"
        )

        # Показываем сообщения о регрессиях
        stdout_lines = detail["stdout"].strip().split("\n")
        for line in stdout_lines:
            if "🚨" in line or "✅" in line:
                print(f"    {line}")

    print("\n" + "=" * 60)


def save_report(
    report, filename: str = "docs/results/performance_regression_report.md"
):
    """Сохранить отчет в файл."""
    Path(filename).parent.mkdir(parents=True, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Отчет о регрессиях производительности\n\n")

        summary = report["summary"]
        f.write("## Общая статистика\n\n")
        f.write(f"- **Всего тестов:** {summary['total_tests']}\n")
        f.write(f"- **Пройдено:** {summary['passed']}\n")
        f.write(f"- **Провалено:** {summary['failed']}\n")
        f.write(f"- **Регрессий:** {len(summary['regressions'])}\n\n")

        if summary["regressions"]:
            f.write("## 🚨 Обнаруженные регрессии\n\n")
            for regression in summary["regressions"]:
                f.write(f"- {regression}\n")
            f.write("\n")
        else:
            f.write("## ✅ Регрессий не обнаружено\n\n")

        f.write("## Детали по тестам\n\n")
        for detail in report["details"]:
            regression_marker = " 🚨" if detail["has_regression"] else ""
            f.write(
                f"### {detail['status']} {detail['test_name']}{regression_marker}\n\n"
            )
            f.write(f"**Время выполнения:** {detail['duration']:.3f} сек\n\n")

            # Добавляем логи регрессий
            stdout_lines = detail["stdout"].strip().split("\n")
            regression_logs = [
                line for line in stdout_lines if "🚨" in line or "✅" in line
            ]
            if regression_logs:
                f.write("**Результаты проверки:**\n\n")
                for line in regression_logs:
                    f.write(f"```\n{line}\n```\n\n")

        f.write("---\n*Отчет создан автоматически*")

    print(f"📄 Отчет сохранен в {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Запуск performance тестов с проверкой регрессий"
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Обновить baseline значения производительности",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Только показать отчет по существующим результатам",
    )

    args = parser.parse_args()

    if args.report_only:
        # Только отчет
        report = generate_regression_report()
        if report:
            print_report(report)
        else:
            print("❌ Не удалось сгенерировать отчет")
            sys.exit(1)
    else:
        # Запуск тестов
        success, stdout, stderr = run_performance_tests(
            update_baseline=args.update_baseline
        )

        if success:
            print("✅ Performance тесты пройдены успешно")
        else:
            print("❌ Performance тесты провалены")
            sys.exit(1)

        # Генерируем отчет
        report = generate_regression_report(stdout, stderr)
        if report:
            print_report(report)
            save_report(report)

            # Выходим с ошибкой если есть регрессии
            if report["summary"]["regressions"]:
                print(
                    f"\n🚨 ОБНАРУЖЕНЫ РЕГРЕССИИ ПРОИЗВОДИТЕЛЬНОСТИ: {len(report['summary']['regressions'])}"
                )
                sys.exit(1)
        else:
            print("❌ Не удалось сгенерировать отчет")
            sys.exit(1)


if __name__ == "__main__":
    import os

    main()
