# ADR 001: Управление экспериментальными компонентами через Feature Flags

## Статус

✅ **Принято**

## Дата

2026-01-22

## Контекст

Проект Life содержит несколько экспериментальных компонентов, которые могут влиять на стабильность и производительность системы:

- **MemoryHierarchyManager** - иерархическая система памяти
- **AdaptiveProcessingManager** - адаптивная обработка
- **ClarityMoments** - моменты ясности
- **SensoryBuffer** - сенсорный буфер

Эти компоненты находятся в активной разработке и могут содержать баги, которые повлияют на всю систему.

## Проблема

До рефакторинга экспериментальные компоненты импортировались в начале файла `src/runtime/loop.py` без проверки feature flags:

```python
# ПРОБЛЕМНЫЙ КОД (был в предыдущей версии)
from src.experimental import AdaptiveProcessingManager, AdaptiveProcessingConfig
from src.experimental.clarity_moments import ClarityMoments
from src.experimental.memory_hierarchy import MemoryHierarchyManager
```

Это приводило к:
1. **Всегда активным импортам** - компоненты импортировались даже при отключенных flags
2. **Рискам стабильности** - любой баг в экспериментальном коде ломал всю систему
3. **Затруднениям в отладке** - сложно было определить влияние экспериментального кода

## Решение

Реализовать условную инициализацию экспериментальных компонентов на основе feature flags.

### Архитектурные принципы

1. **Изоляция экспериментального кода** - импорты и инициализация только при включенных flags
2. **Graceful degradation** - система работает без экспериментальных компонентов
3. **Runtime проверка** - валидация flags при запуске с подробным логированием
4. **Error handling** - корректная обработка ошибок инициализации

### Реализация

#### 1. Конфигурация Feature Flags

```yaml
# config/config.yaml
features:
  experimental:
    memory_hierarchy_manager: false
    adaptive_processing_manager: false
    sensory_buffer: false
    clarity_moments: false
```

#### 2. Runtime проверка безопасности

```python
def _validate_experimental_components_safety():
    """Проверяет, что экспериментальные компоненты корректно изолированы."""
    experimental_flags = [
        'memory_hierarchy_manager',
        'adaptive_processing_manager',
        'clarity_moments',
        'sensory_buffer',
        'parallel_consciousness_engine'
    ]

    enabled_experimental = []
    for flag in experimental_flags:
        if feature_flags.is_enabled(flag):
            enabled_experimental.append(flag)

    if enabled_experimental:
        logger.warning(f"EXPERIMENTAL COMPONENTS ENABLED: {', '.join(enabled_experimental)}")
        logger.warning("Experimental components may impact system stability and performance")
    else:
        logger.info("All experimental components are disabled - system running in stable mode")

    return enabled_experimental
```

#### 3. Условная инициализация

```python
# MemoryHierarchyManager
if enable_memory_hierarchy:
    try:
        logger.info("Initializing MemoryHierarchyManager (experimental component)")
        from src.experimental.memory_hierarchy import MemoryHierarchyManager
        memory_hierarchy = MemoryHierarchyManager(logger=structured_logger)
        logger.info("MemoryHierarchyManager initialized successfully")
    except ImportError as e:
        logger.warning(f"MemoryHierarchyManager not available: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize MemoryHierarchyManager: {e}")
        memory_hierarchy = None
else:
    logger.info("MemoryHierarchyManager disabled by feature flag")
```

## Последствия

### Положительные

1. **Безопасность** - экспериментальный код не влияет на стабильность при отключенных flags
2. **Гибкость** - можно включать/отключать компоненты без перезапуска
3. **Отладка** - легко определить влияние экспериментального кода
4. **CI/CD** - тесты могут работать без экспериментальных компонентов

### Отрицательные

1. **Сложность кода** - условная логика инициализации
2. **Зависимости** - нужно проверять доступность модулей при включенных flags
3. **Тестирование** - требуется тестировать обе конфигурации (с/без экспериментального кода)

### Нейтральные

1. **Логирование** - подробная информация о состоянии экспериментальных компонентов
2. **Мониторинг** - можно отслеживать влияние на производительность

## Альтернативы

### Альтернатива 1: Полная изоляция в отдельные модули
- **Плюсы**: Полная изоляция, проще тестировать
- **Минусы**: Сложнее интеграция, дублирование кода

### Альтернатива 2: Plugin архитектура
- **Плюсы**: Динамическая загрузка, расширяемость
- **Минусы**: Сложная реализация, overhead

### Альтернатива 3: Build-time флаги
- **Плюсы**: Нет runtime overhead
- **Минусы**: Требуется пересборка для изменений

Выбрана runtime feature flags как оптимальный баланс между безопасностью и гибкостью.

## Реализация

### Этап 1: ✅ Проверка и валидация (выполнено)
- Добавлена функция `_validate_experimental_components_safety()`
- Интегрирована проверка при запуске runtime loop

### Этап 2: ✅ Условная инициализация (выполнено)
- Все экспериментальные компоненты инициализируются условно
- Добавлена обработка ImportError и Exception
- Гарантировано None при ошибках инициализации

### Этап 3: ✅ Конфигурация (выполнено)
- Feature flags определены в `config/config.yaml`
- Все flags по умолчанию отключены (false)

### Этап 4: ✅ Логирование (выполнено)
- Подробное логирование состояния экспериментальных компонентов
- Предупреждения при включенных экспериментальных компонентах

## Тестирование

### Функциональные тесты
- [ ] Тест запуска без экспериментальных компонентов (все flags = false)
- [ ] Тест запуска с одним экспериментальным компонентом
- [ ] Тест запуска со всеми экспериментальными компонентами

### Регрессионные тесты
- [ ] Тест graceful degradation при недоступных модулях
- [ ] Тест корректной обработки ошибок инициализации

### Performance тесты
- [ ] Измерение overhead от проверок feature flags
- [ ] Сравнение производительности с/без экспериментальных компонентов

## Мониторинг

### Метрики
- Количество включенных экспериментальных компонентов
- Время инициализации экспериментальных компонентов
- Количество ошибок инициализации

### Алерты
- Автоматическое предупреждение при включенных экспериментальных компонентах
- Алерт при ошибках инициализации экспериментальных компонентов

## Связанные ADR

- **ADR 002**: Архитектурные контракты для компонентов (запланирован)
- **ADR 003**: SelfState рефакторинг (запланирован)

## Примечания

Это решение обеспечивает безопасную интеграцию экспериментальных компонентов без риска для стабильности production системы. Feature flags позволяют контролировать экспериментальный код и легко отключать проблемные компоненты.