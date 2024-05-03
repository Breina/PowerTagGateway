"""Platform for Schneider Energy."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CONF_CLIENT, DOMAIN
from .entity_base import GatewayEntity, PowerTagEntity, setup_entities, gateway_device_info
from .powertag_features import FeatureClass
from .schneider_modbus import SchneiderModbus, Phase, LineVoltage, PowerFactorSignConvention, \
    TypeOfGateway

PLATFORMS: list[str] = ["sensor"]

_LOGGER = logging.getLogger(__name__)


def list_sensors() -> list[type[PowerTagEntity]]:
    return [
        PowerTagTotalActiveEnergy,
        PowerTagTotalActiveEnergyPerPhase,
        PowerTagReactivePower,
        PowerTagReactivePowerPerPhase,
        PowerTagApparentPower,
        PowerTagApparentPowerPerPhase,
        PowerTagPowerFactor,
        PowerTagPowerFactorPerPhase,
        PowerTagPartialActiveEnergyDelivered,
        PowerTagTotalActiveEnergyDelivered,
        PowerTagPartialActiveEnergyDeliveredPerPhase,
        PowerTagTotalActiveEnergyDeliveredPerPhase,
        PowerTagPartialActiveEnergyReceived,
        PowerTagTotalActiveEnergyReceived,
        PowerTagPartialActiveEnergyReceivedPerPhase,
        PowerTagTotalActiveEnergyReceivedPerPhase,
        PowerTagPartialActiveEnergyDeliveredAndReceived,
        PowerTagTotalActiveEnergyDeliveredAndReceived,
        # PowerTagPartialActiveEnergyDeliveredAndReceivedPerPhase,
        PowerTagPartialReactiveEnergyDelivered,
        PowerTagTotalReactiveEnergyDelivered,
        PowerTagPartialReactiveEnergyDeliveredPerPhase,
        PowerTagTotalReactiveEnergyDeliveredPerPhase,
        PowerTagPartialReactiveEnergyReceived,
        PowerTagTotalReactiveEnergyReceived,
        PowerTagPartialReactiveEnergyReceivedPerPhase,
        PowerTagTotalReactiveEnergyReceivedPerPhase,
        PowerTagPartialApparentEnergy,
        PowerTagTotalApparentEnergy,
        PowerTagPartialApparentEnergyPerPhase,
        PowerTagTotalApparentEnergyPerPhase,
        PowerTagCurrent,
        PowerTagCurrentNeutral,
        PowerTagVoltage,
        PowerTagFrequency,
        PowerTagTemperature,
        PowerTagActivePower,
        PowerTagActivePowerPerPhase,
        PowerTagDemandActivePower,
        PowerTagRssiTag,
        PowerTagRssiGateway,
        PowerTagLqiTag,
        PowerTagLqiGateway,
        PowerTagPerTag,
        PowerTagPerGateway
    ]


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PowerTag Link Gateway from a config entry."""
    sensors = list_sensors()
    entities = setup_entities(hass, config_entry, sensors)

    data = hass.data[DOMAIN][config_entry.entry_id]
    presentation_url = data[CONF_INTERNAL_URL]
    client = data[CONF_CLIENT]
    gateway_device = gateway_device_info(client, presentation_url)

    entities.extend([
        GatewayTime(client, gateway_device),
    ])

    async_add_entities(entities, update_before_add=False)


class GatewayTime(GatewayEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, client: SchneiderModbus, tag_device: DeviceInfo):
        super().__init__(client, tag_device, "datetime")

    async def async_update(self):
        self._attr_native_value = self._client.date_time()

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergy(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total active energy")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_plus_received_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergyPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"total active energy phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delta(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagReactivePower(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.REACTIVE_POWER
    _attr_native_unit_of_measurement = "var"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reactive power")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_reactive_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagReactivePowerPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.REACTIVE_POWER
    _attr_native_unit_of_measurement = "var"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"reactive power phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_reactive(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagApparentPower(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_native_unit_of_measurement = "VA"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "apparent power")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_apparent_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagApparentPowerPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_native_unit_of_measurement = "VA"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"apparent power phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_apparent(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPowerFactor(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, feature_class: FeatureClass):
        super().__init__(client, modbus_index, tag_device, "power factor")

        if feature_class == FeatureClass.R1:
            convention = client.tag_power_factor_sign_convention(self._modbus_index)
            if convention != PowerFactorSignConvention.INVALID:
                self._attr_extra_state_attributes = {
                    "Power factor sign convention": convention
                }

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_factor_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPowerFactorPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"power factor phase {phase}")
        self.__phase = phase

        convention = client.tag_power_factor_sign_convention(self._modbus_index)
        if convention != PowerFactorSignConvention.INVALID:
            self._attr_extra_state_attributes = {
                "Power factor sign convention": convention
            }

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_factor(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialActiveEnergyDelivered(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial active energy delivered")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_partial(self._modbus_index)
        self._attr_last_reset = self._client.tag_load_operating_time_start(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergyDelivered(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total active energy delivered")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialActiveEnergyDeliveredPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"partial active energy delivered phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_partial_phase(
            self._modbus_index, self.__phase
        )
        self._attr_last_reset = self._client.tag_load_operating_time_start(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergyDeliveredPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"total active energy delivered phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_total_phase(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialActiveEnergyReceived(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial active energy received")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_partial(self._modbus_index)
        self._attr_last_reset = self._client.tag_load_operating_time_start(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergyReceived(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total active energy received")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialActiveEnergyReceivedPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"partial active energy received phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_partial_phase(
            self._modbus_index, self.__phase
        )
        self._attr_last_reset = self._client.tag_load_operating_time_start(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergyReceivedPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"total active energy received phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_total_phase(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialActiveEnergyDeliveredAndReceived(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial energy delivered and received")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_plus_received_partial(self._modbus_index)
        self._attr_last_reset = self._client.tag_load_operating_time_start(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergyDeliveredAndReceived(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total energy delivered and received")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_plus_received_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


# FIXME There doesn't seem to be a modbus address for this one, even though it's specifically mentioned
#       in DOCA0172EN-09.pdf page 166.
# class PowerTagPartialActiveEnergyDeliveredAndReceivedPerPhase(PowerTagEntity, SensorEntity):
#     _attr_device_class = SensorDeviceClass.ENERGY
#     _attr_native_unit_of_measurement = "Wh"
#     _attr_state_class = SensorStateClass.TOTAL
#
#     def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
#         super().__init__(client, modbus_index, tag_device, f"partial energy delivered and received phase {phase}")
#         self.__phase = phase
#
#     async def async_update(self):
#         self._attr_native_value = self._client.tag_energy_active_delivered_plus_received_total_phase(
#             self._modbus_index, self.__phase
#         )
#
#     @staticmethod
#     def supports_feature_set(feature_class: FeatureClass) -> bool:
#         return feature_class in [FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3]
#
#     @staticmethod
#     def supports_gateway(type_of_gateway: TypeOfGateway):
#         return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialReactiveEnergyDelivered(PowerTagEntity, SensorEntity):
    # TODO lobby for Reactive-energy
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial reactive energy delivered")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalReactiveEnergyDelivered(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total reactive energy delivered")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialReactiveEnergyDeliveredPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"partial reactive energy delivered phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_partial_phase(
            self._modbus_index, self.__phase
        )

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalReactiveEnergyDeliveredPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"total reactive energy delivered phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_total_phase(
            self._modbus_index, self.__phase
        )

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialReactiveEnergyReceived(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial reactive energy received")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalReactiveEnergyReceived(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total reactive energy received")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialReactiveEnergyReceivedPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"partial reactive energy received phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_partial_phase(
            self._modbus_index, self.__phase
        )

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalReactiveEnergyReceivedPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"total reactive energy received phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_total_phase(
            self._modbus_index, self.__phase
        )

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialApparentEnergy(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial apparent energy")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalApparentEnergy(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total apparent energy")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialApparentEnergyPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"partial apparent energy phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_partial_phase(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalApparentEnergyPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"total apparent energy phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_total_phase(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagCurrent(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = "A"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"current {phase.name}")
        self.__phase = phase

        self._attr_extra_state_attributes = {
            "Rated current": client.tag_rated_current(modbus_index)
        }

    async def async_update(self):
        self._attr_native_value = self._client.tag_current(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagCurrentNeutral(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = "A"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, f"current neutral")

        self._attr_extra_state_attributes = {
            "Rated current": client.tag_rated_current(modbus_index)
        }

    async def async_update(self):
        self._attr_native_value = self._client.tag_current_neutral(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagVoltage(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, line: LineVoltage):
        super().__init__(client, modbus_index, tag_device, f"voltage {line.name}")
        self.__line = line

        rated_voltage = client.tag_rated_voltage(modbus_index)

        if rated_voltage:
            self._attr_extra_state_attributes = {
                "Rated voltage": rated_voltage
            }

    async def async_update(self):
        self._attr_native_value = self._client.tag_voltage(self._modbus_index, self.__line)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagFrequency(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_native_unit_of_measurement = "Hz"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, f"frequency")

    async def async_update(self):
        self._attr_native_value = self._client.tag_ac_frequency(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTemperature(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "C"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, f"temperature")

    async def async_update(self):
        self._attr_native_value = self._client.tag_device_temperature(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        """
        The documentation says that A1, A2, P1, F1, F2 and F3 do not support internal temperature.
        However, they do seem to report temperature values, so let's use them. Let's not tell Schneider about this. ;)
        """
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagActivePower(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "active power")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_active_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagActivePowerPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"active power phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_active(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.P1, FeatureClass.F1, FeatureClass.F3, FeatureClass.FL,
                                 FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3, FeatureClass.R1,
                                 FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagDemandActivePower(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "demand active power")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_active_demand_total(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Maximum demand active power (W)": self._client.tag_power_active_power_demand_total_maximum(
                self._modbus_index),
            "Maximum demand active power timestamp": self._client.tag_power_active_demand_total_maximum_timestamp(
                self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagRssiTag(PowerTagEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "RSSI in tag")

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_rssi_inside_tag(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Minimum": self._client.tag_radio_rssi_minimum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagRssiGateway(PowerTagEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "RSSI in gateway")

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_rssi_inside_gateway(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Minimum": self._client.tag_radio_rssi_minimum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagLqiTag(PowerTagEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "LQI in tag")

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_lqi_tag(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Minimum": self._client.tag_radio_lqi_minimum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagLqiGateway(PowerTagEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "LQI in gateway")

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_lqi_gateway(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Minimum": self._client.tag_radio_lqi_minimum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPerTag(PowerTagEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "packet error rate in tag")

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_per_tag(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Maximum": self._client.tag_radio_per_maximum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPerGateway(PowerTagEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "packet error rate in gateway")

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_per_gateway(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Maximum": self._client.tag_radio_per_maximum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway):
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]
