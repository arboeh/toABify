"""The toABify notify platform."""

from __future__ import annotations

from homeassistant.components.notify import BaseNotificationService
from homeassistant.core import Context, EventOrigin
from homeassistant.helpers.event import async_call_later

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


async def async_get_service(hass, config, discovery_info=None):
    """Set up the toABify notification platform."""
    return ToastifyNotificationService(hass)


class ToastifyNotificationService(BaseNotificationService):
    """Notification service that fires toasts to the frontend via WebSocket."""

    def __init__(self, hass):
        """Initialize the service."""
        self.hass = hass

    async def async_send_message(self, message: str = "", **kwargs) -> None:
        """Send a toast notification to the frontend.

        The event is fired on the bus; the frontend WebSocket listener
        (websocket_subscribe_toast) forwards it to connected clients.

        Callback data can be a string URL or a dict specifying a
        server-side service call to execute after *duration* milliseconds.
        """
        data = kwargs.get("data") or {}
        callback_data = data.get("callback")
        js_callback = None

        if isinstance(callback_data, str) and (
            callback_data.startswith("/") or callback_data.startswith("http")
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

        if isinstance(callback_data, dict):
            action = callback_data.get("action", "")
            if "." in action:
                domain, service = action.split(".")
                service_params = callback_data.get("action_data", {})

                if duration > 0:

                    async def execute_callback(_):
                        await self.hass.services.async_call(domain, service, service_params)

                    async_call_later(self.hass, duration / 1000, execute_callback)
