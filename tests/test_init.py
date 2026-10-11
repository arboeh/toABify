"""Tests for the toABify notification platform initialization.

These are characterization tests verifying the existing behavior of async_setup:
  - static path '/toastify_lib' pointing at the vendored dist directory
  - WebSocket command 'toastify/subscribe'
  - extra JS URL '/toastify_lib/toast_engine.js'

The identifiers (event, WS type, URL path) come from toast_engine.js and do
not change during the refactor (see D2).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.toabify import async_setup


async def test_async_setup_registers_static_path(hass, enable_custom_integrations):
    """Test that async_setup registers a static path at /toastify_lib."""
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch("custom_components.toabify.websocket_api.async_register_command"),
        patch("custom_components.toabify.add_extra_js_url"),
    ):
        result = await async_setup(hass, {})

    assert result is True
    hass.http.async_register_static_paths.assert_called_once()
    configs = hass.http.async_register_static_paths.call_args[0][0]
    assert configs[0].url_path == "/toastify_lib"
    assert configs[0].path.endswith("dist")


async def test_async_setup_registers_websocket_command(hass, enable_custom_integrations):
    """Test that async_setup registers the 'toastify/subscribe' WebSocket command."""
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch("custom_components.toabify.websocket_api.async_register_command") as mock_register_ws,
        patch("custom_components.toabify.add_extra_js_url"),
    ):
        await async_setup(hass, {})

    assert mock_register_ws.called
    handler = mock_register_ws.call_args[0][1]
    assert handler.__name__ == "websocket_subscribe_toast"


async def test_async_setup_adds_extra_js_url(hass, enable_custom_integrations):
    """Test that async_setup injects /toastify_lib/toast_engine.js into the frontend."""
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch("custom_components.toabify.websocket_api.async_register_command"),
        patch("homeassistant.components.frontend.add_extra_js_url") as mock_add_js,
    ):
        await async_setup(hass, {})

    mock_add_js.assert_called_once_with(hass, "/toastify_lib/toast_engine.js")
