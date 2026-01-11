import time
from state.self_state import save_snapshot
import traceback
from environment import Event
from planning.planning import record_potential_sequences
from intelligence.intelligence import process_information

def run_loop(self_state, monitor, tick_interval=1.0, snapshot_period=10, stop_event=None, event_queue=None):
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
    last_time = time.time()
    while self_state['alive'] and (stop_event is None or not stop_event.is_set()):
        try:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # Обновление состояния
            self_state['ticks'] += 1
            self_state['age'] += dt

            # === ШАГ 1: Получить события из среды ===
            if event_queue and not event_queue.is_empty():
                print(f"[LOOP] Queue not empty, size={event_queue.size()}")
                events = event_queue.pop_all()
                print(f"[LOOP] POPPED {len(events)} events")

                # === ШАГ 2: Интерпретировать события ===
                for event in events:
                    print(f"[LOOP] Interpreting event: type={event.type}, intensity={event.intensity}")
                    _interpret_event(event, self_state)
                    print(f"[LOOP] After interpret: energy={self_state['energy']:.2f}, stability={self_state['stability']:.4f}")
                    self_state['recent_events'].append(event.type)

                record_potential_sequences(self_state)
                process_information(self_state)

            # Вызов мониторинга
            try:
                monitor(self_state)
            except Exception as e:
                print(f"Ошибка в monitor: {e}")
                traceback.print_exc()

            # Snapshot каждые snapshot_period тиков
            if self_state['ticks'] % snapshot_period == 0:
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
            self_state['integrity'] -= 0.05
            print(f"Ошибка в цикле: {e}")
            traceback.print_exc()

        finally:
            if (self_state['energy'] <= 0 or 
                self_state['integrity'] <= 0 or 
                self_state['stability'] <= 0):
                self_state['alive'] = False

def _interpret_event(event: Event, self_state: dict) -> None:
    """
    Интерпретирует событие и изменяет self_state.
    
    Логика интерпретации — минимальная для старта (этап 07):
    - noise: слегка влияет на stability
    - decay: снижает energy
    - recovery: восстанавливает energy
    - shock: влияет на integrity и stability
    - idle: ничего не делает
    
    Args:
        event: Event из Environment
        self_state: Состояние Life
    """
    event_type = event.type
    intensity = event.intensity
    
    if event_type == 'noise':
        # Шум влияет на стабильность
        self_state['stability'] += intensity * 0.01
    
    elif event_type == 'decay':
        # Износ снижает энергию (intensity отрицательная)
        self_state['energy'] += intensity
    
    elif event_type == 'recovery':
        # Восстановление повышает энергию
        self_state['energy'] += intensity
    
    elif event_type == 'shock':
        # Шок влияет на integrity и stability
        self_state['integrity'] += intensity * 0.1
        self_state['stability'] += intensity * 0.05
    
    elif event_type == 'idle':
        # Ничего не делаем при idle
        pass
    
    # Ограничиваем значения в допустимых пределах
    self_state['energy'] = max(0.0, min(100.0, self_state['energy']))
    self_state['stability'] = max(0.0, min(1.0, self_state['stability']))
    self_state['integrity'] = max(0.0, min(1.0, self_state['integrity']))
