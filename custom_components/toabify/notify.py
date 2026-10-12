"""The toABify notify platform."""

from __future__ import annotations

import logging
import re
from html import escape as _escape_html
from typing import Any, cast

import voluptuous as vol
from homeassistant.components.notify.legacy import BaseNotificationService
from homeassistant.core import Context, EventOrigin, HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.service import async_set_service_schema
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    DEFAULT_BUTTON_LABEL,
    DEFAULT_COLOR,
    DEFAULT_DURATION_EVENT,
    DEFAULT_GRAVITY,
    DEFAULT_POSITION,
    DEFAULT_TIMEOUT,
    DEFAULT_VISIBILITY,
    DOMAIN,
    EVENT_TOAST,
    NOTIFY_SERVICE_DESCRIPTION,
    NOTIFY_SERVICE_FIELDS,
    NOTIFY_SERVICE_NAME,
)

_LOGGER = logging.getLogger(__name__)

_VALID_SERVICE_RE = re.compile(r"^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$")

_MAX_DURATION_MS: int = 600_000

_MAX_LABEL_LENGTH: int = 200

_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")

_COLOR_NAMES: tuple[str, ...] = (
    "success",
    "info",
    "warning",
    "error",
    "alert",
    "default",
)


def _validate_color(value: str) -> str:
    """Accept a theme name or a hex color.

    The frontend engine resolves theme names via TOAST_THEMES and falls back
    to the raw value for hex colors (#RGB, #RRGGBB, #RRGGBBAA). A #RGB value
    is expanded to #RRGGBB because the engine derives the label contrast from
    the first six characters only.
    """
    if not isinstance(value, str) or (value not in _COLOR_NAMES and not _HEX_COLOR_RE.match(value)):
        raise vol.Invalid(f"must be one of {list(_COLOR_NAMES)} or a hex color like #ff5f6d")
    if value.startswith("#"):
        if len(value) == 4:
            return "#" + "".join(char * 2 for char in value[1:])
        return value
    return value


def _apply_button_label(on_click: dict | None, button_label: str) -> dict | None:
    """Return *on_click* with its button label defaulting to *button_label*.

    The frontend engine renders the button label from onClick.label only and
    otherwise falls back to its own hardcoded "CLOSE". Copying button_label
    into the dict (without overwriting an explicit onClick.label) keeps the
    engine showing the label the caller chose. The resulting label is
    sanitized, because the engine inserts it as HTML.
    """
    if not isinstance(on_click, dict):
        return on_click
    labeled = dict(on_click)
    label_value = labeled.get("label") or button_label
    if not isinstance(label_value, str):
        raise vol.Invalid(f"button label must be a string, got {type(label_value).__name__}")
    plain = _escape_html(label_value)[:_MAX_LABEL_LENGTH]
    labeled["label"] = plain or "CLOSE"
    return labeled


_CALLBACK_DICT_SCHEMA = vol.Schema(
    {
        vol.Optional("action"): str,
        vol.Optional("action_data", default={}): dict,
    },
    extra=vol.PREVENT_EXTRA,
)

_NOTIFY_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("duration"): vol.All(vol.Coerce(int), vol.Range(min=-1, max=_MAX_DURATION_MS)),
        vol.Optional("close", default=False): bool,
        vol.Optional("position", default=DEFAULT_POSITION): vol.In(["left", "right", "center"]),
        vol.Optional("gravity", default=DEFAULT_GRAVITY): vol.In(["top", "bottom", "center"]),
        vol.Optional("icon", default=""): str,
        vol.Optional("avatar", default=""): str,
        vol.Optional("color", default=DEFAULT_COLOR): _validate_color,
        vol.Optional("visibility", default=DEFAULT_VISIBILITY): vol.In(["all", "dashboard"]),
        vol.Optional("button_label", default=DEFAULT_BUTTON_LABEL): str,
        vol.Optional("oldestFirst", default=True): bool,
        vol.Optional("onClick"): dict,
        vol.Optional("callback"): vol.Any(str, _CALLBACK_DICT_SCHEMA),
    },
    extra=vol.PREVENT_EXTRA,
)


class ToastifyNotificationService(BaseNotificationService):
    """Notification service that fires toasts to the frontend via WebSocket."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the service."""
        self.hass = hass

    async def async_register_services(self) -> None:
        """Register the notify service and replace the generic UI description.

        A failure of the core registration propagates, because nothing is
        registered in that case. Overriding the description is cosmetic: the
        service keeps working, so a failure here is only logged to avoid
        breaking a registered service over its UI description.
        """
        await super().async_register_services()
        try:
            async_set_service_schema(
                self.hass,
                "notify",
                DOMAIN,
                {
                    "name": NOTIFY_SERVICE_NAME,
                    "description": NOTIFY_SERVICE_DESCRIPTION,
                    "fields": NOTIFY_SERVICE_FIELDS,
                },
            )
        except Exception:
            _LOGGER.exception(
                "Failed to override the description of the notify.%s service",
                DOMAIN,
            )

    async def async_send_message(self, message: str = "", **kwargs) -> None:
        """Send a toast notification to the frontend.

        The event is fired on the bus; the frontend WebSocket listener
        (websocket_subscribe_toast) forwards it to connected clients.

        Callback data can be a string URL or a dict specifying a
        server-side service call to execute after *duration* milliseconds.

        The *title* and *target* kwargs of the generic core notify schema are
        accepted but deliberately ignored — toabify has no use for them.

        A *button_label* is copied into the onClick object, because the
        frontend engine only reads the button label from onClick.label.
        Both label sources are escaped, capped at _MAX_LABEL_LENGTH and
        validated as strings in one place.
        """
        try:
            data = cast(
                dict[str, Any],
                _NOTIFY_DATA_SCHEMA(
                    {k: v for k, v in (kwargs.get("data") or {}).items() if v is not None}
                ),
            )
            on_click = _apply_button_label(data.get("onClick"), data["button_label"])
        except vol.Invalid as err:
            raise ServiceValidationError(f"Invalid notification data: {err}") from err

        callback_data: Any = data.get("callback")
        js_callback: str | None = None
        if isinstance(callback_data, str) and callback_data.startswith(("/", "http")):
            js_callback = callback_data

        duration = data.get("duration")  # May be None if not provided

        event_data = {
            "message": message,
            "duration": duration if duration is not None else DEFAULT_DURATION_EVENT,
            "close": data["close"],
            "position": data.get("position", DEFAULT_POSITION),
            "gravity": data.get("gravity", DEFAULT_GRAVITY),
            "icon": data.get("icon") or data.get("avatar", ""),
            "color": data.get("color", DEFAULT_COLOR),
            "visibility": data.get("visibility", DEFAULT_VISIBILITY),
            "button_label": data.get("button_label", DEFAULT_BUTTON_LABEL),
            "oldestFirst": data.get("oldestFirst", True),
            "onClick": on_click,
            "callback": js_callback,
        }

        self.hass.bus.async_fire(
            EVENT_TOAST, event_data, origin=EventOrigin.local, context=Context()
        )

        if isinstance(callback_data, dict):
            await self._handle_callback(callback_data, duration)

    async def _handle_callback(self, callback_data: dict | None, duration: int | None) -> None:
        """Schedule a server-side service call if callback data specifies one.

        Validates the service action format to prevent injection attacks
        and enforces a maximum duration limit.

        Args:
            callback_data: Dict containing 'action' and optional 'action_data'
            duration: Delay in milliseconds before executing the callback
        """
        if not isinstance(callback_data, dict):
            return

        action = callback_data.get("action", "")

        if not isinstance(action, str) or not _VALID_SERVICE_RE.match(action):
            _LOGGER.warning("Invalid callback action format: %s", action)
            return

        timer_duration = duration if duration is not None else DEFAULT_TIMEOUT
        if timer_duration <= 0:
            return

        domain, service = action.split(".", 1)
        service_params = callback_data.get("action_data", {})
        if not isinstance(service_params, dict):
            _LOGGER.warning("action_data must be a dict, got: %s", type(service_params))
            return
        service_params = dict(service_params)

        async def execute_callback(_) -> None:
            try:
                await self.hass.services.async_call(domain, service, service_params)
            except (ServiceValidationError, ValueError) as err:
                _LOGGER.error(
                    "Failed to execute callback service %s.%s: %s",
                    domain,
                    service,
                    err,
                )
            except Exception:
                _LOGGER.exception(
                    "Unexpected error executing callback service %s.%s",
                    domain,
                    service,
                )

        async_call_later(self.hass, timer_duration / 1000, execute_callback)


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> ToastifyNotificationService:
    """Return the toABify notification service."""
    return ToastifyNotificationService(hass)
