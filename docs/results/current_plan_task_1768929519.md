# План выполнения: Добавить в `SelfState` поля субъективного времени и коэффициенты модуляции

> **Задача:** "Добавить в `SelfState` поля субъективного времени (например `subjective_age`/`subjective_time`) и коэффициенты модуляции"
> **Дата создания:** 2026-01-20
> **ID:** task_1768929519

## 1. Анализ текущего состояния

Из анализа кода проекта установлено:

### Уже реализованное:
- ✅ Поле `subjective_time: float = 0.0` в `SelfState`
- ✅ Коэффициенты модуляции субъективного времени:
  - `subjective_time_base_rate: float = 1.0`
  - `subjective_time_rate_min: float = 0.1`
  - `subjective_time_rate_max: float = 3.0`
  - `subjective_time_intensity_coeff: float = 1.0`
  - `subjective_time_stability_coeff: float = 0.5`
  - `last_event_intensity: float = 0.0`
- ✅ Функции расчета субъективного времени в `src/runtime/subjective_time.py`
- ✅ Интеграция в runtime loop (`src/runtime/loop.py`)
- ✅ Тесты для субъективного времени (`src/test/test_subjective_time.py`)

### Что требует добавления:
- ❌ Поле `subjective_age` как alias/property к `subjective_time`
- ❌ Возможное поле `physical_age` как alias к `age` (для симметрии)
- ❌ Дополнительные коэффициенты модуляции (если требуются)

## 2. План реализации

### 2.1. Добавить property `subjective_age` в `SelfState`

```python
@property
def subjective_age(self) -> float:
    """Alias for subjective_time - accumulated subjective time in seconds."""
    return self.subjective_time

@subjective_age.setter
def subjective_age(self, value: float) -> None:
    """Set subjective_time via subjective_age alias."""
    self.subjective_time = value
```

### 2.2. Добавить property `physical_age` в `SelfState` (опционально)

```python
@property
def physical_age(self) -> float:
    """Alias for age - physical time in seconds."""
    return self.age

@physical_age.setter
def physical_age(self, value: float) -> None:
    """Set age via physical_age alias."""
    self.age = value
```

### 2.3. Проверить и обновить валидацию

Убедиться, что валидация в `_validate_field` корректно обрабатывает новые поля:
- `subjective_time` уже валидируется как неотрицательное поле
- Коэффициенты модуляции валидируются в `_validate_field`

### 2.4. Обновить тесты

Добавить тесты в `src/test/test_state.py`:
- Проверка работы property `subjective_age`
- Проверка работы property `physical_age` (если добавляется)
- Проверка, что изменения через alias обновляют базовое поле

### 2.5. Проверить snapshot-совместимость

Убедиться, что:
- Новые property не сериализуются в snapshot (только базовые поля)
- Загрузка старых snapshots работает корректно
- Property работают после загрузки snapshot

## 3. Критерии приемки

- ✅ Поле `subjective_age` работает как alias к `subjective_time`
- ✅ Поле `physical_age` работает как alias к `age` (если добавляется)
- ✅ Все тесты проходят
- ✅ Snapshot-совместимость сохранена
- ✅ Валидация работает корректно

## 4. Риски и mitigation

### Риск: Нарушение обратной совместимости
**Mitigation:** Property не добавляют новые поля в dataclass, только удобные алиасы

### Риск: Проблемы с сериализацией
**Mitigation:** Property не сериализуются в snapshot, только базовые поля

### Риск: Конфликты в тестах
**Mitigation:** Добавить интеграционные тесты для проверки работы алиасов

---

**Автор плана:** AI Agent (Project Executor)