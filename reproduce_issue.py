
import asyncio
import time
import json
from pathlib import Path
from nanobot.session.manager import Session, SessionManager

async def heartbeat():
    """Background task that expects to run every 10ms."""
    delays = []
    start_time = time.time()
    next_tick = start_time

    while True:
        now = time.time()
        delay = now - next_tick
        if delay > 0.005:  # If delayed by more than 5ms
            delays.append(delay)

        await asyncio.sleep(0.01)
        next_tick += 0.01

        # Stop after 2 seconds
        if now - start_time > 2.0:
            break

    return delays

async def main():
    # Setup
    workspace = Path("./benchmark_workspace")
    workspace.mkdir(exist_ok=True)
    manager = SessionManager(workspace)
    session = Session(key="benchmark:test")

    # Create a large session
    print("Generating large session...")
    for i in range(5000):
        session.add_message("user", f"This is message number {i} " * 10)
        session.add_message("assistant", f"This is response number {i} " * 10)

    print(f"Session ready. Messages: {len(session.messages)}")

    # Run heartbeat and save concurrently
    print("Starting save operation with heartbeat...")

    # Start heartbeat
    heartbeat_task = asyncio.create_task(heartbeat())

    # Wait a bit
    await asyncio.sleep(0.1)

    # Measure save time
    t0 = time.time()
    await manager.asave(session)
    t1 = time.time()
    print(f"Save took: {t1 - t0:.4f}s")

    # Wait for heartbeat to finish
    delays = await heartbeat_task

    max_delay = max(delays) if delays else 0
    print(f"Max heartbeat delay: {max_delay:.4f}s")

    # Cleanup
    import shutil
    shutil.rmtree(workspace)

if __name__ == "__main__":
    asyncio.run(main())
