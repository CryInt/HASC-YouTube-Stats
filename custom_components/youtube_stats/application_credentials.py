"""Application credentials platform for YouTube Stats."""

from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.core import HomeAssistant

from .const import OAUTH2_AUTHORIZE, OAUTH2_TOKEN


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return authorization server for Google OAuth2."""
    return AuthorizationServer(
        authorize_url=OAUTH2_AUTHORIZE,
        token_url=OAUTH2_TOKEN,
    )


async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Return description placeholders shown on the Application Credentials form."""
    return {
        "oauth_creds_url": "https://console.cloud.google.com/apis/credentials",
        "more_info_url": "https://www.home-assistant.io/integrations/application_credentials/",
        "redirect_url": "https://my.home-assistant.io/redirect/oauth",
    }
