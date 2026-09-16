"""Sensor platform for the YouTube Stats integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import YouTubeDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class YouTubeSensorEntityDescription(SensorEntityDescription):
    """Describes a YouTube Stats sensor backed by the coordinator data."""

    value_fn: Callable[[dict[str, Any]], Any]


def _published_at(data: dict[str, Any]) -> datetime | None:
    published_at = data.get("published_at")
    return dt_util.parse_datetime(published_at) if published_at else None


def _truncated(value: str | None) -> str | None:
    return value[:255] if value else None


SENSOR_DESCRIPTIONS: tuple[YouTubeSensorEntityDescription, ...] = (
    YouTubeSensorEntityDescription(
        key="title",
        name="Title",
        icon="mdi:youtube",
        value_fn=lambda data: _truncated(data.get("title")),
    ),
    YouTubeSensorEntityDescription(
        key="published_at",
        name="Published at",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_published_at,
    ),
    YouTubeSensorEntityDescription(
        key="view_count",
        name="View count",
        icon="mdi:eye",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("view_count"),
    ),
    YouTubeSensorEntityDescription(
        key="comment_count",
        name="Comment count",
        icon="mdi:comment-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("comment_count"),
    ),
    YouTubeSensorEntityDescription(
        key="like_count",
        name="Like count",
        icon="mdi:thumb-up",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("like_count"),
    ),
    YouTubeSensorEntityDescription(
        key="content_type",
        name="Content type",
        icon="mdi:shape",
        device_class=SensorDeviceClass.ENUM,
        options=["video", "short"],
        value_fn=lambda data: data.get("content_type"),
    ),
    YouTubeSensorEntityDescription(
        key="duration",
        name="Duration",
        icon="mdi:timer-outline",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda data: data.get("duration_seconds"),
    ),
    YouTubeSensorEntityDescription(
        key="url",
        name="URL",
        icon="mdi:link",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("url"),
    ),
    YouTubeSensorEntityDescription(
        key="video_id",
        name="Video ID",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("id"),
    ),
    YouTubeSensorEntityDescription(
        key="thumbnail_url",
        name="Thumbnail URL",
        icon="mdi:image",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("thumbnail_url"),
    ),
    YouTubeSensorEntityDescription(
        key="description",
        name="Description",
        icon="mdi:text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _truncated(data.get("description")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up YouTube Stats sensors from a config entry."""
    coordinator: YouTubeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        YouTubeSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class YouTubeSensor(CoordinatorEntity[YouTubeDataUpdateCoordinator], SensorEntity):
    """A single data point about the latest published video or Short."""

    _attr_has_entity_name = True
    entity_description: YouTubeSensorEntityDescription

    def __init__(
        self,
        coordinator: YouTubeDataUpdateCoordinator,
        entry: ConfigEntry,
        description: YouTubeSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
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
    def native_value(self) -> Any:
        data = self.coordinator.data
        if not data:
            return None
        return self.entity_description.value_fn(data)

    @property
    def available(self) -> bool:
        return super().available and bool(self.coordinator.data)
