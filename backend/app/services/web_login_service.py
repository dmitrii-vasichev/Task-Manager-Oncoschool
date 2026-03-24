"""In-memory storage for web login requests (Telegram confirmation flow).

Requests live max 5 minutes and are never persisted to DB.
"""

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


REQUEST_TTL = timedelta(minutes=5)


@dataclass
class WebLoginRequest:
    request_id: str
    telegram_id: int
    token: str
    status: str  # "pending" | "confirmed" | "expired"
    created_at: datetime
    expires_at: datetime
    message_id: int | None = None


class WebLoginService:
    def __init__(self) -> None:
        self._requests: dict[str, WebLoginRequest] = {}

    def create_request(self, telegram_id: int) -> WebLoginRequest:
        """Create a new pending login request for the given telegram_id."""
        self.cleanup_expired()

        # Remove any existing pending requests for the same user
        existing = [
            rid for rid, req in self._requests.items()
            if req.telegram_id == telegram_id and req.status == "pending"
        ]
        for rid in existing:
            del self._requests[rid]

        now = datetime.now(timezone.utc)
        request = WebLoginRequest(
            request_id=str(uuid.uuid4()),
            telegram_id=telegram_id,
            token=secrets.token_urlsafe(32),
            status="pending",
            created_at=now,
            expires_at=now + REQUEST_TTL,
        )
        self._requests[request.request_id] = request
        return request

    def get_request(self, request_id: str) -> WebLoginRequest | None:
        """Get a request by ID. Returns None if not found. Marks expired requests."""
        req = self._requests.get(request_id)
        if req is None:
            return None
        if datetime.now(timezone.utc) > req.expires_at:
            req.status = "expired"
        return req

    def confirm_request(self, request_id: str) -> bool:
        """Mark request as confirmed. Returns False if not found, expired, or already used."""
        req = self.get_request(request_id)
        if req is None or req.status != "pending":
            return False
        req.status = "confirmed"
        return True

    def delete_request(self, request_id: str) -> None:
        """Remove a request by ID (e.g. on rejection)."""
        self._requests.pop(request_id, None)

    def cleanup_expired(self) -> None:
        """Remove all expired requests from storage."""
        now = datetime.now(timezone.utc)
        expired_ids = [
            rid for rid, req in self._requests.items() if now > req.expires_at
        ]
        for rid in expired_ids:
            del self._requests[rid]


web_login_service = WebLoginService()
