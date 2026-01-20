# Отчет: Проектирование dev-mode с перезапуском процесса

**Задача:** Спроектировать dev-mode как перезапуск процесса (например через внешний watcher) или строгое "stop → start" внутри одного процесса

**Дата выполнения:** 2026-01-20

**Исполнитель:** Project Executor Agent

## Анализ проблемы и требований

### Текущие проблемы hot reload
Анализ существующей реализации `reloader_thread()` в `src/main_server_api.py` выявил критические проблемы:

1. **Проблемы идентичности объектов** - `importlib.reload()` создает новые классы, но старые ссылки остаются
2. **Висячие потоки** - неполное завершение потоков при перезагрузке
3. **Race conditions** - перезагрузка во время выполнения операций
4. **Непредсказуемость** - состояние системы после reload непредсказуемо

### Архитектурные требования
- **Безопасность**: Полное исключение проблем идентичности объектов
- **Надежность**: Гарантированное восстановление состояния
- **Производительность**: Минимальное время перезапуска (< 3 сек)
- **Совместимость**: Работа с существующими компонентами (SelfState, EventQueue, API сервер, runtime loop)

## Вариант 1: Перезапуск процесса (Рекомендуемый)

### Архитектурный дизайн

#### Основной принцип
Замена hot reload на **полный перезапуск процесса** с сохранением и восстановлением состояния через сериализацию.

#### Компоненты системы

##### 1. ProcessRestarter (`src/dev/process_restarter.py`)
```python
class ProcessRestarter:
    def __init__(self, watch_files: List[str], restart_state_file: str = "data/restart_state.json"):
        self.watch_files = watch_files
        self.restart_state_file = restart_state_file
        self.shutdown_manager = GracefulShutdownManager()
        self.state_serializer = StateSerializer(restart_state_file)
        self.monitoring_active = False

    def start(self) -> None:
        """Запуск мониторинга файлов и graceful shutdown"""
        self.monitoring_active = True
        threading.Thread(target=self._monitor_files, daemon=True).start()

    def _monitor_files(self) -> None:
        """Мониторинг изменений файлов каждые 1 сек"""
        mtime_dict = self._init_mtime_dict()

        while self.monitoring_active:
            time.sleep(1.0)
            if self._files_changed(mtime_dict):
                self._initiate_restart()

    def _initiate_restart(self) -> None:
        """Инициирование graceful shutdown и перезапуска"""
        logger.info("Changes detected, initiating restart...")

        # 1. Сохранение состояния
        self.state_serializer.save_restart_state()

        # 2. Graceful shutdown
        self.shutdown_manager.initiate_shutdown()

        # 3. Перезапуск процесса
        self._restart_process()

    def _restart_process(self) -> None:
        """Перезапуск процесса через os.execv()"""
        restart_args = [sys.executable] + sys.argv + ['--restart']
        os.execv(sys.executable, restart_args)
```

##### 2. StateSerializer
```python
class StateSerializer:
    def save_restart_state(self) -> None:
        """Атомарная запись состояния в JSON"""
        state_data = {
            "restart_marker": True,
            "timestamp": time.time(),
            "self_state": self._serialize_self_state(),
            "event_queue": self._serialize_event_queue(),
            "config": self._serialize_config()
        }

        # Атомарная запись через временный файл
        temp_file = f"{self.restart_state_file}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
        os.rename(temp_file, self.restart_state_file)

    def load_restart_state(self) -> Optional[Dict[str, Any]]:
        """Загрузка состояния после перезапуска"""
        if not os.path.exists(self.restart_state_file):
            return None

        try:
            with open(self.restart_state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data.get("restart_marker"):
                return None

            # Валидация timestamp (не старше 30 сек)
            if time.time() - data["timestamp"] > 30:
                return None

            return data
        except (json.JSONDecodeError, KeyError):
            return None
        finally:
            # Очистка файла после загрузки
            self._cleanup_restart_state()
```

##### 3. GracefulShutdownManager
```python
class GracefulShutdownManager:
    def __init__(self):
        self.components: List[ShutdownComponent] = []
        self.shutdown_timeout = 10.0  # сек

    def register_component(self, name: str, shutdown_func: Callable, join_func: Optional[Callable] = None, timeout: float = 5.0):
        """Регистрация компонента для graceful shutdown"""
        self.components.append(ShutdownComponent(name, shutdown_func, join_func, timeout))

    def initiate_shutdown(self) -> bool:
        """Последовательное завершение всех компонентов"""
        logger.info("Starting graceful shutdown...")

        for component in self.components:
            try:
                # Вызов shutdown функции
                component.shutdown_func()

                # Ожидание завершения (если есть join_func)
                if component.join_func:
                    component.join_func(timeout=component.timeout)

                logger.info(f"Component '{component.name}' shut down successfully")
            except Exception as e:
                logger.error(f"Error shutting down component '{component.name}': {e}")

        logger.info("Graceful shutdown completed")
        return True
```

#### Протокол перезапуска процесса

1. **Обнаружение изменений** (каждые 1 сек):
   - Проверка mtime всех отслеживаемых файлов
   - Сравнение с сохраненными значениями

2. **Инициирование shutdown**:
   - Установка флага graceful_shutdown
   - Вызов `shutdown_manager.initiate_shutdown()`

3. **Сохранение состояния**:
   - Сериализация SelfState, EventQueue, конфигурации
   - Атомарная запись в `data/restart_state.json`

4. **Перезапуск процесса**:
   ```python
   restart_args = [sys.executable] + sys.argv + ['--restart']
   os.execv(sys.executable, restart_args)
   ```

5. **Восстановление состояния**:
   - Проверка флага `--restart`
   - Загрузка из `restart_state.json`
   - Инициализация компонентов с сохраненным состоянием

### Отслеживаемые файлы
```
src/main_server_api.py
src/monitor/console.py
src/runtime/loop.py
src/state/self_state.py
src/environment/event.py
src/environment/event_queue.py
src/environment/generator.py
```

### Формат состояния
```json
{
  "restart_marker": true,
  "timestamp": 1705708800.0,
  "self_state": {
    "energy": 85.3,
    "stability": 92.1,
    "adaptation": 78.9,
    "memory": [...],
    "energy_history": [...],
    "stability_history": [...],
    "adaptation_history": [...]
  },
  "event_queue": [
    {"type": "external", "data": {...}, "timestamp": 1705708795.0},
    {"type": "internal", "data": {...}, "timestamp": 1705708798.0}
  ],
  "config": {
    "tick_interval": 1.0,
    "snapshot_period": 10
  }
}
```

## Вариант 2: Strict "stop → start" внутри процесса

### Архитектурный дизайн

#### Основной принцип
Полная остановка всех компонентов внутри одного процесса с последующим перезапуском без перезагрузки модулей.

#### Компоненты системы

##### 1. StrictProcessRestarter
```python
class StrictProcessRestarter:
    def __init__(self, component_registry: ComponentRegistry):
        self.component_registry = component_registry
        self.state_serializer = StateSerializer()
        self.watch_files = self._get_watch_files()

    def restart_cycle(self) -> None:
        """Полный цикл stop → start внутри процесса"""
        logger.info("Starting strict restart cycle...")

        # 1. Сохранение состояния
        state = self._capture_current_state()

        # 2. Полная остановка всех компонентов
        self._stop_all_components()

        # 3. Очистка состояния процесса
        self._cleanup_process_state()

        # 4. Перезапуск всех компонентов
        self._start_all_components(state)

        logger.info("Strict restart cycle completed")
```

##### 2. ComponentRegistry
```python
class ComponentRegistry:
    def __init__(self):
        self.components: Dict[str, Component] = {}

    def register(self, name: str, start_func: Callable, stop_func: Callable, state_capture_func: Optional[Callable] = None):
        """Регистрация компонента с функциями управления"""
        self.components[name] = Component(name, start_func, stop_func, state_capture_func)

    def stop_all(self) -> None:
        """Остановка всех компонентов в правильном порядке"""
        # Обратный порядок запуска
        for component in reversed(list(self.components.values())):
            try:
                component.stop_func()
                logger.info(f"Component '{component.name}' stopped")
            except Exception as e:
                logger.error(f"Error stopping component '{component.name}': {e}")

    def start_all(self, state: Dict[str, Any]) -> None:
        """Запуск всех компонентов с восстановлением состояния"""
        for component in self.components.values():
            try:
                if component.state_capture_func and component.name in state:
                    component.start_func(state[component.name])
                else:
                    component.start_func()
                logger.info(f"Component '{component.name}' started")
            except Exception as e:
                logger.error(f"Error starting component '{component.name}': {e}")
```

#### Протокол strict stop-start

1. **Обнаружение изменений**:
   - Аналогично варианту 1

2. **Stop всех компонентов**:
   - API сервер: `server.shutdown()` + `thread.join()`
   - Runtime loop: `loop_stop.set()` + `thread.join()`
   - Event queue: сохранение текущих событий
   - State: сериализация в память

3. **Очистка состояния процесса**:
   - Удаление всех глобальных переменных
   - Очистка кэшей модулей
   - Сброс внутренних состояний

4. **Перезапуск компонентов**:
   - Восстановление из сохраненного состояния
   - Перезапуск потоков с чистым состоянием

5. **Восстановление состояния**:
   - Загрузка SelfState из памяти
   - Восстановление EventQueue
   - Инициализация конфигурации

### Проблемы варианта 2
- **Сложность очистки**: Невозможно полностью очистить состояние Python процесса
- **Остаточные эффекты**: Некоторые изменения модулей могут сохраняться
- **Утечки памяти**: Накопление объектов в долгосрочной перспективе
- **Сложность отладки**: Смешивание старого и нового кода

## Сравнительный анализ вариантов

### Критерии оценки

| Критерий | Вариант 1 (Перезапуск) | Вариант 2 (Strict stop-start) |
|----------|------------------------|-------------------------------|
| **Безопасность** | ✅ Полная | ⚠️ Частичная (остаточные эффекты) |
| **Надежность** | ✅ Высокая | ⚠️ Средняя (проблемы очистки) |
| **Производительность** | ⚠️ 2-3 сек | ✅ < 1 сек |
| **Сложность реализации** | ⚠️ Средняя | ❌ Высокая |
| **Риски** | ✅ Минимальные | ⚠️ Значительные |
| **Совместимость** | ✅ Полная | ⚠️ Ограниченная |

### Выбор оптимального варианта

**Рекомендация: Вариант 1 (Перезапуск процесса)**

**Обоснование:**
1. **Безопасность превыше всего** - полное исключение проблем идентичности объектов
2. **Надежность** - предсказуемое поведение после каждого перезапуска
3. **Простота** - четкая архитектура без сложной логики очистки состояния
4. **Тестируемость** - каждый перезапуск = чистое состояние
5. **Производительность** - 2-3 секунды приемлемы для dev-режима

## Детальный план реализации

### Этап 1: Создание базовой инфраструктуры
- [ ] Создать `src/dev/process_restarter.py` с ProcessRestarter классом
- [ ] Реализовать GracefulShutdownManager
- [ ] Добавить StateSerializer для сохранения/восстановления
- [ ] Создать механизм обнаружения перезапуска (`--restart` флаг)

### Этап 2: Интеграция в main_server_api.py
- [ ] Заменить `reloader_thread()` на `process_restarter_thread()`
- [ ] Удалить весь код `importlib.reload`
- [ ] Интегрировать graceful shutdown в основной цикл
- [ ] Добавить логику восстановления состояния при старте

### Этап 3: Тестирование и отладка
- [ ] Создать unit-тесты для всех новых компонентов
- [ ] Добавить интеграционные тесты dev-mode
- [ ] Протестировать сценарии с большими состояниями
- [ ] Проверить корректность восстановления после перезапуска

## Риски и mitigation

### Риск: Длительное завершение потоков
**Mitigation:**
- Увеличенные таймауты (10 сек)
- Fallback на force kill для критичных случаев
- Логирование проблем завершения

### Риск: Потеря данных при сбое
**Mitigation:**
- Двойное сохранение состояния (snapshot + restart_state)
- Checksum валидация
- Backup предыдущих состояний

### Риск: Race conditions при сохранении
**Mitigation:**
- Threading.Lock для синхронизации
- Атомарные операции записи
- Валидация целостности состояния

## Заключение и рекомендации

**Выбранный вариант:** Перезапуск процесса (Вариант 1)

**Основные преимущества:**
- Полная безопасность и предсказуемость
- Простая и надежная архитектура
- Гарантированное исключение проблем hot reload
- Хорошая тестируемость и отладка

**Следующие шаги:**
1. Начать реализацию с базовой инфраструктуры (ProcessRestarter, StateSerializer)
2. Интегрировать в main_server_api.py
3. Провести полное тестирование системы
4. Обновить документацию

Отчет завершен!
