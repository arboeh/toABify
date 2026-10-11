"""Tests for the toABify notify platform.

These are characterization tests capturing the current behavior of
ToastifyNotificationService.send_message / async_send_message.

The internal protocol identifiers (EVENT_TOAST = "toastify_event",
WS_TYPE_SUBSCRIBE = "toastify/subscribe", STATIC_URL_PATH = "/toastify_lib")
are hardcoded in dist/toast_engine.js and do not change during the refactor.
"""

from __future__ import annotations

import datetime as dt

import pytest
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.toabify.notify import ToastifyNotificationService

# These values match the current hardcoded defaults and will be preserved
# in const.py during the refactoring (Task 5).
EVENT_TOAST = "toastify_event"
DEFAULT_BUTTON_LABEL = "VOIR"
DEFAULT_COLOR = "info"
DEFAULT_GRAVITY = "top"
DEFAULT_POSITION = "right"
DEFAULT_VISIBILITY = "dashboard"


async def test_send_message_defaults(hass, enable_custom_integrations):
    """Test that default values match the existing hardcoded defaults."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message("Hello world")
    await hass.async_block_till_done()

    assert len(events) == 1
    data = events[0].data
    assert data["message"] == "Hello world"
    assert data["duration"] == 5000
    assert data["close"] is False
    assert data["position"] == DEFAULT_POSITION
    assert data["gravity"] == DEFAULT_GRAVITY
    assert data["color"] == DEFAULT_COLOR
    assert data["visibility"] == DEFAULT_VISIBILITY
    assert data["button_label"] == DEFAULT_BUTTON_LABEL
    assert data["oldestFirst"] is True
    assert data["icon"] == ""
    assert data["onClick"] is None
    assert data["callback"] is None


async def test_send_message_empty_message(hass, enable_custom_integrations):
    """Empty message still produces a valid event."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message("")
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["message"] == ""


# Icon / avatar fallback


async def test_icon_falls_back_to_avatar(hass, enable_custom_integrations):
    """When 'icon' is not provided, 'avatar' should be used."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={"avatar": "https://example.com/avatar.png"},
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["icon"] == "https://example.com/avatar.png"


async def test_icon_overrides_avatar(hass, enable_custom_integrations):
    """When both 'icon' and 'avatar' are provided, 'icon' wins."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={
            "icon": "/local/icon.png",
            "avatar": "/local/avatar.png",
        },
    )
    await hass.async_block_till_done()

    assert events[0].data["icon"] == "/local/icon.png"


# ---------------------------------------------------------------------------
# Callback as string
# ---------------------------------------------------------------------------


async def test_callback_url_with_slash(hass, enable_custom_integrations):
    """callback as a string starting with '/' is passed through."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={"callback": "/local/foo"},
    )
    await hass.async_block_till_done()

    assert events[0].data["callback"] == "/local/foo"


async def test_callback_url_with_http(hass, enable_custom_integrations):
    """callback as a string starting with 'http' is passed through."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={"callback": "https://example.com"},
    )
    await hass.async_block_till_done()

    assert events[0].data["callback"] == "https://example.com"


async def test_callback_string_without_url_is_none(hass, enable_custom_integrations):
    """callback string without '/' or 'http' prefix becomes None."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={"callback": "not_a_url"},
    )
    await hass.async_block_till_done()

    assert events[0].data["callback"] is None


# ---------------------------------------------------------------------------
# Callback as dict (server-side service invocation)
# ---------------------------------------------------------------------------


async def test_callback_dict_calls_service(hass, enable_custom_integrations):
    """callback dict with action triggers a service call after duration/1000."""
    mock_calls = async_mock_service(hass, "light", "turn_on")
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={
            "duration": 3000,
            "callback": {
                "action": "light.turn_on",
                "action_data": {"entity_id": "light.test"},
            },
        },
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["callback"] is None

    # Advance by duration/1000 = 3 seconds
    async_fire_time_changed(
        hass,
        dt.datetime.now(dt.UTC) + dt.timedelta(seconds=3),
    )
    await hass.async_block_till_done()

    assert len(mock_calls) == 1
    assert mock_calls[0].data == {"entity_id": "light.test"}


async def test_callback_dict_default_timer_3000(hass, enable_custom_integrations):
    """Without explicit duration, the timer defaults to 3000 ms.

    duration=3000 → timer fires after 3 seconds.
    The event payload still shows duration=5000 (different default for display).
    """
    mock_calls = async_mock_service(hass, "switch", "toggle")
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={
            "callback": {
                "action": "switch.toggle",
                "action_data": {"entity_id": "switch.test"},
            },
        },
    )
    await hass.async_block_till_done()

    # Event duration default is 5000, timer default is 3000
    assert events[0].data["duration"] == 5000

    # Timer should fire after 3 seconds (3000 ms default)
    async_fire_time_changed(
        hass,
        dt.datetime.now(dt.UTC) + dt.timedelta(seconds=3),
    )
    await hass.async_block_till_done()

    assert len(mock_calls) == 1


async def test_callback_dict_duration_le_zero_no_timer(hass, enable_custom_integrations):
    """When duration <= 0, no timer is scheduled."""
    mock_calls = async_mock_service(hass, "light", "turn_on")
    service = ToastifyNotificationService(hass)

    await service.async_send_message(
        "Hello",
        data={
            "duration": 0,
            "callback": {
                "action": "light.turn_on",
                "action_data": {"entity_id": "light.test"},
            },
        },
    )
    await hass.async_block_till_done()

    # Advance well past the would-be timer
    async_fire_time_changed(
        hass,
        dt.datetime.now(dt.UTC) + dt.timedelta(seconds=10),
    )
    await hass.async_block_till_done()

    assert len(mock_calls) == 0


async def test_callback_dict_negative_duration_no_timer(hass, enable_custom_integrations):
    """Negative duration (e.g. -1 for persistent) does not schedule a timer."""
    mock_calls = async_mock_service(hass, "light", "turn_on")
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={
            "duration": -1,
            "callback": {
                "action": "light.turn_on",
                "action_data": {"entity_id": "light.test"},
            },
        },
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["duration"] == -1

    async_fire_time_changed(
        hass,
        dt.datetime.now(dt.UTC) + dt.timedelta(seconds=10),
    )
    await hass.async_block_till_done()

    assert len(mock_calls) == 0


async def test_callback_dict_multiple_dots_raises_value_error(hass, enable_custom_integrations):
    """An action with more than one dot raises ValueError (split('.', 1) is not used)."""
    mock_calls = async_mock_service(hass, "light", "turn_on")
    service = ToastifyNotificationService(hass)

    with pytest.raises(ValueError):
        await service.async_send_message(
            "Hello",
            data={
                "duration": 3000,
                "callback": {
                    "action": "light.turn_on.foo",
                    "action_data": {"entity_id": "light.test"},
                },
            },
        )
    await hass.async_block_till_done()

    assert len(mock_calls) == 0
