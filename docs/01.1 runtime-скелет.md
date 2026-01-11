life/
├── docs/
│   ├── 00_VISION.md
│   ├── 01_ARCHITECTURE.md
│   ├── 01.1 runtime-скелет.md
│   ├── 02_RUNTIME_LOOP.md      ← цикл жизни
│   ├── 02.1 интерпретации.md
│   ├── 03_SELF_STATE.md        ← внутреннее состояние
│   ├── 04_MONITOR.md           ← система наблюдения
│   ├── 04.0 Pre_MONITOR.md
│   ├── 05_MINIMAL_IMPLEMENTATION.md
│   ├── 06_API_SERVER.md
│   ├── auto-reload-plan.md
│   ├── notes.md
│   └── README.md
│
├── src/
│   ├── main_server_api.py     ← точка входа с API и dev mode
│   ├── main.py                 ← тестовый запуск
│   ├── runtime/
│   │   └── loop.py             ← run_loop с tick_interval
│   │
│   ├── state/
│   │   ├── self_state.py       ← функции snapshot
│   │   └── self_state.py       ← save/load snapshot
│   │
│   ├── monitor/
│   │   └── console.py          ← monitor и log функции
│   │
│   └── utils/                  ← зарезервировано
│
├── data/
│   ├── tick_log.jsonl          ← JSON логи тиков
│   └── snapshots/              ← snapshot файлы
│       └── snapshot_XXXXXX.json
│
└── README.md
