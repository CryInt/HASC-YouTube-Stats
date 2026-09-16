"""Data update coordinator for the YouTube Stats integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import YouTubeApiClient, YouTubeApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class YouTubeDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the YouTube Data API for the latest upload."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: YouTubeApiClient
    ) -> None:
        self.client = client
        self.channel_id: str | None = entry.data.get("channel_id")
        self.channel_title: str | None = entry.data.get("channel_title")
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            video = await self.client.get_latest_upload()
        except YouTubeApiError as err:
            raise UpdateFailed(str(err)) from err
        return video or {}
