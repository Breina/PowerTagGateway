"""PowerTag Link Gateway integration"""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import GATEWAY_DOMAIN

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NAD multi-room audio controller from a config entry."""
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True
