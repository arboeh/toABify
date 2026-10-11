"""The toABify custom integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType

from .const import (
    EVENT_TOAST,
    STATIC_PATH,
    STATIC_URL_PATH,
    TOAST_ENGINE_JS,
    WS_TYPE_SUBSCRIBE,
)


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_SUBSCRIBE,
    }
)
@callback
def websocket_subscribe_toast(hass, connection, msg):
    @callback
    def forward_toast(event):
        connection.send_message(websocket_api.event_message(msg["id"], event.data))

    connection.subscriptions[msg["id"]] = hass.bus.async_listen(EVENT_TOAST, forward_toast)
    connection.send_result(msg["id"])


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register static path, WebSocket command, and extra JS URL."""
    toast_path_config = StaticPathConfig(
        url_path=STATIC_URL_PATH,
        path=hass.config.path(STATIC_PATH),
        cache_headers=False,
    )
    await hass.http.async_register_static_paths([toast_path_config])

    websocket_api.async_register_command(hass, websocket_subscribe_toast)

    add_extra_js_url(hass, TOAST_ENGINE_JS)

    return True
