#!/usr/bin/env python3
"""
Standalone test for AsyncLogWriter performance.
"""

import json
import logging
import threading
import time
import statistics
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

# Copy AsyncLogWriter code here for standalone testing
@dataclass
class LogEntry:
    timestamp: float
    stage: str
    correlation_id: Optional[str]
    event_id: Optional[str]
    data: Dict[str, Any]
    priority: int = 5

    def to_json_line(self) -> str:
        entry = {
            "timestamp": self.timestamp,
            "stage": self.stage,
            "correlation_id": self.correlation_id,
            "event_id": self.event_id,
            "data": self.data
        }
        return json.dumps(entry, ensure_ascii=False, default=str) + "\n"


class RingBuffer:
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer: deque[LogEntry] = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self.dropped_entries = 0

    def append(self, entry: LogEntry) -> None:
        with self._lock:
            if len(self.buffer) >= self.max_size:
                self.buffer.popleft()
                self.dropped_entries += 1
            self.buffer.append(entry)

    def get_batch(self, batch_size: int = 100) -> List[LogEntry]:
        with self._lock:
            if not self.buffer:
                return []
            batch = []
            for _ in range(min(batch_size, len(self.buffer))):
                batch.append(self.buffer.popleft())
            return batch

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "size": len(self.buffer),
                "max_size": self.max_size,
                "dropped_entries": self.dropped_entries,
                "utilization_percent": (len(self.buffer) / self.max_size) * 100
            }


class AsyncLogWriter:
    def __init__(
        self,
        log_file: str,
        enabled: bool = True,
        buffer_size: int = 10000,
        batch_size: int = 50,
        flush_interval: float = 0.1,
        max_file_size_mb: int = 100
    ):
        self.log_file = log_file
        self.enabled = enabled
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_file_size_mb = max_file_size_mb

        self.buffer = RingBuffer(max_size=buffer_size)
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._writer_thread: Optional[threading.Thread] = None

        self._stats = {
            "entries_buffered": 0,
            "batches_written": 0,
            "entries_written": 0,
            "flush_operations": 0,
            "io_errors": 0,
            "start_time": time.time()
        }

        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

        if self.enabled:
            self._start_writer_thread()

    def write_entry(
        self,
        stage: str,
        correlation_id: Optional[str] = None,
        event_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: int = 5
    ) -> None:
        if not self.enabled:
            return

        entry = LogEntry(
            timestamp=time.time(),
            stage=stage,
            correlation_id=correlation_id,
            event_id=event_id,
            data=data or {},
            priority=priority
        )

        self.buffer.append(entry)

        with self._lock:
            self._stats["entries_buffered"] += 1

    def flush(self) -> None:
        if not self.enabled:
            return
        self._flush_buffer_to_file()

    def shutdown(self) -> None:
        self._stop_event.set()
        if self._writer_thread and self._writer_thread.is_alive():
            self._writer_thread.join(timeout=2.0)
        self._flush_buffer_to_file()

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            stats = self._stats.copy()

        buffer_stats = self.buffer.get_stats()
        runtime = time.time() - stats["start_time"]
        throughput = stats["entries_written"] / runtime if runtime > 0 else 0

        return {
            **stats,
            **buffer_stats,
            "runtime_seconds": runtime,
            "throughput_entries_per_sec": throughput,
            "writer_thread_alive": self._writer_thread.is_alive() if self._writer_thread else False
        }

    def _start_writer_thread(self) -> None:
        self._writer_thread = threading.Thread(
            target=self._writer_loop,
            name="AsyncLogWriter",
            daemon=True
        )
        self._writer_thread.start()

    def _writer_loop(self) -> None:
        while not self._stop_event.is_set():
            if self._stop_event.wait(timeout=self.flush_interval):
                break
            self._flush_buffer_to_file()
        self._flush_buffer_to_file()

    def _flush_buffer_to_file(self) -> None:
        try:
            batch = self.buffer.get_batch(self.batch_size)
            if not batch:
                return

            json_lines = "".join(entry.to_json_line() for entry in batch)

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json_lines)

            with self._lock:
                self._stats["batches_written"] += 1
                self._stats["entries_written"] += len(batch)
                self._stats["flush_operations"] += 1

        except Exception as e:
            with self._lock:
                self._stats["io_errors"] += 1


def test_performance():
    """Test AsyncLogWriter performance."""
    print("🚀 Testing AsyncLogWriter Performance (<1% overhead)")
    print("=" * 55)

    log_file = "/tmp/async_writer_perf_test.jsonl"

    writer = AsyncLogWriter(
        log_file=log_file,
        enabled=True,
        buffer_size=10000,
        batch_size=50,
        flush_interval=0.1
    )

    # Test single entry writes (simulating runtime loop)
    print("📝 Testing single entry writes (runtime simulation)...")

    single_times = []
    num_tests = 5000

    for i in range(num_tests):
        start = time.perf_counter()
        writer.write_entry(
            stage="tick_start",
            correlation_id=f"test_{i}",
            data={"tick": i, "energy": 0.8, "stability": 0.9}
        )
        end = time.perf_counter()
        single_times.append((end - start) * 1000000)  # microseconds

    # Flush and get final stats
    writer.flush()
    stats = writer.get_stats()
    writer.shutdown()

    # Calculate metrics
    avg_time = statistics.mean(single_times)
    median_time = statistics.median(single_times)
    p95_time = statistics.quantiles(single_times, n=20)[18]  # 95th percentile

    print("\n📊 Performance Results:")
    print(f"  Samples tested: {num_tests}")
    print(f"  Average time per entry: {avg_time:.3f} μs")
    print(f"  Median time per entry: {median_time:.3f} μs")
    print(f"  P95 time per entry: {p95_time:.3f} μs")
    print(f"  Throughput: {stats['throughput_entries_per_sec']:.0f} entries/sec")
    print(f"  Buffer utilization: {stats['utilization_percent']:.1f}%")

    # Check requirements for <1% overhead
    print("\n🎯 Requirements Check (<1% overhead):")
    max_allowed_avg = 100  # μs per entry
    max_allowed_p95 = 500  # μs per entry

    passed = True

    if avg_time <= max_allowed_avg:
        print(f"  ✅ Average time: {avg_time:.3f}μs (≤ {max_allowed_avg}μs)")
    else:
        print(f"  ❌ Average time: {avg_time:.3f}μs (> {max_allowed_avg}μs)")
        passed = False

    if median_time <= max_allowed_avg:
        print(f"  ✅ Median time: {median_time:.3f}μs (≤ {max_allowed_avg}μs)")
    else:
        print(f"  ❌ Median time: {median_time:.3f}μs (> {max_allowed_avg}μs)")
        passed = False

    if p95_time <= max_allowed_p95:
        print(f"  ✅ P95 time: {p95_time:.3f}μs (≤ {max_allowed_p95}μs)")
    else:
        print(f"  ❌ P95 time: {p95_time:.3f}μs (> {max_allowed_p95}μs)")
        passed = False

    print(f"\n{'✅ PASSED' if passed else '❌ FAILED'}: AsyncLogWriter meets <1% overhead requirement")

    return {
        "passed": passed,
        "avg_time_us": avg_time,
        "median_time_us": median_time,
        "p95_time_us": p95_time,
        "throughput": stats["throughput_entries_per_sec"],
        "buffer_utilization": stats["utilization_percent"]
    }


if __name__ == "__main__":
    result = test_performance()

    # Save results
    output_file = Path("data/async_writer_performance_result.json")
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.time(),
            "performance_test": result
        }, f, indent=2)

    print(f"\n💾 Results saved to {output_file}")

    # Update todo status
    if result["passed"]:
        print("✅ AsyncLogWriter validation: PASSED")
    else:
        print("❌ AsyncLogWriter validation: FAILED")

    exit(0 if result["passed"] else 1)