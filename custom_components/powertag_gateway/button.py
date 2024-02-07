import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_CLIENT, DOMAIN
from .entity_base import PowerTagEntity, gateway_device_info, tag_device_info, is_r, is_powertag
from .schneider_modbus import SchneiderModbus

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PowerTag Link Gateway from a config entry."""

    data = hass.data[DOMAIN][config_entry.entry_id]

    client = data[CONF_CLIENT]
    presentation_url = data[CONF_INTERNAL_URL]

    entities = []

    gateway_device = gateway_device_info(client, presentation_url)

    for i in range(1, 100):
        _LOGGER.info(f"Setting up device index {i}")
        modbus_address = client.modbus_address_of_node(i)
        _LOGGER.info(f"Modbus address of that device is {i}")
        if modbus_address is None:
            break

        product_type = client.tag_product_type(modbus_address)
        _LOGGER.info(f"Setting up {product_type}...")
        if not is_powertag(product_type):
            _LOGGER.warning(f"Product {product_type} is not yet supported by this integration.")
            continue

        tag_device = tag_device_info(
            client, modbus_address, presentation_url, next(iter(gateway_device["identifiers"]))
        )

        if client.type_of_gateway is not TypeOfGateway.SMARTLINK:
            is_disabled = client.tag_radio_lqi_gateway(modbus_address) is None
            if is_disabled:
                _LOGGER.warning(f"The device {client.tag_name(modbus_address)} is not reachable; will ignore this one.")
                continue

        entities.append(PowerTagResetPeakDemand(client, modbus_address, tag_device))

        class_r = is_r(product_type)

        if class_r:
            entities.extend([
                PowerTagResetActiveEnergy(client, modbus_address, tag_device),
                PowerTagResetActiveEnergyDelivered(client, modbus_address, tag_device),
                PowerTagResetActiveEnergyReceived(client, modbus_address, tag_device),
                PowerTagResetReactiveEnergyDelivered(client, modbus_address, tag_device),
                PowerTagResetReactiveEnergyReceived(client, modbus_address, tag_device),
            ])

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


class PowerTagResetActiveEnergy(PowerTagEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reset active energy")

    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_energy_active_partial(self._modbus_index)


class PowerTagResetActiveEnergyDelivered(PowerTagEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reset active energy delivered")

    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_energy_active_delivered_partial(self._modbus_index)


class PowerTagResetActiveEnergyReceived(PowerTagEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reset active energy received")

    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_energy_active_received_partial(self._modbus_index)


class PowerTagResetReactiveEnergyDelivered(PowerTagEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reset reactive energy delivered")

    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_energy_reactive_delivered_partial(self._modbus_index)


class PowerTagResetReactiveEnergyReceived(PowerTagEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reset reactive energy received")

    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_energy_reactive_received_partial(self._modbus_index)
