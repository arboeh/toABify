"""Constants for the toABify custom integration.

The internal protocol identifiers (EVENT_TOAST, WS_TYPE_SUBSCRIBE,
STATIC_URL_PATH) are hardcoded in dist/toast_engine.js and must not
change during refactoring — see D2.
"""

from __future__ import annotations

DOMAIN: str = "toabify"

# --- Internal protocol identifiers (matched by toast_engine.js) ---
EVENT_TOAST: str = "toastify_event"
WS_TYPE_SUBSCRIBE: str = "toastify/subscribe"
STATIC_URL_PATH: str = "/toastify_lib"
TOAST_ENGINE_JS: str = f"{STATIC_URL_PATH}/toast_engine.js"

# Path relative to config dir, used for hass.config.path()
STATIC_PATH: str = f"custom_components/{DOMAIN}/dist"

# --- Default values for notification data ---
DEFAULT_BUTTON_LABEL: str = "CLOSE"
DEFAULT_COLOR: str = "info"
DEFAULT_GRAVITY: str = "top"
DEFAULT_POSITION: str = "right"
DEFAULT_VISIBILITY: str = "dashboard"
DEFAULT_DURATION_EVENT: int = 5000
DEFAULT_TIMEOUT: int = 3000
