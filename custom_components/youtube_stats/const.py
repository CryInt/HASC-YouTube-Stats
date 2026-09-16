"""Constants for the YouTube Stats integration."""

from datetime import timedelta

DOMAIN = "youtube_stats"

OAUTH2_AUTHORIZE = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH2_TOKEN = "https://oauth2.googleapis.com/token"

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

API_BASE_URL = "https://www.googleapis.com/youtube/v3"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=15)

# YouTube does not expose an official "is this a Short" flag via the Data
# API. Shorts are limited to 3 minutes (180s); a small buffer is used to
# tolerate rounding on YouTube's side. This is a heuristic, not a guarantee.
SHORT_MAX_DURATION_SECONDS = 183
