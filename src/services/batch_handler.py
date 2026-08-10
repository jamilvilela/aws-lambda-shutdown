"""AWS Batch handler."""

from __future__ import annotations

from typing import Any, List

from .base import ServiceHandler

RUNNING_STATES = {"SUBMITTED", "PENDING", "RUNNABLE", "STARTING", "RUNNING"}


class BatchHandler(ServiceHandler):
    service_name = "batch"

    def __init__(self, batch: Any) -> None:
        self._batch = batch

    def list_active_items(self) -> List[str]:
        job_ids: List[str] = []
        for state in RUNNING_STATES:
            job_ids.extend(self._list_jobs_by_status(state))
        return job_ids

    def shutdown_item(self, item_id: str) -> None:
        self._batch.terminate_job(jobId=item_id, reason="Forced shutdown by aws-lambda-shutdown")

    def _list_jobs_by_status(self, status: str) -> List[str]:
        job_ids: List[str] = []
        paginator = self._batch.get_paginator("list_jobs")
        for page in paginator.paginate(jobStatus=status):
            job_ids.extend(job["jobId"] for job in page.get("jobSummaryList", []))
        return job_ids