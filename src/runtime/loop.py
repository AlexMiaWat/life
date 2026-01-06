import time
from state.self_state import save_snapshot
import traceback

def run_loop(self_state, monitor, tick_interval=1.0, snapshot_period=10, stop_event=None):
    
    last_time = time.time()
    while self_state['alive'] and (stop_event is None or not stop_event.is_set()):
        try:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # Обновление состояния
            self_state['ticks'] += 1
            self_state['age'] += dt
            self_state['energy'] -= 0.1
            self_state['stability'] -= 0.001

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
