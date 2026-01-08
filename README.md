# Проект Life

## Краткое описание

**Life** — это экспериментальный умный компаньон с непрерывной жизнью, наблюдением и API. Проект исследует концепцию длительного существования вычислительной системы, где процесс работает постоянно, накапливая состояние и историю, которая влияет на будущее поведение.

В отличие от традиционных приложений, Life не реагирует только на внешние запросы, а существует как непрерывный процесс с внутренними циклами обновления, деградацией и необратимыми изменениями.

## Структура проекта

```
life/
├── src/
│   ├── main_server_api.py    # Основной файл с API сервером и точкой входа
│   ├── main.py                # Тестовый файл для проверки функциональности
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
│   └── meaning/
│       ├── meaning.py         # Структура интерпретации (Meaning)
│       └── engine.py           # Движок интерпретации (MeaningEngine)
├── docs/                      # Документация проекта
├── data/                      # Директория для данных (логи, snapshots)
├── .venv/                     # Виртуальное окружение Python
└── README.md                  # Этот файл
```

### Ключевые модули

- **`main_server_api.py`**: Основной сервер с HTTP API (`/status`, `/clear-data`, `/event`), потоками runtime и dev-режимом с авто-перезагрузкой.
- **`runtime/loop.py`**: Бесконечный цикл с тиками, обработкой событий из [`EventQueue`](src/environment/event_queue.py) и простой интерпретацией `_interpret_event`.
- **`state/self_state.py`**: Сохранение/загрузка snapshots в `data/snapshots/snapshot_XXXXXX.json`.
- **`monitor/console.py`**: Цветной консольный мониторинг и логи в `data/tick_log.jsonl`.
- **`environment/`** (этап 07, интегрирован):
  - [`event.py`](src/environment/event.py): [`Event`](src/environment/event.py) - `type`, `intensity:[-1..1]`, `timestamp`, `metadata`.
  - [`event_queue.py`](src/environment/event_queue.py): [`EventQueue`](src/environment/event_queue.py) - thread-safe очередь с `push/pop/pop_all`, maxsize=100.
  - [`generator.py`](src/environment/generator.py): [`EventGenerator`](src/environment/generator.py) - `generate()` с типами `noise/decay/recovery/shock/idle` (weights [0.4,0.3,0.2,0.05,0.05]), intensity ranges.
  - [`generator_cli.py`](src/environment/generator_cli.py): CLI `python -m environment.generator_cli --interval 5 --host localhost --port 8000`.
- **`meaning/`** (этап 08, реализован но не интегрирован):
  - [`meaning.py`](src/meaning/meaning.py): [`Meaning`](src/meaning/meaning.py) - `significance:[0..1]`, `impact:{energy/stability/integrity: delta}`.
  - [`engine.py`](src/meaning/engine.py): [`MeaningEngine`](src/meaning/engine.py) - `process(event, self_state) -> Meaning` через `appraisal/significance`, `impact_model`, `response_pattern` (ignore/absorb/dampen/amplify).

## Установка

### Требования

- Python 3.14 или выше

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

   > **Примечание**: Проект использует только стандартную библиотеку Python, поэтому файл requirements.txt может быть пустым или содержать только базовые зависимости.

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
  "alive": true,
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
• [ticks] age=X.Xs energy=X.X int=X.XX stab=X.XX
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

- **alive**: Флаг жизни (завершается при energy/integrity/stability <= 0)
- **ticks**: Количество прошедших тиков
- **age**: Время жизни в секундах
- **energy**: Энергия (изменяется под влиянием событий среды)
- **stability**: Стабильность (изменяется под влиянием событий среды)
- **integrity**: Целостность (уменьшается при ошибках и событиях типа shock)

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