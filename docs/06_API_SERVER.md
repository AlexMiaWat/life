06_API_SERVER.md
Цель шага

Создать Life Server с HTTP API, который позволяет:

Запускать жизнь в непрерывном режиме без остановки

Горячо наблюдать текущее состояние Self-State

Горячо очищать логи и snapshot без перезапуска

Управлять параметрами запуска (tick_interval, snapshot_period, очистка данных)

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

Интеграция с проектом

Подключить API сервер в main_server_api.py через threading.Thread(target=start_api_server, args=(self_state,), daemon=True).start()

Передавать текущий self_state в сервер, чтобы API мог возвращать актуальное состояние и управлять очисткой

Логика run_loop не меняется, snapshot вызывается как раньше

Последующие шаги

Добавить новые endpoints, например:

Изменение tick_interval во время работы

Изменение snapshot_period

Введение событий/среды (events/environment)

Визуализатор состояния через веб или графики по JSON log

Документировать все новые endpoints в отдельном модуле doc