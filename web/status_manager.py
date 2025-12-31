"""
Thread-safe job status manager for tracking generation progress.

Manages job status updates from the workflow and provides thread-safe
access for web API endpoints.
"""

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any

from src.utils.progress import ProgressStage


@dataclass
class JobStatus:
    """Status information for a generation job"""

    job_id: str
    stage: ProgressStage
    progress: int  # 0-100
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error: str | None = None


class JobStatusManager:
    """
    Thread-safe job status manager.

    Manages status updates for multiple concurrent generation jobs.
    Provides thread-safe access for both status updates (from workflow)
    and status queries (from web API).
    """

    def __init__(self):
        """Initialize the status manager"""
        self._statuses: dict[str, JobStatus] = {}
        self._lock = Lock()

    def create_job(self, job_id: str) -> None:
        """
        Initialize a new job with initial status.

        Args:
            job_id: Unique job identifier
        """
        with self._lock:
            self._statuses[job_id] = JobStatus(
                job_id=job_id, stage=ProgressStage.ANALYZING, progress=0, message="Initializing..."
            )

    def update_status(
        self,
        job_id: str,
        stage: ProgressStage,
        progress: int,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Update job status.

        Args:
            job_id: Job identifier
            stage: Current workflow stage
            progress: Progress percentage (0-100)
            message: Human-readable progress message
            details: Optional additional details
        """
        with self._lock:
            if job_id in self._statuses:
                self._statuses[job_id].stage = stage
                self._statuses[job_id].progress = progress
                self._statuses[job_id].message = message
                self._statuses[job_id].details = details or {}
                self._statuses[job_id].updated_at = datetime.now()

    def get_status(self, job_id: str) -> JobStatus | None:
        """
        Get current job status.

        Args:
            job_id: Job identifier

        Returns:
            JobStatus object or None if job not found
        """
        with self._lock:
            return self._statuses.get(job_id)

    def set_error(self, job_id: str, error: str) -> None:
        """
        Mark job as failed with error message.

        Args:
            job_id: Job identifier
            error: Error message
        """
        with self._lock:
            if job_id in self._statuses:
                self._statuses[job_id].stage = ProgressStage.ERROR
                self._statuses[job_id].error = error
                self._statuses[job_id].updated_at = datetime.now()

    def delete_job(self, job_id: str) -> None:
        """
        Remove job from status tracking.

        Args:
            job_id: Job identifier
        """
        with self._lock:
            if job_id in self._statuses:
                del self._statuses[job_id]

    def list_jobs(self) -> dict[str, JobStatus]:
        """
        Get all current jobs.

        Returns:
            Dictionary mapping job_id to JobStatus
        """
        with self._lock:
            return self._statuses.copy()
