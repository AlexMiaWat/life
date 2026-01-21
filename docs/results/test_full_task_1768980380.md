# Отчет о тестировании - 2026-01-21 08:02:12

## Общая статистика

- **Всего тестов:** 327
- **Пройдено:** 318
- **Провалено:** 5
- **Ошибки:** 0
- **Пропущено:** 4
- **Время выполнения:** 33.91 секунд

## Статус тестирования

❌ **ОБНАРУЖЕНЫ ПРОБЛЕМЫ:** 5 тестов не прошли

## Детали проваленных тестов

### 1. src.test.test_runtime_integration.TestRuntimeLoop::test_loop_stops_on_stop_event

**Время выполнения:** 0.503 сек

**Ошибка:**

```
AssertionError: assert 3 == 2
 +  where 3 = SelfState(life_id='dd12a32c-2c0e-464f-a2cb-bbf839ac95b7', birth_timestamp=1768952421.5776045, age=0.20035934448242188, subjective_time=0.20035934448242188, ticks=3, energy=50.0, integrity=0.9, stability=0.8, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7d3ff4adeda0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).ticks
src/test/test_runtime_integration.py:164: in test_loop_stops_on_stop_event
    assert base_state.ticks == initial_ticks
E   AssertionError: assert 3 == 2
E    +  where 3 = SelfState(life_id='dd12a32c-2c0e-464f-a2cb-bbf839ac95b7', birth_timestamp=1768952421.5776045, age=0.20035934448242188, subjective_time=0.20035934448242188, ticks=3, energy=50.0, integrity=0.9, stability=0.8, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7d3ff4adeda0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).ticks
```

### 2. src.test.test_degradation.TestDegradationUnit::test_active_flag_remains_true_on_zero_energy

**Время выполнения:** 0.001 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='fdaa7a6f-dd20-4d32-90a2-938c45fe31a4', birth_timestamp=1768952429.2477186, age=0.0, subjective_time=0.0, ticks=0, energy=0.0, integrity=1.0, stability=1.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7d3ff7c7ef80>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:126: in test_active_flag_remains_true_on_zero_energy
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='fdaa7a6f-dd20-4d32-90a2-938c45fe31a4', birth_timestamp=1768952429.2477186, age=0.0, subjective_time=0.0, ticks=0, energy=0.0, integrity=1.0, stability=1.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7d3ff7c7ef80>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 3. src.test.test_degradation.TestDegradationUnit::test_active_flag_remains_true_on_zero_integrity

**Время выполнения:** 0.001 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='7b7d437a-d9e5-4ff3-b50b-68fd860b505c', birth_timestamp=1768952429.352196, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=0.0, stability=1.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7d3ff7c7cd00>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:137: in test_active_flag_remains_true_on_zero_integrity
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='7b7d437a-d9e5-4ff3-b50b-68fd860b505c', birth_timestamp=1768952429.352196, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=0.0, stability=1.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7d3ff7c7cd00>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 4. src.test.test_degradation.TestDegradationUnit::test_active_flag_remains_true_on_zero_stability

**Время выполнения:** 0.001 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='2132271e-e57a-4e0b-89c4-f9daf3ff4301', birth_timestamp=1768952429.3782787, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=1.0, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7d3ff599a110>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:147: in test_active_flag_remains_true_on_zero_stability
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='2132271e-e57a-4e0b-89c4-f9daf3ff4301', birth_timestamp=1768952429.3782787, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=1.0, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7d3ff599a110>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 5. src.test.test_degradation.TestDegradationIntegration::test_system_continues_on_energy_zero

**Время выполнения:** 0.303 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='5b5252d9-7232-4f5c-b53d-7a4f38cbafa1', birth_timestamp=1768952431.0709476, age=0.2507617473602295, subjective_time=0.2507617473602295, ticks=6, energy=0.004984765052795409, integrity=0.0, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7d3ff7c7dc30>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:309: in test_system_continues_on_energy_zero
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='5b5252d9-7232-4f5c-b53d-7a4f38cbafa1', birth_timestamp=1768952431.0709476, age=0.2507617473602295, subjective_time=0.2507617473602295, ticks=6, energy=0.004984765052795409, integrity=0.0, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7d3ff7c7dc30>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

## Пропущенные тесты

Количество пропущенных тестов: 4

Пропущенные тесты обычно требуют специальных условий выполнения (например, реального сервера).

## Статистика по файлам тестов

| Файл | Всего | Пройдено | Провалено |
|------|-------|----------|-----------|
| test | 327 | 322 | 5 |

## Рекомендации

- Необходимо исправить проваленные тесты
- Проверить логику и реализации соответствующих функций
- Возможно, требуется обновление зависимостей или конфигурации
- 4 тестов пропущено - возможно, требуется запуск с дополнительными опциями

---
*Отчет создан автоматически*

Тестирование завершено!