# notification.py
from .base import JobError


class NotificationError(JobError):
    """Base exception for notification failures."""

    def __init__(
        self,
        channel: str,
        original_exception: Exception | None = None,
        message: str | None = None,
    ):
        self.channel = channel
        self.original_exception = original_exception
        msg = message or f"Notification via '{channel}' failed"
        if message is None and original_exception:
            msg += f": {original_exception}"
        super().__init__(msg)


class EmailError(NotificationError):
    """Raised when sending an email fails."""

    def __init__(
        self,
        recipient: str,
        subject: str,
        original_exception: Exception | None = None,
    ):
        self.recipient = recipient
        self.subject = subject
        self.original_exception = original_exception
        msg = f"Email to '{recipient}' with subject '{subject}' failed"
        if original_exception:
            msg += f": {original_exception}"
        super().__init__("email", original_exception, message=msg)


class WebhookError(NotificationError):
    """Raised when a webhook POST fails."""

    def __init__(self, url: str, original_exception: Exception = None):
        self.url = url
        self.original_exception = original_exception
        msg = f"Webhook to URL '{url}' failed"
        if original_exception:
            msg += f": {original_exception}"
        super().__init__("webhook", original_exception, message=msg)
