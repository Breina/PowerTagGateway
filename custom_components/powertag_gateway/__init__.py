"""PowerTag Link Gateway integration"""

import asyncio
import logging
from enum import Enum, auto

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT, CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from pymodbus.exceptions import ConnectionException

from .const import (
    CONF_CLIENT,
    CONF_SETUP_LOCK,
    CONF_PRESENT_DEVICES,
    DOMAIN,
    CONF_TYPE_OF_GATEWAY,
    CONF_DEVICE_UNIQUE_ID_VERSION,
)
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
    type_of_gateway_string = entry.data.get(
        CONF_TYPE_OF_GATEWAY, TypeOfGateway.POWERTAG_LINK.value
    )

    type_of_gateway = [t for t in TypeOfGateway if t.value == type_of_gateway_string][0]

    unique_id_version_val = entry.data.get(CONF_DEVICE_UNIQUE_ID_VERSION)
    if unique_id_version_val is None:
        unique_id_version = UniqueIdVersion.V0
    else:
        unique_id_version = UniqueIdVersion(unique_id_version_val)

    try:
        client = await SchneiderModbus.create(host, type_of_gateway, port)
    except ConnectionException as e:
        raise ConfigEntryNotReady from e

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_CLIENT: client,
        CONF_INTERNAL_URL: presentation_url,
        CONF_DEVICE_UNIQUE_ID_VERSION: unique_id_version,
        # Platforms scan the gateway one after another, see async_setup_entities.
        CONF_SETUP_LOCK: asyncio.Lock(),
        # Identifiers of the devices found on the gateway during the last scan,
        # see async_remove_config_entry_device.
        CONF_PRESENT_DEVICES: set(),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: ConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Allow removing a device from the UI once it is no longer on the gateway.

    Devices that were removed or replaced in the gateway (e.g. a faulty PowerTag
    swapped for a new one) otherwise stay behind in the device registry forever.
    A device that the gateway still reports is refused, as it would simply be
    re-created on the next reload.
    """
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if data is None:
        # Entry not loaded: we cannot tell what is on the gateway, be safe.
        return False
    present = data[CONF_PRESENT_DEVICES]
    return not any(identifier in present for identifier in device_entry.identifiers)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if data is None:
        return True
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False
    client = data.get(CONF_CLIENT)
    if client is not None:
        try:
            if getattr(client, "client", None) is not None:
                client.client.close()
        except Exception as err:
            _LOGGER.warning("Error while closing Modbus client: %s", err)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
