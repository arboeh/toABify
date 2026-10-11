"""Constants for the toABify custom integration.

The internal protocol identifiers (EVENT_TOAST, WS_TYPE_SUBSCRIBE,
STATIC_URL_PATH) are hardcoded in dist/toast_engine.js and must not
change during refactoring — see D2.
"""

DOMAIN = "toabify"

# --- Internal protocol identifiers (matched by toast_engine.js) ---
EVENT_TOAST = "toastify_event"
WS_TYPE_SUBSCRIBE = "toastify/subscribe"
STATIC_URL_PATH = "/toastify_lib"
TOAST_ENGINE_JS = f"{STATIC_URL_PATH}/toast_engine.js"

# Path relative to config dir, used for hass.config.path()
STATIC_PATH = f"custom_components/{DOMAIN}/dist"

# --- Default values for notification data ---
DEFAULT_BUTTON_LABEL = "CLOSE"
DEFAULT_COLOR = "info"
DEFAULT_GRAVITY = "top"
DEFAULT_POSITION = "right"
DEFAULT_VISIBILITY = "dashboard"
DEFAULT_DURATION_EVENT = 5000
DEFAULT_TIMEOUT = 3000
