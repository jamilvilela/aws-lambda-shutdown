"""Glue handler (batch and streaming)."""

from __future__ import annotations

from typing import Any, List

from .base import ServiceHandler

RUNNING_STATES = {"STARTING", "RUNNING", "STOPPING"}
STREAMING_COMMAND = "gluestreaming"


class GlueHandler(ServiceHandler):
    """Handles both glue-batch and glue-stream based on service_name."""

    def __init__(self, glue: Any, service_name: str = "glue-batch") -> None:
        self._glue = glue
        self.service_name = service_name

    def list_active_items(self) -> List[str]:
        items: List[str] = []
        for job in self._list_jobs():
            if self._is_streaming(job) != (self.service_name == "glue-stream"):
                continue
            for run in self._list_job_runs(job["Name"]):
                if run.get("JobRunState") in RUNNING_STATES:
                    items.append(f"{job['Name']}:{run['Id']}")
        return items

    def shutdown_item(self, item_id: str) -> None:
        job_name, run_id = item_id.split(":", 1)
        self._glue.batch_stop_job_run(JobName=job_name, JobRunIds=[run_id])

    def _list_jobs(self) -> List[dict]:
        jobs: List[dict] = []
        paginator = self._glue.get_paginator("get_jobs")
        for page in paginator.paginate():
            jobs.extend(page.get("Jobs", []))
        return jobs

    def _list_job_runs(self, job_name: str) -> List[dict]:
        runs: List[dict] = []
        paginator = self._glue.get_paginator("get_job_runs")
        for page in paginator.paginate(JobName=job_name):
            runs.extend(page.get("JobRuns", []))
        return runs

    @staticmethod
    def _is_streaming(job: dict) -> bool:
        command = job.get("Command", {})
        return command.get("Name") == STREAMING_COMMAND