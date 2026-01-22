#!/usr/bin/env python3
"""
Оптимизация тестовой базы системы Life.

Анализирует текущую тестовую базу и предлагает стратегию сокращения
объема тестирования при сохранении качества.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class TestFileInfo:
    """Информация о тестовом файле."""
    path: Path
    size_bytes: int
    line_count: int
    test_functions: int
    test_classes: int
    category: str
    component: str
    test_type: str  # static, smoke, integration


class TestSuiteOptimizer:
    """
    Оптимизатор тестовой базы.

    Анализирует тестовую базу и предлагает стратегию оптимизации.
    """

    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.test_files: List[TestFileInfo] = []
        self.analysis_results = {}

    def analyze_test_suite(self) -> Dict[str, any]:
        """Проводит полный анализ тестовой базы."""

        # Сканируем все тестовые файлы
        self._scan_test_files()

        # Анализируем структуру
        self._analyze_structure()

        # Оцениваем избыточность
        self._analyze_redundancy()

        # Предлагаем оптимизации
        self._propose_optimizations()

        return self.analysis_results

    def _scan_test_files(self) -> None:
        """Сканирует все тестовые файлы."""
        for test_file in self.test_dir.glob("test*.py"):
            if test_file.is_file():
                info = self._analyze_test_file(test_file)
                self.test_files.append(info)

    def _analyze_test_file(self, file_path: Path) -> TestFileInfo:
        """Анализирует отдельный тестовый файл."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            line_count = len(lines)

            # Считаем функции и классы тестов
            test_functions = len(re.findall(r'def test_', content))
            test_classes = len(re.findall(r'class Test', content))

            # Определяем категорию и тип
            filename = file_path.name
            category, component, test_type = self._classify_test_file(filename)

            return TestFileInfo(
                path=file_path,
                size_bytes=file_path.stat().st_size,
                line_count=line_count,
                test_functions=test_functions,
                test_classes=test_classes,
                category=category,
                component=component,
                test_type=test_type
            )

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return TestFileInfo(
                path=file_path,
                size_bytes=0,
                line_count=0,
                test_functions=0,
                test_classes=0,
                category="error",
                component="unknown",
                test_type="unknown"
            )

    def _classify_test_file(self, filename: str) -> Tuple[str, str, str]:
        """Классифицирует тестовый файл."""
        # Определяем тип теста
        if 'static' in filename:
            test_type = 'static'
        elif 'smoke' in filename:
            test_type = 'smoke'
        elif 'integration' in filename:
            test_type = 'integration'
        else:
            test_type = 'unit'

        # Определяем компонент
        component_patterns = {
            'memory': ['memory'],
            'event': ['event'],
            'state': ['state', 'selfstate'],
            'runtime': ['runtime'],
            'api': ['api'],
            'consciousness': ['consciousness'],
            'clarity': ['clarity'],
            'subjective': ['subjective', 'time'],
            'comparison': ['comparison'],
            'structured_logger': ['structured', 'logger'],
            'generator': ['generator'],
            'decision': ['decision'],
            'planning': ['planning'],
            'learning': ['learning'],
            'adaptation': ['adaptation'],
            'observability': ['observability'],
            'technical_monitor': ['technical', 'monitor'],
            'field_validator': ['field', 'validator'],
            'checkpoint_manager': ['checkpoint'],
            'todo_manager': ['todo'],
            'executor_agent': ['executor', 'agent'],
            'scenario_manager': ['scenario'],
            'impact_analyzer': ['impact'],
            'sensory_buffer': ['sensory', 'buffer'],
            'adaptive_processing': ['adaptive', 'processing'],
            'prompt_formatter': ['prompt'],
            'session_tracker': ['session'],
            'security_utils': ['security'],
            'hybrid_cursor': ['hybrid', 'cursor'],
            'git_utils': ['git'],
            'memory_index': ['memory', 'index'],
            'silence_detector': ['silence'],
            'semantic_store': ['semantic'],
            'analysis_api': ['analysis', 'api'],
            'export': ['export'],
            'log_analysis': ['log', 'analysis'],
            'cli_scripts': ['cli'],
            'analyze_logs': ['analyze', 'logs'],
            'new_functionality': ['new'],
            'architectural_passivity': ['architectural'],
            'invariants': ['invariants'],
            'status_contract': ['status', 'contract'],
            'snapshot_recovery': ['snapshot'],
            'internal_event': ['internal', 'event'],
            'memory_echo': ['memory', 'echo'],
            'meaning_echo': ['meaning', 'echo'],
            'new_event_types': ['new', 'event'],
            'race_conditions': ['race'],
            'loop_managers': ['loop', 'managers'],
            'critical_issues': ['critical'],
            'critical_fixes': ['critical', 'fixes'],
            'concurrency': ['concurrency'],
            'auth': ['auth']
        }

        component = 'misc'
        for comp_name, patterns in component_patterns.items():
            if any(pattern in filename.lower() for pattern in patterns):
                component = comp_name
                break

        # Определяем категорию
        if test_type in ['static', 'smoke']:
            category = 'lightweight'
        elif test_type == 'integration':
            category = 'heavy'
        else:
            category = 'unit'

        return category, component, test_type

    def _analyze_structure(self) -> None:
        """Анализирует структуру тестовой базы."""
        total_files = len(self.test_files)
        total_size = sum(f.size_bytes for f in self.test_files)
        total_lines = sum(f.line_count for f in self.test_files)
        total_functions = sum(f.test_functions for f in self.test_files)
        total_classes = sum(f.test_classes for f in self.test_files)

        # Анализ по типам
        type_stats = {}
        for test_file in self.test_files:
            test_type = test_file.test_type
            if test_type not in type_stats:
                type_stats[test_type] = {'count': 0, 'size': 0, 'functions': 0}
            type_stats[test_type]['count'] += 1
            type_stats[test_type]['size'] += test_file.size_bytes
            type_stats[test_type]['functions'] += test_file.test_functions

        # Анализ по компонентам
        component_stats = {}
        for test_file in self.test_files:
            component = test_file.component
            if component not in component_stats:
                component_stats[component] = {'count': 0, 'size': 0}
            component_stats[component]['count'] += 1
            component_stats[component]['size'] += test_file.size_bytes

        self.analysis_results['structure'] = {
            'total_files': total_files,
            'total_size_mb': total_size / (1024 * 1024),
            'total_lines': total_lines,
            'total_test_functions': total_functions,
            'total_test_classes': total_classes,
            'avg_functions_per_file': total_functions / max(1, total_files),
            'type_distribution': type_stats,
            'component_distribution': dict(sorted(component_stats.items(),
                                                key=lambda x: x[1]['count'], reverse=True))
        }

    def _analyze_redundancy(self) -> None:
        """Анализирует избыточность тестов."""
        redundancy_issues = []

        # Ищем множественные тесты одного компонента
        component_files = {}
        for test_file in self.test_files:
            component = test_file.component
            if component not in component_files:
                component_files[component] = []
            component_files[component].append(test_file)

        # Анализируем компоненты с множественными тестами
        for component, files in component_files.items():
            if len(files) >= 3:  # 3+ типа тестов для одного компонента
                types = [f.test_type for f in files]
                if len(set(types)) < len(types):  # Есть дубликаты типов
                    redundancy_issues.append({
                        'component': component,
                        'files': len(files),
                        'types': types,
                        'issue': 'duplicate_test_types',
                        'recommendation': 'consolidate_similar_tests'
                    })

        # Ищем очень маленькие файлы (возможно, бесполезные)
        tiny_files = [f for f in self.test_files if f.line_count < 20]
        if tiny_files:
            redundancy_issues.append({
                'issue': 'tiny_test_files',
                'count': len(tiny_files),
                'files': [str(f.path) for f in tiny_files[:5]],  # Первые 5
                'recommendation': 'review_and_merge_tiny_tests'
            })

        # Ищем очень большие файлы
        large_files = [f for f in self.test_files if f.line_count > 500]
        if large_files:
            redundancy_issues.append({
                'issue': 'large_test_files',
                'count': len(large_files),
                'files': [str(f.path) for f in large_files[:3]],  # Первые 3
                'recommendation': 'split_large_test_files'
            })

        self.analysis_results['redundancy'] = {
            'issues': redundancy_issues,
            'components_with_multiple_tests': len([c for c in component_files.values() if len(c) > 1])
        }

    def _propose_optimizations(self) -> None:
        """Предлагает оптимизации тестовой базы."""
        structure = self.analysis_results.get('structure', {})
        redundancy = self.analysis_results.get('redundancy', {})

        total_files = structure.get('total_files', 0)
        type_dist = structure.get('type_distribution', {})

        # Расчет целевых показателей
        target_files = max(20, total_files // 3)  # Цель: уменьшить в 3 раза, минимум 20
        target_reduction_percent = ((total_files - target_files) / total_files) * 100

        # Стратегия оптимизации
        optimization_strategy = {
            'target_metrics': {
                'target_files': target_files,
                'target_reduction_percent': target_reduction_percent,
                'maintain_coverage_for': ['core', 'critical', 'api']
            },
            'removal_priorities': [
                'Remove redundant static/smoke tests for same component',
                'Merge tiny test files (< 20 lines)',
                'Eliminate duplicate integration tests',
                'Remove tests for deprecated/unused components',
                'Consolidate similar test scenarios'
            ],
            'keep_priorities': [
                'Core functionality tests (state, memory, runtime)',
                'API and integration tests',
                'Critical path tests',
                'Performance regression tests',
                'New functionality smoke tests'
            ],
            'implementation_plan': [
                'Phase 1: Analyze test coverage and identify redundancies',
                'Phase 2: Merge similar tests and remove obvious duplicates',
                'Phase 3: Implement test categorization and selective running',
                'Phase 4: Add automated test suite health monitoring',
                'Phase 5: Establish test maintenance procedures'
            ]
        }

        # Конкретные рекомендации
        specific_recommendations = []

        # Анализ типов тестов
        static_count = type_dist.get('static', {}).get('count', 0)
        smoke_count = type_dist.get('smoke', {}).get('count', 0)
        integration_count = type_dist.get('integration', {}).get('count', 0)

        if static_count > smoke_count * 2:
            specific_recommendations.append(
                f"Reduce static tests: {static_count} -> {smoke_count}. "
                "Many static tests duplicate smoke test coverage."
            )

        if integration_count > 10:
            specific_recommendations.append(
                f"Review integration tests: {integration_count} tests. "
                "Consider consolidating heavy integration tests."
            )

        # Анализ компонентов с множественными тестами
        component_dist = structure.get('component_distribution', {})
        over_tested_components = [comp for comp, stats in component_dist.items() if stats['count'] > 3]

        if over_tested_components:
            specific_recommendations.append(
                f"Components with excessive testing: {over_tested_components}. "
                "Review and consolidate test coverage."
            )

        optimization_strategy['specific_recommendations'] = specific_recommendations

        self.analysis_results['optimization'] = optimization_strategy

    def generate_optimization_report(self) -> str:
        """Генерирует отчет об оптимизации."""
        if not self.analysis_results:
            self.analyze_test_suite()

        structure = self.analysis_results.get('structure', {})
        redundancy = self.analysis_results.get('redundancy', {})
        optimization = self.analysis_results.get('optimization', {})

        report = []
        report.append("# Test Suite Optimization Report")
        report.append("")

        # Структура
        report.append("## Current Test Suite Structure")
        report.append(f"- Total test files: {structure.get('total_files', 0)}")
        report.append(".1f")
        report.append(f"- Total lines of code: {structure.get('total_lines', 0):,}")
        report.append(f"- Total test functions: {structure.get('total_test_functions', 0)}")
        report.append(".1f")
        report.append("")

        # Распределение по типам
        report.append("## Test Distribution by Type")
        type_dist = structure.get('type_distribution', {})
        for test_type, stats in type_dist.items():
            report.append(f"- {test_type}: {stats['count']} files, "
                         f"{stats['functions']} functions, "
                         ".1f")
        report.append("")

        # Распределение по компонентам
        report.append("## Test Distribution by Component")
        comp_dist = structure.get('component_distribution', {})
        for comp, stats in list(comp_dist.items())[:10]:  # Top 10
            report.append(f"- {comp}: {stats['count']} files")
        report.append("")

        # Избыточность
        report.append("## Redundancy Analysis")
        issues = redundancy.get('issues', [])
        report.append(f"- Identified issues: {len(issues)}")
        for issue in issues[:5]:  # Первые 5
            report.append(f"- {issue.get('issue', 'Unknown')}: {issue.get('recommendation', '')}")
        report.append("")

        # Оптимизация
        report.append("## Optimization Strategy")
        target = optimization.get('target_metrics', {})
        report.append(f"- Target files: {target.get('target_files', 0)} "
                     ".1f")
        report.append("")

        report.append("### Removal Priorities:")
        for priority in optimization.get('removal_priorities', []):
            report.append(f"- {priority}")
        report.append("")

        report.append("### Keep Priorities:")
        for priority in optimization.get('keep_priorities', []):
            report.append(f"- {priority}")
        report.append("")

        report.append("### Implementation Plan:")
        for phase in optimization.get('implementation_plan', []):
            report.append(f"1. {phase}")
        report.append("")

        report.append("### Specific Recommendations:")
        for rec in optimization.get('specific_recommendations', []):
            report.append(f"- {rec}")
        report.append("")

        return "\n".join(report)


def main():
    """Основная функция."""
    test_dir = Path("src/test")

    if not test_dir.exists():
        print(f"Test directory {test_dir} not found!")
        return

    optimizer = TestSuiteOptimizer(test_dir)
    optimizer.analyze_test_suite()

    print("=== Test Suite Optimization Analysis ===")
    print(optimizer.generate_optimization_report())

    # Сохраняем детальный отчет
    report = optimizer.generate_optimization_report()
    with open("docs/results/test_optimization_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("\nDetailed report saved to: docs/results/test_optimization_report.md")


if __name__ == "__main__":
    main()