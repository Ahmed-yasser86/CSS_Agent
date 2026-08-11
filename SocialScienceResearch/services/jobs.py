"""In-process asynchronous job registry for long-running collection work.

Collection runs are synchronous under the hood (yt-dlp extraction is
blocking), so each job runs in a dedicated worker thread and the registry
exposes async-friendly status, progress and cancellation semantics.

Cancellation is cooperative and honest: it is honoured before a job starts
and acknowledged once the current unit of work finishes (a job is never torn
down mid-extraction, because that could leave a run half-persisted).
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Callable, Protocol

from SocialScienceResearch.utils.idgen import new_id, utcnow

#: Signature of the progress callback handed to a worker function.
ProgressCallback = Callable[[], None] | None


class _ProgressSink(Protocol):
    def __call__(
        self,
        *,
        stage: str = "",
        discovered: int = 0,
        succeeded: int = 0,
        failed: int = 0,
        message: str | None = None,
    ) -> None: ...


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """One submitted collection job and its lifecycle state."""

    job_id: str
    kind: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    progress: dict[str, Any] = field(default_factory=dict)
    message: str | None = None
    cancel_requested: bool = False
    result: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """JSON-safe snapshot of the job's live state (no result/error bodies)."""
        return {
            "job_id": self.job_id,
            "kind": self.kind,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "progress": self.progress,
            "message": self.message,
            "cancel_requested": self.cancel_requested,
        }


class JobManager:
    """Thread-backed job registry. Safe to call from any thread."""

    def __init__(self, max_workers: int = 2) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="collect"
        )

    # ------------------------------------------------------------------
    # Submission / lifecycle
    # ------------------------------------------------------------------
    def submit(
        self, fn: Callable[[_ProgressSink], Any], *, kind: str = "collect"
    ) -> Job:
        """Schedule ``fn(progress_cb)`` on a worker thread; returns the job."""
        job = Job(job_id=new_id("job"), kind=kind)
        with self._lock:
            self._jobs[job.job_id] = job
        self._executor.submit(self._run, job, fn)
        return job

    def _run(self, job: Job, fn: Callable[[_ProgressSink], Any]) -> None:
        job.status = JobStatus.RUNNING
        job.started_at = utcnow()
        try:
            result = fn(self._progress_cb(job))
            if job.cancel_requested:
                job.status = JobStatus.CANCELLED
                job.message = "cancelled after the current unit of work finished"
            else:
                job.status = JobStatus.SUCCEEDED
                job.result = result
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
            if job.cancel_requested:
                job.status = JobStatus.CANCELLED
                job.message = "cancelled after the current unit of work finished"
            else:
                job.status = JobStatus.FAILED
                job.error = str(exc)
        finally:
            job.finished_at = utcnow()

    def cancel(self, job_id: str) -> bool:
        """Request cancellation. True if the job could accept the request."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False
            if job.status in (JobStatus.PENDING, JobStatus.RUNNING):
                job.cancel_requested = True
                return True
            return False

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def _progress_cb(self, job: Job) -> _ProgressSink:
        def _report(
            *,
            stage: str = "",
            discovered: int = 0,
            succeeded: int = 0,
            failed: int = 0,
            message: str | None = None,
        ) -> None:
            snapshot = {
                "stage": stage,
                "discovered": discovered,
                "succeeded": succeeded,
                "failed": failed,
                "message": message,
            }
            with self._lock:
                job.progress = snapshot
                job.message = message

        return _report

    def shutdown(self) -> None:
        """Stop accepting work and release the worker pool (non-blocking)."""
        self._executor.shutdown(wait=False, cancel_futures=True)
