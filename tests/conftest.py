"""Test configuration for toABify custom component tests.

Re-exports the enable_custom_integrations fixture provided by
pytest-homeassistant-custom-component so that custom integrations
defined in the test directory can be loaded.
"""

import sys
from collections.abc import Generator

import pytest
import pytest_socket
from homeassistant.core import HomeAssistant
from homeassistant.loader import DATA_CUSTOM_COMPONENTS

if sys.platform == "win32":
    # Windows: Der asyncio-Event-Loop (Proactor) erzeugt intern ein socketpair
    # (AF_INET). Das HA-Plugin sperrt alle Nicht-Unix-Sockets, daher wird die
    # Sperre hier deaktiviert. Linux/CI bleiben unveraendert.
    def _disable_socket_noop(*_args: object, **_kwargs: object) -> None:
        """Sperre unter Windows nicht aktivieren."""

    pytest_socket.disable_socket = _disable_socket_noop


@pytest.fixture
def enable_custom_integrations(hass: HomeAssistant) -> Generator[None]:
    """Enable custom integrations defined in the test directory."""
    hass.data.pop(DATA_CUSTOM_COMPONENTS)
    yield
