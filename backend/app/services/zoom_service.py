import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)


class ZoomService:
    """Zoom Server-to-Server OAuth integration."""

    BASE_URL = "https://api.zoom.us/v2"
    TOKEN_URL = "https://zoom.us/oauth/token"

    def __init__(self, account_id: str, client_id: str, client_secret: str):
        self.account_id = account_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None
        self._token_expires: datetime | None = None
        self._token_lock = asyncio.Lock()

    async def _get_token(self) -> str:
        """Get or refresh Server-to-Server OAuth token (thread-safe)."""
        async with self._token_lock:
            if self._token and self._token_expires and datetime.now(timezone.utc) < self._token_expires:
                return self._token

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    params={"grant_type": "account_credentials", "account_id": self.account_id},
                    auth=(self.client_id, self.client_secret),
                )
                response.raise_for_status()
                data = response.json()
                self._token = data["access_token"]
                self._token_expires = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"] - 60)
                return self._token

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Execute an authorized request to Zoom API."""
        token = await self._get_token()
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.BASE_URL}{path}",
                headers={"Authorization": f"Bearer {token}"},
                **kwargs,
            )
            response.raise_for_status()
            if response.status_code == 204:
                return {}
            return response.json()

    async def create_meeting(
        self,
        topic: str,
        start_time: datetime,
        duration: int = 60,
        timezone: str = "Europe/Moscow",
    ) -> dict:
        """Create a Zoom meeting. Returns {id, join_url, start_url, ...}."""
        data = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "duration": duration,
            "timezone": timezone,
            "settings": {
                "join_before_host": True,
                "waiting_room": False,
                "auto_recording": "cloud",
                "meeting_authentication": False,
            },
        }
        return await self._request("POST", "/users/me/meetings", json=data)

    async def update_meeting(self, meeting_id: str, **kwargs) -> dict:
        """Update Zoom meeting parameters."""
        return await self._request("PATCH", f"/meetings/{meeting_id}", json=kwargs)

    async def delete_meeting(self, meeting_id: str) -> None:
        """Delete a Zoom meeting."""
        await self._request("DELETE", f"/meetings/{meeting_id}")

    async def get_meeting(self, meeting_id: str) -> dict:
        """Get Zoom meeting details."""
        return await self._request("GET", f"/meetings/{meeting_id}")

    async def get_recordings(self, meeting_id: str) -> dict | None:
        """Get meeting recordings. None if no recordings available."""
        try:
            return await self._request("GET", f"/meetings/{meeting_id}/recordings")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_transcript(self, meeting_id: str) -> str | None:
        """
        Get meeting transcript.
        1. Request recordings
        2. Find file with file_type="TRANSCRIPT"
        3. Download .vtt file
        4. Parse VTT -> plain text
        Returns None if transcript is unavailable.
        """
        recordings = await self.get_recordings(meeting_id)
        if not recordings or "recording_files" not in recordings:
            return None

        transcript_file = next(
            (f for f in recordings["recording_files"] if f.get("file_type") == "TRANSCRIPT"),
            None,
        )
        if not transcript_file:
            return None

        # Download VTT
        download_url = transcript_file["download_url"]
        token = await self._get_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                download_url,
                headers={"Authorization": f"Bearer {token}"},
                follow_redirects=True,
            )
            resp.raise_for_status()
            vtt_content = resp.text

        return self._parse_vtt(vtt_content)

    @staticmethod
    def _parse_vtt(vtt_text: str) -> str:
        """Parse WebVTT format to plain text."""
        lines = []
        for line in vtt_text.strip().split("\n"):
            line = line.strip()
            # Skip WEBVTT header, empty lines, timestamps
            if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
                continue
            if "-->" in line:  # Timestamp like "00:00:01.000 --> 00:00:03.000"
                continue
            if line.isdigit():  # Block number
                continue
            lines.append(line)
        return "\n".join(lines)
