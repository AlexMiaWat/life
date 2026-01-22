# Архитектура системы наблюдаемости

## Реальная архитектура: Активное структурированное логирование

**Архитектурное решение (2026-01-22):** Система Life использует **АКТИВНУЮ** архитектуру наблюдаемости, где StructuredLogger полностью интегрирован в runtime цикл и активно логирует ключевые стадии обработки для анализа и отладки.

### Принципы активной архитектуры

1. **Интеграция в runtime**: StructuredLogger вызывается на каждом тике runtime loop
2. **Структурированные события**: JSONL формат с correlation_id для трассировки цепочек
3. **Ключевые стадии**: Логирование event → meaning → decision → action → feedback
4. **Оптимизация производительности**: Batch-запись, буферизация, асинхронные операции

### Компоненты активной архитектуры

#### StructuredLogger ⭐ **ОСНОВНОЙ КОМПОНЕНТ**
**Файл:** `src/observability/structured_logger.py`

Основной компонент активного логирования:
- Интегрирован в `src/runtime/loop.py`
- Логирует каждый 10-й тик по умолчанию
- Использует JSONL формат для эффективного хранения
- Поддерживает correlation_id для связывания событий
- **Единственный компонент, данные которого анализируются**

#### AsyncLogWriter
**Файл:** `src/observability/async_log_writer.py`

Асинхронный writer для минимального влияния на производительность:
- Batch-запись по 50 записей
- Буфер 10000 записей в памяти
- Flush каждые 100ms
- <1% overhead на runtime

#### Устаревшие компоненты (рекомендуется удалить)
- **PassiveDataSink**: Получает данные из runtime, но результаты не используются
- **AsyncDataSink**: Получает данные из runtime, но результаты не используются
- **RuntimeAnalysisEngine**: Создает фоновые потоки, признан как часть активной архитектуры

#### Runtime интеграция

```python
# В src/runtime/loop.py
structured_logger.log_tick_start(self_state.ticks, queue_size)
# ... обработка тика ...
structured_logger.log_event({"stage": "event", "data": event_data})
structured_logger.log_event({"stage": "meaning", "data": meaning_data})
structured_logger.log_event({"stage": "decision", "data": decision_data})
structured_logger.log_tick_end(tick_duration_ms)
```

### Архитектурные границы

#### ✅ Допустимые паттерны

1. **Активное логирование в runtime**
   ```python
   structured_logger.log_event({"stage": "custom_stage", "correlation_id": chain_id})
   ```

2. **Оптимизированные вызовы**
   ```python
   # Batch логирование для снижения overhead
   structured_logger.log_events_batch([event1, event2, event3])
   ```

#### ❌ Запрещенные паттерны

1. **Пассивное наблюдение** - система не поддерживает пассивные компоненты
2. **Блокирующие операции** - все логирование асинхронное
3. **Синхронный I/O** - только асинхронная запись

### Производительность

- **Накладные расходы**: ~14.9 мс среднее на тик (медиана 9.76 мс)
- **Формат**: JSONL для эффективного парсинга
- **Хранение**: Оптимизировано для больших объемов данных

### Конфигурация

```python
structured_logger = StructuredLogger(
    log_tick_interval=10,      # Каждый 10-й тик
    enable_detailed_logging=False,  # Для production
    buffer_size=10000,         # Буфер в памяти
    batch_size=50,            # Batch-запись
    flush_interval=0.1         # Flush каждые 100ms
)
```

### История архитектурных решений

#### ❌ Старая пассивная архитектура (2025-2026)
- UnifiedObservationAPI (удален как мертвый код)
- PassiveDataSink (не использовался)
- AsyncObservationAPI (удален как мертвый код)
- Ложные заявления о "пассивности"

#### ✅ Текущая активная архитектура (2026+)
- StructuredLogger интегрирован в runtime
- Активное логирование ключевых стадий
- Оптимизированная производительность
- Четкая документация реальной архитектуры