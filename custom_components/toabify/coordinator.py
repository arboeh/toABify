"""Coordinator for the toABify custom integration.

Manages integration-wide state, resource registration tracking, and
lifecycle cleanup in accordance with Home Assistant best practices.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


@dataclass
class IntegrationState:
    """Tracks resources registered by this integration instance."""

    static_paths: set[str] = field(default_factory=set)
    ws_commands: set[str] = field(default_factory=set)
    js_urls: list[str] = field(default_factory=list)


class ToastifyCoordinator(DataUpdateCoordinator[None]):
    """Coordinators for the toABify integration.

    This integration is event-driven (no polling needed), but the
    coordinator pattern provides a single place to manage the
    integration's registered resources and shared state.
    """

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry | None = None) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=__name__,
            name="ToABify",
            config_entry=config_entry,
        )
        self._state = IntegrationState()

    @property
    def static_paths(self) -> set[str]:
        """Return registered static paths."""
        return self._state.static_paths

    @property
    def ws_commands(self) -> set[str]:
        """Return registered WebSocket commands."""
        return self._state.ws_commands

    @property
    def js_urls(self) -> list[str]:
        """Return registered extra JS URLs."""
        return self._state.js_urls

    def async_register_static_path(self, url_path: str) -> None:
        """Track a registered static path."""
        self._state.static_paths.add(url_path)

    def async_register_ws_command(self, command_type: str) -> None:
        """Track a registered WebSocket command."""
        self._state.ws_commands.add(command_type)

    def async_register_js_url(self, url: str) -> None:
        """Track a registered extra JS URL."""
        self._state.js_urls.append(url)

    async def _async_update_data(self) -> None:
        """No data to fetch; this is an event-driven integration.

        The coordinator is used for state management and resource
        lifecycle tracking, not for polling.
        """
        return None
