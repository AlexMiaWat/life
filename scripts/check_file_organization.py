#!/usr/bin/env python3
"""
Проверка организации файлов проекта Life.

Запускайте перед коммитом для проверки правильности размещения файлов.
"""

import os
import sys
from pathlib import Path

class FileOrganizationChecker:
    """Проверка правильности организации файлов."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors = []
        self.warnings = []

    def check_root_files(self):
        """Проверка что в корне только разрешенные файлы."""
        allowed_in_root = {
            # Конфигурационные файлы
            '.gitignore', '.pre-commit-config.yaml', 'pyproject.toml',
            'pytest.ini', 'requirements.txt', 'conftest.py',

            # Документация
            'README.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'AGENTS.md',

            # Исполняемые файлы
            '__main__', 'sample_snapshot.json'
        }

        root_files = []
        for item in self.project_root.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                root_files.append(item.name)

        forbidden_files = []
        for file in root_files:
            if file not in allowed_in_root:
                forbidden_files.append(file)

        if forbidden_files:
            self.errors.append(
                f"Запрещенные файлы в корне проекта: {', '.join(forbidden_files)}\n"
                "Все скрипты должны быть в scripts/, приложения в apps/, "
                "исходный код в src/, документация в docs/"
            )

    def check_src_structure(self):
        """Проверка структуры src/."""
        src_dir = self.project_root / 'src'

        # Проверить что все директории имеют __init__.py
        for item in src_dir.iterdir():
            if (item.is_dir() and
                not item.name.startswith('__') and
                not item.name.endswith('.egg-info')):
                init_file = item / '__init__.py'
                if not init_file.exists():
                    self.warnings.append(
                        f"Директория {item.name} в src/ не имеет __init__.py"
                    )

        # Проверить что тесты в правильном месте
        test_files_in_src = list(src_dir.glob('test_*.py'))
        if test_files_in_src:
            self.errors.append(
                f"Найдены тесты в корне src/: {[f.name for f in test_files_in_src]}\n"
                "Все тесты должны быть в src/test/"
            )

    def check_docs_structure(self):
        """Проверка структуры docs/."""
        docs_dir = self.project_root / 'docs'

        # Проверить основные разделы
        required_sections = ['guides', 'components', 'architecture', 'testing']
        missing_sections = []

        for section in required_sections:
            if not (docs_dir / section).exists():
                missing_sections.append(section)

        if missing_sections:
            self.warnings.append(
                f"Отсутствуют разделы документации: {', '.join(missing_sections)}"
            )

    def check_temp_files(self):
        """Проверка на временные файлы."""
        temp_patterns = [
            'src.*', 'test_*', 'test_results*.xml',
            'test_execution_output.txt', '*.jsonl', '=*.0', '=*.5'
        ]

        temp_files = []
        for pattern in temp_patterns:
            temp_files.extend(list(self.project_root.glob(pattern)))

        if temp_files:
            self.errors.append(
                f"Найдены временные файлы: {[f.name for f in temp_files]}\n"
                "Запустите очистку: rm -f src.* test_* test_results*.xml *.jsonl"
            )

    def run_all_checks(self):
        """Запустить все проверки."""
        self.check_root_files()
        self.check_src_structure()
        self.check_docs_structure()
        self.check_temp_files()

        return len(self.errors) == 0

    def print_report(self):
        """Вывести отчет."""
        if not self.errors and not self.warnings:
            print("[OK] Организация файлов корректна!")
            return

        if self.errors:
            print("[ERROR] Критические проблемы:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print("[WARNING] Предупреждения:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.errors:
            print("\n[FIX] Исправьте критические проблемы перед коммитом!")
            print("[DOCS] Подробнее: docs/guides/file_organization.md")
            return False
        else:
            return True

def main():
    """Главная функция."""
    project_root = Path(__file__).parent.parent

    checker = FileOrganizationChecker(project_root)
    checker.run_all_checks()

    success = checker.print_report()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()