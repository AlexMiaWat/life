# Отчет о тестировании - 2026-01-20 20:04:06

## Общая статистика

- **Всего тестов:** 324
- **Пройдено:** 308
- **Провалено:** 11
- **Ошибки:** 1
- **Пропущено:** 4
- **Время выполнения:** 31.48 секунд

## Статус тестирования

❌ **ОБНАРУЖЕНЫ ПРОБЛЕМЫ:** 12 тестов не прошли

## Детали проваленных тестов

### 1. src.test.test_generator.TestGeneratorCLI::test_send_event_success

**Время выполнения:** 0.035 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
src/test/test_generator.py:152: in test_send_event_success
    from environment.generator_cli import send_event
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 2. src.test.test_generator.TestGeneratorCLI::test_send_event_connection_error

**Время выполнения:** 0.007 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
src/test/test_generator.py:173: in test_send_event_connection_error
    from environment.generator_cli import send_event
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 3. src.test.test_generator.TestGeneratorCLI::test_send_event_timeout

**Время выполнения:** 0.007 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
src/test/test_generator.py:189: in test_send_event_timeout
    from environment.generator_cli import send_event
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 4. src.test.test_generator_cli.TestGeneratorCLI::test_main_function_if_name_main

**Время выполнения:** 0.007 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
/usr/lib/python3.10/unittest/mock.py:1248: in _dot_lookup
    return getattr(thing, comp)
E   AttributeError: module 'environment' has no attribute 'generator_cli'. Did you mean: 'generator'?

During handling of the above exception, another exception occurred:
src/test/test_generator_cli.py:201: in test_main_function_if_name_main
    with patch("environment.generator_cli.EventGenerator") as mock_gen_class, patch(
/usr/lib/python3.10/unittest/mock.py:1431: in __enter__
    self.target = self.getter()
/usr/lib/python3.10/unittest/mock.py:1618: in <lambda>
    getter = lambda: _importer(target)
/usr/lib/python3.10/unittest/mock.py:1261: in _importer
    thing = _dot_lookup(thing, comp, import_path)
/usr/lib/python3.10/unittest/mock.py:1250: in _dot_lookup
    __import__(import_path)
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 5. src.test.test_property_based.TestMemoryPropertyBased::test_memory_append_idempotent

**Время выполнения:** 0.093 сек

**Ошибка:**

```
AssertionError: assert 1 == 2
 +  where 1 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768939380.700925, weight=1.0, feedback_data=None, subjective_timestamp=None)])
 +  and   2 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768939380.700925, weight=1.0, feedback_data=None, subjective_timestamp=None), MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768939380.700925, weight=1.0, feedback_data=None, subjective_timestamp=None)])
Falsifying example: test_memory_append_idempotent(
    self=<test_property_based.TestMemoryPropertyBased object at 0x74d82e56f910>,
    event_type='0',
    significance=0.0,
    num_appends=2,
)
src/test/test_property_based.py:152: in test_memory_append_idempotent
    event_type=st.text(min_size=1, max_size=20),
src/test/test_property_based.py:176: in test_memory_append_idempotent
    assert len(memory1) == len(memory2)
E   AssertionError: assert 1 == 2
E    +  where 1 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768939380.700925, weight=1.0, feedback_data=None, subjective_timestamp=None)])
E    +  and   2 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768939380.700925, weight=1.0, feedback_data=None, subjective_timestamp=None), MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768939380.700925, weight=1.0, feedback_data=None, subjective_timestamp=None)])
E   Falsifying example: test_memory_append_idempotent(
E       self=<test_property_based.TestMemoryPropertyBased object at 0x74d82e56f910>,
E       event_type='0',
E       significance=0.0,
E       num_appends=2,
E   )
```

### 6. src.test.test_api_integration.TestAPIServer::test_get_status_returns_current_state

**Время выполнения:** 0.589 сек

**Ошибка:**

```
assert 50.0 == 75.0
src/test/test_api_integration.py:54: in test_get_status_returns_current_state
    assert data["energy"] == 75.0
E   assert 50.0 == 75.0
```

### 7. src.test.test_degradation.TestDegradationUnit::test_active_flag_remains_true_on_zero_energy

**Время выполнения:** 0.001 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='b159ac60-bace-4986-9cbb-22f7d81e8514', birth_timestamp=1768939402.151825, age=0.0, subjective_time=0.0, ticks=0, energy=0.0, integrity=1.0, stability=1.0, fatigue=0.0, tension=0.0, active=False, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x74d82d2fe7a0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:126: in test_active_flag_remains_true_on_zero_energy
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='b159ac60-bace-4986-9cbb-22f7d81e8514', birth_timestamp=1768939402.151825, age=0.0, subjective_time=0.0, ticks=0, energy=0.0, integrity=1.0, stability=1.0, fatigue=0.0, tension=0.0, active=False, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x74d82d2fe7a0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 8. src.test.test_degradation.TestDegradationUnit::test_active_flag_remains_true_on_zero_integrity

**Время выполнения:** 0.001 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='86bd5176-9cb4-429d-91f1-bd47447a583b', birth_timestamp=1768939402.2392783, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=0.0, stability=1.0, fatigue=0.0, tension=0.0, active=False, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x74d82d5bc700>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:137: in test_active_flag_remains_true_on_zero_integrity
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='86bd5176-9cb4-429d-91f1-bd47447a583b', birth_timestamp=1768939402.2392783, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=0.0, stability=1.0, fatigue=0.0, tension=0.0, active=False, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x74d82d5bc700>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 9. src.test.test_degradation.TestDegradationUnit::test_active_flag_remains_true_on_zero_stability

**Время выполнения:** 0.001 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='ae0559d3-9144-4fca-9aa1-d7811e298323', birth_timestamp=1768939402.2621598, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=1.0, stability=0.0, fatigue=0.0, tension=0.0, active=False, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x74d82d2fcb20>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:147: in test_active_flag_remains_true_on_zero_stability
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='ae0559d3-9144-4fca-9aa1-d7811e298323', birth_timestamp=1768939402.2621598, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=1.0, stability=0.0, fatigue=0.0, tension=0.0, active=False, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x74d82d2fcb20>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 10. src.test.test_degradation.TestDegradationIntegration::test_system_continues_on_energy_zero

**Время выполнения:** 0.302 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='38ee8cde-563b-4381-8c1d-259fbd07f4c3', birth_timestamp=1768939403.9180942, age=0.2507450580596924, subjective_time=0.1261332809276566, ticks=6, energy=0.0049850988388061524, integrity=0.0, stability=0.0, fatigue=0.0, tension=0.0, active=False, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x74d82d5be830>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:309: in test_system_continues_on_energy_zero
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='38ee8cde-563b-4381-8c1d-259fbd07f4c3', birth_timestamp=1768939403.9180942, age=0.2507450580596924, subjective_time=0.1261332809276566, ticks=6, energy=0.0049850988388061524, integrity=0.0, stability=0.0, fatigue=0.0, tension=0.0, active=False, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x74d82d5be830>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 11. src.test.test_degradation.TestDegradationIntegration::test_system_continues_on_integrity_zero

**Время выполнения:** 0.203 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='fc92119b-d046-41bd-b9f7-696c06047e3d', birth_timestamp=1768939404.24417, age=0.15065455436706543, subjective_time=0.2258297510237942, ticks=4, energy=99.99698690891265, integrity=0.0, stability=0.9939738178253175, fatigue=0.0, tension=0.0, active=False, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x74d82d2fd900>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:333: in test_system_continues_on_integrity_zero
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='fc92119b-d046-41bd-b9f7-696c06047e3d', birth_timestamp=1768939404.24417, age=0.15065455436706543, subjective_time=0.2258297510237942, ticks=4, energy=99.99698690891265, integrity=0.0, stability=0.9939738178253175, fatigue=0.0, tension=0.0, active=False, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x74d82d2fd900>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 12. pytest::internal

**Время выполнения:** 0.000 сек

**Ошибка:**

```
internal error
Traceback (most recent call last):
  File "/usr/local/lib/python3.10/dist-packages/_pytest/main.py", line 318, in wrap_session
    session.exitstatus = doit(config, session) or 0
  File "/usr/local/lib/python3.10/dist-packages/_pytest/main.py", line 372, in _main
    config.hook.pytest_runtestloop(session=session)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_hooks.py", line 512, in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_manager.py", line 120, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 167, in _multicall
    raise exception
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 139, in _multicall
    teardown.throw(exception)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/logging.py", line 801, in pytest_runtestloop
    return (yield)  # Run all the tests.
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 139, in _multicall
    teardown.throw(exception)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/terminal.py", line 707, in pytest_runtestloop
    result = yield
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 121, in _multicall
    res = hook_impl.function(*args)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/main.py", line 396, in pytest_runtestloop
    item.config.hook.pytest_runtest_protocol(item=item, nextitem=nextitem)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_hooks.py", line 512, in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_manager.py", line 120, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 167, in _multicall
    raise exception
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 139, in _multicall
    teardown.throw(exception)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/warnings.py", line 89, in pytest_runtest_protocol
    return (yield)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 139, in _multicall
    teardown.throw(exception)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/assertion/__init__.py", line 192, in pytest_runtest_protocol
    return (yield)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 139, in _multicall
    teardown.throw(exception)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/unittest.py", line 587, in pytest_runtest_protocol
    return (yield)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 139, in _multicall
    teardown.throw(exception)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/faulthandler.py", line 102, in pytest_runtest_protocol
    return (yield)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 121, in _multicall
    res = hook_impl.function(*args)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/runner.py", line 118, in pytest_runtest_protocol
    runtestprotocol(item, nextitem=nextitem)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/runner.py", line 137, in runtestprotocol
    reports.append(call_and_report(item, "call", log))
  File "/usr/local/lib/python3.10/dist-packages/_pytest/runner.py", line 251, in call_and_report
    ihook.pytest_runtest_logreport(report=report)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_hooks.py", line 512, in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_manager.py", line 120, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 167, in _multicall
    raise exception
  File "/usr/local/lib/python3.10/dist-packages/pluggy/_callers.py", line 121, in _multicall
    res = hook_impl.function(*args)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/terminal.py", line 685, in pytest_runtest_logreport
    self._write_progress_information_filling_space()
  File "/usr/local/lib/python3.10/dist-packages/_pytest/terminal.py", line 785, in _write_progress_information_filling_space
    self.write(msg.rjust(fill), flush=True, **{color: True})
  File "/usr/local/lib/python3.10/dist-packages/_pytest/terminal.py", line 525, in write
    self._tw.write(content, flush=flush, **markup)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/_io/terminalwriter.py", line 164, in write
    self.write_raw(msg, flush=flush)
  File "/usr/local/lib/python3.10/dist-packages/_pytest/_io/terminalwriter.py", line 180, in write_raw
    self.flush()
  File "/usr/local/lib/python3.10/dist-packages/_pytest/_io/terminalwriter.py", line 187, in flush
    self._file.flush()
BrokenPipeError: [Errno 32] Broken pipe
```

## Пропущенные тесты

Количество пропущенных тестов: 4

Пропущенные тесты обычно требуют специальных условий выполнения (например, реального сервера).

## Статистика по файлам тестов

| Файл | Всего | Пройдено | Провалено |
|------|-------|----------|-----------|
| pytest | 1 | 0 | 1 |
| test | 323 | 312 | 11 |

## Рекомендации

- Необходимо исправить проваленные тесты
- Проверить логику и реализации соответствующих функций
- Возможно, требуется обновление зависимостей или конфигурации
- Исправить ошибки в коде тестов или зависимостях
- Проверить импорты и структуру проекта
- 4 тестов пропущено - возможно, требуется запуск с дополнительными опциями

---
*Отчет создан автоматически*