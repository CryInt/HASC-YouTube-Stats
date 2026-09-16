"""Config flow for the YouTube Stats integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow

from .const import API_BASE_URL, DOMAIN, SCOPES

_LOGGER = logging.getLogger(__name__)


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle the OAuth2 config flow for YouTube Stats."""

    DOMAIN = DOMAIN
    VERSION = 1

    @property
    def logger(self) -> logging.Logger:
        """Return the logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data appended to the authorize URL."""
        return {
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Resolve the authenticated channel and create the config entry."""
        session = aiohttp_client.async_get_clientsession(self.hass)
        headers = {"Authorization": f"Bearer {data['token']['access_token']}"}

        try:
            async with session.get(
                f"{API_BASE_URL}/channels",
                params={"part": "snippet", "mine": "true"},
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                channel_json = await resp.json()
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Failed to resolve the YouTube channel for this account")
            return self.async_abort(reason="cannot_resolve_channel")

        items = channel_json.get("items") or []
        if not items:
            return self.async_abort(reason="no_channel")

        channel = items[0]
        channel_id = channel["id"]
        channel_title = channel["snippet"]["title"]

        await self.async_set_unique_id(channel_id)
        self._abort_if_unique_id_configured()

        data["channel_id"] = channel_id
        data["channel_title"] = channel_title

        return self.async_create_entry(title=channel_title, data=data)
