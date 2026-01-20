# Отчет о тестировании - 2026-01-20 21:38:52

## Общая статистика

- **Всего тестов:** 343
- **Пройдено:** 324
- **Провалено:** 14
- **Ошибки:** 1
- **Пропущено:** 4
- **Время выполнения:** 66.08 секунд

## Статус тестирования

❌ **ОБНАРУЖЕНЫ ПРОБЛЕМЫ:** 15 тестов не прошли

## Детали проваленных тестов

### 1. src.test.test_generator.TestGeneratorCLI::test_send_event_success

**Время выполнения:** 0.047 сек

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

**Время выполнения:** 0.010 сек

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

**Время выполнения:** 0.009 сек

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

**Время выполнения:** 0.009 сек

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

**Время выполнения:** 0.193 сек

**Ошибка:**

```
AssertionError: assert 1 == 2
 +  where 1 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768944146.2603366, weight=1.0, feedback_data=None, subjective_timestamp=None)])
 +  and   2 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768944146.2603366, weight=1.0, feedback_data=None, subjective_timestamp=None), MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768944146.2603366, weight=1.0, feedback_data=None, subjective_timestamp=None)])
Falsifying example: test_memory_append_idempotent(
    self=<test_property_based.TestMemoryPropertyBased object at 0x7a52ead9a5f0>,
    event_type='0',
    significance=0.0,
    num_appends=2,
)
src/test/test_property_based.py:152: in test_memory_append_idempotent
    event_type=st.text(min_size=1, max_size=20),
src/test/test_property_based.py:176: in test_memory_append_idempotent
    assert len(memory1) == len(memory2)
E   AssertionError: assert 1 == 2
E    +  where 1 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768944146.2603366, weight=1.0, feedback_data=None, subjective_timestamp=None)])
E    +  and   2 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768944146.2603366, weight=1.0, feedback_data=None, subjective_timestamp=None), MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768944146.2603366, weight=1.0, feedback_data=None, subjective_timestamp=None)])
E   Falsifying example: test_memory_append_idempotent(
E       self=<test_property_based.TestMemoryPropertyBased object at 0x7a52ead9a5f0>,
E       event_type='0',
E       significance=0.0,
E       num_appends=2,
E   )
```

### 6. src.test.test_runtime_integration.TestRuntimeLoop::test_loop_stops_on_stop_event

**Время выполнения:** 0.503 сек

**Ошибка:**

```
AssertionError: assert 3 == 2
 +  where 3 = SelfState(life_id='d8ef4feb-5682-4d1e-9d34-56ea6ee11238', birth_timestamp=1768944161.2524407, age=0.20030832290649414, subjective_time=0.23035457134246826, ticks=3, energy=50.0, integrity=0.9, stability=0.8, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52ea2f5810>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).ticks
src/test/test_runtime_integration.py:164: in test_loop_stops_on_stop_event
    assert base_state.ticks == initial_ticks
E   AssertionError: assert 3 == 2
E    +  where 3 = SelfState(life_id='d8ef4feb-5682-4d1e-9d34-56ea6ee11238', birth_timestamp=1768944161.2524407, age=0.20030832290649414, subjective_time=0.23035457134246826, ticks=3, energy=50.0, integrity=0.9, stability=0.8, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52ea2f5810>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).ticks
```

### 7. src.test.test_degradation.TestDegradationUnit::test_active_flag_remains_true_on_zero_energy

**Время выполнения:** 0.001 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='c7d95e62-5afc-4e62-8648-36333fb0e04f', birth_timestamp=1768944167.9611483, age=0.0, subjective_time=0.0, ticks=0, energy=0.0, integrity=1.0, stability=1.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52e9ed1bd0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:126: in test_active_flag_remains_true_on_zero_energy
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='c7d95e62-5afc-4e62-8648-36333fb0e04f', birth_timestamp=1768944167.9611483, age=0.0, subjective_time=0.0, ticks=0, energy=0.0, integrity=1.0, stability=1.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52e9ed1bd0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 8. src.test.test_degradation.TestDegradationUnit::test_active_flag_remains_true_on_zero_integrity

**Время выполнения:** 0.001 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='d7b9b6ac-d378-4831-9c30-7b93bfb4fec6', birth_timestamp=1768944167.9929068, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=0.0, stability=1.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52ea3deb90>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:137: in test_active_flag_remains_true_on_zero_integrity
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='d7b9b6ac-d378-4831-9c30-7b93bfb4fec6', birth_timestamp=1768944167.9929068, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=0.0, stability=1.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52ea3deb90>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 9. src.test.test_degradation.TestDegradationUnit::test_active_flag_remains_true_on_zero_stability

**Время выполнения:** 0.001 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='d4b27cb0-9d38-48b7-b497-6aed0b40c033', birth_timestamp=1768944168.0169055, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=1.0, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52ead56590>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:147: in test_active_flag_remains_true_on_zero_stability
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='d4b27cb0-9d38-48b7-b497-6aed0b40c033', birth_timestamp=1768944168.0169055, age=0.0, subjective_time=0.0, ticks=0, energy=100.0, integrity=1.0, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52ead56590>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 10. src.test.test_degradation.TestDegradationIntegration::test_system_continues_on_energy_zero

**Время выполнения:** 0.302 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='8850492f-7733-43d0-a583-4b2ddad4b2d1', birth_timestamp=1768944169.697413, age=0.25061821937561035, subjective_time=0.12606972826508805, ticks=6, energy=0.004987635612487793, integrity=0.0, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52ea3bdba0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:309: in test_system_continues_on_energy_zero
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='8850492f-7733-43d0-a583-4b2ddad4b2d1', birth_timestamp=1768944169.697413, age=0.25061821937561035, subjective_time=0.12606972826508805, ticks=6, energy=0.004987635612487793, integrity=0.0, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52ea3bdba0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 11. src.test.test_degradation.TestDegradationIntegration::test_system_continues_on_integrity_zero

**Время выполнения:** 0.202 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='ef6ee384-657a-4031-8cf3-c30056aec63a', birth_timestamp=1768944170.0250642, age=0.1503744125366211, subjective_time=0.22541009992644456, ticks=4, energy=99.99699251174927, integrity=0.0, stability=0.9939850234985351, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52e9d8df00>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:333: in test_system_continues_on_integrity_zero
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='ef6ee384-657a-4031-8cf3-c30056aec63a', birth_timestamp=1768944170.0250642, age=0.1503744125366211, subjective_time=0.22541009992644456, ticks=4, energy=99.99699251174927, integrity=0.0, stability=0.9939850234985351, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52e9d8df00>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 12. src.test.test_degradation.TestDegradationIntegration::test_system_continues_on_stability_zero

**Время выполнения:** 0.202 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='18b68498-01dd-4423-91ce-1e22f8b16665', birth_timestamp=1768944170.2509441, age=0.15043282508850098, subjective_time=0.15043207067759967, ticks=4, energy=99.99699134349824, integrity=0.9939826869964601, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52e9f15240>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:356: in test_system_continues_on_stability_zero
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='18b68498-01dd-4423-91ce-1e22f8b16665', birth_timestamp=1768944170.2509441, age=0.15043282508850098, subjective_time=0.15043207067759967, ticks=4, energy=99.99699134349824, integrity=0.9939826869964601, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52e9f15240>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 13. src.test.test_degradation.TestDegradationEdgeCases::test_system_continues_with_all_params_zero

**Время выполнения:** 0.202 сек

**Ошибка:**

```
AssertionError: assert False is True
 +  where False = SelfState(life_id='a5e4f49e-3a59-4d8f-9659-ef4c1a6bfc2d', birth_timestamp=1768944172.426179, age=0.1504521369934082, subjective_time=0.0752260684967041, ticks=4, energy=0.0, integrity=0.0, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52eae444f0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
src/test/test_degradation.py:595: in test_system_continues_with_all_params_zero
    assert state.active is True
E   AssertionError: assert False is True
E    +  where False = SelfState(life_id='a5e4f49e-3a59-4d8f-9659-ef4c1a6bfc2d', birth_timestamp=1768944172.426179, age=0.1504521369934082, subjective_time=0.0752260684967041, ticks=4, energy=0.0, integrity=0.0, stability=0.0, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52eae444f0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[]).active
```

### 14. src.test.test_degradation.TestDegradationLongRunning::test_degradation_over_1000_ticks

**Время выполнения:** 15.041 сек

**Ошибка:**

```
AssertionError: Expected >= 1000 ticks, got 627
assert 627 >= 1000
 +  where 627 = SelfState(life_id='5504faf4-cc2a-4cb6-a83c-8e3c73d9d000', birth_timestamp=1768944172.8172934, age=15.012507200241089, subjective_time=20.266884720325447, ticks=627, energy=80.0, integrity=0.9, stability=0.9, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52ea2793f0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[{'timestamp': 1768944175.2261791, 'tick': 100, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}, {'timestamp': 1768944177.6949143, 'tick': 200, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}, {'timestamp': 1768944180.137176, 'tick': 300, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}, {'timestamp': 1768944182.537588, 'tick': 400, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}, {'timestamp': 1768944184.9846766, 'tick': 500, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}, {'timestamp': 1768944187.3395452, 'tick': 600, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}]).ticks
src/test/test_degradation.py:818: in test_degradation_over_1000_ticks
    assert state.ticks >= 1000, f"Expected >= 1000 ticks, got {state.ticks}"
E   AssertionError: Expected >= 1000 ticks, got 627
E   assert 627 >= 1000
E    +  where 627 = SelfState(life_id='5504faf4-cc2a-4cb6-a83c-8e3c73d9d000', birth_timestamp=1768944172.8172934, age=15.012507200241089, subjective_time=20.266884720325447, ticks=627, energy=80.0, integrity=0.9, stability=0.9, fatigue=0.0, tension=0.0, _active=True, recent_events=[], last_significance=0.0, energy_history=[], stability_history=[], planning={}, intelligence={}, memory=[], archive_memory=<src.memory.memory.ArchiveMemory object at 0x7a52ea2793f0>, subjective_time_base_rate=1.0, subjective_time_rate_min=0.1, subjective_time_rate_max=3.0, subjective_time_intensity_coeff=1.0, subjective_time_stability_coeff=0.5, subjective_time_energy_coeff=0.5, subjective_time_intensity_smoothing=0.3, time_ratio_history=[], last_event_intensity=0.0, activated_memory=[], last_pattern='', learning_params={'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_params={'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[{'timestamp': 1768944175.2261791, 'tick': 100, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}, {'timestamp': 1768944177.6949143, 'tick': 200, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}, {'timestamp': 1768944180.137176, 'tick': 300, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}, {'timestamp': 1768944182.537588, 'tick': 400, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}, {'timestamp': 1768944184.9846766, 'tick': 500, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}, {'timestamp': 1768944187.3395452, 'tick': 600, 'old_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'new_params': {'behavior_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'behavior_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, 'changes': {}, 'learning_params_snapshot': {'event_type_sensitivity': {'noise': 0.2, 'decay': 0.2, 'recovery': 0.2, 'shock': 0.2, 'idle': 0.2}, 'significance_thresholds': {'noise': 0.1, 'decay': 0.1, 'recovery': 0.1, 'shock': 0.1, 'idle': 0.1}, 'response_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}}]).ticks
```

### 15. pytest::internal

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
| test | 342 | 328 | 14 |

## Рекомендации

- Необходимо исправить проваленные тесты
- Проверить логику и реализации соответствующих функций
- Возможно, требуется обновление зависимостей или конфигурации
- Исправить ошибки в коде тестов или зависимостях
- Проверить импорты и структуру проекта
- 4 тестов пропущено - возможно, требуется запуск с дополнительными опциями

---
*Отчет создан автоматически*
