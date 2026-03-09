import asyncio
import time
import os
import tempfile
from pathlib import Path

def _resolve_path(path: str, allowed_dir: Path | None = None) -> Path:
    """Resolve path and optionally enforce directory restriction."""
    resolved = Path(path).expanduser().resolve()
    if allowed_dir and not str(resolved).startswith(str(allowed_dir.resolve())):
        raise PermissionError(f"Path {path} is outside allowed directory {allowed_dir}")
    return resolved

def _read_sync_old(path: str, allowed_dir: Path | None) -> str:
    file_path = _resolve_path(path, allowed_dir)
    if not file_path.exists():
        return f"Error: File not found: {path}"
    if not file_path.is_file():
        return f"Error: Not a file: {path}"

    return file_path.read_text(encoding="utf-8")

async def execute_old(path: str, allowed_dir: Path | None = None) -> str:
    try:
        file_path = _resolve_path(path, allowed_dir)
        if not file_path.exists():
            return f"Error: File not found: {path}"
        if not file_path.is_file():
            return f"Error: Not a file: {path}"

        content = await asyncio.to_thread(file_path.read_text, encoding="utf-8")
        return content
    except PermissionError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

async def execute_new(path: str, allowed_dir: Path | None = None) -> str:
    try:
        return await asyncio.to_thread(_read_sync_old, path, allowed_dir)
    except PermissionError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

async def benchmark_read():
    with tempfile.TemporaryDirectory() as td:
        tf = os.path.join(td, "test_file.txt")
        # Ensure it takes enough time to block significantly
        content = "A" * (1024 * 1024 * 50) # 50MB
        with open(tf, "w") as f:
            f.write(content)

        # Benchmark old
        print("Benchmarking OLD...")

        async def sleeper():
            st = time.time()
            await asyncio.sleep(0.0)
            return time.time() - st

        async def benchmark_iteration_old():
            t1 = asyncio.create_task(execute_old(tf))
            t2 = asyncio.create_task(sleeper())
            await t1
            return await t2

        delays = []
        for _ in range(5):
            delays.append(await benchmark_iteration_old())
        print(f"Old delays: {delays}, Avg: {sum(delays)/len(delays):.4f}s")

        # Wait a bit
        await asyncio.sleep(1)

        # Benchmark new
        print("\nBenchmarking NEW...")

        async def benchmark_iteration_new():
            t1 = asyncio.create_task(execute_new(tf))
            t2 = asyncio.create_task(sleeper())
            await t1
            return await t2

        delays = []
        for _ in range(5):
            delays.append(await benchmark_iteration_new())
        print(f"New delays: {delays}, Avg: {sum(delays)/len(delays):.4f}s")

if __name__ == "__main__":
    asyncio.run(benchmark_read())
