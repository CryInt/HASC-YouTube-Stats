"""Sensor platform for the YouTube Stats integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import YouTubeDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the YouTube Stats sensor from a config entry."""
    coordinator: YouTubeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([YouTubeLatestUploadSensor(coordinator, entry)])


class YouTubeLatestUploadSensor(
    CoordinatorEntity[YouTubeDataUpdateCoordinator], SensorEntity
):
    """Sensor exposing the latest published video or Short."""

    _attr_has_entity_name = True
    _attr_name = "Latest upload"
    _attr_icon = "mdi:youtube"

    def __init__(
        self, coordinator: YouTubeDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_latest_upload"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=coordinator.channel_title or "YouTube channel",
            manufacturer="YouTube",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=(
                f"https://www.youtube.com/channel/{coordinator.channel_id}"
                if coordinator.channel_id
                else None
            ),
        )

    @property
    def native_value(self) -> str | None:
        title = (self.coordinator.data or {}).get("title")
        if not title:
            return None
        # Home Assistant truncates/warns on states longer than 255 chars.
        return title[:255]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        if not data:
            return {}
        return {
            "video_id": data.get("id"),
            "content_type": data.get("content_type"),
            "published_at": data.get("published_at"),
            "view_count": data.get("view_count"),
            "like_count": data.get("like_count"),
            "comment_count": data.get("comment_count"),
            "duration_seconds": data.get("duration_seconds"),
            "url": data.get("url"),
            "thumbnail_url": data.get("thumbnail_url"),
            "description": data.get("description"),
        }

    @property
    def available(self) -> bool:
        return super().available and bool(self.coordinator.data)
