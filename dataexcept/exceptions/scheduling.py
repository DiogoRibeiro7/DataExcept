# scheduling.py
from .base import JobError


class ScheduleConflictError(JobError):
    """Raised when two jobs have conflicting schedules."""

    def __init__(self, job_name: str, schedule: str):
        self.job_name = job_name
        self.schedule = schedule
        msg = f"Schedule conflict for job '{job_name}' on schedule '{schedule}'"
        super().__init__(msg)


class CronExpressionError(JobError):
    """Raised when a cron expression is invalid."""

    def __init__(self, expression: str, message: str = None):
        self.expression = expression
        self.message = message or f"Invalid cron expression: '{expression}'"
        super().__init__(self.message)
