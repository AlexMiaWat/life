# Architecture Decision Records (ADR)

Этот каталог содержит Architecture Decision Records - документы, фиксирующие важные архитектурные решения проекта Life.

## Формат ADR

Каждый ADR следует структуре:

```
# ADR {номер}: {Название решения}

## Статус
{Proposed | Accepted | Deprecated | Superseded}

## Контекст
{Описание проблемы или ситуации}

## Решение
{Описание принятого решения}

## Последствия
{Положительные и отрицательные последствия решения}

## Связанные ADR
{Ссылки на связанные решения}
```

## Категории решений

### Архитектурные принципы
- [ADR 001](001-architectural-principles.md) - Основные архитектурные принципы
- [ADR 002](002-composition-over-inheritance.md) - Композиция вместо наследования

### Компоненты системы
- [ADR 003](003-event-generator-decomposition.md) - Декомпозиция EventGenerator
- [ADR 004](004-self-state-composition.md) - Композиция SelfState
- [ADR 005](005-feature-flags-integration.md) - Интеграция Feature Flags

### Качество кода
- [ADR 006](006-architectural-contracts.md) - Архитектурные контракты
- [ADR 007](007-testing-strategy.md) - Стратегия тестирования

## Процесс принятия решений

1. **Предложение**: Создание ADR в статусе "Proposed"
2. **Обсуждение**: Ревью и обсуждение с командой
3. **Принятие**: Изменение статуса на "Accepted" с датой
4. **Внедрение**: Реализация решения в коде
5. **Документирование**: Обновление документации

## Инструменты

- Шаблон ADR: `docs/adr/templates/adr-template.md`
- Генератор ADR: `scripts/generate_adr.py`
- Валидатор ADR: `scripts/validate_adr.py`