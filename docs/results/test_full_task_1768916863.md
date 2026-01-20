# Отчет о тестировании

**Дата:** 2026-01-20 14:03:49
**Задача:** test_full_task_1768916863

## Статистика тестирования

- **Всего тестов:** 654
- **Пройдено:** 576 ✅
- **Провалено:** 74 ❌
- **Пропущено:** 4 ⏭️
- **Время выполнения:** 181.57s

## Общая информация

Тестирование выполнено для всех тестов из каталога `src/test`.

### Процент успешности

Успешность: 88.62%

## Детальный отчет об ошибках

Всего провалено тестов: **74**


### test_adaptation (2 ошибок)

1. `src/test/test_adaptation.py::TestAdaptationManager::test_apply_adaptation_initialization`
2. `src/test/test_adaptation.py::TestAdaptationManager::test_apply_adaptation_no_decision_action_control`

### test_degradation (3 ошибок)

1. `src/test/test_degradation.py::TestDegradationRecovery::test_active_flag_stays_false_after_deactivation`
2. `src/test/test_degradation.py::TestDegradationLongRunning::test_degradation_over_1000_ticks`
3. `src/test/test_degradation.py::TestDegradationLongRunning::test_degradation_stability_over_time`

### test_learning (7 ошибок)

1. `src/test/test_learning.py::TestLearningIntegration::test_learning_persistence_in_snapshots`
2. `src/test/test_learning.py::TestLearningStatic::test_method_signatures`
3. `src/test/test_learning.py::TestLearningStatic::test_method_return_types`
4. `src/test/test_learning.py::TestLearningStatic::test_imports_structure`
5. `src/test/test_learning.py::TestLearningSmoke::test_full_cycle_smoke`
6. `src/test/test_learning.py::TestLearningIntegrationExtended::test_learning_persistence_across_snapshots`
7. `src/test/test_learning.py::TestLearningIntegrationExtended::test_learning_with_large_memory`

### test_learning_adaptation_integration (3 ошибок)

1. `src/test/test_learning_adaptation_integration.py::TestLearningAdaptationStatic::test_learning_interval_constants`
2. `src/test/test_learning_adaptation_integration.py::TestLearningAdaptationStatic::test_return_types`
3. `src/test/test_learning_adaptation_integration.py::TestLearningAdaptationRuntimeIntegration::test_learning_frequency_in_runtime`

### test_mcp_interactive (1 ошибок)

1. `src/test/test_mcp_interactive.py::test_mcp_functions`

### test_mcp_refresh_index (1 ошибок)

1. `src/test/test_mcp_refresh_index.py::TestRefreshIndexErrorHandling::test_refresh_index_handles_os_error`

### test_mcp_server (21 ошибок)

1. `src/test/test_mcp_server.py::test_search_docs`
2. `src/test/test_mcp_server.py::test_list_docs`
3. `src/test/test_mcp_server.py::test_get_doc_content`
4. `src/test/test_mcp_server.py::test_search_todo`
5. `src/test/test_mcp_server.py::test_search_docs_and_mode`
6. `src/test/test_mcp_server.py::test_search_docs_or_mode`
7. `src/test/test_mcp_server.py::test_search_docs_or_mode_with_quoted_query`
8. `src/test/test_mcp_server.py::test_search_docs_phrase_mode`
9. `src/test/test_mcp_server.py::test_tokenize_query_quotes_auto_phrase`
10. `src/test/test_mcp_server.py::test_tokenize_query_explicit_mode_priority`
11. `src/test/test_mcp_server.py::test_tokenize_query_empty_query`
12. `src/test/test_mcp_server.py::test_search_docs_empty_query`
13. `src/test/test_mcp_server.py::test_search_todo_and_mode`
14. `src/test/test_mcp_server.py::test_search_todo_or_mode`
15. `src/test/test_mcp_server.py::test_search_todo_phrase_mode`
16. `src/test/test_mcp_server.py::test_list_todo`
17. `src/test/test_mcp_server.py::test_get_todo_content`
18. `src/test/test_mcp_server.py::test_refresh_index`
19. `src/test/test_mcp_server.py::test_refresh_index_statistics`
20. `src/test/test_mcp_server.py::test_refresh_index_timing`
21. `src/test/test_mcp_server.py::test_mcp_server_init`

### test_memory (10 ошибок)

1. `src/test/test_memory.py::TestMemoryDecayWeights::test_decay_weights_multiple_entries`
2. `src/test/test_memory.py::TestArchiveMemory::test_archive_memory_initialization`
3. `src/test/test_memory.py::TestArchiveMemory::test_archive_memory_add_entry`
4. `src/test/test_memory.py::TestArchiveMemory::test_archive_memory_add_entries`
5. `src/test/test_memory.py::TestArchiveMemory::test_archive_memory_get_entries_by_type`
6. `src/test/test_memory.py::TestArchiveMemory::test_archive_memory_get_entries_by_significance`
7. `src/test/test_memory.py::TestMemoryArchive::test_archive_old_entries_by_age`
8. `src/test/test_memory.py::TestMemoryArchive::test_archive_old_entries_by_weight`
9. `src/test/test_memory.py::TestMemoryArchive::test_archive_old_entries_by_significance`
10. `src/test/test_memory.py::TestMemoryStatistics::test_get_statistics_empty`

### test_monitor (6 ошибок)

1. `src/test/test_monitor.py::TestMonitor::test_monitor_basic`
2. `src/test/test_monitor.py::TestMonitor::test_monitor_with_activated_memory`
3. `src/test/test_monitor.py::TestMonitor::test_monitor_without_activated_memory`
4. `src/test/test_monitor.py::TestMonitor::test_monitor_multiple_calls`
5. `src/test/test_monitor.py::TestMonitor::test_monitor_log_file_append`
6. `src/test/test_monitor.py::TestMonitor::test_monitor_all_state_fields`

### test_performance (4 ошибок)

1. `src/test/test_performance.py::TestPerformanceBenchmarks::test_event_queue_performance`
2. `src/test/test_performance.py::TestPerformanceBenchmarks::test_self_state_apply_delta_performance`
3. `src/test/test_performance.py::TestPerformanceBenchmarks::test_runtime_loop_ticks_per_second`
4. `src/test/test_performance.py::TestPerformanceBenchmarks::test_state_snapshot_performance`

### test_property_based (1 ошибок)

1. `src/test/test_property_based.py::TestMemoryPropertyBased::test_memory_append_idempotent`

### test_state (15 ошибок)

1. `src/test/test_state.py::TestSnapshots::test_save_snapshot`
2. `src/test/test_state.py::TestSnapshots::test_load_snapshot`
3. `src/test/test_state.py::TestSnapshots::test_load_latest_snapshot`
4. `src/test/test_state.py::TestSnapshots::test_load_latest_snapshot_not_found`
5. `src/test/test_state.py::TestSelfStateValidation::test_energy_validation_invalid`
6. `src/test/test_state.py::TestSelfStateValidation::test_integrity_validation_invalid`
7. `src/test/test_state.py::TestSelfStateValidation::test_stability_validation_invalid`
8. `src/test/test_state.py::TestSelfStateValidation::test_fatigue_validation`
9. `src/test/test_state.py::TestSelfStateValidation::test_tension_validation`
10. `src/test/test_state.py::TestSelfStateValidation::test_age_validation`
11. `src/test/test_state.py::TestSelfStateSafeMethods::test_update_energy`
12. `src/test/test_state.py::TestSelfStateSafeMethods::test_update_integrity`
13. `src/test/test_state.py::TestSelfStateSafeMethods::test_update_stability`
14. `src/test/test_state.py::TestSelfStateLogging::test_logging_enabled`
15. `src/test/test_state.py::TestSelfStateLogging::test_get_change_history`

## Категории ошибок

- **AssertionError:** 46 упоминаний
- **AsyncTestError:** 44 упоминаний
- **ValueError:** 39 упоминаний
- **FileNotFoundError:** 7 упоминаний
- **TypeError:** 4 упоминаний
- **AttributeError:** 3 упоминаний

## Основные проблемные области

Модули с наибольшим количеством ошибок:

- **test_mcp_server**: 21 ошибок
- **test_state**: 15 ошибок
- **test_memory**: 10 ошибок
- **test_learning**: 7 ошибок
- **test_monitor**: 6 ошибок
- **test_performance**: 4 ошибок
- **test_degradation**: 3 ошибок
- **test_learning_adaptation_integration**: 3 ошибок
- **test_adaptation**: 2 ошибок
- **test_property_based**: 1 ошибок

## Рекомендации

1. Исправить ошибки в модулях с наибольшим количеством провалов
2. Проверить async тесты - требуется установка pytest-asyncio или anyio
3. Проверить тесты snapshots и monitor - возможно, требуется настройка путей
4. Проверить тесты learning и adaptation - возможно, требуется обновление структуры данных
5. Проверить тесты memory - возможно, требуется обновление логики архивации
6. Проверить тесты state - возможно, требуется обновление валидации и методов

## Полный список проваленных тестов

1. `src/test/test_monitor.py::TestMonitor::test_monitor_basic`
2. `src/test/test_monitor.py::TestMonitor::test_monitor_with_activated_memory`
3. `src/test/test_monitor.py::TestMonitor::test_monitor_without_activated_memory`
4. `src/test/test_monitor.py::TestMonitor::test_monitor_multiple_calls`
5. `src/test/test_monitor.py::TestMonitor::test_monitor_log_file_append`
6. `src/test/test_monitor.py::TestMonitor::test_monitor_all_state_fields`
7. `src/test/test_property_based.py::TestMemoryPropertyBased::test_memory_append_idempotent`
8. `src/test/test_state.py::TestSnapshots::test_save_snapshot`
9. `src/test/test_state.py::TestSnapshots::test_load_snapshot`
10. `src/test/test_state.py::TestSnapshots::test_load_latest_snapshot`
11. `src/test/test_state.py::TestSnapshots::test_load_latest_snapshot_not_found`
12. `src/test/test_memory.py::TestMemoryDecayWeights::test_decay_weights_multiple_entries`
13. `src/test/test_memory.py::TestArchiveMemory::test_archive_memory_initialization`
14. `src/test/test_memory.py::TestArchiveMemory::test_archive_memory_add_entry`
15. `src/test/test_memory.py::TestArchiveMemory::test_archive_memory_add_entries`
16. `src/test/test_memory.py::TestArchiveMemory::test_archive_memory_get_entries_by_type`
17. `src/test/test_memory.py::TestArchiveMemory::test_archive_memory_get_entries_by_significance`
18. `src/test/test_memory.py::TestMemoryArchive::test_archive_old_entries_by_age`
19. `src/test/test_memory.py::TestMemoryArchive::test_archive_old_entries_by_weight`
20. `src/test/test_memory.py::TestMemoryArchive::test_archive_old_entries_by_significance`
21. `src/test/test_memory.py::TestMemoryStatistics::test_get_statistics_empty`
22. `src/test/test_state.py::TestSelfStateValidation::test_energy_validation_invalid`
23. `src/test/test_state.py::TestSelfStateValidation::test_integrity_validation_invalid`
24. `src/test/test_state.py::TestSelfStateValidation::test_stability_validation_invalid`
25. `src/test/test_state.py::TestSelfStateValidation::test_fatigue_validation`
26. `src/test/test_state.py::TestSelfStateValidation::test_tension_validation`
27. `src/test/test_state.py::TestSelfStateValidation::test_age_validation`
28. `src/test/test_state.py::TestSelfStateSafeMethods::test_update_energy`
29. `src/test/test_state.py::TestSelfStateSafeMethods::test_update_integrity`
30. `src/test/test_state.py::TestSelfStateSafeMethods::test_update_stability`
31. `src/test/test_state.py::TestSelfStateLogging::test_logging_enabled`
32. `src/test/test_state.py::TestSelfStateLogging::test_get_change_history`
33. `src/test/test_degradation.py::TestDegradationRecovery::test_active_flag_stays_false_after_deactivation`
34. `src/test/test_degradation.py::TestDegradationLongRunning::test_degradation_over_1000_ticks`
35. `src/test/test_degradation.py::TestDegradationLongRunning::test_degradation_stability_over_time`
36. `src/test/test_performance.py::TestPerformanceBenchmarks::test_event_queue_performance`
37. `src/test/test_performance.py::TestPerformanceBenchmarks::test_self_state_apply_delta_performance`
38. `src/test/test_performance.py::TestPerformanceBenchmarks::test_runtime_loop_ticks_per_second`
39. `src/test/test_performance.py::TestPerformanceBenchmarks::test_state_snapshot_performance`
40. `src/test/test_adaptation.py::TestAdaptationManager::test_apply_adaptation_initialization`
41. `src/test/test_adaptation.py::TestAdaptationManager::test_apply_adaptation_no_decision_action_control`
42. `src/test/test_learning.py::TestLearningIntegration::test_learning_persistence_in_snapshots`
43. `src/test/test_learning.py::TestLearningStatic::test_method_signatures`
44. `src/test/test_learning.py::TestLearningStatic::test_method_return_types`
45. `src/test/test_learning.py::TestLearningStatic::test_imports_structure`
46. `src/test/test_learning.py::TestLearningSmoke::test_full_cycle_smoke`
47. `src/test/test_learning.py::TestLearningIntegrationExtended::test_learning_persistence_across_snapshots`
48. `src/test/test_learning.py::TestLearningIntegrationExtended::test_learning_with_large_memory`
49. `src/test/test_learning_adaptation_integration.py::TestLearningAdaptationStatic::test_learning_interval_constants`
50. `src/test/test_learning_adaptation_integration.py::TestLearningAdaptationStatic::test_return_types`
51. `src/test/test_learning_adaptation_integration.py::TestLearningAdaptationRuntimeIntegration::test_learning_frequency_in_runtime`
52. `src/test/test_mcp_interactive.py::test_mcp_functions`
53. `src/test/test_mcp_refresh_index.py::TestRefreshIndexErrorHandling::test_refresh_index_handles_os_error`
54. `src/test/test_mcp_server.py::test_search_docs`
55. `src/test/test_mcp_server.py::test_list_docs`
56. `src/test/test_mcp_server.py::test_get_doc_content`
57. `src/test/test_mcp_server.py::test_search_todo`
58. `src/test/test_mcp_server.py::test_search_docs_and_mode`
59. `src/test/test_mcp_server.py::test_search_docs_or_mode`
60. `src/test/test_mcp_server.py::test_search_docs_or_mode_with_quoted_query`
61. `src/test/test_mcp_server.py::test_search_docs_phrase_mode`
62. `src/test/test_mcp_server.py::test_tokenize_query_quotes_auto_phrase`
63. `src/test/test_mcp_server.py::test_tokenize_query_explicit_mode_priority`
64. `src/test/test_mcp_server.py::test_tokenize_query_empty_query`
65. `src/test/test_mcp_server.py::test_search_docs_empty_query`
66. `src/test/test_mcp_server.py::test_search_todo_and_mode`
67. `src/test/test_mcp_server.py::test_search_todo_or_mode`
68. `src/test/test_mcp_server.py::test_search_todo_phrase_mode`
69. `src/test/test_mcp_server.py::test_list_todo`
70. `src/test/test_mcp_server.py::test_get_todo_content`
71. `src/test/test_mcp_server.py::test_refresh_index`
72. `src/test/test_mcp_server.py::test_refresh_index_statistics`
73. `src/test/test_mcp_server.py::test_refresh_index_timing`
74. `src/test/test_mcp_server.py::test_mcp_server_init`

---

**Тестирование завершено!**
