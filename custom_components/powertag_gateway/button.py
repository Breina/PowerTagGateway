import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UniqueIdVersion
from .device_features import FeatureClass
from .entity_base import WirelessDeviceEntity, async_setup_entities
from .schneider_modbus import SchneiderModbus, TypeOfGateway

_LOGGER = logging.getLogger(__name__)


def list_buttons() -> list[type[WirelessDeviceEntity]]:
    return [
        PowerTagResetPeakDemand,
        PowerTagResetActiveEnergyDelivered,
        PowerTagResetActiveEnergyReceived,
        PowerTagResetReactiveEnergyDelivered,
        PowerTagResetReactiveEnergyReceived,
        PowerTagResetApparentEnergy
    ]


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PowerTag Link Gateway from a config entry."""
    buttons = list_buttons()

    entities = await async_setup_entities(hass, config_entry, buttons)
    async_add_entities(entities, update_before_add=False)


class PowerTagResetPeakDemand(WirelessDeviceEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "reset peak demand", unique_id_version)

    async def async_press(self) -> None:
        await self.async_reset()

    async def async_reset(self):
        await self._client.tag_reset_peak_demands(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagResetActiveEnergyDelivered(WirelessDeviceEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "reset active energy delivered", unique_id_version)

    async def async_press(self) -> None:
        await self.async_reset()

    async def async_reset(self):
        await self._client.tag_reset_energy_active_delivered_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.F1 , FeatureClass.F3, FeatureClass.FL,
                                 FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagResetActiveEnergyReceived(WirelessDeviceEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "reset active energy received", unique_id_version)

    async def async_press(self) -> None:
        await self.async_reset()

    async def async_reset(self):
        await self._client.tag_reset_energy_active_received_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.F1, FeatureClass.F3, FeatureClass.FL,
                                 FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagResetReactiveEnergyDelivered(WirelessDeviceEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "reset reactive energy delivered", unique_id_version)

    async def async_press(self) -> None:
        await self.async_reset()

    async def async_reset(self):
        await self._client.tag_reset_energy_reactive_delivered_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3, FeatureClass.R1
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagResetReactiveEnergyReceived(WirelessDeviceEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "reset reactive energy received", unique_id_version)

    async def async_press(self) -> None:
        await self.async_reset()

    async def async_reset(self):
        await self._client.tag_reset_energy_reactive_received_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3, FeatureClass.R1
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagResetApparentEnergy(WirelessDeviceEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "reset apparent energy", unique_id_version)

    async def async_press(self) -> None:
        await self.async_reset()

    async def async_reset(self):
        await self._client.tag_reset_energy_apparent_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]
