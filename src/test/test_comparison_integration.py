"""
Интеграционные тесты для системы сравнения жизней
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.comparison import ComparisonManager, PatternAnalyzer, ComparisonMetrics


class TestComparisonIntegration:
    """Интеграционные тесты системы сравнения."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.manager = ComparisonManager()
        self.analyzer = PatternAnalyzer()
        self.metrics = ComparisonMetrics()

    def test_full_comparison_workflow(self):
        """Тест полного рабочего процесса сравнения."""
        # Создаем инстансы
        instance1 = self.manager.create_instance("life_a")
        instance2 = self.manager.create_instance("life_b")

        assert instance1 is not None
        assert instance2 is not None

        # Имитируем сбор данных (в реальности это делалось бы запущенными инстансами)
        mock_comparison_data = {
            'timestamp': time.time(),
            'instances': {
                'life_a': {
                    'status': {'is_running': True, 'is_alive': True, 'uptime': 10.0},
                    'snapshot': {
                        'energy': 60.0,
                        'stability': 0.85,
                        'integrity': 0.95,
                        'ticks': 50,
                        'age': 10.0
                    },
                    'recent_logs': [
                        {'stage': 'event', 'data': {'type': 'noise'}},
                        {'stage': 'decision', 'data': {'pattern': 'ignore'}},
                        {'stage': 'action', 'data': {'executed': True}},
                        {'stage': 'event', 'data': {'type': 'decay'}},
                        {'stage': 'decision', 'data': {'pattern': 'absorb'}},
                        {'stage': 'action', 'data': {'executed': True}},
                    ]
                },
                'life_b': {
                    'status': {'is_running': True, 'is_alive': True, 'uptime': 12.0},
                    'snapshot': {
                        'energy': 45.0,
                        'stability': 0.75,
                        'integrity': 0.80,
                        'ticks': 48,
                        'age': 12.0
                    },
                    'recent_logs': [
                        {'stage': 'event', 'data': {'type': 'recovery'}},
                        {'stage': 'decision', 'data': {'pattern': 'dampen'}},
                        {'stage': 'action', 'data': {'executed': True}},
                        {'stage': 'event', 'data': {'type': 'shock'}},
                        {'stage': 'decision', 'data': {'pattern': 'ignore'}},
                        {'stage': 'action', 'data': {'executed': True}},
                    ]
                }
            }
        }

        # Тестируем анализ паттернов
        analysis_result = self.analyzer.analyze_comparison_data(mock_comparison_data)

        assert 'instances_analysis' in analysis_result
        assert len(analysis_result['instances_analysis']) == 2
        assert 'life_a' in analysis_result['instances_analysis']
        assert 'life_b' in analysis_result['instances_analysis']

        # Проверяем, что анализ содержит ожидаемые метрики
        life_a_analysis = analysis_result['instances_analysis']['life_a']
        assert 'decision_patterns' in life_a_analysis
        assert 'event_types' in life_a_analysis
        assert 'correlations' in life_a_analysis

        # Тестируем метрики сравнения
        instances_data = mock_comparison_data['instances']
        metrics_result = self.metrics.get_summary_report(instances_data)

        assert 'similarity_metrics' in metrics_result
        assert 'performance_metrics' in metrics_result
        assert 'diversity_metrics' in metrics_result

        # Проверяем метрики схожести
        similarity = metrics_result['similarity_metrics']
        assert 'overall_similarity' in similarity
        pair_key = 'life_a_vs_life_b'
        assert pair_key in similarity['overall_similarity']

        # Проверяем метрики производительности
        performance = metrics_result['performance_metrics']
        assert 'survival_rates' in performance
        assert 'life_a' in performance['survival_rates']
        assert 'life_b' in performance['survival_rates']

        # Проверяем метрики разнообразия
        diversity = metrics_result['diversity_metrics']
        assert 'pattern_diversity' in diversity
        assert 'diversity_score' in diversity

        # Проверяем, что разнообразие рассчитано корректно
        assert diversity['pattern_diversity'] > 0  # Должны быть разные паттерны

    def test_comparison_with_empty_instances(self):
        """Тест сравнения с пустыми данными инстансов."""
        mock_comparison_data = {
            'timestamp': time.time(),
            'instances': {}
        }

        # Анализ должен работать даже с пустыми данными
        analysis_result = self.analyzer.analyze_comparison_data(mock_comparison_data)
        assert analysis_result is not None

        metrics_result = self.metrics.get_summary_report({})
        assert metrics_result is not None

    def test_comparison_with_single_instance(self):
        """Тест сравнения с одним инстансом."""
        mock_comparison_data = {
            'timestamp': time.time(),
            'instances': {
                'single_life': {
                    'status': {'is_running': True, 'is_alive': True},
                    'snapshot': {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9},
                    'recent_logs': [
                        {'stage': 'decision', 'data': {'pattern': 'ignore'}}
                    ]
                }
            }
        }

        analysis_result = self.analyzer.analyze_comparison_data(mock_comparison_data)
        assert len(analysis_result['instances_analysis']) == 1

        instances_data = mock_comparison_data['instances']
        metrics_result = self.metrics.get_summary_report(instances_data)

        # Метрики схожести должны быть пустыми для одного инстанса
        similarity = metrics_result['similarity_metrics']
        assert similarity['state_similarity'] == {}
        assert similarity['behavior_similarity'] == {}

    def test_historical_data_accumulation(self):
        """Тест накопления исторических данных."""
        instance_id = 'test_life'

        # Добавляем несколько snapshot'ов
        snapshots = [
            {'energy': 40.0, 'stability': 0.7, 'integrity': 0.8},
            {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9},
            {'energy': 60.0, 'stability': 0.9, 'integrity': 1.0},
        ]

        for snapshot in snapshots:
            instances_data = {instance_id: {'snapshot': snapshot}}
            self.metrics.compute_performance_metrics(instances_data)

        # Проверяем, что история накопилась
        assert instance_id in self.metrics.historical_data
        assert len(self.metrics.historical_data[instance_id]) == 3

        # Проверяем метрики эволюции
        evolution = self.metrics.compute_evolution_metrics(instances_data)
        assert instance_id in evolution['growth_rates']
        assert instance_id in evolution['adaptation_curves']

    @patch('src.comparison.comparison_manager.ComparisonManager.collect_comparison_data')
    def test_data_collection_workflow(self, mock_collect):
        """Тест рабочего процесса сбора данных."""
        mock_collect.return_value = {
            'timestamp': time.time(),
            'instances': {
                'life1': {'status': {'is_running': True}, 'snapshot': {'energy': 50.0}},
                'life2': {'status': {'is_running': True}, 'snapshot': {'energy': 55.0}}
            },
            'summary': {'total_instances': 2, 'active_instances': 2}
        }

        # Создаем инстансы
        self.manager.create_instance('life1')
        self.manager.create_instance('life2')

        # Собираем данные
        data = self.manager.collect_comparison_data()

        # Проверяем структуру данных
        assert 'timestamp' in data
        assert 'instances' in data
        assert 'summary' in data
        assert len(data['instances']) == 2

    def test_manager_lifecycle(self):
        """Тест жизненного цикла менеджера сравнения."""
        # Создание инстансов
        inst1 = self.manager.create_instance('life1')
        inst2 = self.manager.create_instance('life2')
        assert inst1 is not None
        assert inst2 is not None

        # Проверка статусов
        statuses = self.manager.get_all_instances_status()
        assert len(statuses) == 2

        # Имитация запуска (без реального запуска процессов)
        self.manager.instances['life1'].is_running = True
        self.manager.instances['life1'].is_alive = Mock(return_value=True)
        self.manager.instances['life2'].is_running = True
        self.manager.instances['life2'].is_alive = Mock(return_value=True)

        # Проверка активных инстансов
        stats = self.manager.get_comparison_stats()
        assert stats['total_instances'] == 2
        assert stats['active_instances'] == 2  # После имитации запуска

        # Очистка
        cleanup = self.manager.cleanup_instances(force=True)
        assert cleanup['life1'] is True
        assert cleanup['life2'] is True
        assert len(self.manager.instances) == 0

    def test_error_handling_in_analysis(self):
        """Тест обработки ошибок в анализе."""
        # Данные с некорректной структурой
        malformed_data = {
            'timestamp': time.time(),
            'instances': {
                'bad_life': {
                    'status': None,  # Некорректные данные
                    'snapshot': None,
                    'recent_logs': None
                }
            }
        }

        # Анализ должен обработать ошибки gracefully
        analysis_result = self.analyzer.analyze_comparison_data(malformed_data)
        assert analysis_result is not None

        metrics_result = self.metrics.get_summary_report(malformed_data['instances'])
        assert metrics_result is not None

    def test_large_scale_comparison(self):
        """Тест сравнения большого количества инстансов."""
        # Создаем много инстансов
        num_instances = 5
        instances_data = {}

        for i in range(num_instances):
            instance_id = f'life_{i+1}'
            self.manager.create_instance(instance_id)

            # Генерируем тестовые данные
            instances_data[instance_id] = {
                'status': {'is_running': True, 'is_alive': True},
                'snapshot': {
                    'energy': 50.0 + i * 5,
                    'stability': 0.8 - i * 0.05,
                    'integrity': 0.9 - i * 0.02
                },
                'recent_logs': [
                    {'stage': 'decision', 'data': {'pattern': 'ignore' if i % 2 == 0 else 'absorb'}}
                ]
            }

        # Тестируем анализ
        analysis_result = self.analyzer.analyze_comparison_data({
            'timestamp': time.time(),
            'instances': instances_data
        })

        assert len(analysis_result['instances_analysis']) == num_instances

        # Тестируем метрики
        metrics_result = self.metrics.get_summary_report(instances_data)

        similarity = metrics_result['similarity_metrics']['overall_similarity']
        assert len(similarity) == num_instances * (num_instances - 1) // 2  # Количество пар

        diversity = metrics_result['diversity_metrics']
        assert diversity['diversity_score'] > 0