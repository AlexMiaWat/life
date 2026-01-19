# 06_API_SERVER.md — API Сервер

## Назначение
API Server предоставляет HTTP интерфейс для управления системой Life и получения её состояния из внешних приложений.

## Текущий статус
✅ **Реализован** (v1.0)
*   Основной файл: [`src/main_server_api.py`](../../src/main_server_api.py)
*   API с аутентификацией: [`api.py`](../../api.py)
*   Фреймворк: FastAPI
*   Запускается в отдельном потоке (Daemon), параллельно с Runtime Loop

## Два варианта API

### 1. Основной API Server (`src/main_server_api.py`)

Основной API сервер для работы с Life системой.

**Endpoints:**

#### GET /status
Возвращает текущее состояние Life (Self-State).

**Ответ:**
```json
{
  "active": true,
  "ticks": 150,
  "age": 75.0,
  "energy": 95.5,
  "integrity": 1.0,
  "stability": 0.98
}
```

#### GET /clear-data
Очищает все накопленные данные (логи, снапшоты).
Полезно для сброса "памяти" между экспериментами без перезапуска сервера.

**Пример запроса:**
```bash
curl http://localhost:8000/clear-data
```

**Ответ:**
```json
"Data cleared"
```

#### POST /event
Отправляет событие в систему Life для обработки.

**Тело запроса:**
```json
{
  "type": "noise",
  "intensity": 0.1,
  "timestamp": 1704987654.321,
  "metadata": {
    "source": "manual",
    "description": "Тестовое событие"
  }
}
```

**Параметры:**
- `type` (string, required): Тип события (`noise`, `decay`, `recovery`, `shock`, `idle`)
- `intensity` (float, optional): Интенсивность события (-1.0 до 1.0)
- `timestamp` (float, optional): Временная метка (Unix timestamp)
- `metadata` (object, optional): Дополнительные данные

**Примеры запросов:**

1. **Простое событие:**
```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"type":"noise","intensity":0.5}'
```

2. **Событие с метаданными:**
```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"type":"shock","intensity":-0.8,"metadata":{"source":"test","reason":"experiment"}}'
```

**Ответ:**
```json
"Event accepted"
```

**Ошибки:**
- `400 Bad Request`: Неверный формат данных
- `422 Unprocessable Entity`: Неверные значения параметров

**Запуск:**
```bash
python src/main_server_api.py --tick-interval 0.5
```

*   Порт по умолчанию: `8000`
*   Документация API (Swagger): `http://localhost:8000/docs`

### 2. API с аутентификацией (`api.py`)

REST API с JWT токенами для аутентификации пользователей.

**Особенности:**
- JWT токены для аутентификации
- Регистрация и авторизация пользователей
- Защищенные endpoints
- Использует FastAPI с OAuth2

**Endpoints:**

#### POST /register
Регистрация нового пользователя.

**Запрос:**
```json
{
  "username": "user",
  "email": "user@example.com",
  "password": "password123",
  "full_name": "User Name"
}
```

**Пример запроса:**
```bash
curl -X POST "http://localhost:8001/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"test123","full_name":"Test User"}'
```

**Ответ (успех):**
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "Test User"
}
```

#### POST /token
Получение JWT токена для аутентификации.

**Запрос:**
```
username=user&password=password123
```

**Пример запроса:**
```bash
curl -X POST "http://localhost:8001/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### GET /users/me
Получение информации о текущем пользователе (требует аутентификации).

**Пример запроса:**
```bash
curl -X GET "http://localhost:8001/users/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Ответ:**
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "Administrator"
}
```

#### GET /protected
Пример защищенного endpoint (требует аутентификации).

**Пример запроса:**
```bash
curl -X GET "http://localhost:8001/protected" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Ответ:**
```json
{"message": "You are authenticated!"}
```

#### GET /status
Получение статуса системы Life (требует аутентификации).

**Пример запроса:**
```bash
curl -X GET "http://localhost:8001/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Ответ:**
```json
{
  "active": true,
  "ticks": 150,
  "age": 75.0,
  "energy": 95.5,
  "integrity": 1.0,
  "stability": 0.98
}
```

#### POST /event
Создание события в системе Life (требует аутентификации).

**Пример запроса:**
```bash
curl -X POST "http://localhost:8001/event" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"recovery","intensity":0.3,"metadata":{"source":"api"}}'
```

**Ответ:**
```json
{"message": "Event created successfully"}
```

**Запуск:**
```bash
python api.py
# или
uvicorn api:app --host 0.0.0.0 --port 8001
```

*   Порт по умолчанию: `8001`
*   Документация API (Swagger): `http://localhost:8001/docs`

**Тестовые пользователи:**
- `admin` / `admin123`
- `user` / `user123`

**Использование токена:**
```bash
# Получение токена
curl -X POST "http://localhost:8001/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Использование токена
curl -X GET "http://localhost:8001/protected" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Архитектура

Сервер работает в режиме "Sidecar" для Runtime Loop:
1.  Loop обновляет `Self-State` (словарь).
2.  API читает этот же словарь (по ссылке) и отдает клиенту.
3.  Благодаря GIL в Python, чтение атомарных значений безопасно, но для сложных структур может потребоваться блокировка (пока не реализована).

## Зависимости

Для API с аутентификацией требуются дополнительные зависимости:
- `python-jose[cryptography]>=3.3.0` — для JWT токенов
- `passlib[bcrypt]>=1.7.4` — для хеширования паролей
- `python-multipart>=0.0.6` — для OAuth2 форм

Все зависимости указаны в `requirements.txt`.
