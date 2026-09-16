"""Thin async client for the YouTube Data API v3."""

from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow

from .const import API_BASE_URL, SHORT_MAX_DURATION_SECONDS

_LOGGER = logging.getLogger(__name__)

_DURATION_RE = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


class YouTubeApiError(Exception):
    """Raised when the YouTube Data API returns an error."""


def _parse_duration(duration: str | None) -> int:
    """Parse an ISO-8601 duration (e.g. PT1M30S) into seconds."""
    if not duration:
        return 0
    match = _DURATION_RE.match(duration)
    if not match:
        return 0
    hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds


class YouTubeApiClient:
    """Client for reading data about the authenticated user's own channel."""

    def __init__(self, oauth_session: config_entry_oauth2_flow.OAuth2Session) -> None:
        self._oauth_session = oauth_session

    async def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        await self._oauth_session.async_ensure_token_valid()
        access_token = self._oauth_session.token["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        http_session = aiohttp_client.async_get_clientsession(self._oauth_session.hass)
        async with http_session.get(
            f"{API_BASE_URL}{path}", params=params, headers=headers
        ) as resp:
            if resp.status == 401:
                raise YouTubeApiError("Unauthorized while calling the YouTube Data API")
            if resp.status == 403:
                body = await resp.text()
                raise YouTubeApiError(f"Forbidden (quota exceeded or API not enabled?): {body}")
            resp.raise_for_status()
            return await resp.json()

    async def _get_uploads_playlist_id(self) -> str:
        data = await self._request(
            "/channels", {"part": "contentDetails", "mine": "true"}
        )
        items = data.get("items") or []
        if not items:
            raise YouTubeApiError("No channel found for this account")
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    async def get_latest_upload(self) -> dict[str, Any] | None:
        """Return normalized data about the most recently published video or short."""
        playlist_id = await self._get_uploads_playlist_id()

        playlist_data = await self._request(
            "/playlistItems",
            {
                "part": "contentDetails",
                "playlistId": playlist_id,
                "maxResults": 5,
            },
        )
        items = playlist_data.get("items") or []
        if not items:
            return None

        # The uploads playlist is *usually* newest-first, but sort
        # defensively by publish date so we never report a stale item.
        items.sort(
            key=lambda item: item.get("contentDetails", {}).get("videoPublishedAt") or "",
            reverse=True,
        )
        video_id = items[0]["contentDetails"]["videoId"]

        video_data = await self._request(
            "/videos",
            {"part": "snippet,statistics,contentDetails", "id": video_id},
        )
        video_items = video_data.get("items") or []
        if not video_items:
            return None

        return self._parse_video(video_items[0])

    @staticmethod
    def _parse_video(video: dict[str, Any]) -> dict[str, Any]:
        snippet = video.get("snippet", {})
        statistics = video.get("statistics", {})
        content_details = video.get("contentDetails", {})
        thumbnails = snippet.get("thumbnails", {})

        duration_seconds = _parse_duration(content_details.get("duration"))
        is_short = 0 < duration_seconds <= SHORT_MAX_DURATION_SECONDS

        thumbnail = (
            thumbnails.get("maxres")
            or thumbnails.get("standard")
            or thumbnails.get("high")
            or thumbnails.get("medium")
            or thumbnails.get("default")
            or {}
        )

        return {
            "id": video.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "published_at": snippet.get("publishedAt"),
            "channel_title": snippet.get("channelTitle"),
            "thumbnail_url": thumbnail.get("url"),
            "view_count": _safe_int(statistics.get("viewCount")),
            "like_count": _safe_int(statistics.get("likeCount")),
            "comment_count": _safe_int(statistics.get("commentCount")),
            "duration_seconds": duration_seconds,
            "content_type": "short" if is_short else "video",
            "url": f"https://www.youtube.com/watch?v={video.get('id')}",
        }


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
