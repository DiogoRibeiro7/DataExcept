from .base import JobError


class JobCancellationError(JobError):
    """Raised when a job is cancelled before completion."""

    def __init__(self, job_id: str, reason: str | None = None):
        self.job_id = job_id
        self.reason = reason
        msg = f"Job '{job_id}' was cancelled"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
