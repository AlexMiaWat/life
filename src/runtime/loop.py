import time
from state.self_state import save_snapshot, SelfState
import traceback
from environment import Event
from planning.planning import record_potential_sequences
from intelligence.intelligence import process_information
from meaning.engine import MeaningEngine
from dataclasses import asdict
from memory.memory import MemoryEntry
from datetime import datetime
from activation.activation import activate_memory
from decision.decision import decide_response

def run_loop(self_state: SelfState, monitor, tick_interval=1.0, snapshot_period=10, stop_event=None, event_queue=None):
    """
    Runtime Loop с интеграцией Environment (этап 07)

    Args:
        self_state: Состояние Life
        monitor: Функция мониторинга
        tick_interval: Интервал между тиками
        snapshot_period: Периодичность snapshot
        stop_event: threading.Event для остановки
        event_queue: Очередь событий из Environment
    """
    engine = MeaningEngine()
    last_time = time.time()
    while (stop_event is None or not stop_event.is_set()):
        try:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # Обновление состояния
            self_state.apply_delta({'ticks': 1})
            self_state.apply_delta({'age': dt})

            # === ШАГ 1: Получить события из среды ===
            if event_queue and not event_queue.is_empty():
                print(f"[LOOP] Queue not empty, size={event_queue.size()}")
                events = event_queue.pop_all()
                print(f"[LOOP] POPPED {len(events)} events")

                # === ШАГ 2: Интерпретировать события ===
                for event in events:
                    print(f"[LOOP] Interpreting event: type={event.type}, intensity={event.intensity}")
                    meaning = engine.process(event, asdict(self_state))
                    if meaning.significance > 0:
                        # Активация памяти для события
                        activated = activate_memory(event.type, self_state.memory)
                        self_state.activated_memory = activated
                        print(f"[LOOP] Activated {len(activated)} memories for type '{event.type}'")

                        # Decision
                        pattern = decide_response(self_state, meaning)
                        self_state.last_pattern = pattern
                        if pattern == "ignore":
                            continue  # skip apply_delta
                        elif pattern == "dampen":
                            meaning.impact = {k: v * 0.5 for k, v in meaning.impact.items()}
                        # else "absorb" — no change

                        self_state.apply_delta(meaning.impact)
                        self_state.recent_events.append(event.type)
                        self_state.last_significance = meaning.significance
                        self_state.memory.append(MemoryEntry(event_type=event.type, meaning_significance=meaning.significance, timestamp=time.time()))
                    print(f"[LOOP] After interpret: energy={self_state.energy:.2f}, stability={self_state.stability:.4f}")

                record_potential_sequences(self_state)
                process_information(self_state)

            # Логика слабости: когда параметры низкие, добавляем штрафы за немощность
            weakness_threshold = 0.05
            if (self_state.energy <= weakness_threshold or
                self_state.integrity <= weakness_threshold or
                self_state.stability <= weakness_threshold):
                penalty = 0.02 * dt
                self_state.apply_delta({
                    'energy': -penalty,
                    'stability': -penalty * 2,
                    'integrity': -penalty * 2
                })
                print(f"[LOOP] Слабость: штрафы penalty={penalty:.4f}, energy={self_state.energy:.2f}")

            # Вызов мониторинга
            try:
                monitor(self_state)
            except Exception as e:
                print(f"Ошибка в monitor: {e}")
                traceback.print_exc()

            # Snapshot каждые snapshot_period тиков
            if self_state.ticks % snapshot_period == 0:
                try:
                    save_snapshot(self_state)
                except Exception as e:
                    print(f"Ошибка при сохранении snapshot: {e}")
                    traceback.print_exc()
     
            # Поддержка постоянного интервала тиков
            tick_end = time.time()
            elapsed_tick = tick_end - current_time
            sleep_duration = max(0.0, tick_interval - elapsed_tick)
            time.sleep(sleep_duration)

        except Exception as e:
            self_state.apply_delta({'integrity': -0.05})
            print(f"Ошибка в цикле: {e}")
            traceback.print_exc()

        finally:
            if (self_state.energy <= 0 or
                self_state.integrity <= 0 or
                self_state.stability <= 0):
                self_state.active = False

