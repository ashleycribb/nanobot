import asyncio
import json
import time
from pathlib import Path

# Create a dummy cursor file
cursor_path = Path("test_cursors.json")
data = {
    "cursors": {f"session_{i}": i for i in range(10000)}
}
cursor_path.write_text(json.dumps(data))

async def test_sync_read():
    start = time.perf_counter()
    for _ in range(100):
        try:
            data = json.loads(cursor_path.read_text("utf-8"))
        except Exception:
            pass
    duration = time.perf_counter() - start
    print(f"Sync read duration: {duration:.4f}s")
    return duration

async def test_async_read():
    start = time.perf_counter()
    for _ in range(100):
        try:
            text = await asyncio.to_thread(cursor_path.read_text, "utf-8")
            data = json.loads(text)
        except Exception:
            pass
    duration = time.perf_counter() - start
    print(f"Async read duration: {duration:.4f}s")
    return duration

async def main():
    await test_sync_read()
    await test_async_read()

    # Clean up
    cursor_path.unlink()

if __name__ == "__main__":
    asyncio.run(main())
