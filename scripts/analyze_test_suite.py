#!/usr/bin/env python3
"""
Анализатор тестовой базы проекта Life.

Выполняет комплексный анализ тестов для оптимизации и рефакторинга.
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TestFileAnalysis:
    """Результат анализа тестового файла."""
    path: str
    test_count: int
    lines_count: int
    complexity: float
    imports: List[str]
    fixtures: List[str]
    marks: List[str]
    test_types: List[str]  # unit, integration, system, smoke


@dataclass
class TestSuiteAnalysis:
    """Результат анализа всей тестовой базы."""
    total_files: int
    total_tests: int
    total_lines: int
    files_by_type: Dict[str, List[TestFileAnalysis]]
    coverage_estimate: float
    recommendations: List[str]


class TestAnalyzer:
    """Анализатор тестовой базы."""

    def __init__(self, test_dir: str = "src/test"):
        self.test_dir = Path(test_dir)
        self.analysis = TestSuiteAnalysis(
            total_files=0,
            total_tests=0,
            total_lines=0,
            files_by_type=defaultdict(list),
            coverage_estimate=0.0,
            recommendations=[]
        )

    def analyze(self) -> TestSuiteAnalysis:
        """Выполнить полный анализ тестовой базы."""
        print("🔍 Анализ тестовой базы...")

        if not self.test_dir.exists():
            print(f"❌ Директория {self.test_dir} не найдена")
            return self.analysis

        # Анализ каждого тестового файла
        for test_file in self.test_dir.rglob("test_*.py"):
            file_analysis = self._analyze_test_file(test_file)
            if file_analysis:
                self.analysis.total_files += 1
                self.analysis.total_tests += file_analysis.test_count
                self.analysis.total_lines += file_analysis.lines_count

                # Классификация по типам
                test_type = self._classify_test_type(file_analysis)
                self.analysis.files_by_type[test_type].append(file_analysis)

        # Расчет оценок
        self._calculate_coverage_estimate()
        self._generate_recommendations()

        return self.analysis

    def _analyze_test_file(self, file_path: Path) -> TestFileAnalysis | None:
        """Анализировать отдельный тестовый файл."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Подсчет тестов
            test_functions = []
            fixtures = []
            marks = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_'):
                        test_functions.append(node.name)
                    elif 'fixture' in node.name or 'Fixture' in str(node.decorator_list):
                        fixtures.append(node.name)

                # Поиск декораторов pytest
                if isinstance(node, ast.decorator_list) and node:
                    for decorator in node:
                        if isinstance(decorator, ast.Call):
                            if hasattr(decorator.func, 'id') and decorator.func.id == 'pytest':
                                marks.extend(self._extract_marks(decorator))

            # Анализ импортов
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    imports.extend(f"{module}.{alias.name}" for alias in node.names)

            # Оценка сложности (простая метрика)
            complexity = len(test_functions) * 0.1 + len(content.split('\n')) * 0.01

            return TestFileAnalysis(
                path=str(file_path.relative_to(self.test_dir.parent)),
                test_count=len(test_functions),
                lines_count=len(content.split('\n')),
                complexity=complexity,
                imports=imports,
                fixtures=fixtures,
                marks=marks,
                test_types=[]
            )

        except Exception as e:
            print(f"❌ Ошибка анализа {file_path}: {e}")
            return None

    def _classify_test_type(self, analysis: TestFileAnalysis) -> str:
        """Классифицировать тест по типу."""
        filename = analysis.path.lower()

        # Определение типа по названию файла
        if 'smoke' in filename:
            return 'smoke'
        elif 'integration' in filename or 'api' in filename:
            return 'integration'
        elif 'system' in filename or 'e2e' in filename:
            return 'system'
        elif any(mark in analysis.marks for mark in ['unit', 'isolated']):
            return 'unit'

        # Определение по содержимому
        if any('integration' in mark for mark in analysis.marks):
            return 'integration'
        elif len(analysis.imports) > 10:  # Много импортов = интеграционный тест
            return 'integration'
        elif len(analysis.fixtures) > 5:  # Много fixtures = интеграционный тест
            return 'integration'

        return 'unit'  # По умолчанию unit

    def _extract_marks(self, decorator) -> List[str]:
        """Извлечь marks из декоратора pytest."""
        marks = []
        try:
            if hasattr(decorator, 'keywords'):
                for keyword in decorator.keywords:
                    if keyword.arg:
                        marks.append(keyword.arg)
        except:
            pass
        return marks

    def _calculate_coverage_estimate(self):
        """Оценить покрытие кода тестами."""
        # Простая оценка: 1 тест = ~10 строк кода
        estimated_covered_lines = self.analysis.total_tests * 10

        # Предполагаем 100k строк кода в проекте
        total_code_lines = 100000
        self.analysis.coverage_estimate = min(100.0, (estimated_covered_lines / total_code_lines) * 100)

    def _generate_recommendations(self):
        """Сгенерировать рекомендации по оптимизации."""
        recommendations = []

        # Анализ количества тестов
        if self.analysis.total_files > 100:
            recommendations.append("🚨 Слишком много тестовых файлов. Рекомендуется консолидация.")

        # Анализ баланса типов тестов
        unit_count = len(self.analysis.files_by_type.get('unit', []))
        integration_count = len(self.analysis.files_by_type.get('integration', []))
        system_count = len(self.analysis.files_by_type.get('system', []))

        if unit_count < integration_count:
            recommendations.append("⚠️ Недостаточно unit тестов. Рекомендуется увеличить покрытие unit тестами.")

        if system_count > unit_count * 0.5:
            recommendations.append("⚠️ Слишком много system тестов. Рекомендуется оптимизация.")

        # Анализ среднего размера файлов
        avg_tests_per_file = self.analysis.total_tests / max(1, self.analysis.total_files)
        if avg_tests_per_file > 20:
            recommendations.append("📝 Файлы тестов слишком большие. Рекомендуется разделение.")

        self.analysis.recommendations = recommendations


def main():
    """Основная функция."""
    analyzer = TestAnalyzer()
    analysis = analyzer.analyze()

    print("\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА ТЕСТОВОЙ БАЗЫ")
    print("=" * 50)
    print(f"📁 Всего файлов: {analysis.total_files}")
    print(f"🧪 Всего тестов: {analysis.total_tests}")
    print(f"📝 Всего строк: {analysis.total_lines}")
    print(f"🎯 Оценка покрытия: {analysis.coverage_estimate:.1f}%")

    print("\n📂 Распределение по типам:")
    for test_type, files in analysis.files_by_type.items():
        count = len(files)
        percentage = (count / analysis.total_files) * 100 if analysis.total_files > 0 else 0
        print(f"  {test_type}: {count} файлов ({percentage:.1f}%)")
    print("\n💡 РЕКОМЕНДАЦИИ:")
    if analysis.recommendations:
        for rec in analysis.recommendations:
            print(f"  • {rec}")
    else:
        print("  ✅ Тестовая база выглядит оптимально")

    # Сохранение детального отчета
    report_file = "docs/test_analysis_report.json"
    report_data = {
        'summary': {
            'total_files': analysis.total_files,
            'total_tests': analysis.total_tests,
            'total_lines': analysis.total_lines,
            'coverage_estimate': analysis.coverage_estimate,
            'files_by_type': {k: len(v) for k, v in analysis.files_by_type.items()}
        },
        'recommendations': analysis.recommendations,
        'files': [
            {
                'path': f.path,
                'test_count': f.test_count,
                'lines_count': f.lines_count,
                'complexity': f.complexity,
                'type': next((t for t, files in analysis.files_by_type.items() if f in files), 'unknown')
            }
            for files_list in analysis.files_by_type.values()
            for f in files_list
        ]
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Детальный отчет сохранен в {report_file}")


if __name__ == "__main__":
    main()