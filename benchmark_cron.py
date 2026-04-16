import asyncio
import time
from pathlib import Path
from nanobot.cron.service import CronService
from nanobot.cron.types import CronSchedule, CronJob, CronPayload, CronJobState

async def mock_on_job(job: CronJob):
    await asyncio.sleep(0.1) # Simulate some network/IO work
    return "done"

async def run_benchmark():
    store_path = Path("test_cron_bench.json")
    if store_path.exists():
        store_path.unlink()

    service = CronService(store_path, on_job=mock_on_job)

    # Add 20 jobs
    schedule = CronSchedule(kind="every", every_ms=10) # they will all be due
    for i in range(20):
        service.add_job(name=f"job_{i}", schedule=schedule, message="hello")

    # Wait for file to write, then manually trigger _on_timer

    # Wait a bit so they are due
    await asyncio.sleep(0.05)

    start_time = time.time()
    await service._on_timer()
    end_time = time.time()

    duration = end_time - start_time
    print(f"Time taken to run 20 jobs: {duration:.4f} seconds")

    if store_path.exists():
        store_path.unlink()

asyncio.run(run_benchmark())
