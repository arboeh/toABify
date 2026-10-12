"""Tests for the toABify notify platform.

These are characterization tests capturing the current behavior of
ToastifyNotificationService.send_message / async_send_message.

The internal protocol identifiers (EVENT_TOAST = "toastify_event",
WS_TYPE_SUBSCRIBE = "toastify/subscribe", STATIC_URL_PATH = "/toastify_lib")
are hardcoded in dist/toast_engine.js and do not change during the refactor.
"""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.notify import BaseNotificationService
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.toabify.const import DOMAIN
from custom_components.toabify.notify import ToastifyNotificationService, _apply_button_label

# These values match the current hardcoded defaults and will be preserved
# in const.py during the refactoring (Task 5).
EVENT_TOAST = "toastify_event"
DEFAULT_BUTTON_LABEL = "CLOSE"
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


# ---------------------------------------------------------------------------
# Color validation (theme names and hex codes)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "color",
    ["success", "info", "warning", "error", "alert", "default"],
)
async def test_color_theme_names_are_accepted(hass, enable_custom_integrations, color):
    """All theme names configured in TOAST_THEMES pass validation."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message("Hello", data={"color": color})
    await hass.async_block_till_done()

    assert events[0].data["color"] == color


@pytest.mark.parametrize(
    ("color", "expected"),
    [
        ("#fff", "#ffffff"),
        ("#ff5f6d", "#ff5f6d"),
        ("#FF5F6D", "#FF5F6D"),
        ("#ff5f6d80", "#ff5f6d80"),
        ("#ff5f6dff", "#ff5f6dff"),
    ],
)
async def test_color_hex_codes_are_accepted(hass, enable_custom_integrations, color, expected):
    """Hex colors are rendered by the engine, so they must pass validation.

    A #RGB value is expanded to #RRGGBB because the engine derives the label
    contrast from the first six characters only.
    """
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message("Hello", data={"color": color})
    await hass.async_block_till_done()

    assert events[0].data["color"] == expected


@pytest.mark.parametrize("color", ["purple", "#ff5f6", "#gggggg", "", 5])
async def test_color_invalid_rejected(hass, enable_custom_integrations, color):
    """Values that are neither a theme name nor a hex color are rejected."""
    service = ToastifyNotificationService(hass)

    with pytest.raises(ServiceValidationError):
        await service.async_send_message("Hello", data={"color": color})


# ---------------------------------------------------------------------------
# Explicit nulls are treated as "not provided"
# ---------------------------------------------------------------------------


async def test_explicit_nulls_fall_back_to_defaults(hass, enable_custom_integrations):
    """YAML/template callers may pass every optional key as null."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={
            "duration": None,
            "close": None,
            "position": None,
            "gravity": None,
            "color": None,
            "visibility": None,
            "icon": None,
            "avatar": None,
            "button_label": None,
            "oldestFirst": None,
            "onClick": None,
            "callback": None,
        },
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    data = events[0].data
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


async def test_explicit_null_does_not_override_provided_value(hass, enable_custom_integrations):
    """A null next to a real value must not wipe the real value."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={"color": "#ff5f6d", "duration": None, "visibility": None},
    )
    await hass.async_block_till_done()

    assert events[0].data["color"] == "#ff5f6d"
    assert events[0].data["duration"] == 5000
    assert events[0].data["visibility"] == DEFAULT_VISIBILITY


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
# button_label is copied into the onClick object
# ---------------------------------------------------------------------------


async def test_button_label_applied_to_on_click(hass, enable_custom_integrations):
    """The engine reads the button label from onClick.label only."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={"button_label": "Open", "onClick": {"action": "/dashboard-home/default_view"}},
    )
    await hass.async_block_till_done()

    assert events[0].data["onClick"] == {
        "action": "/dashboard-home/default_view",
        "label": "Open",
    }


async def test_explicit_on_click_label_wins(hass, enable_custom_integrations):
    """An explicit onClick.label is not overwritten by button_label."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={
            "button_label": "Open",
            "onClick": {"action": "/dashboard-home/default_view", "label": "Dashboard"},
        },
    )
    await hass.async_block_till_done()

    assert events[0].data["onClick"] == {
        "action": "/dashboard-home/default_view",
        "label": "Dashboard",
    }


async def test_button_label_without_on_click_stays_none(hass, enable_custom_integrations):
    """Without onClick the engine renders no button, so nothing is copied."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message("Hello", data={"button_label": "Open"})
    await hass.async_block_till_done()

    assert events[0].data["onClick"] is None
    assert events[0].data["button_label"] == "Open"


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("</span><img src=x onerror=alert(1)>", "&lt;/span&gt;&lt;img src=x onerror=alert(1)&gt;"),
        ("<script>alert(1)</script>", "&lt;script&gt;alert(1)&lt;/script&gt;"),
        ("<b>x</b>", "&lt;b&gt;x&lt;/b&gt;"),
        ("ON & OFF", "ON &amp; OFF"),
        ('Say "hi"', "Say &quot;hi&quot;"),
        ("a" * 500, "a" * 200),
        ("", "CLOSE"),
    ],
)
async def test_button_label_is_escaped(hass, enable_custom_integrations, label, expected):
    """The engine inserts the label as HTML, so the server must neutralize it."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={"button_label": label, "onClick": {"action": "/dashboard-home/default_view"}},
    )
    await hass.async_block_till_done()

    assert events[0].data["onClick"]["label"] == expected


async def test_explicit_on_click_label_is_escaped(hass, enable_custom_integrations):
    """An explicit label goes through the same choke point."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={"onClick": {"action": "/dash", "label": "<b>Open</b>"}},
    )
    await hass.async_block_till_done()

    assert events[0].data["onClick"]["label"] == "&lt;b&gt;Open&lt;/b&gt;"


async def test_non_string_on_click_label_raises(hass, enable_custom_integrations):
    """A non-string label is rejected as invalid data, not coerced."""
    service = ToastifyNotificationService(hass)

    with pytest.raises(ServiceValidationError, match="must be a string"):
        await service.async_send_message(
            "Hello",
            data={"onClick": {"action": "/dash", "label": 5}},
        )


def test_apply_button_label_does_not_mutate_input():
    """The caller's onClick dict is copied, never modified in place."""
    on_click = {"action": "/dash", "label": "<b>x</b>"}

    labeled = _apply_button_label(on_click, "Open")

    assert on_click == {"action": "/dash", "label": "<b>x</b>"}
    assert labeled["label"] == "&lt;b&gt;x&lt;/b&gt;"


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


# ---------------------------------------------------------------------------
# Direct tests for refactored _handle_callback method
# ---------------------------------------------------------------------------


async def test_handle_callback_passes_through_callback_field(hass, enable_custom_integrations):
    """The callback field in event_data should always be js_callback (string or None)."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={"callback": "https://example.com/callback"},
    )
    await hass.async_block_till_done()

    assert events[0].data["callback"] == "https://example.com/callback"


async def test_handle_callback_dict_passes_none_to_event(hass, enable_custom_integrations):
    """When callback is a dict, the event's callback field should be None (server-side only)."""
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

    await service.async_send_message(
        "Hello",
        data={
            "callback": {
                "action": "light.turn_on",
                "action_data": {"entity_id": "light.test"},
            },
            "duration": 0,
        },
    )
    await hass.async_block_till_done()

    assert events[0].data["callback"] is None


async def test_handle_callback_no_action_no_timer(hass, enable_custom_integrations):
    """Dict callback without an action key should not schedule a timer."""
    mock_calls = async_mock_service(hass, "light", "turn_on")
    service = ToastifyNotificationService(hass)

    await service.async_send_message(
        "Hello",
        data={
            "duration": 3000,
            "callback": {"action_data": {"entity_id": "light.test"}},
        },
    )
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt.datetime.now(dt.UTC) + dt.timedelta(seconds=5),
    )
    await hass.async_block_till_done()

    assert len(mock_calls) == 0


async def test_callback_dict_with_action_data(hass, enable_custom_integrations):
    """Server-side callback with action_data passes params to the service call."""
    mock_calls = async_mock_service(hass, "light", "turn_on")
    service = ToastifyNotificationService(hass)

    await service.async_send_message(
        "Hello",
        data={
            "duration": 1000,
            "callback": {
                "action": "light.turn_on",
                "action_data": {"entity_id": "light.living_room", "brightness": 255},
            },
        },
    )
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt.datetime.now(dt.UTC) + dt.timedelta(seconds=2))
    await hass.async_block_till_done()

    assert len(mock_calls) == 1
    assert mock_calls[0].data == {"entity_id": "light.living_room", "brightness": 255}


async def test_callback_dict_multiple_dots_raises_value_error(hass, enable_custom_integrations):
    """Action with more than one dot fails validation (regex rejects dots in service name)."""
    mock_calls = async_mock_service(hass, "light", "turn_on")
    service = ToastifyNotificationService(hass)
    events = async_capture_events(hass, EVENT_TOAST)

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

    assert events[0].data["callback"] is None  # Server-side callback, not in event
    async_fire_time_changed(hass, dt.datetime.now(dt.UTC) + dt.timedelta(seconds=5))
    await hass.async_block_till_done()

    assert len(mock_calls) == 0  # No service call due to invalid action format


# ---------------------------------------------------------------------------
# Dead code removal verification
# ---------------------------------------------------------------------------


async def test_async_get_service_returns_service(hass, enable_custom_integrations):
    """Verify async_get_service returns a ToastifyNotificationService instance."""
    from custom_components.toabify.notify import async_get_service

    result = await async_get_service(hass, {})
    assert isinstance(result, ToastifyNotificationService)


# ---------------------------------------------------------------------------
# Service description override (replaces the generic core notify schema)
# ---------------------------------------------------------------------------


async def test_async_register_services_overrides_description(hass, enable_custom_integrations):
    """async_register_services keeps the core registration and overrides the schema."""
    super_register = AsyncMock()

    with (
        patch.object(BaseNotificationService, "async_register_services", super_register),
        patch("custom_components.toabify.notify.async_set_service_schema") as mock_set_schema,
    ):
        service = ToastifyNotificationService(hass)
        await service.async_register_services()

    super_register.assert_awaited_once()
    assert mock_set_schema.call_count == 1

    call_args = mock_set_schema.call_args.args
    assert call_args[0] is hass
    assert call_args[1] == "notify"
    assert call_args[2] == DOMAIN

    schema = call_args[3]
    assert set(schema["fields"]) == {"message", "data"}
    assert "target" not in schema["fields"]
    assert "title" not in schema["fields"]
    assert schema["fields"]["message"]["required"] is True


async def test_async_register_services_schema_error_is_logged_only(
    hass, enable_custom_integrations
):
    """A failing description override is logged and does not break the service."""
    super_register = AsyncMock()

    with (
        patch.object(BaseNotificationService, "async_register_services", super_register),
        patch(
            "custom_components.toabify.notify.async_set_service_schema",
            side_effect=RuntimeError("boom"),
        ),
        patch("custom_components.toabify.notify._LOGGER") as mock_logger,
    ):
        service = ToastifyNotificationService(hass)
        await service.async_register_services()

    # The core registration still happened and the error did not propagate.
    super_register.assert_awaited_once()
    mock_logger.exception.assert_called_once()


async def test_non_string_action_no_crash(hass, enable_custom_integrations):
    """Direct call to _handle_callback with a non-string action does not crash."""
    service = ToastifyNotificationService(hass)
    mock_calls = async_mock_service(hass, "light", "turn_on")

    await service._handle_callback({"action": {"not": "a string"}}, 1000)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt.datetime.now(dt.UTC) + dt.timedelta(seconds=2))
    await hass.async_block_till_done()

    assert len(mock_calls) == 0
