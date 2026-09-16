# YouTube Stats — Home Assistant integration

A custom component (distributed via HACS as a custom repository) that uses
the **YouTube Data API v3** and **OAuth2** to fetch data about the most
recently published video or Short on your own channel and exposes it
through the `sensor.<channel>_latest_upload` entity:

- **Title** — the sensor's state (video title)
- **Publish date and time** — `published_at` attribute
- **View count** — `view_count` attribute
- **Comment count** — `comment_count` attribute
- plus `content_type` (`video`/`short`), `like_count`, `duration_seconds`,
  `url`, `thumbnail_url`, `description`, `video_id`

The content type (`video` or `short`) is determined heuristically from the
video's duration (≤ 3 minutes = Shorts), since the YouTube Data API does not
expose an official Shorts flag.

Only **your own** channel is polled (via `mine=true`), granted through an
OAuth login with Google. Data refreshes every 15 minutes (~3 YouTube API
quota units per poll; the default daily quota is 10,000).

## How authentication works and where data is stored

This integration uses Home Assistant's **standard mechanism** for OAuth2
integrations (`config_entry_oauth2_flow` + the `application_credentials`
platform, the same pattern used by Google Calendar/Nest and other core
integrations):

- Your Google project's Client ID/Secret are registered in HA via
  **Settings → Devices & Services → Application Credentials** — they are
  stored in `.storage/application_credentials`.
- After signing in with Google, the access/refresh token is saved directly
  in the corresponding config entry — in `.storage/core.config_entries`,
  just like any other HA OAuth integration. The component does not create
  its own token storage and does not keep secrets in `configuration.yaml`.
- Home Assistant automatically refreshes the token when it expires
  (`async_ensure_token_valid`).

## Installation

### 1. Create an OAuth client in Google Cloud

1. Open the [Google API Console](https://console.cloud.google.com/apis/credentials)
   and create (or select) a project.
2. In the [API library](https://console.cloud.google.com/apis/library),
   enable **YouTube Data API v3**.
3. Configure the **OAuth consent screen**:
   - User type — External;
   - add the `.../auth/youtube.readonly` scope;
   - on the Test users tab, add your own Google account (until the app is
     published, only test users can sign in).
4. Create **Credentials → OAuth client ID** of type **Web application**.
5. Under **Authorized redirect URIs**, add:
   - `https://my.home-assistant.io/redirect/oauth` (if you use
     My Home Assistant), and/or
   - `https://<your-external-ha-url>/auth/external/callback`.
6. Save the **Client ID** and **Client Secret**.

### 2. Install the component via HACS

1. HACS → three dots in the top-right corner → **Custom repositories**.
2. Add this repository's URL, category — **Integration**.
3. Find **YouTube Stats** in the HACS list and install it.
4. Restart Home Assistant.

(While the repository isn't in the default HACS catalog, it can only be
added as a custom repository.)

### 3. Set up Application Credentials in Home Assistant

**Settings → Devices & Services → Application Credentials → Add
Application Credential**:

- Integration: **YouTube Stats**
- Client ID / Client Secret — from step 1.

### 4. Add the integration

**Settings → Devices & Services → Add Integration → YouTube Stats**, sign
in with Google and grant read access to your YouTube data. A device named
after your channel will appear, along with a **Latest upload** sensor.

## Limitations

- Only the authenticated account's own channel is supported.
- The video/Shorts distinction is a duration-based heuristic, not an
  official API field.
- It's not recommended to lower the polling interval much below 15
  minutes — that burns through the YouTube Data API's daily quota faster.
