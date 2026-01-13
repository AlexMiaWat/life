2026-01-13: Завершён слой 09_MEMORY v1.0. 
- Минимальная эпизодическая память (event_type + significance + timestamp). 
- Ограничение 50 записей. 
- Интеграция: append в loop после MeaningEngine. 
- Генерация событий остаётся внешней (CLI + API).
- 
2026-01-13: Завершён слой 10_ACTIVATION v1.0. 
- Минимальная активация по event_type + significance (top-3).
- Transient activated_memory, не сохраняется.
- Интеграция: После событий в loop.py.
- Риски: Очистка transient при load; перенести логи в monitor.