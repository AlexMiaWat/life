# Заметки по проекту life

## HTTP API

| Endpoint    | Метод | Действие |
|-------------|-------|----------|
| /status     | GET   | Возвращает текущее Self-State в JSON |
| /clear-data | GET   | Очищает лог data/tick_log.jsonl и все snapshot-файлы |
| /event      | POST  | Инъекция события в EventQueue: {"type": "str" (req), "intensity": float (opt=0.0), "timestamp": float (opt=time.time()), "metadata": dict (opt={})} |

Пример запроса:

```bash
curl http://localhost:8000/status
curl http://localhost:8000/clear-data
curl -X POST http://localhost:8000/event \\
  -H "Content-Type: application/json" \\
  -d '{"type": "noise", "intensity": 0.5}'
```

## Запуск

Базовый:
```bash
python src/main_server_api.py
```

С параметрами:
```bash
python src/main_server_api.py --tick-interval 0.5 --snapshot-period 20 --clear-data yes
```

Dev mode:
```bash
python src/main_server_api.py --dev
```

## Структура состояния

```json
{
  "active": true,
  "ticks": 100,
  "age": 100.5,
  "energy": 95.0,
  "stability": 0.95,
  "integrity": 0.98
}
```

## Мониторинг

Консоль: `• [ticks] age=Xs energy=X int=X stab=X`

Логи: `data/tick_log.jsonl`

Snapshot: `data/snapshots/snapshot_XXXXXX.json`


## Генерация событий - запуск сервера:
python -m src.environment.generator_cli --interval 1 --host localhost --port 8000

Либо через curl Api