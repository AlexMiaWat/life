# Ручное тестирование Feedback данных

## Быстрая проверка

### Шаг 1: Запустите сервер

В первом терминале:

```bash
cd d:\Space\life
python src/main_server_api.py --dev --tick-interval 1.0 --snapshot-period 15
```

Дождитесь сообщения: `API server running on http://localhost:8000`

### Шаг 2: Запустите генератор событий

Во втором терминале:

```bash
cd d:\Space\life
python -m src.environment.generator_cli --interval 1 --host localhost --port 8000
```

### Шаг 3: Подождите 20-30 секунд

Feedback записи создаются через 3-10 тиков после выполнения действий. Подождите достаточно времени.

### Шаг 4: Проверьте через API

В третьем терминале или через браузер:

```bash
curl http://localhost:8000/status
```

Или используйте Python скрипт:

```python
import requests
import json

response = requests.get("http://localhost:8000/status")
data = response.json()

# Фильтруем Feedback записи с данными
feedback = [m for m in data.get("memory", [])
            if m.get("event_type") == "feedback"
            and m.get("feedback_data")]

print(f"Found {len(feedback)} feedback records with data")

if feedback:
    print("\nSample record:")
    print(json.dumps(feedback[0], indent=2))
```

### Шаг 5: Проверьте структуру данных

Убедитесь, что в `feedback_data` присутствуют:

- ✅ `action_id` - строка вида "action_{ticks}_{pattern}_{timestamp}"
- ✅ `action_pattern` - "dampen", "absorb" или "ignore"
- ✅ `state_delta` - словарь с ключами "energy", "stability", "integrity"
- ✅ `delay_ticks` - число от 3 до 10
- ✅ `associated_events` - список (может быть пустым)

## Ожидаемый результат

После ожидания 20-30 секунд вы должны увидеть Feedback записи с полной структурой:

```json
{
  "event_type": "feedback",
  "meaning_significance": 0.0,
  "timestamp": 1768562354.7200325,
  "feedback_data": {
    "action_id": "action_503_dampen_1768562344123",
    "action_pattern": "dampen",
    "state_delta": {
      "energy": -0.01,
      "stability": 0.0,
      "integrity": 0.0
    },
    "delay_ticks": 5,
    "associated_events": []
  }
}
```

## Проверка через snapshots

После того как система проработает некоторое время, проверьте snapshots:

```bash
# Найти последний snapshot
ls -lt data/snapshots/*.json | head -1

# Проверить Feedback записи в snapshot
python -c "
import json
with open('data/snapshots/snapshot_000720.json') as f:
    data = json.load(f)
    feedback = [m for m in data.get('memory', [])
                if m.get('event_type')=='feedback' and m.get('feedback_data')]
    print(f'Feedback records with data in snapshot: {len(feedback)}')
    if len(feedback) > 0:
        print('\nSample:')
        print(json.dumps(feedback[0], indent=2))
"
```

## Критерии успеха

✅ **Найдены Feedback записи с `feedback_data`**
- Поле `feedback_data` присутствует
- Все необходимые поля заполнены

✅ **Структура данных корректна**
- `action_id` - строка
- `action_pattern` - один из: "dampen", "absorb", "ignore"
- `state_delta` - словарь с числовыми значениями
- `delay_ticks` - число от 3 до 10

✅ **Данные сохраняются в snapshots**
- Feedback записи с полными данными присутствуют в snapshots

## Возможные проблемы

### Нет Feedback записей

**Причина:** Система только что запустилась, еще не прошло достаточно тиков.

**Решение:** Подождите еще 15-20 секунд.

### Feedback записи без `feedback_data`

**Причина:** Записи были созданы до исправления кода.

**Решение:** Это нормально для старых записей. Новые записи будут содержать полные данные.

### Сервер не отвечает

**Причина:** Сервер не запущен или порт занят.

**Решение:**
1. Проверьте, что сервер запущен
2. Проверьте, что порт 8000 свободен
3. Попробуйте перезапустить сервер

## Автоматическая проверка

Используйте скрипт `check_feedback_data.py`:

```bash
python check_feedback_data.py
```

Скрипт автоматически:
1. Подключается к серверу
2. Проверяет наличие Feedback записей с данными
3. Выводит структуру данных
4. Проверяет наличие всех необходимых полей
