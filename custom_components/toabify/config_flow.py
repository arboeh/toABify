"""Config flow for toABify integration."""
from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow handler for toABify."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        return self.async_create_entry(title="toABify", data={})

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration."""
        if user_input is None:
            return self.async_show_form(step_id="reconfigure")
        return self.async_update_reload_and_abort(
            self._get_reconfigure_entry(), data={},
        )

    @staticmethod
    def async_get_reconfigure_flow_context() -> dict[str, Any]:
        """Return the reconfigure flow context."""
        return {}

    def _get_reconfigure_entry(self) -> config_entries.ConfigEntry:
        """Get the config entry for reconfiguration."""
        return self.config_entry  # type: ignore[attr-defined]