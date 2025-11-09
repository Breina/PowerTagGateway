"""PowerTag Link Gateway integration"""
import logging
from enum import Enum, auto

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT, \
    CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pymodbus.exceptions import ConnectionException

from .const import CONF_CLIENT, DOMAIN, CONF_TYPE_OF_GATEWAY, \
    CONF_DEVICE_UNIQUE_ID_VERSION
from .schneider_modbus import SchneiderModbus, TypeOfGateway

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


class UniqueIdVersion(Enum):
    V0 = auto()
    V1 = auto()  # V1 is the same as V0 because of the bug in Issue #51
    V2 = auto()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EcoStruxure PowerTag Link Gateway from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT)
    presentation_url = entry.data.get(CONF_INTERNAL_URL)
    type_of_gateway_string = (
        entry.data.get(CONF_TYPE_OF_GATEWAY, TypeOfGateway.POWERTAG_LINK.value))

    type_of_gateway = [t for t in TypeOfGateway if t.value == type_of_gateway_string][0]

    unique_id_version = UniqueIdVersion(entry.data.get(CONF_DEVICE_UNIQUE_ID_VERSION))
    if unique_id_version is None:
        _LOGGER.warning("Using older version of device's unique ID, "
                        "may cause conflicts with duplicate serials.")
        unique_id_version = UniqueIdVersion.V0

    try:
        client = SchneiderModbus(host, type_of_gateway, port)
    except ConnectionException as e:
        raise ConfigEntryNotReady from e

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_CLIENT: client,
        CONF_INTERNAL_URL: presentation_url,
        CONF_DEVICE_UNIQUE_ID_VERSION: unique_id_version
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
