"""Test configuration for toABify custom component tests.

Re-exports the enable_custom_integrations fixture provided by
pytest-homeassistant-custom-component so that custom integrations
defined in the test directory can be loaded.
"""

from collections.abc import Generator

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.loader import DATA_CUSTOM_COMPONENTS


@pytest.fixture
def enable_custom_integrations(hass: HomeAssistant) -> Generator[None]:
    """Enable custom integrations defined in the test directory."""
    hass.data.pop(DATA_CUSTOM_COMPONENTS)
    yield
