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

#### POST /event (Планируется)
Позволит отправлять события в Environment через HTTP.

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

#### POST /token
Получение JWT токена для аутентификации.

**Запрос:**
```
username=user&password=password123
```

**Ответ:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

#### GET /users/me
Получение информации о текущем пользователе (требует аутентификации).

#### GET /protected
Пример защищенного endpoint (требует аутентификации).

#### GET /status
Получение статуса системы (требует аутентификации).

#### POST /event
Создание события (требует аутентификации).

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
