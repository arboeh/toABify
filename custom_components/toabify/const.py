"""Constants for the toABify custom integration.

The internal protocol identifiers (EVENT_TOAST, WS_TYPE_SUBSCRIBE,
STATIC_URL_PATH) are hardcoded in dist/toast_engine.js and must not
change during refactoring — see D2.
"""

from __future__ import annotations

from typing import Any

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

# --- Description of the notify service registered in "notify.<domain>" ---
# Home Assistant's legacy notify layer registers the service with the generic
# NOTIFY_SERVICE_SCHEMA (message, title, target, data). The core also fills the
# UI description from notify/services.yaml, which advertises "title" and
# "target". Both are accepted by the runtime schema but never read by this
# integration, so the registered description is replaced with the fields that
# are actually supported (see notify.async_register_services).
NOTIFY_SERVICE_NAME: str = "Send a toast notification with toabify"
NOTIFY_SERVICE_DESCRIPTION: str = (
    "Shows a toast message in the Home Assistant frontend. The toast options "
    "(color, duration, position, gravity, close, icon, avatar, visibility, "
    "onClick, callback) are passed via the data field. The generic core "
    "fields title and target are not supported by toabify."
)
NOTIFY_SERVICE_FIELDS: dict[str, dict[str, Any]] = {
    "message": {
        "name": "Message",
        "description": "Text to show in the toast.",
        "required": True,
        "example": "The garage door has been open for 10 minutes.",
        "selector": {"text": {}},
    },
    "data": {
        "name": "Data",
        "description": (
            "Optional toast options: color, duration, position, gravity, "
            "close, icon, avatar, visibility, onClick and callback. See "
            "README.md for the supported values."
        ),
        "selector": {"object": {}},
    },
}
