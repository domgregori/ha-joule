"""Root conftest: enable custom integrations for all tests."""
import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow HA to load custom integrations from the custom_components/ folder."""
    yield
