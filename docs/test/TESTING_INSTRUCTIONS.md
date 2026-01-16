# Инструкции по тестированию

## Обзор

Проект Life покрыт комплексными тестами для всех разработанных модулей. Тесты написаны с использованием pytest и организованы по модулям.

## Структура тестов

Все тесты находятся в директории `src/test/`:

- `test_memory.py` - Тесты модуля Memory (MemoryEntry, Memory)
- `test_state.py` - Тесты модуля State (SelfState, snapshots)
- `test_activation.py` - Тесты модуля Activation
- `test_meaning.py` - Тесты модуля Meaning (Meaning, MeaningEngine)
- `test_decision.py` - Тесты модуля Decision
- `test_action.py` - Тесты модуля Action
- `test_environment.py` - Тесты модуля Environment (Event, EventQueue)
- `test_feedback.py` - Тесты модуля Feedback
- `test_planning.py` - Тесты модуля Planning
- `test_intelligence.py` - Тесты модуля Intelligence
- `test_runtime_integration.py` - Интеграционные тесты для Runtime Loop
- `test_api.py` - Базовые тесты API сервера
- `test_api_integration.py` - Интеграционные тесты API сервера с запуском сервера
- `test_generator.py` - Тесты генератора событий
- `test_generator_integration.py` - Интеграционные тесты генератора с сервером
- `test_generator_cli.py` - Тесты CLI генератора
- `test_monitor.py` - Тесты модуля Monitor
- `test_runtime_loop_edge_cases.py` - Edge cases Runtime Loop
- `test_runtime_loop_feedback_coverage.py` - Тесты обработки Feedback в Loop
- `test_event_queue_edge_cases.py` - Edge cases EventQueue
- `test_event_queue_race_condition.py` - Race conditions в EventQueue

## Установка зависимостей

Убедитесь, что установлены все необходимые зависимости:

```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

## Запуск тестов

### Запуск всех тестов

```bash
# Из корневой директории проекта
pytest src/test/

# Или с более подробным выводом
pytest src/test/ -v

# С покрытием кода
pytest src/test/ --cov=src --cov-report=html
```

### Запуск конкретного модуля тестов

```bash
# Тесты для модуля Memory
pytest src/test/test_memory.py -v

# Тесты для модуля State
pytest src/test/test_state.py -v

# Тесты для модуля Feedback
pytest src/test/test_feedback.py -v

# Интеграционные тесты API сервера
pytest src/test/test_api_integration.py -v

# Тесты генератора событий
pytest src/test/test_generator.py -v

# Интеграционные тесты генератора с сервером
pytest src/test/test_generator_integration.py -v

# Тесты Monitor
pytest src/test/test_monitor.py -v

# Edge cases Runtime Loop
pytest src/test/test_runtime_loop_edge_cases.py -v
```

### Запуск конкретного теста

```bash
# По имени класса
pytest src/test/test_memory.py::TestMemoryEntry -v

# По имени функции
pytest src/test/test_memory.py::TestMemoryEntry::test_memory_entry_creation -v
```

### Запуск с фильтрацией

```bash
# Только unit тесты
pytest src/test/ -m unit

# Только integration тесты
pytest src/test/ -m integration

# Пропустить медленные тесты
pytest src/test/ -m "not slow"
```

## Описание тестов по модулям

### Memory (test_memory.py)

**Тестируемые компоненты:**
- `MemoryEntry` - запись в памяти
- `Memory` - контейнер памяти с автоматическим ограничением размера

**Основные тесты:**
- Создание записей с разными параметрами
- Работа с feedback_data
- Автоматическое ограничение размера (clamp_size)
- Сохранение порядка элементов (FIFO)
- Операции со списком

**Количество тестов:** ~15

### State (test_state.py)

**Тестируемые компоненты:**
- `SelfState` - состояние Life
- `save_snapshot()` - сохранение снимков
- `load_snapshot()` - загрузка снимков
- `load_latest_snapshot()` - загрузка последнего снимка

**Основные тесты:**
- Инициализация состояния
- Применение дельт к параметрам (energy, integrity, stability)
- Ограничения значений (0-100 для energy, 0-1 для integrity/stability)
- Сохранение и загрузка снимков
- Работа с памятью в снимках

**Количество тестов:** ~20

### Activation (test_activation.py)

**Тестируемые компоненты:**
- `activate_memory()` - активация памяти по типу события

**Основные тесты:**
- Активация при пустой памяти
- Фильтрация по типу события
- Сортировка по significance (по убыванию)
- Ограничение количества результатов (limit)
- Работа с разными типами событий

**Количество тестов:** ~12

### Meaning (test_meaning.py)

**Тестируемые компоненты:**
- `Meaning` - интерпретированное значение события
- `MeaningEngine` - движок интерпретации
  - `appraisal()` - оценка значимости
  - `impact_model()` - модель влияния
  - `response_pattern()` - паттерн реакции
  - `process()` - полный процесс обработки

**Основные тесты:**
- Валидация significance
- Оценка значимости для разных типов событий
- Влияние интенсивности на значимость
- Модель влияния для разных типов событий
- Определение паттернов реакции
- Полный процесс обработки события

**Количество тестов:** ~25

### Decision (test_decision.py)

**Тестируемые компоненты:**
- `decide_response()` - выбор паттерна реакции

**Основные тесты:**
- Выбор "dampen" при высокой significance в памяти
- Выбор "ignore" при низкой significance
- Выбор "absorb" при нормальных условиях
- Работа с пустой активированной памятью
- Обработка нескольких активированных воспоминаний

**Количество тестов:** ~12

### Action (test_action.py)

**Тестируемые компоненты:**
- `execute_action()` - выполнение действия

**Основные тесты:**
- Выполнение разных паттернов (dampen, absorb, ignore)
- Эффект dampen на energy
- Запись действий в память
- Работа с неизвестными паттернами
- Сохранение других параметров состояния

**Количество тестов:** ~12

### Environment (test_environment.py)

**Тестируемые компоненты:**
- `Event` - событие из среды
- `EventQueue` - очередь событий

**Основные тесты:**
- Создание событий с разными параметрами
- Работа с metadata
- Добавление и извлечение событий (FIFO)
- Метод pop_all()
- Обработка переполнения очереди

**Количество тестов:** ~20

### Feedback (test_feedback.py)

**Тестируемые компоненты:**
- `register_action()` - регистрация действия
- `observe_consequences()` - наблюдение последствий
- `PendingAction` - ожидающее действие
- `FeedbackRecord` - запись обратной связи

**Основные тесты:**
- Регистрация действий
- Наблюдение последствий с изменениями
- Игнорирование минимальных изменений
- Таймаут действий (20 тиков)
- Обработка нескольких действий
- Интеграция с Memory

**Количество тестов:** ~10

### Planning (test_planning.py)

**Тестируемые компоненты:**
- `record_potential_sequences()` - запись потенциальных последовательностей

**Основные тесты:**
- Запись последовательностей из recent_events
- Работа с пустыми данными
- Запись источников данных
- Сохранение других полей состояния

**Количество тестов:** ~10

### Intelligence (test_intelligence.py)

**Тестируемые компоненты:**
- `process_information()` - обработка информации

**Основные тесты:**
- Обработка информации из разных источников
- Работа с пустыми данными
- Обработка разных значений параметров
- Сохранение других полей состояния

**Количество тестов:** ~10

### Runtime Integration (test_runtime_integration.py)

**Тестируемые компоненты:**
- `run_loop()` - основной цикл выполнения

**Основные тесты:**
- Выполнение тиков цикла
- Обработка событий
- Регистрация действий для Feedback
- Обновление состояния
- Остановка по stop_event
- Создание снимков
- Штрафы за слабость
- Деактивация при нулевых параметрах

**Количество тестов:** ~10

### API Integration (test_api_integration.py)

**Тестируемые компоненты:**
- HTTP API сервер (с запуском в отдельном потоке)
- Все эндпоинты: GET /status, GET /clear-data, POST /event

**Основные тесты:**
- GET /status - получение состояния
- GET /clear-data - очистка данных
- POST /event - отправка событий
- Валидация входных данных
- Обработка ошибок
- Переполнение очереди

**Количество тестов:** 15

### Generator (test_generator.py)

**Тестируемые компоненты:**
- `EventGenerator` - генератор событий
- `send_event()` - отправка событий на сервер

**Основные тесты:**
- Генерация всех типов событий
- Проверка диапазонов интенсивности
- Распределение типов событий
- Обработка ошибок соединения

**Количество тестов:** 16

### Generator Integration (test_generator_integration.py)

**Тестируемые компоненты:**
- Интеграция генератора с API сервером
- Полный цикл: генерация -> отправка -> получение

**Основные тесты:**
- Отправка сгенерированных событий на сервер
- Множественные события
- Все типы событий
- Проверка диапазонов интенсивности
- Полный цикл работы

**Количество тестов:** 5

## Покрытие кода

Для проверки покрытия кода тестами:

```bash
# Генерация HTML отчета
pytest src/test/ --cov=src --cov-report=html

# Отчет в консоли
pytest src/test/ --cov=src --cov-report=term-missing

# Минимальный порог покрытия (80%)
pytest src/test/ --cov=src --cov-report=term-missing --cov-fail-under=80
```

Отчет будет доступен в `htmlcov/index.html`.

## Отладка тестов

### Запуск с выводом print

```bash
pytest src/test/ -v -s
```

### Запуск с остановкой на первой ошибке

```bash
pytest src/test/ -x
```

### Запуск с подробным traceback

```bash
pytest src/test/ -v --tb=long
```

### Запуск конкретного теста с отладкой

```bash
# Использование pdb
pytest src/test/test_memory.py::TestMemoryEntry::test_memory_entry_creation --pdb
```

## Написание новых тестов

### Структура теста

```python
import pytest
from module import function

class TestFunction:
    """Тесты для функции function"""
    
    def test_basic_case(self):
        """Тест базового случая"""
        result = function(param1, param2)
        assert result == expected_value
    
    def test_edge_case(self):
        """Тест граничного случая"""
        result = function(edge_param)
        assert result is not None
```

### Фикстуры

```python
@pytest.fixture
def base_state():
    """Создает базовое состояние"""
    return SelfState()

def test_with_fixture(base_state):
    """Тест с использованием фикстуры"""
    assert base_state.energy == 100.0
```

### Параметризация

```python
@pytest.mark.parametrize("value,expected", [
    (0.0, 0.0),
    (0.5, 0.5),
    (1.0, 1.0)
])
def test_values(value, expected):
    assert process(value) == expected
```

## Лучшие практики

1. **Именование тестов**: Используйте описательные имена, которые объясняют, что тестируется
2. **Один тест - одна проверка**: Каждый тест должен проверять одну конкретную функциональность
3. **Изоляция**: Тесты не должны зависеть друг от друга
4. **Фикстуры**: Используйте фикстуры для подготовки данных
5. **Очистка**: Убедитесь, что тесты не оставляют побочных эффектов
6. **Граничные случаи**: Тестируйте граничные значения и крайние случаи
7. **Отрицательные тесты**: Тестируйте обработку ошибок и невалидных данных

## Непрерывная интеграция

Тесты можно интегрировать в CI/CD пайплайн:

```yaml
# Пример для GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-cov
    pytest src/test/ --cov=src --cov-report=xml
```

## Решение проблем

### Проблема: Импорты не работают

**Решение:** Убедитесь, что путь к `src` добавлен в `sys.path` в начале каждого тестового файла.

### Проблема: Тесты падают из-за временных файлов

**Решение:** Используйте `tmp_path` фикстуру pytest для временных файлов.

### Проблема: Тесты зависят от порядка выполнения

**Решение:** Убедитесь, что каждый тест изолирован и не зависит от состояния других тестов.

## Контакты

При возникновении вопросов или проблем с тестами, обратитесь к документации проекта или создайте issue.
