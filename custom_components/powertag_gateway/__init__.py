"""PowerTag Link Gateway integration"""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, DOMAIN
from homeassistant.exceptions import ConfigEntryNotReady
from pymodbus.exceptions import ConnectionException

from .const import CONF_CLIENT
from .schneider_modbus import SchneiderModbus

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NAD multi-room audio controller from a config entry."""

    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT)

    try:
        client = SchneiderModbus(host, port)
    except ConnectionException as e:
        raise ConfigEntryNotReady from e

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_CLIENT: client
    }

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True
