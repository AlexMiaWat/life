# План выполнения задачи: Добавить тесты на восстановление из snapshot после перезапуска

## Обзор задачи

Добавить комплексные тесты для проверки восстановления состояния системы Life из snapshot после перезапуска процесса. Тесты должны покрывать:

1. Загрузку состояния из последнего snapshot
2. Восстановление после перезапуска через ProcessRestarter
3. Консистентность состояния после восстановления
4. Обработку ошибок при загрузке поврежденных snapshot

## Компоненты системы, участвующие в восстановлении

### SnapshotManager
- Управляет периодичностью создания снапшотов
- Изолирует I/O операции от runtime loop
- Обрабатывает ошибки без падения системы

### SelfState
- `load_latest_snapshot()` - загрузка последнего доступного snapshot
- `_load_snapshot_from_data()` - загрузка из данных snapshot с валидацией
- `_validate_learning_params()` и `_validate_adaptation_params()` - валидация параметров

### ProcessRestarter
- `StateSerializer` - сериализация/десериализация состояния для перезапуска
- Сохранение состояния в `data/restart_state.json`
- Graceful shutdown перед перезапуском

## План тестирования

### Фаза 1: Тесты загрузки snapshot (Unit-тесты)
1. **test_load_latest_snapshot_success** - успешная загрузка последнего snapshot
2. **test_load_latest_snapshot_no_snapshots** - обработка отсутствия snapshots
3. **test_load_snapshot_by_tick** - загрузка конкретного snapshot по номеру тика
4. **test_snapshot_data_validation** - валидация данных при загрузке
5. **test_corrupted_snapshot_handling** - обработка поврежденных snapshot файлов

### Фаза 2: Тесты восстановления после перезапуска (Integration-тесты)
1. **test_process_restart_state_save_load** - сохранение и загрузка состояния перезапуска
2. **test_restart_state_cleanup** - очистка файла состояния после загрузки
3. **test_restart_with_snapshot_recovery** - полный цикл перезапуска с восстановлением
4. **test_restart_state_corruption** - обработка поврежденного состояния перезапуска

### Фаза 3: Тесты консистентности состояния (Integration-тесты)
1. **test_state_consistency_after_snapshot_load** - консистентность после загрузки
2. **test_memory_persistence_through_restart** - сохранение памяти через перезапуск
3. **test_runtime_loop_resume_after_restart** - продолжение работы после восстановления
4. **test_snapshot_recovery_with_evolution** - восстановление с учетом эволюции состояния

### Фаза 4: Тесты производительности и регрессий
1. **test_snapshot_loading_performance** - производительность загрузки больших snapshot
2. **test_restart_recovery_performance** - время восстановления после перезапуска
3. **test_snapshot_size_regression** - контроль размера snapshot файлов

## Структура тестового файла

Создать новый файл `src/test/test_snapshot_recovery.py` со следующими классами:

```python
@pytest.mark.unit
class TestSnapshotLoading:
    # Unit-тесты загрузки snapshot

@pytest.mark.integration
class TestProcessRestartRecovery:
    # Integration-тесты восстановления после перезапуска

@pytest.mark.integration
class TestStateConsistencyAfterRecovery:
    # Тесты консистентности состояния

@pytest.mark.performance
class TestSnapshotRecoveryPerformance:
    # Тесты производительности восстановления
```

## Критерии успешного выполнения

1. ✅ Все тесты проходят (unit, integration, performance)
2. ✅ Покрытие кода >95% для тестируемых компонентов
3. ✅ Тесты устойчивы к изменениям в формате snapshot
4. ✅ Документация обновлена с описанием новых тестов
5. ✅ Интеграция с существующей системой тестирования

## Риски и меры предосторожности

1. **Изменения формата snapshot** - тесты должны быть устойчивы к backward-compatible изменениям
2. **Производительность** - тесты не должны существенно замедлять CI/CD
3. **Файловая система** - тесты должны корректно очищать временные файлы
4. **Thread-safety** - тесты должны учитывать многопоточность

## Временная оценка

- Фаза 1 (Unit-тесты): 4-6 часов
- Фаза 2 (Integration-тесты): 6-8 часов
- Фаза 3 (Consistency-тесты): 4-6 часов
- Фаза 4 (Performance-тесты): 2-4 часа
- Документация и рефакторинг: 2-3 часа

**Итого: 18-27 часов**

## Следующие шаги

1. Создать базовую структуру тестового файла
2. Реализовать unit-тесты загрузки snapshot
3. Добавить integration-тесты восстановления
4. Протестировать и отладить
5. Обновить документацию