from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.powertag_gateway.const import GATEWAY_DOMAIN, CONF_CLIENT
from custom_components.powertag_gateway.entity_base import PowerTagEntity, gateway_device_info, tag_device_info
from custom_components.powertag_gateway.schneider_modbus import SchneiderModbus


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PowerTag Link Gateway from a config entry."""

    data = hass.data[GATEWAY_DOMAIN][config_entry.entry_id]

    client = data(CONF_CLIENT)
    presentation_url = data(CONF_INTERNAL_URL)

    entities = []

    gateway_device = gateway_device_info(client, presentation_url)

    for i in range(1, 100):
        modbus_address = client.modbus_address_of_node(1)
        if modbus_address is None:
            break

        tag_device = tag_device_info(
            client, modbus_address, presentation_url, next(iter(gateway_device["identifiers"]))
        )

        entities.append(PowerTagResetPeakDemand(client, modbus_address, tag_device))

    async_add_entities(entities, update_before_add=False)


class PowerTagResetPeakDemand(PowerTagEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reset peak demand")

    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_peak_demands(self._modbus_index)