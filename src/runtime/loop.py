import time

def run_loop(self_state, monitor):
    last_time = time.time()
    while self_state['alive']:
        try:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            self_state['ticks'] += 1
            self_state['age'] += dt
            self_state['energy'] -= 0.1
            self_state['stability'] -= 0.001
            monitor(self_state)
            tick_end = time.time()
            elapsed_tick = tick_end - current_time
            sleep_duration = max(0.0, 1.0 - elapsed_tick)
            time.sleep(sleep_duration)
        except Exception as e:
            self_state['integrity'] -= 0.05
            print(f"Ошибка в цикле: {e}")
        finally:
            if (self_state['energy'] <= 0 or
                self_state['integrity'] <= 0 or
                self_state['stability'] <= 0):
                self_state['alive'] = False
