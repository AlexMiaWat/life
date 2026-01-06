HTTP API
Endpoint	Метод	Действие
/status	GET	Возвращает текущее Self-State в JSON
/clear-data	GET	Очищает лог data/tick_log.jsonl и все snapshot-файлы

Пример запроса:

curl http://localhost:8000/status
curl http://localhost:8000/clear-data