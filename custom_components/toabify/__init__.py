"""The toABify custom integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    EVENT_TOAST,
    STATIC_PATH,
    STATIC_URL_PATH,
    TOAST_ENGINE_JS,
    WS_TYPE_SUBSCRIBE,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({})},
    extra=vol.ALLOW_EXTRA,
)


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_SUBSCRIBE,
    }
)
@callback
def websocket_subscribe_toast(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Subscribe to toast notifications via WebSocket."""
    @callback
    def forward_toast(event: Event) -> None:
        connection.send_message(
            websocket_api.event_message(msg["id"], event.data)
        )

    connection.subscriptions[msg["id"]] = hass.bus.async_listen(
        EVENT_TOAST, forward_toast
    )
    connection.send_result(msg["id"])

    _LOGGER.debug("WebSocket subscription established for toast notifications")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up toABify - keep for YAML compatibility / migrations."""
    _LOGGER.debug("toABify async_setup (YAML) called")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Register static path, WebSocket command, and extra JS URL.

    Args:
        hass: HomeAssistant instance
        entry: ConfigEntry for this integration

    Returns:
        True if setup succeeded

    Raises:
        ConfigEntryNotReady: If static path registration fails
    """
    _LOGGER.debug("Setting up toABify integration")

    try:
        toast_path_config = StaticPathConfig(
            url_path=STATIC_URL_PATH,
            path=hass.config.path(STATIC_PATH),
            cache_headers=False,
        )
        await hass.http.async_register_static_paths([toast_path_config])
        _LOGGER.debug("Static path registered: %s", STATIC_URL_PATH)
    except Exception as err:
        _LOGGER.error(
            "Failed to register static path for toABify: %s", err
        )
        raise ConfigEntryNotReady(
            f"Failed to register static path: {err}"
        ) from err

    websocket_api.async_register_command(hass, websocket_subscribe_toast)
    add_extra_js_url(hass, TOAST_ENGINE_JS)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "static_path": STATIC_URL_PATH,
        "ws_type": WS_TYPE_SUBSCRIBE,
    }

    _LOGGER.info("toABify integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: HomeAssistant instance
        entry: ConfigEntry to unload

    Returns:
        True if unload succeeded
    """
    _LOGGER.debug("Unloading toABify integration")

    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        del hass.data[DOMAIN][entry.entry_id]

    # Note: WebSocket commands and static paths are not explicitly
    # unregisterable in HA without a full reload. The entry unload
    # primarily clears our internal data structures.

    _LOGGER.info("toABify integration unloaded")
    return True
