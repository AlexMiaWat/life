import random
import time
from typing import Any

from .event import Event


class EventGenerator:
    def generate(self) -> Event:
        """
        Генерирует событие согласно спецификации этапа 07.

        Диапазоны интенсивности:
        - noise: [-0.3, 0.3]
        - decay: [-0.5, 0.0]
        - recovery: [0.0, 0.5]
        - shock: [-1.0, 1.0]
        - idle: 0.0
        - memory_echo: [-0.2, 0.2] (внутренняя генерация)
        - social_presence: [-0.4, 0.4] (социальное присутствие)
        - social_conflict: [-0.6, 0.0] (социальный конфликт)
        - social_harmony: [0.0, 0.6] (социальная гармония)
        - cognitive_doubt: [-0.5, 0.0] (когнитивное сомнение)
        - cognitive_clarity: [0.0, 0.5] (когнитивная ясность)
        - cognitive_confusion: [-0.4, 0.0] (когнитивная путаница)
        - existential_void: [-0.7, 0.0] (экзистенциальная пустота)
        - existential_purpose: [0.0, 0.7] (экзистенциальное ощущение цели)
        - existential_finitude: [-0.6, 0.0] (осознание конечности)
        - connection: [0.0, 0.8] (ощущение связи с другими)
        - isolation: [-0.7, 0.0] (ощущение изоляции, одиночества)
        - insight: [0.0, 0.6] (момент озарения, понимания)
        - confusion: [-0.5, 0.0] (состояние замешательства, непонимания)
        - curiosity: [-0.3, 0.4] (интерес, желание узнать больше)
        - meaning_found: [0.0, 0.9] (ощущение нахождения смысла)
        - void: [-0.8, 0.0] (ощущение пустоты, отсутствия содержания)
        - acceptance: [0.0, 0.5] (принятие текущего состояния)
        - silence: [-0.4, 0.6] (осознание тишины - комфортная или тревожная)
        """
        types = [
            "noise",
            "decay",
            "recovery",
            "shock",
            "idle",
            "memory_echo",
            "social_presence",
            "social_conflict",
            "social_harmony",
            "cognitive_doubt",
            "cognitive_clarity",
            "cognitive_confusion",
            "existential_void",
            "existential_purpose",
            "existential_finitude",
            "connection",
            "isolation",
            "insight",
            "confusion",
            "curiosity",
            "meaning_found",
            "void",
            "acceptance",
            "silence",
        ]
        weights = [
            0.347,  # noise (скорректирован для учета нового типа silence)
            0.241,  # decay (скорректирован для учета нового типа silence)
            0.178,  # recovery (скорректирован для учета нового типа silence)
            0.039,  # shock (скорректирован для учета нового типа silence)
            0.039,  # idle (скорректирован для учета нового типа silence)
            0.0,  # memory_echo (генерируется только внутренне)
            0.014,  # social_presence (скорректирован для учета нового типа silence)
            0.010,  # social_conflict (скорректирован для учета нового типа silence)
            0.010,  # social_harmony (скорректирован для учета нового типа silence)
            0.014,  # cognitive_doubt (скорректирован для учета нового типа silence)
            0.010,  # cognitive_clarity (скорректирован для учета нового типа silence)
            0.014,  # cognitive_confusion (скорректирован для учета нового типа silence)
            0.007,  # existential_void (скорректирован для учета нового типа silence)
            0.006,  # existential_purpose (скорректирован для учета нового типа silence)
            0.008,  # existential_finitude (скорректирован для учета нового типа silence)
            0.007,  # connection (скорректирован для учета нового типа silence)
            0.007,  # isolation (скорректирован для учета нового типа silence)
            0.007,  # insight (скорректирован для учета нового типа silence)
            0.007,  # confusion (скорректирован для учета нового типа silence)
            0.007,  # curiosity (скорректирован для учета нового типа silence)
            0.007,  # meaning_found (скорректирован для учета нового типа silence)
            0.007,  # void (скорректирован для учета нового типа silence)
            0.007,  # acceptance (скорректирован для учета нового типа silence)
            0.005,  # silence (низкая вероятность, генерируется преимущественно детектором)
        ]
        event_type = random.choices(types, weights=weights)[0]

        # Генерируем интенсивность согласно спецификации
        if event_type == "noise":
            intensity = random.uniform(-0.3, 0.3)
        elif event_type == "decay":
            intensity = random.uniform(-0.5, 0.0)
        elif event_type == "recovery":
            intensity = random.uniform(0.0, 0.5)
        elif event_type == "shock":
            intensity = random.uniform(-1.0, 1.0)
        elif event_type == "memory_echo":
            intensity = random.uniform(
                -0.2, 0.2
            )  # Мягкое влияние для внутренних воспоминаний
        elif event_type == "social_presence":
            intensity = random.uniform(
                -0.4, 0.4
            )  # Может быть как комфортным, так и тревожным
        elif event_type == "social_conflict":
            intensity = random.uniform(-0.6, 0.0)  # Конфликт всегда негативен
        elif event_type == "social_harmony":
            intensity = random.uniform(0.0, 0.6)  # Гармония всегда положительна
        elif event_type == "cognitive_doubt":
            intensity = random.uniform(-0.5, 0.0)  # Сомнение всегда негативно
        elif event_type == "cognitive_clarity":
            intensity = random.uniform(0.0, 0.5)  # Ясность всегда положительна
        elif event_type == "cognitive_confusion":
            intensity = random.uniform(-0.4, 0.0)  # Путаница всегда негативна
        elif event_type == "existential_void":
            intensity = random.uniform(-0.7, 0.0)  # Пустота всегда негативна
        elif event_type == "existential_purpose":
            intensity = random.uniform(0.0, 0.7)  # Цель всегда положительна
        elif event_type == "existential_finitude":
            intensity = random.uniform(-0.6, 0.0)  # Осознание конечности тревожно
        elif event_type == "connection":
            intensity = random.uniform(0.0, 0.8)  # Ощущение связи всегда положительно
        elif event_type == "isolation":
            intensity = random.uniform(-0.7, 0.0)  # Изоляция всегда негативна
        elif event_type == "insight":
            intensity = random.uniform(0.0, 0.6)  # Озарение всегда положительно
        elif event_type == "confusion":
            intensity = random.uniform(-0.5, 0.0)  # Замешательство всегда негативно
        elif event_type == "curiosity":
            intensity = random.uniform(
                -0.3, 0.4
            )  # Любопытство может быть как положительным, так и отрицательным
        elif event_type == "meaning_found":
            intensity = random.uniform(
                0.0, 0.9
            )  # Нахождение смысла всегда положительно
        elif event_type == "void":
            intensity = random.uniform(-0.8, 0.0)  # Пустота всегда негативна
        elif event_type == "acceptance":
            intensity = random.uniform(0.0, 0.5)  # Принятие всегда положительно
        elif event_type == "silence":
            intensity = random.uniform(
                -0.4, 0.6
            )  # Тишина может быть комфортной (положительной) или тревожной (отрицательной)
        else:  # idle
            intensity = 0.0

        timestamp = time.time()
        metadata: dict[str, Any] = {}
        return Event(
            type=event_type, intensity=intensity, timestamp=timestamp, metadata=metadata
        )
