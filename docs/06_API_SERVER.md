# 06_API_SERVER.md

## Цель шага

Создать Life Server с HTTP API, который позволяет:

* Запускать жизнь в непрерывном режиме без остановки
* Горячо наблюдать текущее состояние Self-State
* Горячо очищать логи и snapshot без перезапуска
* Управлять параметрами запуска (tick_interval, snapshot_period, очистка данных)
* Включать dev mode с auto-reload для разработки

Архитектура
life/
└── src/
    ├── main_server_api.py        # Новый API сервер
    ├── main_server.py            # Старый server без API
    ├── runtime/
    │   └── loop.py               # Основной loop жизни
    ├── state/
    │   ├── self_state.py         # Определение self_state
    │   └── self_snapshot.py      # Snapshot и load_snapshot
    └── monitor/
        └── console.py            # Мониторинг и лог

Потоки

Основной поток — выполняет run_loop и обновляет Self-State

API поток (daemon) — поднимает HTTP сервер, обслуживает запросы /status и /clear-data

Конфигурация запуска

Параметры запуска через argparse:

Аргумент	Тип/По умолчанию	Описание
--clear-data	str, "no"	Очистка логов и snapshot перед стартом (yes/no)
--tick-interval	float, 1.0	Интервал тика, сек
--snapshot-period	int, 10	Периодичность snapshot (в тиках)

Пример запуска сервера:

python src/main_server_api.py --clear-data yes --tick-interval 1.0 --snapshot-period 10

HTTP API
Endpoint	Метод	Действие
/status	GET	Возвращает текущее Self-State в JSON
/clear-data	GET	Очищает лог data/tick_log.jsonl и все snapshot-файлы

Пример запроса:

curl http://localhost:8000/status
curl http://localhost:8000/clear-data

Особенности реализации

Жизнь продолжается непрерывно, API работает в отдельном потоке

Мониторинг через консоль остаётся прежним — вывод обновляется в одной строке

Snapshot продолжает фиксироваться по заданной периодичности (snapshot_period)

Горячая очистка данных возможна через /clear-data без остановки сервера

## Dev Mode и Auto-Reload

Dev mode включает автоматическую перезагрузку модулей при изменении кода:

* отслеживает изменения в src/*.py файлах
* перезагружает модули с importlib.reload
* перезапускает API сервер и Runtime Loop
* позволяет разрабатывать без остановки жизни

Запуск с dev mode:

```
python src/main_server_api.py --dev
```

## Интеграция с проектом

* API сервер запускается в daemon-потоке
* Runtime Loop в отдельном потоке
* Self-State передается по ссылке для синхронного доступа
* Логика run_loop не меняется, snapshot вызывается как раньше

Последующие шаги

Добавить новые endpoints, например:

Изменение tick_interval во время работы

Изменение snapshot_period

Введение событий/среды (events/environment)

Визуализатор состояния через веб или графики по JSON log

---

## См. также

* [05_MINIMAL_IMPLEMENTATION.md](05_MINIMAL_IMPLEMENTATION.md) — базовая реализация
* [01_ARCHITECTURE.md](01_ARCHITECTURE.md) — архитектура системы

Документировать все новые endpoints в отдельном модуле doc