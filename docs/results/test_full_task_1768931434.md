# Отчет о тестировании - 2026-01-20 18:16:21

## Общая статистика

- **Всего тестов:** 336
- **Пройдено:** 316
- **Провалено:** 15
- **Ошибки:** 1
- **Пропущено:** 4
- **Время выполнения:** 54.91 секунд

## Статус тестирования

❌ **ОБНАРУЖЕНЫ ПРОБЛЕМЫ:** 16 тестов не прошли

## Детали проваленных тестов

### 1. src.test.test_generator.TestGeneratorCLI::test_send_event_success

**Время выполнения:** 0.039 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
self = <test_generator.TestGeneratorCLI object at 0x7b89f05649a0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7b89ef773190>

    def test_send_event_success(self, monkeypatch):
        """Тест успешной отправки события"""
>       from environment.generator_cli import send_event

src/test/test_generator.py:152: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """
    CLI для генерации событий и отправки их на API сервера.
    
    Пример:
        python -m environment.generator_cli --interval 5 --host localhost --port 8000
    """
    
    import argparse
    import os
    import sys
    import time
    
    import requests
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from .generator import EventGenerator
>   from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package

src/environment/generator_cli.py:17: ImportError
```

### 2. src.test.test_generator.TestGeneratorCLI::test_send_event_connection_error

**Время выполнения:** 0.009 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
self = <test_generator.TestGeneratorCLI object at 0x7b89f0565870>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7b89eee685b0>

    def test_send_event_connection_error(self, monkeypatch):
        """Тест обработки ошибки соединения"""
        import requests
    
>       from environment.generator_cli import send_event

src/test/test_generator.py:173: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """
    CLI для генерации событий и отправки их на API сервера.
    
    Пример:
        python -m environment.generator_cli --interval 5 --host localhost --port 8000
    """
    
    import argparse
    import os
    import sys
    import time
    
    import requests
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from .generator import EventGenerator
>   from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package

src/environment/generator_cli.py:17: ImportError
```

### 3. src.test.test_generator.TestGeneratorCLI::test_send_event_timeout

**Время выполнения:** 0.008 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
self = <test_generator.TestGeneratorCLI object at 0x7b89f0565ba0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7b89eee6ef80>

    def test_send_event_timeout(self, monkeypatch):
        """Тест обработки таймаута"""
        import requests
    
>       from environment.generator_cli import send_event

src/test/test_generator.py:189: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """
    CLI для генерации событий и отправки их на API сервера.
    
    Пример:
        python -m environment.generator_cli --interval 5 --host localhost --port 8000
    """
    
    import argparse
    import os
    import sys
    import time
    
    import requests
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from .generator import EventGenerator
>   from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package

src/environment/generator_cli.py:17: ImportError
```

### 4. src.test.test_generator_cli.TestGeneratorCLI::test_main_function_if_name_main

**Время выполнения:** 0.013 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
thing = <module 'environment' from '/workspace/src/environment/__init__.py'>
comp = 'generator_cli', import_path = 'environment.generator_cli'

    def _dot_lookup(thing, comp, import_path):
        try:
>           return getattr(thing, comp)
E           AttributeError: module 'environment' has no attribute 'generator_cli'. Did you mean: 'generator'?

/usr/lib/python3.10/unittest/mock.py:1248: AttributeError

During handling of the above exception, another exception occurred:

self = <test_generator_cli.TestGeneratorCLI object at 0x7b89f0565570>

    def test_main_function_if_name_main(self):
        """Тест вызова main при запуске как скрипт (строка 64)"""
        import sys
        from unittest.mock import patch
    
        # Мокируем все зависимости
>       with patch("environment.generator_cli.EventGenerator") as mock_gen_class, patch(
            "environment.generator_cli.send_event"
        ) as mock_send, patch("time.sleep", side_effect=KeyboardInterrupt()), patch(
            "builtins.print"
        ):

src/test/test_generator_cli.py:201: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <unittest.mock._patch object at 0x7b89eeeb3d00>

    def __enter__(self):
        """Perform the patch."""
        new, spec, spec_set = self.new, self.spec, self.spec_set
        autospec, kwargs = self.autospec, self.kwargs
        new_callable = self.new_callable
>       self.target = self.getter()

/usr/lib/python3.10/unittest/mock.py:1431: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   getter = lambda: _importer(target)

/usr/lib/python3.10/unittest/mock.py:1618: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

target = 'environment.generator_cli'

    def _importer(target):
        components = target.split('.')
        import_path = components.pop(0)
        thing = __import__(import_path)
    
        for comp in components:
            import_path += ".%s" % comp
>           thing = _dot_lookup(thing, comp, import_path)

/usr/lib/python3.10/unittest/mock.py:1261: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

thing = <module 'environment' from '/workspace/src/environment/__init__.py'>
comp = 'generator_cli', import_path = 'environment.generator_cli'

    def _dot_lookup(thing, comp, import_path):
        try:
            return getattr(thing, comp)
        except AttributeError:
>           __import__(import_path)

/usr/lib/python3.10/unittest/mock.py:1250: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """
    CLI для генерации событий и отправки их на API сервера.
    
    Пример:
        python -m environment.generator_cli --interval 5 --host localhost --port 8000
    """
    
    import argparse
    import os
    import sys
    import time
    
    import requests
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from .generator import EventGenerator
>   from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package

src/environment/generator_cli.py:17: ImportError
```

### 5. src.test.test_monitor.TestMonitor::test_log_function

**Время выполнения:** 0.001 сек

**Ошибка:**

```
AssertionError: assert '[RELOAD] Test message' in ''
 +  where '' = CaptureResult(out='', err='').out
self = <test_monitor.TestMonitor object at 0x7b89efb6b4f0>
capsys = <_pytest.capture.CaptureFixture object at 0x7b89eeeaaf20>

    def test_log_function(self, capsys):
        """Тест функции log (строки 13-14)"""
        log("Test message")
        captured = capsys.readouterr()
>       assert "[RELOAD] Test message" in captured.out
E       AssertionError: assert '[RELOAD] Test message' in ''
E        +  where '' = CaptureResult(out='', err='').out

src/test/test_monitor.py:37: AssertionError
```

### 6. src.test.test_property_based.TestSelfStatePropertyBased::test_state_parameters_always_in_bounds

**Время выполнения:** 1.271 сек

**Ошибка:**

```
hypothesis.errors.FailedHealthCheck: Input generation is slow: Hypothesis only generated 4 valid inputs after 1.20 seconds.

              count | fraction |    slowest draws (seconds)
  stability |    4  |    100%  |      --      --      --      --   1.199
   energy   |    4  |      0%  |      --      --      --      --      -- 
  integrity |    4  |      0%  |      --      --      --      --      -- 

This could be for a few reasons:
1. This strategy could be generating too much data per input. Try decreasing the amount of data generated, for example by decreasing the minimum size of collection strategies like st.lists().
2. Some other expensive computation could be running during input generation. For example, if @st.composite or st.data() is interspersed with an expensive computation, HealthCheck.too_slow is likely to trigger. If this computation is unrelated to input generation, move it elsewhere. Otherwise, try making it more efficient, or disable this health check if that is not possible.

If you expect input generation to take this long, you can disable this health check with @settings(suppress_health_check=[HealthCheck.too_slow]). See https://hypothesis.readthedocs.io/en/latest/reference/api.html#hypothesis.HealthCheck for details.
self = <test_property_based.TestSelfStatePropertyBased object at 0x7b89f2871390>

    @given(
>       energy=st.floats(min_value=0.0, max_value=100.0),
        integrity=st.floats(min_value=0.0, max_value=1.0),
        stability=st.floats(min_value=0.0, max_value=1.0),
    )
E   hypothesis.errors.FailedHealthCheck: Input generation is slow: Hypothesis only generated 4 valid inputs after 1.20 seconds.
E   
E                 count | fraction |    slowest draws (seconds)
E     stability |    4  |    100%  |      --      --      --      --   1.199
E      energy   |    4  |      0%  |      --      --      --      --      -- 
E     integrity |    4  |      0%  |      --      --      --      --      -- 
E   
E   This could be for a few reasons:
E   1. This strategy could be generating too much data per input. Try decreasing the amount of data generated, for example by decreasing the minimum size of collection strategies like st.lists().
E   2. Some other expensive computation could be running during input generation. For example, if @st.composite or st.data() is interspersed with an expensive computation, HealthCheck.too_slow is likely to trigger. If this computation is unrelated to input generation, move it elsewhere. Otherwise, try making it more efficient, or disable this health check if that is not possible.
E   
E   If you expect input generation to take this long, you can disable this health check with @settings(suppress_health_check=[HealthCheck.too_slow]). See https://hypothesis.readthedocs.io/en/latest/reference/api.html#hypothesis.HealthCheck for details.

src/test/test_property_based.py:29: FailedHealthCheck
```

### 7. src.test.test_property_based.TestMemoryPropertyBased::test_memory_append_idempotent

**Время выполнения:** 0.123 сек

**Ошибка:**

```
AssertionError: assert 1 == 2
 +  where 1 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768929388.1512513, weight=1.0, feedback_data=None, subjective_timestamp=None)])
 +  and   2 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768929388.1512513, weight=1.0, feedback_data=None, subjective_timestamp=None), MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768929388.1512513, weight=1.0, feedback_data=None, subjective_timestamp=None)])
Falsifying example: test_memory_append_idempotent(
    self=<test_property_based.TestMemoryPropertyBased object at 0x7b89f2890f70>,
    event_type='0',
    significance=0.0,
    num_appends=2,
)
self = <test_property_based.TestMemoryPropertyBased object at 0x7b89f2890f70>

    @given(
>       event_type=st.text(min_size=1, max_size=20),
        significance=st.floats(min_value=0.0, max_value=1.0),
        num_appends=st.integers(min_value=1, max_value=100),
    )

src/test/test_property_based.py:152: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <test_property_based.TestMemoryPropertyBased object at 0x7b89f2890f70>
event_type = '0', significance = 0.0, num_appends = 2

    @given(
        event_type=st.text(min_size=1, max_size=20),
        significance=st.floats(min_value=0.0, max_value=1.0),
        num_appends=st.integers(min_value=1, max_value=100),
    )
    def test_memory_append_idempotent(self, event_type, significance, num_appends):
        """Свойство: множественные append одного элемента эквивалентны одному append"""
        memory1 = Memory()
        memory2 = Memory()
    
        entry = MemoryEntry(
            event_type=event_type,
            meaning_significance=significance,
            timestamp=time.time(),
        )
    
        # Добавляем один раз
        memory1.append(entry)
    
        # Добавляем много раз (но из-за ограничения размера результат должен быть одинаковым)
        for _ in range(num_appends):
            memory2.append(entry)
    
        # Если память не переполнена, результаты должны быть одинаковыми
        if num_appends <= 50:
>           assert len(memory1) == len(memory2)
E           AssertionError: assert 1 == 2
E            +  where 1 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768929388.1512513, weight=1.0, feedback_data=None, subjective_timestamp=None)])
E            +  and   2 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768929388.1512513, weight=1.0, feedback_data=None, subjective_timestamp=None), MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768929388.1512513, weight=1.0, feedback_data=None, subjective_timestamp=None)])
E           Falsifying example: test_memory_append_idempotent(
E               self=<test_property_based.TestMemoryPropertyBased object at 0x7b89f2890f70>,
E               event_type='0',
E               significance=0.0,
E               num_appends=2,
E           )

src/test/test_property_based.py:176: AssertionError
```

### 8. src.test.test_state.TestSnapshots::test_save_snapshot

**Время выполнения:** 0.015 сек

**Ошибка:**

```
TypeError: cannot pickle '_thread.RLock' object
self = <test_state.TestSnapshots object at 0x7b89f28d73a0>
temp_snapshot_dir = PosixPath('/tmp/tmpnz2c0jz5')

    def test_save_snapshot(self, temp_snapshot_dir):
        """Тест сохранения снимка"""
        state = SelfState()
        state.ticks = 100
        state.energy = 75.0
        state.integrity = 0.8
        state.stability = 0.9
    
        # Добавляем запись в память
        entry = MemoryEntry(
            event_type="test", meaning_significance=0.5, timestamp=time.time()
        )
        state.memory.append(entry)
    
>       save_snapshot(state)

src/test/test_state.py:237: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

state = SelfState(life_id='e3165080-aabc-4679-86ca-0bbeb0e12c1a', birth_timestamp=1768929388.948939, age=0.0, subjective_time=...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def save_snapshot(state: SelfState):
        """
        Сохраняет текущее состояние жизни как отдельный JSON файл.
        Оптимизированная сериализация с исключением transient полей.
    
        ПРИМЕЧАНИЕ: Логирование временно отключается во время сериализации для производительности.
        Изменения состояния, которые могут произойти во время вызова asdict() (например,
        конвертация dataclass), не будут залогированы. Это намеренное решение для оптимизации.
    
        ПРИМЕЧАНИЕ: Flush буфера логов должен управляться через LogManager в runtime loop,
        а не внутри этой функции. Это обеспечивает правильное разделение ответственности.
    
        Args:
            state: Состояние для сохранения
        """
        # Временно отключаем логирование для сериализации
        # Это предотвращает логирование изменений, которые могут произойти при конвертации dataclass
        logging_was_enabled = state._logging_enabled
        state.disable_logging()
    
        try:
>           snapshot = asdict(state)

src/state/self_state.py:1038: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='e3165080-aabc-4679-86ca-0bbeb0e12c1a', birth_timestamp=1768929388.948939, age=0.0, subjective_time=...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def asdict(obj, *, dict_factory=dict):
        """Return the fields of a dataclass instance as a new dictionary mapping
        field names to field values.
    
        Example usage:
    
          @dataclass
          class C:
              x: int
              y: int
    
          c = C(1, 2)
          assert asdict(c) == {'x': 1, 'y': 2}
    
        If given, 'dict_factory' will be used instead of built-in dict.
        The function applies recursively to field values that are
        dataclass instances. This will also look into built-in containers:
        tuples, lists, and dicts.
        """
        if not _is_dataclass_instance(obj):
            raise TypeError("asdict() should be called on dataclass instances")
>       return _asdict_inner(obj, dict_factory)

/usr/lib/python3.10/dataclasses.py:1238: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='e3165080-aabc-4679-86ca-0bbeb0e12c1a', birth_timestamp=1768929388.948939, age=0.0, subjective_time=...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
>               value = _asdict_inner(getattr(obj, f.name), dict_factory)

/usr/lib/python3.10/dataclasses.py:1245: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89eeba3040>
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
                value = _asdict_inner(getattr(obj, f.name), dict_factory)
                result.append((f.name, value))
            return dict_factory(result)
        elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
            # obj is a namedtuple.  Recurse into it, but the returned
            # object is another namedtuple of the same type.  This is
            # similar to how other list- or tuple-derived classes are
            # treated (see below), but we just need to create them
            # differently because a namedtuple's __init__ needs to be
            # called differently (see bpo-34363).
    
            # I'm not using namedtuple's _asdict()
            # method, because:
            # - it does not recurse in to the namedtuple fields and
            #   convert them to dicts (using dict_factory).
            # - I don't actually want to return a dict here.  The main
            #   use case here is json.dumps, and it handles converting
            #   namedtuples to lists.  Admittedly we're losing some
            #   information here when we produce a json list instead of a
            #   dict.  Note that if we returned dicts here instead of
            #   namedtuples, we could no longer call asdict() on a data
            #   structure where a namedtuple was used as a dict key.
    
            return type(obj)(*[_asdict_inner(v, dict_factory) for v in obj])
        elif isinstance(obj, (list, tuple)):
            # Assume we can create an object of this type by passing in a
            # generator (which is not true for namedtuples, handled
            # above).
            return type(obj)(_asdict_inner(v, dict_factory) for v in obj)
        elif isinstance(obj, dict):
            return type(obj)((_asdict_inner(k, dict_factory),
                              _asdict_inner(v, dict_factory))
                             for k, v in obj.items())
        else:
>           return copy.deepcopy(obj)

/usr/lib/python3.10/dataclasses.py:1279: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

x = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89eeba3040>, memo = {}
_nil = []

    def deepcopy(x, memo=None, _nil=[]):
        """Deep copy operation on arbitrary Python objects.
    
        See the module's __doc__ string for more info.
        """
    
        if memo is None:
            memo = {}
    
        d = id(x)
        y = memo.get(d, _nil)
        if y is not _nil:
            return y
    
        cls = type(x)
    
        copier = _deepcopy_dispatch.get(cls)
        if copier is not None:
            y = copier(x, memo)
        else:
            if issubclass(cls, type):
                y = _deepcopy_atomic(x, memo)
            else:
                copier = getattr(x, "__deepcopy__", None)
                if copier is not None:
                    y = copier(memo)
                else:
                    reductor = dispatch_table.get(cls)
                    if reductor:
                        rv = reductor(x)
                    else:
                        reductor = getattr(x, "__reduce_ex__", None)
                        if reductor is not None:
>                           rv = reductor(4)
E                           TypeError: cannot pickle '_thread.RLock' object

/usr/lib/python3.10/copy.py:161: TypeError
```

### 9. src.test.test_state.TestSnapshots::test_load_snapshot

**Время выполнения:** 0.013 сек

**Ошибка:**

```
TypeError: cannot pickle '_thread.RLock' object
self = <test_state.TestSnapshots object at 0x7b89f28bfdc0>
temp_snapshot_dir = PosixPath('/tmp/tmp4p9eri1m')

    def test_load_snapshot(self, temp_snapshot_dir):
        """Тест загрузки снимка"""
        # Создаем снимок
        state = SelfState(life_id="test_life_id")
        state.ticks = 200
        state.energy = 50.0
        state.integrity = 0.6
        state.stability = 0.7
    
        entry = MemoryEntry(
            event_type="loaded_event", meaning_significance=0.7, timestamp=time.time()
        )
        state.memory.append(entry)
    
>       save_snapshot(state)

src/test/test_state.py:272: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

state = SelfState(life_id='test_life_id', birth_timestamp=1768929389.0491216, age=0.0, subjective_time=0.0, ticks=200, energy=...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def save_snapshot(state: SelfState):
        """
        Сохраняет текущее состояние жизни как отдельный JSON файл.
        Оптимизированная сериализация с исключением transient полей.
    
        ПРИМЕЧАНИЕ: Логирование временно отключается во время сериализации для производительности.
        Изменения состояния, которые могут произойти во время вызова asdict() (например,
        конвертация dataclass), не будут залогированы. Это намеренное решение для оптимизации.
    
        ПРИМЕЧАНИЕ: Flush буфера логов должен управляться через LogManager в runtime loop,
        а не внутри этой функции. Это обеспечивает правильное разделение ответственности.
    
        Args:
            state: Состояние для сохранения
        """
        # Временно отключаем логирование для сериализации
        # Это предотвращает логирование изменений, которые могут произойти при конвертации dataclass
        logging_was_enabled = state._logging_enabled
        state.disable_logging()
    
        try:
>           snapshot = asdict(state)

src/state/self_state.py:1038: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='test_life_id', birth_timestamp=1768929389.0491216, age=0.0, subjective_time=0.0, ticks=200, energy=...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def asdict(obj, *, dict_factory=dict):
        """Return the fields of a dataclass instance as a new dictionary mapping
        field names to field values.
    
        Example usage:
    
          @dataclass
          class C:
              x: int
              y: int
    
          c = C(1, 2)
          assert asdict(c) == {'x': 1, 'y': 2}
    
        If given, 'dict_factory' will be used instead of built-in dict.
        The function applies recursively to field values that are
        dataclass instances. This will also look into built-in containers:
        tuples, lists, and dicts.
        """
        if not _is_dataclass_instance(obj):
            raise TypeError("asdict() should be called on dataclass instances")
>       return _asdict_inner(obj, dict_factory)

/usr/lib/python3.10/dataclasses.py:1238: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='test_life_id', birth_timestamp=1768929389.0491216, age=0.0, subjective_time=0.0, ticks=200, energy=...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
>               value = _asdict_inner(getattr(obj, f.name), dict_factory)

/usr/lib/python3.10/dataclasses.py:1245: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89ef7d1980>
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
                value = _asdict_inner(getattr(obj, f.name), dict_factory)
                result.append((f.name, value))
            return dict_factory(result)
        elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
            # obj is a namedtuple.  Recurse into it, but the returned
            # object is another namedtuple of the same type.  This is
            # similar to how other list- or tuple-derived classes are
            # treated (see below), but we just need to create them
            # differently because a namedtuple's __init__ needs to be
            # called differently (see bpo-34363).
    
            # I'm not using namedtuple's _asdict()
            # method, because:
            # - it does not recurse in to the namedtuple fields and
            #   convert them to dicts (using dict_factory).
            # - I don't actually want to return a dict here.  The main
            #   use case here is json.dumps, and it handles converting
            #   namedtuples to lists.  Admittedly we're losing some
            #   information here when we produce a json list instead of a
            #   dict.  Note that if we returned dicts here instead of
            #   namedtuples, we could no longer call asdict() on a data
            #   structure where a namedtuple was used as a dict key.
    
            return type(obj)(*[_asdict_inner(v, dict_factory) for v in obj])
        elif isinstance(obj, (list, tuple)):
            # Assume we can create an object of this type by passing in a
            # generator (which is not true for namedtuples, handled
            # above).
            return type(obj)(_asdict_inner(v, dict_factory) for v in obj)
        elif isinstance(obj, dict):
            return type(obj)((_asdict_inner(k, dict_factory),
                              _asdict_inner(v, dict_factory))
                             for k, v in obj.items())
        else:
>           return copy.deepcopy(obj)

/usr/lib/python3.10/dataclasses.py:1279: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

x = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89ef7d1980>, memo = {}
_nil = []

    def deepcopy(x, memo=None, _nil=[]):
        """Deep copy operation on arbitrary Python objects.
    
        See the module's __doc__ string for more info.
        """
    
        if memo is None:
            memo = {}
    
        d = id(x)
        y = memo.get(d, _nil)
        if y is not _nil:
            return y
    
        cls = type(x)
    
        copier = _deepcopy_dispatch.get(cls)
        if copier is not None:
            y = copier(x, memo)
        else:
            if issubclass(cls, type):
                y = _deepcopy_atomic(x, memo)
            else:
                copier = getattr(x, "__deepcopy__", None)
                if copier is not None:
                    y = copier(memo)
                else:
                    reductor = dispatch_table.get(cls)
                    if reductor:
                        rv = reductor(x)
                    else:
                        reductor = getattr(x, "__reduce_ex__", None)
                        if reductor is not None:
>                           rv = reductor(4)
E                           TypeError: cannot pickle '_thread.RLock' object

/usr/lib/python3.10/copy.py:161: TypeError
```

### 10. src.test.test_state.TestSnapshots::test_load_latest_snapshot

**Время выполнения:** 0.014 сек

**Ошибка:**

```
TypeError: cannot pickle '_thread.RLock' object
self = <test_state.TestSnapshots object at 0x7b89f28d7280>
temp_snapshot_dir = PosixPath('/tmp/tmp7olry_9a')

    def test_load_latest_snapshot(self, temp_snapshot_dir):
        """Тест загрузки последнего снимка"""
        # Создаем несколько снимков
        for ticks in [10, 20, 30]:
            state = SelfState()
            state.ticks = ticks
            state.energy = ticks * 2.0
>           save_snapshot(state)

src/test/test_state.py:298: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

state = SelfState(life_id='4add5cb4-1fd2-4b9a-9d58-9fc10d34e89b', birth_timestamp=1768929389.1985357, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def save_snapshot(state: SelfState):
        """
        Сохраняет текущее состояние жизни как отдельный JSON файл.
        Оптимизированная сериализация с исключением transient полей.
    
        ПРИМЕЧАНИЕ: Логирование временно отключается во время сериализации для производительности.
        Изменения состояния, которые могут произойти во время вызова asdict() (например,
        конвертация dataclass), не будут залогированы. Это намеренное решение для оптимизации.
    
        ПРИМЕЧАНИЕ: Flush буфера логов должен управляться через LogManager в runtime loop,
        а не внутри этой функции. Это обеспечивает правильное разделение ответственности.
    
        Args:
            state: Состояние для сохранения
        """
        # Временно отключаем логирование для сериализации
        # Это предотвращает логирование изменений, которые могут произойти при конвертации dataclass
        logging_was_enabled = state._logging_enabled
        state.disable_logging()
    
        try:
>           snapshot = asdict(state)

src/state/self_state.py:1038: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='4add5cb4-1fd2-4b9a-9d58-9fc10d34e89b', birth_timestamp=1768929389.1985357, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def asdict(obj, *, dict_factory=dict):
        """Return the fields of a dataclass instance as a new dictionary mapping
        field names to field values.
    
        Example usage:
    
          @dataclass
          class C:
              x: int
              y: int
    
          c = C(1, 2)
          assert asdict(c) == {'x': 1, 'y': 2}
    
        If given, 'dict_factory' will be used instead of built-in dict.
        The function applies recursively to field values that are
        dataclass instances. This will also look into built-in containers:
        tuples, lists, and dicts.
        """
        if not _is_dataclass_instance(obj):
            raise TypeError("asdict() should be called on dataclass instances")
>       return _asdict_inner(obj, dict_factory)

/usr/lib/python3.10/dataclasses.py:1238: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='4add5cb4-1fd2-4b9a-9d58-9fc10d34e89b', birth_timestamp=1768929389.1985357, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
>               value = _asdict_inner(getattr(obj, f.name), dict_factory)

/usr/lib/python3.10/dataclasses.py:1245: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89f28fc740>
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
                value = _asdict_inner(getattr(obj, f.name), dict_factory)
                result.append((f.name, value))
            return dict_factory(result)
        elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
            # obj is a namedtuple.  Recurse into it, but the returned
            # object is another namedtuple of the same type.  This is
            # similar to how other list- or tuple-derived classes are
            # treated (see below), but we just need to create them
            # differently because a namedtuple's __init__ needs to be
            # called differently (see bpo-34363).
    
            # I'm not using namedtuple's _asdict()
            # method, because:
            # - it does not recurse in to the namedtuple fields and
            #   convert them to dicts (using dict_factory).
            # - I don't actually want to return a dict here.  The main
            #   use case here is json.dumps, and it handles converting
            #   namedtuples to lists.  Admittedly we're losing some
            #   information here when we produce a json list instead of a
            #   dict.  Note that if we returned dicts here instead of
            #   namedtuples, we could no longer call asdict() on a data
            #   structure where a namedtuple was used as a dict key.
    
            return type(obj)(*[_asdict_inner(v, dict_factory) for v in obj])
        elif isinstance(obj, (list, tuple)):
            # Assume we can create an object of this type by passing in a
            # generator (which is not true for namedtuples, handled
            # above).
            return type(obj)(_asdict_inner(v, dict_factory) for v in obj)
        elif isinstance(obj, dict):
            return type(obj)((_asdict_inner(k, dict_factory),
                              _asdict_inner(v, dict_factory))
                             for k, v in obj.items())
        else:
>           return copy.deepcopy(obj)

/usr/lib/python3.10/dataclasses.py:1279: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

x = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89f28fc740>, memo = {}
_nil = []

    def deepcopy(x, memo=None, _nil=[]):
        """Deep copy operation on arbitrary Python objects.
    
        See the module's __doc__ string for more info.
        """
    
        if memo is None:
            memo = {}
    
        d = id(x)
        y = memo.get(d, _nil)
        if y is not _nil:
            return y
    
        cls = type(x)
    
        copier = _deepcopy_dispatch.get(cls)
        if copier is not None:
            y = copier(x, memo)
        else:
            if issubclass(cls, type):
                y = _deepcopy_atomic(x, memo)
            else:
                copier = getattr(x, "__deepcopy__", None)
                if copier is not None:
                    y = copier(memo)
                else:
                    reductor = dispatch_table.get(cls)
                    if reductor:
                        rv = reductor(x)
                    else:
                        reductor = getattr(x, "__reduce_ex__", None)
                        if reductor is not None:
>                           rv = reductor(4)
E                           TypeError: cannot pickle '_thread.RLock' object

/usr/lib/python3.10/copy.py:161: TypeError
```

### 11. src.test.test_state.TestSnapshots::test_snapshot_preserves_memory

**Время выполнения:** 0.015 сек

**Ошибка:**

```
TypeError: cannot pickle '_thread.RLock' object
self = <test_state.TestSnapshots object at 0x7b89f28d63b0>
temp_snapshot_dir = PosixPath('/tmp/tmpm5lzy3pw')

    def test_snapshot_preserves_memory(self, temp_snapshot_dir):
        """Тест сохранения памяти в снимке"""
        state = SelfState()
    
        # Добавляем несколько записей
        for i in range(5):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.1 * i,
                timestamp=time.time(),
            )
            state.memory.append(entry)
    
        state.ticks = 50
>       save_snapshot(state)

src/test/test_state.py:326: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

state = SelfState(life_id='d3c54144-7b1c-4c64-8c45-8ae675064594', birth_timestamp=1768929389.2973232, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def save_snapshot(state: SelfState):
        """
        Сохраняет текущее состояние жизни как отдельный JSON файл.
        Оптимизированная сериализация с исключением transient полей.
    
        ПРИМЕЧАНИЕ: Логирование временно отключается во время сериализации для производительности.
        Изменения состояния, которые могут произойти во время вызова asdict() (например,
        конвертация dataclass), не будут залогированы. Это намеренное решение для оптимизации.
    
        ПРИМЕЧАНИЕ: Flush буфера логов должен управляться через LogManager в runtime loop,
        а не внутри этой функции. Это обеспечивает правильное разделение ответственности.
    
        Args:
            state: Состояние для сохранения
        """
        # Временно отключаем логирование для сериализации
        # Это предотвращает логирование изменений, которые могут произойти при конвертации dataclass
        logging_was_enabled = state._logging_enabled
        state.disable_logging()
    
        try:
>           snapshot = asdict(state)

src/state/self_state.py:1038: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='d3c54144-7b1c-4c64-8c45-8ae675064594', birth_timestamp=1768929389.2973232, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def asdict(obj, *, dict_factory=dict):
        """Return the fields of a dataclass instance as a new dictionary mapping
        field names to field values.
    
        Example usage:
    
          @dataclass
          class C:
              x: int
              y: int
    
          c = C(1, 2)
          assert asdict(c) == {'x': 1, 'y': 2}
    
        If given, 'dict_factory' will be used instead of built-in dict.
        The function applies recursively to field values that are
        dataclass instances. This will also look into built-in containers:
        tuples, lists, and dicts.
        """
        if not _is_dataclass_instance(obj):
            raise TypeError("asdict() should be called on dataclass instances")
>       return _asdict_inner(obj, dict_factory)

/usr/lib/python3.10/dataclasses.py:1238: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='d3c54144-7b1c-4c64-8c45-8ae675064594', birth_timestamp=1768929389.2973232, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
>               value = _asdict_inner(getattr(obj, f.name), dict_factory)

/usr/lib/python3.10/dataclasses.py:1245: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89eeca8180>
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
                value = _asdict_inner(getattr(obj, f.name), dict_factory)
                result.append((f.name, value))
            return dict_factory(result)
        elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
            # obj is a namedtuple.  Recurse into it, but the returned
            # object is another namedtuple of the same type.  This is
            # similar to how other list- or tuple-derived classes are
            # treated (see below), but we just need to create them
            # differently because a namedtuple's __init__ needs to be
            # called differently (see bpo-34363).
    
            # I'm not using namedtuple's _asdict()
            # method, because:
            # - it does not recurse in to the namedtuple fields and
            #   convert them to dicts (using dict_factory).
            # - I don't actually want to return a dict here.  The main
            #   use case here is json.dumps, and it handles converting
            #   namedtuples to lists.  Admittedly we're losing some
            #   information here when we produce a json list instead of a
            #   dict.  Note that if we returned dicts here instead of
            #   namedtuples, we could no longer call asdict() on a data
            #   structure where a namedtuple was used as a dict key.
    
            return type(obj)(*[_asdict_inner(v, dict_factory) for v in obj])
        elif isinstance(obj, (list, tuple)):
            # Assume we can create an object of this type by passing in a
            # generator (which is not true for namedtuples, handled
            # above).
            return type(obj)(_asdict_inner(v, dict_factory) for v in obj)
        elif isinstance(obj, dict):
            return type(obj)((_asdict_inner(k, dict_factory),
                              _asdict_inner(v, dict_factory))
                             for k, v in obj.items())
        else:
>           return copy.deepcopy(obj)

/usr/lib/python3.10/dataclasses.py:1279: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

x = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89eeca8180>, memo = {}
_nil = []

    def deepcopy(x, memo=None, _nil=[]):
        """Deep copy operation on arbitrary Python objects.
    
        See the module's __doc__ string for more info.
        """
    
        if memo is None:
            memo = {}
    
        d = id(x)
        y = memo.get(d, _nil)
        if y is not _nil:
            return y
    
        cls = type(x)
    
        copier = _deepcopy_dispatch.get(cls)
        if copier is not None:
            y = copier(x, memo)
        else:
            if issubclass(cls, type):
                y = _deepcopy_atomic(x, memo)
            else:
                copier = getattr(x, "__deepcopy__", None)
                if copier is not None:
                    y = copier(memo)
                else:
                    reductor = dispatch_table.get(cls)
                    if reductor:
                        rv = reductor(x)
                    else:
                        reductor = getattr(x, "__reduce_ex__", None)
                        if reductor is not None:
>                           rv = reductor(4)
E                           TypeError: cannot pickle '_thread.RLock' object

/usr/lib/python3.10/copy.py:161: TypeError
```

### 12. src.test.test_memory.TestMemoryArchive::test_archive_old_entries_by_weight

**Время выполнения:** 0.003 сек

**Ошибка:**

```
AssertionError: assert 1 == 2
 +  where 1 = len([MemoryEntry(event_type='high_weight', meaning_significance=0.5, timestamp=1768929402.371458, weight=0.8, feedback_data=None, subjective_timestamp=None)])
self = <test_memory.TestMemoryArchive object at 0x7b89efb69c30>
temp_memory = [MemoryEntry(event_type='high_weight', meaning_significance=0.5, timestamp=1768929402.371458, weight=0.8, feedback_data=None, subjective_timestamp=None)]

    def test_archive_old_entries_by_weight(self, temp_memory):
        """Тест архивации записей по весу"""
        memory = temp_memory
        low_weight_entry = MemoryEntry(
            event_type="low_weight",
            meaning_significance=0.5,
            timestamp=time.time(),
            weight=0.05,  # Ниже порога 0.1 для clamp_size, но тест проверяет архивацию
        )
        high_weight_entry = MemoryEntry(
            event_type="high_weight",
            meaning_significance=0.5,
            timestamp=time.time(),
            weight=0.8,
        )
        memory.append(low_weight_entry)
        memory.append(high_weight_entry)
    
>       assert len(memory) == 2  # Убеждаемся, что обе записи добавлены
E       AssertionError: assert 1 == 2
E        +  where 1 = len([MemoryEntry(event_type='high_weight', meaning_significance=0.5, timestamp=1768929402.371458, weight=0.8, feedback_data=None, subjective_timestamp=None)])

src/test/test_memory.py:671: AssertionError
```

### 13. src.test.test_degradation.TestDegradationRecovery::test_learning_params_recovery_from_snapshot

**Время выполнения:** 0.011 сек

**Ошибка:**

```
TypeError: cannot pickle '_thread.RLock' object
self = <test_degradation.TestDegradationRecovery object at 0x7b89f051ce80>

    def test_learning_params_recovery_from_snapshot(self):
        """Тест: восстановление learning_params из snapshot"""
        from state.self_state import load_snapshot, save_snapshot
    
        state = SelfState()
        state.energy = 50.0
    
        # Модифицируем learning_params
        state.learning_params["event_type_sensitivity"]["noise"] = 0.8
        state.learning_params["event_type_sensitivity"]["shock"] = 0.9
        state.learning_params["significance_thresholds"]["noise"] = 0.15
        state.learning_params["response_coefficients"]["dampen"] = 0.7
    
        # Сохраняем snapshot
>       save_snapshot(state)

src/test/test_degradation.py:682: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

state = SelfState(life_id='39320e08-f913-4c81-8349-ed7959a13197', birth_timestamp=1768929415.0557504, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def save_snapshot(state: SelfState):
        """
        Сохраняет текущее состояние жизни как отдельный JSON файл.
        Оптимизированная сериализация с исключением transient полей.
    
        ПРИМЕЧАНИЕ: Логирование временно отключается во время сериализации для производительности.
        Изменения состояния, которые могут произойти во время вызова asdict() (например,
        конвертация dataclass), не будут залогированы. Это намеренное решение для оптимизации.
    
        ПРИМЕЧАНИЕ: Flush буфера логов должен управляться через LogManager в runtime loop,
        а не внутри этой функции. Это обеспечивает правильное разделение ответственности.
    
        Args:
            state: Состояние для сохранения
        """
        # Временно отключаем логирование для сериализации
        # Это предотвращает логирование изменений, которые могут произойти при конвертации dataclass
        logging_was_enabled = state._logging_enabled
        state.disable_logging()
    
        try:
>           snapshot = asdict(state)

src/state/self_state.py:1038: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='39320e08-f913-4c81-8349-ed7959a13197', birth_timestamp=1768929415.0557504, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def asdict(obj, *, dict_factory=dict):
        """Return the fields of a dataclass instance as a new dictionary mapping
        field names to field values.
    
        Example usage:
    
          @dataclass
          class C:
              x: int
              y: int
    
          c = C(1, 2)
          assert asdict(c) == {'x': 1, 'y': 2}
    
        If given, 'dict_factory' will be used instead of built-in dict.
        The function applies recursively to field values that are
        dataclass instances. This will also look into built-in containers:
        tuples, lists, and dicts.
        """
        if not _is_dataclass_instance(obj):
            raise TypeError("asdict() should be called on dataclass instances")
>       return _asdict_inner(obj, dict_factory)

/usr/lib/python3.10/dataclasses.py:1238: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='39320e08-f913-4c81-8349-ed7959a13197', birth_timestamp=1768929415.0557504, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
>               value = _asdict_inner(getattr(obj, f.name), dict_factory)

/usr/lib/python3.10/dataclasses.py:1245: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89eeafa7c0>
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
                value = _asdict_inner(getattr(obj, f.name), dict_factory)
                result.append((f.name, value))
            return dict_factory(result)
        elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
            # obj is a namedtuple.  Recurse into it, but the returned
            # object is another namedtuple of the same type.  This is
            # similar to how other list- or tuple-derived classes are
            # treated (see below), but we just need to create them
            # differently because a namedtuple's __init__ needs to be
            # called differently (see bpo-34363).
    
            # I'm not using namedtuple's _asdict()
            # method, because:
            # - it does not recurse in to the namedtuple fields and
            #   convert them to dicts (using dict_factory).
            # - I don't actually want to return a dict here.  The main
            #   use case here is json.dumps, and it handles converting
            #   namedtuples to lists.  Admittedly we're losing some
            #   information here when we produce a json list instead of a
            #   dict.  Note that if we returned dicts here instead of
            #   namedtuples, we could no longer call asdict() on a data
            #   structure where a namedtuple was used as a dict key.
    
            return type(obj)(*[_asdict_inner(v, dict_factory) for v in obj])
        elif isinstance(obj, (list, tuple)):
            # Assume we can create an object of this type by passing in a
            # generator (which is not true for namedtuples, handled
            # above).
            return type(obj)(_asdict_inner(v, dict_factory) for v in obj)
        elif isinstance(obj, dict):
            return type(obj)((_asdict_inner(k, dict_factory),
                              _asdict_inner(v, dict_factory))
                             for k, v in obj.items())
        else:
>           return copy.deepcopy(obj)

/usr/lib/python3.10/dataclasses.py:1279: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

x = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89eeafa7c0>, memo = {}
_nil = []

    def deepcopy(x, memo=None, _nil=[]):
        """Deep copy operation on arbitrary Python objects.
    
        See the module's __doc__ string for more info.
        """
    
        if memo is None:
            memo = {}
    
        d = id(x)
        y = memo.get(d, _nil)
        if y is not _nil:
            return y
    
        cls = type(x)
    
        copier = _deepcopy_dispatch.get(cls)
        if copier is not None:
            y = copier(x, memo)
        else:
            if issubclass(cls, type):
                y = _deepcopy_atomic(x, memo)
            else:
                copier = getattr(x, "__deepcopy__", None)
                if copier is not None:
                    y = copier(memo)
                else:
                    reductor = dispatch_table.get(cls)
                    if reductor:
                        rv = reductor(x)
                    else:
                        reductor = getattr(x, "__reduce_ex__", None)
                        if reductor is not None:
>                           rv = reductor(4)
E                           TypeError: cannot pickle '_thread.RLock' object

/usr/lib/python3.10/copy.py:161: TypeError
```

### 14. src.test.test_degradation.TestDegradationRecovery::test_adaptation_params_recovery_from_snapshot

**Время выполнения:** 0.012 сек

**Ошибка:**

```
TypeError: cannot pickle '_thread.RLock' object
self = <test_degradation.TestDegradationRecovery object at 0x7b89f051cd00>

    def test_adaptation_params_recovery_from_snapshot(self):
        """Тест: восстановление adaptation_params из snapshot"""
        from state.self_state import load_snapshot, save_snapshot
    
        state = SelfState()
        state.energy = 50.0
    
        # Модифицируем adaptation_params
        state.adaptation_params["behavior_sensitivity"]["noise"] = 0.8
        state.adaptation_params["behavior_sensitivity"]["shock"] = 0.9
        state.adaptation_params["behavior_thresholds"]["noise"] = 0.15
        state.adaptation_params["behavior_coefficients"]["dampen"] = 0.7
    
        # Сохраняем snapshot
>       save_snapshot(state)

src/test/test_degradation.py:712: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

state = SelfState(life_id='4f839d20-f319-4f4f-9b99-43c20dfb26af', birth_timestamp=1768929415.1996121, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.7, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def save_snapshot(state: SelfState):
        """
        Сохраняет текущее состояние жизни как отдельный JSON файл.
        Оптимизированная сериализация с исключением transient полей.
    
        ПРИМЕЧАНИЕ: Логирование временно отключается во время сериализации для производительности.
        Изменения состояния, которые могут произойти во время вызова asdict() (например,
        конвертация dataclass), не будут залогированы. Это намеренное решение для оптимизации.
    
        ПРИМЕЧАНИЕ: Flush буфера логов должен управляться через LogManager в runtime loop,
        а не внутри этой функции. Это обеспечивает правильное разделение ответственности.
    
        Args:
            state: Состояние для сохранения
        """
        # Временно отключаем логирование для сериализации
        # Это предотвращает логирование изменений, которые могут произойти при конвертации dataclass
        logging_was_enabled = state._logging_enabled
        state.disable_logging()
    
        try:
>           snapshot = asdict(state)

src/state/self_state.py:1038: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='4f839d20-f319-4f4f-9b99-43c20dfb26af', birth_timestamp=1768929415.1996121, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.7, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])

    def asdict(obj, *, dict_factory=dict):
        """Return the fields of a dataclass instance as a new dictionary mapping
        field names to field values.
    
        Example usage:
    
          @dataclass
          class C:
              x: int
              y: int
    
          c = C(1, 2)
          assert asdict(c) == {'x': 1, 'y': 2}
    
        If given, 'dict_factory' will be used instead of built-in dict.
        The function applies recursively to field values that are
        dataclass instances. This will also look into built-in containers:
        tuples, lists, and dicts.
        """
        if not _is_dataclass_instance(obj):
            raise TypeError("asdict() should be called on dataclass instances")
>       return _asdict_inner(obj, dict_factory)

/usr/lib/python3.10/dataclasses.py:1238: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='4f839d20-f319-4f4f-9b99-43c20dfb26af', birth_timestamp=1768929415.1996121, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.7, 'absorb': 1.0, 'ignore': 0.0}}, adaptation_history=[])
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
>               value = _asdict_inner(getattr(obj, f.name), dict_factory)

/usr/lib/python3.10/dataclasses.py:1245: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89eebd4d00>
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
                value = _asdict_inner(getattr(obj, f.name), dict_factory)
                result.append((f.name, value))
            return dict_factory(result)
        elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
            # obj is a namedtuple.  Recurse into it, but the returned
            # object is another namedtuple of the same type.  This is
            # similar to how other list- or tuple-derived classes are
            # treated (see below), but we just need to create them
            # differently because a namedtuple's __init__ needs to be
            # called differently (see bpo-34363).
    
            # I'm not using namedtuple's _asdict()
            # method, because:
            # - it does not recurse in to the namedtuple fields and
            #   convert them to dicts (using dict_factory).
            # - I don't actually want to return a dict here.  The main
            #   use case here is json.dumps, and it handles converting
            #   namedtuples to lists.  Admittedly we're losing some
            #   information here when we produce a json list instead of a
            #   dict.  Note that if we returned dicts here instead of
            #   namedtuples, we could no longer call asdict() on a data
            #   structure where a namedtuple was used as a dict key.
    
            return type(obj)(*[_asdict_inner(v, dict_factory) for v in obj])
        elif isinstance(obj, (list, tuple)):
            # Assume we can create an object of this type by passing in a
            # generator (which is not true for namedtuples, handled
            # above).
            return type(obj)(_asdict_inner(v, dict_factory) for v in obj)
        elif isinstance(obj, dict):
            return type(obj)((_asdict_inner(k, dict_factory),
                              _asdict_inner(v, dict_factory))
                             for k, v in obj.items())
        else:
>           return copy.deepcopy(obj)

/usr/lib/python3.10/dataclasses.py:1279: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

x = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89eebd4d00>, memo = {}
_nil = []

    def deepcopy(x, memo=None, _nil=[]):
        """Deep copy operation on arbitrary Python objects.
    
        See the module's __doc__ string for more info.
        """
    
        if memo is None:
            memo = {}
    
        d = id(x)
        y = memo.get(d, _nil)
        if y is not _nil:
            return y
    
        cls = type(x)
    
        copier = _deepcopy_dispatch.get(cls)
        if copier is not None:
            y = copier(x, memo)
        else:
            if issubclass(cls, type):
                y = _deepcopy_atomic(x, memo)
            else:
                copier = getattr(x, "__deepcopy__", None)
                if copier is not None:
                    y = copier(memo)
                else:
                    reductor = dispatch_table.get(cls)
                    if reductor:
                        rv = reductor(x)
                    else:
                        reductor = getattr(x, "__reduce_ex__", None)
                        if reductor is not None:
>                           rv = reductor(4)
E                           TypeError: cannot pickle '_thread.RLock' object

/usr/lib/python3.10/copy.py:161: TypeError
```

### 15. src.test.test_degradation.TestDegradationRecovery::test_learning_adaptation_params_recovery_together

**Время выполнения:** 0.011 сек

**Ошибка:**

```
TypeError: cannot pickle '_thread.RLock' object
self = <test_degradation.TestDegradationRecovery object at 0x7b89f051c7f0>

    def test_learning_adaptation_params_recovery_together(self):
        """Тест: совместное восстановление learning_params и adaptation_params из snapshot"""
        from state.self_state import load_snapshot, save_snapshot
    
        state = SelfState()
        state.energy = 50.0
    
        # Модифицируем оба набора параметров
        state.learning_params["event_type_sensitivity"]["noise"] = 0.75
        state.adaptation_params["behavior_sensitivity"]["noise"] = 0.85
        state.adaptation_params["behavior_coefficients"]["absorb"] = 0.6
    
        # Сохраняем snapshot
>       save_snapshot(state)

src/test/test_degradation.py:741: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

state = SelfState(life_id='a149acea-8a1b-4812-9208-45b52dc79989', birth_timestamp=1768929415.2815757, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 0.6, 'ignore': 0.0}}, adaptation_history=[])

    def save_snapshot(state: SelfState):
        """
        Сохраняет текущее состояние жизни как отдельный JSON файл.
        Оптимизированная сериализация с исключением transient полей.
    
        ПРИМЕЧАНИЕ: Логирование временно отключается во время сериализации для производительности.
        Изменения состояния, которые могут произойти во время вызова asdict() (например,
        конвертация dataclass), не будут залогированы. Это намеренное решение для оптимизации.
    
        ПРИМЕЧАНИЕ: Flush буфера логов должен управляться через LogManager в runtime loop,
        а не внутри этой функции. Это обеспечивает правильное разделение ответственности.
    
        Args:
            state: Состояние для сохранения
        """
        # Временно отключаем логирование для сериализации
        # Это предотвращает логирование изменений, которые могут произойти при конвертации dataclass
        logging_was_enabled = state._logging_enabled
        state.disable_logging()
    
        try:
>           snapshot = asdict(state)

src/state/self_state.py:1038: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='a149acea-8a1b-4812-9208-45b52dc79989', birth_timestamp=1768929415.2815757, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 0.6, 'ignore': 0.0}}, adaptation_history=[])

    def asdict(obj, *, dict_factory=dict):
        """Return the fields of a dataclass instance as a new dictionary mapping
        field names to field values.
    
        Example usage:
    
          @dataclass
          class C:
              x: int
              y: int
    
          c = C(1, 2)
          assert asdict(c) == {'x': 1, 'y': 2}
    
        If given, 'dict_factory' will be used instead of built-in dict.
        The function applies recursively to field values that are
        dataclass instances. This will also look into built-in containers:
        tuples, lists, and dicts.
        """
        if not _is_dataclass_instance(obj):
            raise TypeError("asdict() should be called on dataclass instances")
>       return _asdict_inner(obj, dict_factory)

/usr/lib/python3.10/dataclasses.py:1238: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = SelfState(life_id='a149acea-8a1b-4812-9208-45b52dc79989', birth_timestamp=1768929415.2815757, age=0.0, subjective_time...ck': 0.1, 'idle': 0.1}, 'behavior_coefficients': {'dampen': 0.5, 'absorb': 0.6, 'ignore': 0.0}}, adaptation_history=[])
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
>               value = _asdict_inner(getattr(obj, f.name), dict_factory)

/usr/lib/python3.10/dataclasses.py:1245: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

obj = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89ee86c680>
dict_factory = <class 'dict'>

    def _asdict_inner(obj, dict_factory):
        if _is_dataclass_instance(obj):
            result = []
            for f in fields(obj):
                value = _asdict_inner(getattr(obj, f.name), dict_factory)
                result.append((f.name, value))
            return dict_factory(result)
        elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
            # obj is a namedtuple.  Recurse into it, but the returned
            # object is another namedtuple of the same type.  This is
            # similar to how other list- or tuple-derived classes are
            # treated (see below), but we just need to create them
            # differently because a namedtuple's __init__ needs to be
            # called differently (see bpo-34363).
    
            # I'm not using namedtuple's _asdict()
            # method, because:
            # - it does not recurse in to the namedtuple fields and
            #   convert them to dicts (using dict_factory).
            # - I don't actually want to return a dict here.  The main
            #   use case here is json.dumps, and it handles converting
            #   namedtuples to lists.  Admittedly we're losing some
            #   information here when we produce a json list instead of a
            #   dict.  Note that if we returned dicts here instead of
            #   namedtuples, we could no longer call asdict() on a data
            #   structure where a namedtuple was used as a dict key.
    
            return type(obj)(*[_asdict_inner(v, dict_factory) for v in obj])
        elif isinstance(obj, (list, tuple)):
            # Assume we can create an object of this type by passing in a
            # generator (which is not true for namedtuples, handled
            # above).
            return type(obj)(_asdict_inner(v, dict_factory) for v in obj)
        elif isinstance(obj, dict):
            return type(obj)((_asdict_inner(k, dict_factory),
                              _asdict_inner(v, dict_factory))
                             for k, v in obj.items())
        else:
>           return copy.deepcopy(obj)

/usr/lib/python3.10/dataclasses.py:1279: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

x = <unlocked _thread.RLock object owner=0 count=0 at 0x7b89ee86c680>, memo = {}
_nil = []

    def deepcopy(x, memo=None, _nil=[]):
        """Deep copy operation on arbitrary Python objects.
    
        See the module's __doc__ string for more info.
        """
    
        if memo is None:
            memo = {}
    
        d = id(x)
        y = memo.get(d, _nil)
        if y is not _nil:
            return y
    
        cls = type(x)
    
        copier = _deepcopy_dispatch.get(cls)
        if copier is not None:
            y = copier(x, memo)
        else:
            if issubclass(cls, type):
                y = _deepcopy_atomic(x, memo)
            else:
                copier = getattr(x, "__deepcopy__", None)
                if copier is not None:
                    y = copier(memo)
                else:
                    reductor = dispatch_table.get(cls)
                    if reductor:
                        rv = reductor(x)
                    else:
                        reductor = getattr(x, "__reduce_ex__", None)
                        if reductor is not None:
>                           rv = reductor(4)
E                           TypeError: cannot pickle '_thread.RLock' object

/usr/lib/python3.10/copy.py:161: TypeError
```

### 16. pytest::internal

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
| test | 335 | 320 | 15 |

## Рекомендации

- Необходимо исправить проваленные тесты
- Проверить логику и реализации соответствующих функций
- Возможно, требуется обновление зависимостей или конфигурации
- Исправить ошибки в коде тестов или зависимостях
- Проверить импорты и структуру проекта
- 4 тестов пропущено - возможно, требуется запуск с дополнительными опциями

---
*Отчет создан автоматически*