# 06_PROCESS RESTARTER — Безопасный перезапуск процесса

## Назначение
Process Restarter — это система безопасного перезапуска процесса вместо hot reload. Модуль отслеживает изменения в исходных файлах и инициирует полный перезапуск процесса, обеспечивая чистое состояние без проблем с идентичностью объектов и висячими потоками.

**Ключевой принцип:** Лучше перезапустить процесс заново, чем пытаться "исправить" его на лету.

## Текущий статус
✅ **Реализован** (v2.2)
*   Файл: [`src/dev/process_restarter.py`](../../src/dev/process_restarter.py)
*   Заменяет проблематичный hot reload на безопасный перезапуск
*   Интегрирован в dev-режим `main_server_api.py`
*   Полная сериализация/десериализация состояния
*   Graceful shutdown всех компонентов

## Архитектура

### Основные компоненты

#### 1. StateSerializer
Отвечает за сохранение и восстановление состояния системы при перезапуске.

#### 2. GracefulShutdownManager
Обеспечивает корректное завершение всех компонентов перед перезапуском.

#### 3. FileChangeWatcher
Отслеживает изменения в исходных файлах для инициирования перезапуска.

#### 4. ProcessRestarter
Основной координатор процесса перезапуска.

## Принципы работы

### Безопасная сериализация состояния

В отличие от традиционного hot reload, Process Restarter:

1. **Полностью останавливает** все компоненты
2. **Сериализует состояние** в JSON файл
3. **Перезапускает процесс** с нуля
4. **Восстанавливает состояние** из сохраненного файла

### Graceful Shutdown

Процесс завершения включает:
- Установку флагов завершения для всех потоков
- Ожидание корректного завершения компонентов
- Таймауты для предотвращения зависаний
- Сохранение состояния перед завершением

### Атомарные операции

- Сериализация состояния через временные файлы
- Атомарное переименование для предотвращения повреждений
- Проверка целостности сохраненных данных

## API

### StateSerializer

```python
from src.dev.process_restarter import StateSerializer

serializer = StateSerializer()

# Сохранение состояния
success = serializer.save_restart_state(self_state, event_queue, config)

# Загрузка состояния
state_data = serializer.load_restart_state()
if state_data:
    # Восстановление состояния из state_data
    pass

# Очистка файла состояния
serializer.cleanup_restart_state()
```

### GracefulShutdownManager

```python
from src.dev.process_restarter import GracefulShutdownManager

shutdown_manager = GracefulShutdownManager(shutdown_timeout=10.0)

# Регистрация компонентов для корректного завершения
shutdown_manager.register_component(
    component_name="runtime_loop",
    shutdown_func=lambda: runtime_loop.stop(),
    join_func=lambda: runtime_loop_thread.join(),
    timeout=5.0
)

# Инициирование завершения
all_shutdown_cleanly = shutdown_manager.initiate_shutdown()
```

### FileChangeWatcher

```python
from src.dev.process_restarter import FileChangeWatcher

watcher = FileChangeWatcher(
    watch_paths=["src/main_server_api.py", "src/runtime/loop.py"],
    ignore_patterns=["*.pyc", "__pycache__"]
)

# Запуск отслеживания в фоне
watcher.start()

# Остановка отслеживания
watcher.stop()
```

### ProcessRestarter (основной интерфейс)

```python
from src.dev.process_restarter import ProcessRestarter

restarter = ProcessRestarter(
    watch_paths=["src/"],
    shutdown_timeout=10.0,
    restart_delay=1.0
)

# Настройка коллбеков
restarter.set_callbacks(
    save_state_callback=lambda: save_current_state(),
    load_state_callback=lambda data: restore_state_from_data(data),
    restart_command=["python", "src/main_server_api.py", "--restart"]
)

# Запуск системы перезапуска
restarter.start()
```

## Примеры использования

### Базовое использование в dev-режиме

```python
from src.dev.process_restarter import ProcessRestarter
from src.main_server_api import create_app_state
import sys

# Создание системы перезапуска
restarter = ProcessRestarter(
    watch_paths=[
        "src/main_server_api.py",
        "src/runtime/loop.py",
        "src/state/self_state.py",
        "src/environment/event.py",
        "src/environment/event_queue.py",
        "src/environment/generator.py",
        "src/dev/process_restarter.py"
    ],
    shutdown_timeout=8.0,
    restart_delay=0.5
)

# Настройка сохранения состояния
def save_state():
    """Сохраняет текущее состояние системы"""
    state = get_current_app_state()
    config = get_current_config()
    event_queue = get_current_event_queue()

    serializer = StateSerializer()
    return serializer.save_restart_state(state, event_queue, config)

# Настройка восстановления состояния
def load_state():
    """Восстанавливает состояние после перезапуска"""
    serializer = StateSerializer()
    state_data = serializer.load_restart_state()

    if state_data:
        # Восстановление состояния
        restore_app_state(state_data["self_state"])
        restore_event_queue(state_data["event_queue"])
        restore_config(state_data["config"])

        # Очистка файла состояния
        serializer.cleanup_restart_state()
        return True
    return False

# Настройка команды перезапуска
restart_cmd = [sys.executable] + sys.argv + ["--restart"]

restarter.set_callbacks(
    save_state_callback=save_state,
    load_state_callback=load_state,
    restart_command=restart_cmd
)

# Проверка, является ли это перезапуском
if "--restart" in sys.argv:
    if not restarter.load_state_callback():
        logger.warning("Failed to load restart state, starting fresh")
else:
    # Первый запуск - стартуем систему перезапуска
    restarter.start()

# Основной цикл приложения
run_main_application()
```

### Отслеживание изменений с кастомными паттернами

```python
from src.dev.process_restarter import FileChangeWatcher
import time

# Создание watcher с кастомными настройками
watcher = FileChangeWatcher(
    watch_paths=[
        "src/",           # Вся директория src
        "config.json",    # Конфигурационный файл
        "requirements.txt" # Зависимости
    ],
    ignore_patterns=[
        "*.pyc",
        "__pycache__/*",
        "*.log",
        "data/*",
        ".git/*"
    ],
    poll_interval=0.5  # Проверка каждые 0.5 секунды
)

# Callback при обнаружении изменений
def on_file_changed(changed_files):
    print(f"Обнаружены изменения в файлах: {changed_files}")
    for file_path in changed_files:
        print(f"  - {file_path}")

    # Здесь можно инициировать перезапуск
    initiate_restart()

watcher.set_change_callback(on_file_changed)
watcher.start()

print("Отслеживание изменений запущено. Нажмите Ctrl+C для остановки.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Останавливаю отслеживание...")
    watcher.stop()
```

### Graceful shutdown с таймаутами

```python
from src.dev.process_restarter import GracefulShutdownManager
import threading
import time

# Пример компонентов системы
class RuntimeLoop:
    def __init__(self):
        self.running = True
        self.thread = None

    def start(self):
        def run():
            while self.running:
                # Имитация работы
                time.sleep(0.1)
            print("Runtime loop stopped")

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self):
        print("Stopping runtime loop...")
        self.running = False

    def join(self):
        if self.thread:
            self.thread.join(timeout=5.0)

# Создание менеджера завершения
shutdown_manager = GracefulShutdownManager(shutdown_timeout=10.0)

# Регистрация компонентов
runtime_loop = RuntimeLoop()
runtime_loop.start()

shutdown_manager.register_component(
    component_name="runtime_loop",
    shutdown_func=runtime_loop.stop,
    join_func=runtime_loop.join,
    timeout=5.0
)

# Имитация работы системы
print("Система работает... Нажмите Ctrl+C для graceful shutdown")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Получен сигнал завершения")

    # Инициирование graceful shutdown
    success = shutdown_manager.initiate_shutdown()

    if success:
        print("✅ Все компоненты завершились корректно")
    else:
        print("⚠️  Некоторые компоненты завершились с таймаутом")

    print("Система остановлена")
```

### Полный цикл перезапуска с сохранением состояния

```python
import os
import sys
import signal
from src.dev.process_restarter import ProcessRestarter, StateSerializer

class Application:
    def __init__(self):
        self.state = {"counter": 0, "message": "Hello World"}
        self.running = True

    def run(self):
        """Основной цикл приложения"""
        print(f"Приложение запущено. Счетчик: {self.state['counter']}")

        while self.running:
            time.sleep(1)
            self.state["counter"] += 1

            if self.state["counter"] % 10 == 0:
                print(f"Счетчик: {self.state['counter']}")

    def stop(self):
        """Остановка приложения"""
        print("Останавливаю приложение...")
        self.running = False

# Глобальная переменная приложения
app = None

def save_application_state():
    """Сохраняет состояние приложения"""
    global app
    if app:
        serializer = StateSerializer()
        # Имитация сохранения состояния
        config = {"app_version": "1.0", "mode": "dev"}
        return serializer.save_restart_state(app.state, [], config)
    return False

def load_application_state():
    """Восстанавливает состояние приложения"""
    global app
    serializer = StateSerializer()
    state_data = serializer.load_restart_state()

    if state_data:
        app.state.update(state_data.get("self_state", {}))
        serializer.cleanup_restart_state()
        print(f"Состояние восстановлено. Счетчик: {app.state['counter']}")
        return True
    return False

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global app
    if app:
        app.stop()

# Настройка обработчиков сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    global app

    # Создание приложения
    app = Application()

    # Проверка на перезапуск
    is_restart = "--restart" in sys.argv

    if is_restart:
        # Это перезапуск - восстанавливаем состояние
        if not load_application_state():
            print("Не удалось восстановить состояние, стартуем заново")
    else:
        # Первый запуск - настраиваем систему перезапуска
        restarter = ProcessRestarter(
            watch_paths=["example_app.py"],  # Файлы для отслеживания
            shutdown_timeout=5.0,
            restart_delay=0.5
        )

        restarter.set_callbacks(
            save_state_callback=save_application_state,
            load_state_callback=load_application_state,
            restart_command=[sys.executable] + sys.argv + ["--restart"]
        )

        restarter.start()
        print("Система перезапуска активирована")

    # Запуск основного цикла
    try:
        app.run()
    except KeyboardInterrupt:
        app.stop()

    print("Приложение завершено")

if __name__ == "__main__":
    main()
```

## Преимущества перед hot reload

### ✅ Решение проблем идентичности

**Hot reload проблемы:**
```python
# Проблема: объекты сохраняют старую идентичность
old_obj = SomeClass()
# После reload: id(old_obj) тот же, но поведение может измениться
# Вызывает неожиданные ошибки и race conditions
```

**Process restart решение:**
```python
# Решение: полный перезапуск с чистым состоянием
# Все объекты создаются заново
# Гарантированная консистентность
```

### ✅ Отсутствие висячих потоков

**Hot reload проблемы:**
- Потоки продолжают работать со старым кодом
- Невозможно корректно завершить фоновые задачи
- Race conditions между старым и новым кодом

**Process restart решение:**
- Все потоки корректно завершаются через GracefulShutdownManager
- Новые потоки создаются с новым кодом
- Полный контроль над жизненным циклом

### ✅ Предсказуемое поведение

**Hot reload проблемы:**
- Сложно предсказать, какие части системы обновятся
- Зависимости между модулями могут сломаться
- Кэши и глобальное состояние становятся неконсистентными

**Process restart решение:**
- Поведение идентично холодному запуску
- Все модули загружаются в правильном порядке
- Чистое состояние без остатков предыдущих запусков

## Производительность и надежность

### Метрики производительности

- **Время перезапуска:** 2-5 секунд (включая graceful shutdown)
- **Размер состояния:** < 1MB для типичного приложения
- **Накладные расходы:** Минимальны при нормальной работе

### Надежность

- **Атомарные операции:** Состояние сохраняется через временные файлы
- **Проверка целостности:** Валидация данных при загрузке
- **Graceful degradation:** Продолжение работы при ошибках сохранения/загрузки

## Ограничения и рекомендации

### Когда использовать

**Рекомендуется для:**
- Dev-режим с частыми изменениями
- Критичные к консистентности системы
- Системы с фоновыми потоками
- Приложения с комплексным состоянием

**Не рекомендуется для:**
- Production сред (используйте традиционное развертывание)
- Систем без сохранения состояния
- Приложений с долгим временем запуска

### Ограничения

1. **Требуется сериализуемое состояние**
   - Все сохраняемые объекты должны поддерживать JSON сериализацию
   - Или реализовывать методы `to_dict()` / `from_dict()`

2. **Перезапуск виден пользователю**
   - В отличие от seamless hot reload
   - Может быть заметен в логах и метриках

3. **Не подходит для real-time систем**
   - Кратковременное прерывание сервиса
   - Подходит для dev/staging, но не для production

## Интеграция в проект

### В main_server_api.py

```python
# Включение dev-mode с process restart
if args.dev:
    from src.dev.process_restarter import ProcessRestarter

    restarter = ProcessRestarter(
        watch_paths=[
            "src/main_server_api.py",
            "src/runtime/loop.py",
            "src/state/self_state.py",
            # ... другие файлы
        ]
    )

    restarter.set_callbacks(
        save_state_callback=lambda: save_app_state(),
        load_state_callback=lambda: load_app_state(),
        restart_command=[sys.executable] + sys.argv + ["--restart"]
    )

    if "--restart" in sys.argv:
        restarter.load_state_callback()
    else:
        restarter.start()
```

## Связанные документы

*   [main_server_api.py](../../src/main_server_api.py) — основное приложение с dev-режимом
*   [logging_config.py](../../src/logging_config.py) — система логирования
*   [ADR: Dev Mode Architecture](../adr/dev-mode-architecture.md) — архитектурные решения dev-режима
