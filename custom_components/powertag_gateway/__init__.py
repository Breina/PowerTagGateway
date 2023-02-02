"""PowerTag Link Gateway integration"""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT, CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pymodbus.exceptions import ConnectionException

from .const import CONF_CLIENT, DOMAIN
from .schneider_modbus import SchneiderModbus

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NAD multi-room audio controller from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT)
    presentation_url = entry.data.get(CONF_INTERNAL_URL)

    try:
        client = SchneiderModbus(host, port)
    except ConnectionException as e:
        raise ConfigEntryNotReady from e

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_CLIENT: client,
        CONF_INTERNAL_URL: presentation_url
    }

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(
                entry, platform
            )
        )

    return True
