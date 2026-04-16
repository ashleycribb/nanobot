import asyncio
import json
import time
from pathlib import Path

# Create a dummy cursor file with a larger size to exaggerate the I/O blocking
cursor_path = Path("test_cursors.json")
data = {
    "cursors": {f"session_{i}": i for i in range(200000)}
}
cursor_path.write_text(json.dumps(data))

# A task that checks event loop responsiveness
async def event_loop_monitor(stop_event):
    max_delay = 0
    intervals = []
    while not stop_event.is_set():
        start = time.perf_counter()
        await asyncio.sleep(0.01)
        delay = time.perf_counter() - start - 0.01
        intervals.append(delay)
        if delay > max_delay:
            max_delay = delay
    print(f"Max event loop blocking delay: {max_delay:.4f}s")
    avg_delay = sum(intervals) / len(intervals) if intervals else 0
    print(f"Average event loop blocking delay: {avg_delay:.4f}s")
    return max_delay

async def test_sync_read():
    stop_event = asyncio.Event()
    monitor_task = asyncio.create_task(event_loop_monitor(stop_event))

    start = time.perf_counter()
    for _ in range(10):
        try:
            data = json.loads(cursor_path.read_text("utf-8"))
        except Exception:
            pass
        # small sleep to let monitor run between reads
        await asyncio.sleep(0)
    duration = time.perf_counter() - start

    stop_event.set()
    max_delay = await monitor_task
    print(f"Sync read total duration: {duration:.4f}s")
    return max_delay

async def test_async_read():
    stop_event = asyncio.Event()
    monitor_task = asyncio.create_task(event_loop_monitor(stop_event))

    start = time.perf_counter()
    for _ in range(10):
        try:
            text = await asyncio.to_thread(cursor_path.read_text, "utf-8")
            data = json.loads(text)
        except Exception:
            pass
        await asyncio.sleep(0)
    duration = time.perf_counter() - start

    stop_event.set()
    max_delay = await monitor_task
    print(f"Async read total duration: {duration:.4f}s")
    return max_delay

async def main():
    print("--- Sync Version ---")
    await test_sync_read()
    print("\n--- Async Version ---")
    await test_async_read()

    # Clean up
    cursor_path.unlink()

if __name__ == "__main__":
    asyncio.run(main())
