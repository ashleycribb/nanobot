import json
import tempfile
from pathlib import Path
from nanobot.cron.service import CronService
from nanobot.cron.types import CronJob, CronSchedule, CronPayload, CronJobState

def test_cron_serialization_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "jobs.json"

        # Create a service and add a job
        service = CronService(store_path)
        schedule = CronSchedule(kind="every", every_ms=60000)
        job = service.add_job(
            name="test_job",
            schedule=schedule,
            message="hello",
            deliver=True,
            channel="slack",
            to="user1",
            delete_after_run=False
        )

        # Verify file exists and has correct format (camelCase)
        assert store_path.exists()
        content = json.loads(store_path.read_text())

        print(json.dumps(content, indent=2))

        assert "jobs" in content
        job_data = content["jobs"][0]
        assert job_data["name"] == "test_job"
        assert job_data["schedule"]["everyMs"] == 60000
        assert job_data["payload"]["channel"] == "slack"
        assert "createdAtMs" in job_data

        # Load again
        service2 = CronService(store_path)
        jobs = service2.list_jobs(include_disabled=True)
        assert len(jobs) == 1
        loaded_job = jobs[0]

        assert loaded_job.id == job.id
        assert loaded_job.name == job.name
        assert loaded_job.schedule.every_ms == 60000
        assert loaded_job.payload.channel == "slack"
