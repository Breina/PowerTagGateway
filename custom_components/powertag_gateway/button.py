import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity_base import PowerTagEntity, setup_entities
from .powertag_features import FeatureClass
from .schneider_modbus import SchneiderModbus, TypeOfGateway

_LOGGER = logging.getLogger(__name__)


def list_buttons() -> list[type[PowerTagEntity]]:
    return [
        PowerTagResetPeakDemand,
        PowerTagResetActiveEnergy,
        PowerTagResetActiveEnergyDelivered,
        PowerTagResetActiveEnergyReceived,
        PowerTagResetReactiveEnergyDelivered,
        PowerTagResetReactiveEnergyReceived
    ]


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PowerTag Link Gateway from a config entry."""
    buttons = list_buttons()

    entities = setup_entities(hass, config_entry, buttons)
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

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagResetActiveEnergy(PowerTagEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reset active energy")

    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_energy_active_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagResetActiveEnergyDelivered(PowerTagEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reset active energy delivered")

    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_energy_active_delivered_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagResetActiveEnergyReceived(PowerTagEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reset active energy received")

    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_energy_active_received_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagResetReactiveEnergyDelivered(PowerTagEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reset reactive energy delivered")

    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_energy_reactive_delivered_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagResetReactiveEnergyReceived(PowerTagEntity, ButtonEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reset reactive energy received")

    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_energy_reactive_received_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]
