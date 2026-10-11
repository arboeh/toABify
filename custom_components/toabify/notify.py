"""The toABify notify platform."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.components.notify import (
    BaseNotificationService,
    PLATFORM_SCHEMA,
)
from homeassistant.components.notify import async_reject_receipt
from homeassistant.core import Context, EventOrigin, HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType

from .const import (
    DEFAULT_BUTTON_LABEL,
    DEFAULT_COLOR,
    DEFAULT_DURATION_EVENT,
    DEFAULT_GRAVITY,
    DEFAULT_POSITION,
    DEFAULT_TIMEOUT,
    DEFAULT_VISIBILITY,
    EVENT_TOAST,
)

_LOGGER = logging.getLogger(__name__)

_NOTIFY_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("duration", default=DEFAULT_TIMEOUT): vol.All(
            vol.Coerce(int), vol.Range(min=0)
        ),
        vol.Optional("close", default=False): bool,
        vol.Optional("position", default=DEFAULT_POSITION): vol.In(
            ["left", "right", "center"]
        ),
        vol.Optional("gravity", default=DEFAULT_GRAVITY): vol.In(
            ["top", "bottom", "center"]
        ),
        vol.Optional("icon", default=""): str,
        vol.Optional("color", default=DEFAULT_COLOR): vol.In(
            ["success", "info", "warning", "error", "alert", "default"]
        ),
        vol.Optional("visibility", default=DEFAULT_VISIBILITY): vol.In(
            ["all", "dashboard"]
        ),
        vol.Optional("button_label", default=DEFAULT_BUTTON_LABEL): str,
        vol.Optional("oldestFirst", default=True): bool,
        vol.Optional("onClick"): dict,
        vol.Optional("callback"): vol.Any(str, dict),
    },
    extra=vol.PREVENT_EXTRA,
)


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: tuple | None = None,
) -> ToastifyNotificationService:
    """Set up the toABify notification platform."""
    return ToastifyNotificationService(hass)


class ToastifyNotificationService(BaseNotificationService):
    """Notification service that fires toasts to the frontend via WebSocket."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the service."""
        self.hass = hass

    async def async_send_message(self, message: str = "", **kwargs) -> None:
        """Send a toast notification to the frontend.

        The event is fired on the bus; the frontend WebSocket listener
        (websocket_subscribe_toast) forwards it to connected clients.

        Callback data can be a string URL or a dict specifying a
        server-side service call to execute after *duration* milliseconds.
        """
        try:
            data = _NOTIFY_DATA_SCHEMA(kwargs.get("data") or {})
        except vol.Invalid as err:
            raise ServiceValidationError(
                f"Invalid notification data: {err}"
            ) from err

        callback_data = data.get("callback")
        js_callback = None

        if isinstance(callback_data, str) and callback_data.startswith(
            ("/", "http")
        ):
            js_callback = callback_data

        duration = data.get("duration", DEFAULT_TIMEOUT)

        event_data = {
            "message": message,
            "duration": data.get("duration", DEFAULT_DURATION_EVENT),
            "close": data.get("close", False),
            "position": data.get("position", DEFAULT_POSITION),
            "gravity": data.get("gravity", DEFAULT_GRAVITY),
            "icon": data.get("icon", data.get("avatar", "")),
            "color": data.get("color", DEFAULT_COLOR),
            "visibility": data.get("visibility", DEFAULT_VISIBILITY),
            "button_label": data.get("button_label", DEFAULT_BUTTON_LABEL),
            "oldestFirst": data.get("oldestFirst", True),
            "onClick": data.get("onClick"),
            "callback": js_callback,
        }

        self.hass.bus.async_fire(
            EVENT_TOAST, event_data, origin=EventOrigin.local, context=Context()
        )

        self._handle_callback(callback_data, duration)

    def _handle_callback(self, callback_data, duration: int) -> None:
        """Schedule a server-side service call if callback data specifies one."""
        if not isinstance(callback_data, dict):
            return

        action = callback_data.get("action", "")
        if "." not in action or duration <= 0:
            return

        domain, service = action.split(".")
        service_params = callback_data.get("action_data", {})

        async def execute_callback(_) -> None:
            await self.hass.services.async_call(
                domain, service, service_params
            )

        async_call_later(self.hass, duration / 1000, execute_callback)