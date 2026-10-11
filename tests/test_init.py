"""Tests for the toABify integration setup and unload.

These are characterization tests verifying the existing behavior:
  - static path '/toastify_lib' pointing at the vendored dist directory
  - WebSocket command 'toastify/subscribe'
  - extra JS URL '/toastify_lib/toast_engine.js'
  - proper cleanup on unload via remove_extra_js_url

The identifiers (event, WS type, URL path) come from toast_engine.js and do
not change during the refactor (see D2).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.toabify import async_setup_entry, async_unload_entry
from custom_components.toabify.const import (
    DOMAIN,
    STATIC_URL_PATH,
    TOAST_ENGINE_JS,
    WS_TYPE_SUBSCRIBE,
)


async def test_setup_entry_registers_static_path(hass, enable_custom_integrations):
    """Test that async_setup_entry registers a static path at /toastify_lib."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch("custom_components.toabify.websocket_api.async_register_command"),
        patch("custom_components.toabify.add_extra_js_url"),
        patch("custom_components.toabify.discovery.async_load_platform", new_callable=AsyncMock),
    ):
        result = await async_setup_entry(hass, entry)

    assert result is True
    hass.http.async_register_static_paths.assert_called_once()
    configs = hass.http.async_register_static_paths.call_args[0][0]
    assert configs[0].url_path == STATIC_URL_PATH
    assert configs[0].path.endswith("dist")


async def test_setup_entry_registers_websocket_command(hass, enable_custom_integrations):
    """Test that async_setup_entry registers the 'toastify/subscribe' WebSocket command."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch("custom_components.toabify.websocket_api.async_register_command") as mock_register_ws,
        patch("custom_components.toabify.add_extra_js_url"),
        patch("custom_components.toabify.discovery.async_load_platform", new_callable=AsyncMock),
    ):
        await async_setup_entry(hass, entry)

    assert mock_register_ws.called
    handler = mock_register_ws.call_args[0][1]
    assert handler.__name__ == "websocket_subscribe_toast"


async def test_setup_entry_adds_extra_js_url(hass, enable_custom_integrations):
    """Test that async_setup_entry injects /toastify_lib/toast_engine.js into the frontend."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch("custom_components.toabify.websocket_api.async_register_command"),
        patch("custom_components.toabify.add_extra_js_url") as mock_add_js,
        patch("custom_components.toabify.discovery.async_load_platform", new_callable=AsyncMock),
    ):
        await async_setup_entry(hass, entry)

    mock_add_js.assert_called_once_with(hass, TOAST_ENGINE_JS)


async def test_unload_entry_removes_extra_js_url(hass, enable_custom_integrations):
    """Test that async_unload_entry removes the JS URL via remove_extra_js_url."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch("custom_components.toabify.websocket_api.async_register_command"),
        patch("custom_components.toabify.add_extra_js_url"),
        patch("custom_components.toabify.remove_extra_js_url") as mock_remove,
        patch("custom_components.toabify.discovery.async_load_platform", new_callable=AsyncMock),
        patch("homeassistant.core.ServiceRegistry.async_remove") as mock_remove_service,
    ):
        await async_setup_entry(hass, entry)
        result = await async_unload_entry(hass, entry)

    assert result is True
    mock_remove.assert_called_once_with(hass, TOAST_ENGINE_JS)
    mock_remove_service.assert_called_once_with("notify", DOMAIN)


async def test_unload_entry_returns_true_when_entry_not_found(
    hass,
    enable_custom_integrations,
):
    """Test that async_unload_entry handles missing entry gracefully."""
    entry = MagicMock()
    entry.entry_id = "nonexistent_entry"

    result = await async_unload_entry(hass, entry)
    assert result is True


async def test_setup_entry_stores_coordinator(hass, enable_custom_integrations):
    """Test that async_setup_entry stores a coordinator in hass.data."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch("custom_components.toabify.websocket_api.async_register_command"),
        patch("custom_components.toabify.add_extra_js_url"),
        patch("custom_components.toabify.discovery.async_load_platform", new_callable=AsyncMock),
    ):
        await async_setup_entry(hass, entry)

    from custom_components.toabify.const import DOMAIN

    assert DOMAIN in hass.data
    assert "test_entry" in hass.data[DOMAIN]
    coordinator = hass.data[DOMAIN]["test_entry"]
    assert STATIC_URL_PATH in coordinator.static_paths
    assert WS_TYPE_SUBSCRIBE in coordinator.ws_commands
    assert TOAST_ENGINE_JS in coordinator.js_urls


async def test_setup_entry_loads_notify_platform(hass, enable_custom_integrations):
    """Test that async_setup_entry loads the notify platform via discovery."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch("custom_components.toabify.websocket_api.async_register_command"),
        patch("custom_components.toabify.add_extra_js_url"),
        patch(
            "custom_components.toabify.discovery.async_load_platform", new_callable=AsyncMock
        ) as mock_load_platform,
    ):
        result = await async_setup_entry(hass, entry)

    assert result is True
    mock_load_platform.assert_called_once_with(hass, "notify", DOMAIN, {"name": DOMAIN}, {})


def test_no_yaml_setup_dead_code():
    """Verify that YAML-compatibility dead code was removed."""
    import custom_components.toabify as init_module

    assert not hasattr(init_module, "CONFIG_SCHEMA")
    assert not hasattr(init_module, "async_setup")
