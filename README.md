This README has been intentionally removed.

## Краткое описание

**Life** — это экспериментальный умный компаньон с непрерывной жизнью, наблюдением и API. Проект исследует концепцию длительного существования вычислительной системы, где процесс работает постоянно, накапливая состояние и историю, которая влияет на будущее поведение.

В отличие от традиционных приложений, Life не реагирует только на внешние запросы, а существует как непрерывный процесс с внутренними циклами обновления, деградацией и необратимыми изменениями. **Смерти нет — только слабость и бессилие**: система не завершается при критических значениях параметров, а продолжает функционировать в ослабленном состоянии, демонстрируя концепцию "жизни" через адаптацию к деградации.

## Структура проекта

```
life/
├── src/
│   ├── main_server_api.py    # Основной файл с API сервером и точкой входа
│   ├── main.py                # Устаревший файл, используется только для тестирования работоспособности кода
│   ├── runtime/
│   │   └── loop.py            # Runtime-цикл с обновлением состояния и обработкой событий
│   ├── state/
│   │   └── self_state.py      # Управление состоянием и snapshots
│   ├── monitor/
│   │   └── console.py         # Мониторинг и логирование
│   ├── environment/
│   │   ├── event.py           # [`Event`](src/environment/event.py) - структура события
│   │   ├── event_queue.py     # [`EventQueue`](src/environment/event_queue.py) - очередь событий (max 100)
│   │   ├── generator.py       # [`EventGenerator`](src/environment/generator.py) - генератор событий
│   │   └── generator_cli.py   # CLI для отправки событий на API
│   ├── meaning/
│   │   ├── meaning.py         # Структура интерпретации (Meaning)
│   │   └── engine.py          # Движок интерпретации (MeaningEngine)
│   ├── activation/            # Модуль активации памяти (этап 10.1, v1.0)
│   │   └── activation.py
│   ├── decision/              # Модуль принятия решений (этап 11.1, v1.0)
│   │   └── decision.py
│   ├── action/                # Модуль действий (этап 12.1, v1.0)
│   │   └── action.py
│   ├── intelligence/          # Модуль интеллекта (этап 18, v1.0)
│   │   └── intelligence.py
│   ├── planning/              # Модуль планирования (этап 17, v1.0)
│   │   └── planning.py
│   ├── memory/                # Модуль памяти (этап 09, v1.0)
│   │   └── memory.py
│   └── test/                  # Тесты (226 тестов, 96% покрытие)
│       ├── test_memory.py
│       ├── test_state.py
│       ├── test_activation.py
│       ├── test_meaning.py
│       ├── test_decision.py
│       ├── test_action.py
│       ├── test_environment.py
│       ├── test_feedback.py
│       ├── test_planning.py
│       ├── test_intelligence.py
│       ├── test_runtime_integration.py
│       ├── test_api_integration.py
│       ├── test_generator.py
│       ├── test_generator_integration.py
│       ├── test_monitor.py
│       └── ... (другие тесты)
├── docs/                      # Документация проекта
│   └── test/                  # Документация по тестированию
├── data/                      # Директория для данных (логи, snapshots)
├── .venv/                     # Виртуальное окружение Python
└── README.md                  # Этот файл
```

### Ключевые модули

- **`main_server_api.py`**: Основной сервер с HTTP API (`/status`, `/clear-data`, `/event`), потоками runtime и dev-режимом с авто-перезагрузкой.
- **`runtime/loop.py`**: Бесконечный цикл с тиками, обработкой событий из [`EventQueue`](src/environment/event_queue.py) и простой интерпретацией `_interpret_event`.
- **`state/self_state.py`**: Управление состоянием и snapshots (этап 03, описан в docs, реализация как dataclass планируется).
- **`monitor/console.py`**: Цветной консольный мониторинг и логи в `data/tick_log.jsonl`.
- **`environment/`** (этап 07, интегрирован):
  - [`event.py`](src/environment/event.py): [`Event`](src/environment/event.py) - `type`, `intensity:[-1..1]`, `timestamp`, `metadata`.
  - [`event_queue.py`](src/environment/event_queue.py): [`EventQueue`](src/environment/event_queue.py) - thread-safe очередь с `push/pop/pop_all`, maxsize=100.
  - [`generator.py`](src/environment/generator.py): [`EventGenerator`](src/environment/generator.py) - `generate()` с типами `noise/decay/recovery/shock/idle` (weights [0.4,0.3,0.2,0.05,0.05]), intensity ranges.
  - [`generator_cli.py`](src/environment/generator_cli.py): CLI `python -m environment.generator_cli --interval 5 --host localhost --port 8000`.
- **`meaning/`** (этап 08, реализован но не интегрирован):
  - [`meaning.py`](src/meaning/meaning.py): [`Meaning`](src/meaning/meaning.py) - `significance:[0..1]`, `impact:{energy/stability/integrity: delta}`.
  - [`engine.py`](src/meaning/engine.py): [`MeaningEngine`](src/meaning/engine.py) - `process(event, self_state) -> Meaning` через `appraisal/significance`, `impact_model`, `response_pattern` (ignore/absorb/dampen/amplify).
- **`activation/`** (этап 10.1, v1.0): Активация релевантных воспоминаний на основе типа текущего события.
- **`decision/`** (этап 11.1, v1.0): Принятие решения о паттерне реакции (ignore/absorb/dampen) на основе activated_memory и meaning.
- **`action/`** (этап 12.1, v1.0): Выполнение внутренних действий на основе принятого решения, с записью в память и минимальными эффектами на состояние.
- **`intelligence/`** (этап 18, v1.0): Минимальная обработка информации из нейтральных источников.
- **`planning/`** (этап 17, v1.0): Минимальная фиксация потенциальных последовательностей.
- **`memory/`** (этап 09, v2.0): Эпизодическая память с забыванием, архивацией и оптимизацией.
- **`learning/`** (этап 14, v1.0): Медленное обучение на основе статистики Memory.
- **`adaptation/`** (этап 15, v1.0): Медленная адаптация поведения на основе Learning.

## Текущий статус проекта

- **Этапы 00–02**: Документация стабилизирована (VISION, ARCHITECTURE, RUNTIME_LOOP с модульностью).
- **Этап 03**: SelfState реализован как dataclass с полями memory, intelligence, planning (v2.1 с валидацией).
- **Этапы 07–08**: Environment и MeaningEngine интегрированы в runtime loop.
- **Этап 09**: Memory v2.0 реализован с забыванием, архивацией и оптимизацией.
- **Этап 10.1**: Activation v1.0 реализован и интегрирован.
- **Этап 11.1**: Decision v1.0 реализован и интегрирован.
- **Этап 12.1**: Action v1.0 реализован и интегрирован (с интеграцией Learning/Adaptation).
- **Этап 13**: Feedback v1.1 реализован и интегрирован.
- **Этапы 17–18**: Planning и Intelligence v1.0 реализованы и интегрированы.
- **Этап 14**: Learning v1.0 реализован и интегрирован (медленное обучение на статистике).
- **Этап 15**: Adaptation v1.0 реализован и интегрирован (медленная адаптация поведения).
- **Архитектурные улучшения**: Lifecycle, Subjective Time, SelfState улучшения, Runtime Loop рефакторинг.

## Тестирование

Проект покрыт комплексными тестами:

- **Всего тестов:** 226+ (см. [docs/development/STATISTICS.md](docs/development/STATISTICS.md) для актуальной статистики)
- **Покрытие кода:** 96%
- **Все тесты проходят:** ✅

### Типы тестов

1. **Unit тесты** - изолированное тестирование отдельных функций и классов
2. **Integration тесты** - тестирование взаимодействия между модулями
3. **Property-based тесты** - автоматическая проверка инвариантов с помощью `hypothesis`
4. **Тесты производительности** - проверка производительности критических операций
5. **Нагрузочные тесты** - тестирование при больших объемах данных

### Быстрый запуск тестов

```bash
# Установка зависимостей для тестирования
pip install -r requirements.txt

# Запуск всех тестов
pytest src/test/ -v

# С покрытием кода
pytest src/test/ --cov=src --cov-report=html

# Только быстрые тесты (без slow и performance)
pytest src/test/ -v -m "not slow and not performance"

# Только тесты производительности
pytest src/test/ -v -m performance

# Property-based тесты
pytest src/test/test_property_based.py -v
```

### Новые тесты

- **`test_degradation.py`** - Тесты на деградацию системы, включая длительную работу (1000+ тиков)
- **`test_property_based.py`** - Property-based тесты для проверки инвариантов системы
- **`test_performance.py`** - Тесты производительности (benchmarks) критических операций
- **`test_memory.py`** - Расширен нагрузочными тестами для больших объемов данных

### Покрытие модулей

**Полностью покрытые модули (100%):**
- Все модули бизнес-логики (action, activation, adaptation, decision, feedback, intelligence, learning, meaning, memory, planning, state)
- API эндпоинты (GET /status, GET /clear-data, POST /event, аутентификация)
- Генератор событий (EventGenerator)
- Monitor (console.py)
- Environment (Event, EventQueue, Generator)

**Подробная документация:** [docs/testing/README.md](docs/testing/README.md)

## Установка

### Требования

- Python 3.10 или выше (рекомендуется 3.11+)

### Шаги установки

1. Клонируйте репозиторий:
   ```bash
   git clone <repository-url>
   cd life
   ```

2. Создайте виртуальное окружение:
   ```bash
   python -m venv .venv
   ```

3. Активируйте виртуальное окружение:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

4. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

   > **Примечание**: Проект использует стандартную библиотеку Python и несколько внешних зависимостей (fastapi, uvicorn, requests, colorama, pytest, pytest-cov, hypothesis для property-based тестов).

## Запуск

### Основной запуск

Запустите сервер с API и runtime-циклом:

```bash
python src/main_server_api.py --tick-interval 1.0 --snapshot-period 10
```

### Dev-режим

Для разработки с автоматической перезагрузкой при изменении кода:

```bash
python src/main_server_api.py --dev --tick-interval 1.0 --snapshot-period 10
```

В dev-режиме система отслеживает изменения в исходных файлах и автоматически перезагружает модули без остановки процесса.

## Конфигурация и параметры

Проект поддерживает следующие параметры командной строки:

- `--tick-interval` (float, по умолчанию 1.0): Интервал между тиками в секундах
- `--snapshot-period` (int, по умолчанию 10): Период сохранения snapshots (в тиках)
- `--clear-data` (str, по умолчанию "no"): Очистка данных при запуске ("yes" для очистки)
- `--dev`: Включение режима разработки с автоматической перезагрузкой

Примеры:

```bash
# Быстрый цикл с частыми snapshots
python src/main_server_api.py --tick-interval 0.5 --snapshot-period 5

# Очистка данных при старте
python src/main_server_api.py --clear-data yes
```

## API

Сервер предоставляет HTTP API на `http://localhost:8000`.

### Endpoints

#### GET /status

Возвращает текущее состояние системы в формате JSON.

**Пример запроса:**
```bash
curl http://localhost:8000/status
```

**Пример ответа:**
```json
{
  "active": true,
  "ticks": 150,
  "age": 150.2,
  "energy": 85.0,
  "stability": 0.95,
  "integrity": 0.98
}
```

#### GET /clear-data

Очищает все логи и snapshots. Полезно для сброса состояния системы.

**Пример запроса:**
```bash
curl http://localhost:8000/clear-data
```

**Ответ:** "Data cleared"

#### POST /event

Добавляет событие в очередь Environment.

**Тело запроса (JSON):**
```json
{
  "type": "noise",
  "intensity": 0.1,
  "timestamp": 1700000.0,
  "metadata": {"source": "manual"}
}
```

`intensity`, `timestamp`, `metadata` — опциональны. Если `timestamp` не передан, используется текущее время.

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"type":"shock","intensity":-0.5}'
```

**Ответ:** "Event accepted"

## Мониторинг

### Консольный вывод

Система выводит состояние в реальном времени в консоль в формате:
```
* [ticks] возраст: X.X сек. | энергия: X.X % | интеллект: X.XX | стабильность: X.XX | значимость: X.XX | активация: X (X.XX) | decision: pattern | action: executed pattern |
```

### Snapshots

Каждые `snapshot-period` тиков состояние сохраняется в JSON-файл в директории `data/snapshots/`. Файлы именуются как `snapshot_XXXXXX.json`, где XXXXXX - номер тика.

### Логирование

Все тики логируются в `data/tick_log.jsonl` в формате JSON Lines. Каждый тик - отдельная строка с полным состоянием.

## Особенности

### Горячая очистка данных

- Очистка логов и snapshots возможна как через API (`/clear-data`), так и параметром `--clear-data yes` при запуске
- Позволяет сбросить состояние без перезапуска процесса

### Надежный перезапуск API

- В dev-режиме API сервер автоматически перезапускается при изменении кода
- Runtime-цикл продолжает работать без прерываний

### Обработка ошибок

- Исключения в runtime-цикле уменьшают integrity системы
- Ошибки логируются с полным traceback
- Система продолжает работу даже при сбоях в отдельных компонентах

### Состояние системы

Life отслеживает следующие параметры состояния:

- **active**: Флаг активности (система всегда "жива", но может быть в состоянии слабости)
- **ticks**: Количество прошедших тиков
- **age**: Время жизни в секундах
- **energy**: Энергия (изменяется под влиянием событий среды, может падать до 0 и ниже)
- **stability**: Стабильность (изменяется под влиянием событий среды, может падать до 0 и ниже)
- **integrity**: Целостность (уменьшается при ошибках и событиях типа shock, может падать до 0 и ниже)
- **recent_events**: Список последних типов событий
- **last_significance**: Значимость последнего обработанного события
- **activated_memory**: Временный список активированных воспоминаний (не сохраняется в snapshots)
- **last_pattern**: Последний выбранный паттерн decision (не сохраняется в snapshots)
- **memory**: Список эпизодических воспоминаний (MemoryEntry)
- **planning**: Словарь с данными планирования
- **intelligence**: Словарь с данными интеллекта

**Смерти нет — только слабость и бессилие**: система не завершается при критических значениях параметров (<=0), а продолжает функционировать, демонстрируя адаптацию к деградации. Это отражает концепцию "жизни" через непрерывное существование в различных состояниях.

Эти параметры создают динамику, где прошлое влияет на будущее, делая систему "живой" в экспериментальном смысле.

### Environment (этап 07, интегрирован)

Life взаимодействует с [`EventQueue`](src/environment/event_queue.py), заполняемой через API `/event` или [`generator_cli.py`](src/environment/generator_cli.py).

**Типы событий** ([`EventGenerator`](src/environment/generator.py)):
- `noise` (40%): intensity `[-0.3, 0.3]` → stability
- `decay` (30%): `[-0.5, 0.0]` → energy
- `recovery` (20%): `[0.0, 0.5]` → energy
- `shock` (5%): `[-1.0, 1.0]` → integrity/stability
- `idle` (5%): `0.0` → ничего

**Обработка** в [`loop.py`](src/runtime/loop.py): `pop_all()` → `_interpret_event` (простая логика, без MeaningEngine).

### MeaningEngine (этап 08, реализован но не интегрирован)

[`MeaningEngine`](src/meaning/engine.py).`process(event, self_state) -> [`Meaning`](src/meaning/meaning.py)`:

1. **appraisal()**: significance = |intensity| * type_weight * state_modifiers ∈ [0,1]
2. **impact_model()**: base_deltas * |intensity| * significance для energy/stability/integrity
3. **response_pattern()**: "ignore" (<0.1), "dampen" (>stab0.8), "amplify" (<stab0.3), "absorb"
4. Применить паттерн к impact.

Готов к интеграции в loop.py вместо _interpret_event.

### Activation (этап 10.1, интегрирован)

Модуль активации памяти активирует релевантные воспоминания на основе типа текущего события. Возвращает топ-N воспоминаний с совпадающим event_type, отсортированных по significance (desc). Если совпадений нет — пустой список.

Интегрирован в loop.py: после process(event) активирует память и сохраняет в self_state.activated_memory.

### Decision (этап 11.1, интегрирован)

Модуль принятия решений выбирает паттерн реакции (ignore/absorb/dampen) на основе activated_memory и meaning. Если max sig в activated >0.5 — "dampen" (опыт учит смягчать), иначе fallback к Meaning's pattern.

Интегрирован в loop.py: после активации выбирает паттерн, сохраняет в self_state.last_pattern, применяет модификатор к impact если dampen.

### Action (этап 12.1, интегрирован)

Модуль действий выполняет внутренние эффекты на основе паттерна. Записывает действие в память, для "dampen" уменьшает энергию на 0.01 (минимальный эффект усталости).

Интегрирован в loop.py: после apply_delta вызывает execute_action(pattern).

### Генерация событий

Два способа создавать события:

1. **Через API** (ручное добавление):
   ```bash
   curl -X POST http://localhost:8000/event \
     -H "Content-Type: application/json" \
     -d '{"type":"noise","intensity":0.1}'
   ```

2. **Отдельный генератор в другом терминале** (периодическая отправка на API):
   ```bash
   python -m environment.generator_cli --interval 5 --host localhost --port 8000
   ```
   Интервал можно менять параметром `--interval` (секунды).

## Тестирование

### Запуск тестов

```bash
# Все тесты (unit, затем integration)
pytest src/test/ -v

# С покрытием кода
pytest src/test/ --cov=src --cov-report=html

# Только unit тесты (статические, не требуют сервер)
pytest src/test/ -m unit --cov=src --cov-report=html

# Только integration тесты
pytest src/test/ -m integration --cov=src --cov-report=html

# Конкретный модуль
pytest src/test/test_memory.py -v
```

### Тестирование с реальным сервером

Для тестирования на реальном запущенном сервере используйте опции `--real-server` и `--server-port`:

```bash
# 1. Запустите сервер в отдельном терминале
python src/main_server_api.py --dev --tick-interval 1.0 --snapshot-period 15

# 2. В другом терминале запустите тесты с опцией --real-server
pytest src/test/ --real-server --server-port 8000 --cov=src --cov-report=html

# Только тесты, которые могут работать с реальным сервером
pytest src/test/ -m "real_server" --real-server --server-port 8000
```

**Примечание:** Тесты с маркером `real_server` автоматически подключаются к реальному серверу при использовании `--real-server`. Без этой опции они используют тестовые серверы в отдельных потоках (текущее поведение по умолчанию).

### Отладка тестов (просмотр warnings и skipped)

Для просмотра причин пропущенных тестов и предупреждений:

```bash
# Показать причины skipped тестов (без warnings)
pytest src/test/ --real-server --server-port 8000 --cov=src --cov-report=html -rs

# Показать все warnings и причины skipped
# ВАЖНО: -W default обязателен для просмотра warnings (переопределяет --disable-warnings)
pytest src/test/ --real-server --server-port 8000 --cov=src --cov-report=html -W default -rs

# Максимальная детализация (все warnings + причины skipped)
pytest src/test/ --real-server --server-port 8000 --cov=src --cov-report=html -W default -rs -v

# Только warnings определенных типов
pytest src/test/ --real-server --server-port 8000 --cov=src --cov-report=html -W default::DeprecationWarning -W default::UserWarning -rs

# Показать только warnings (без skipped)
pytest src/test/ --real-server --server-port 8000 --cov=src --cov-report=html -W default
```

**Опции:**
- `-rs` - показать причины пропущенных (skipped) тестов (выводится в конце)
- `-W default` - **обязательно** для просмотра warnings (переопределяет `--disable-warnings` из `pytest.ini`)
- `-v` - подробный вывод

**Примечание:** Warnings выводятся **во время выполнения тестов**, а не в конце. Skipped тесты выводятся в конце с опцией `-rs`.

### Результаты тестирования

- **Всего тестов:** 226
- **Все проходят:** ✅
- **Покрытие кода:** 96%
- **Основные модули:** 100% покрытие

### Документация по тестированию

Подробная документация находится в [docs/testing/README.md](docs/testing/README.md):
- Инструкции по запуску тестов
- Описание всех тестовых файлов
- Руководство по написанию новых тестов
- Отчеты о покрытии кода
