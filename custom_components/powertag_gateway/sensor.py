"""Platform for Schneider Energy."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CONF_CLIENT, DOMAIN, UniqueIdVersion
from .device_features import FeatureClass
from .entity_base import GatewayEntity, WirelessDeviceEntity, setup_entities, gateway_device_info
from .schneider_modbus import SchneiderModbus, Phase, LineVoltage, PowerFactorSignConvention, \
    TypeOfGateway

PLATFORMS: list[str] = ["sensor"]

_LOGGER = logging.getLogger(__name__)


def list_sensors() -> list[type[WirelessDeviceEntity]]:
    return [
        PowerTagTotalActiveEnergy,
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
        EnvTagBatteryVoltage,
        EnvTagTemperature,
        EnvTagHumidity,
        EnvTagCO2,
        DeviceRssiTag,
        DeviceRssiGateway,
        DeviceLqiTag,
        DeviceLqiGateway,
        DevicePerTag,
        DevicePerGateway,
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
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergy(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "total active energy", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_plus_received_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagReactivePower(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.REACTIVE_POWER
    _attr_native_unit_of_measurement = "var"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "reactive power", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_reactive_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagReactivePowerPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.REACTIVE_POWER
    _attr_native_unit_of_measurement = "var"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"reactive power phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_reactive(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagApparentPower(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_native_unit_of_measurement = "VA"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "apparent power", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_apparent_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagApparentPowerPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_native_unit_of_measurement = "VA"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"apparent power phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_apparent(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPowerFactor(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, feature_class: FeatureClass, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "power factor", unique_id_version)

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
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPowerFactorPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"power factor phase {phase}", unique_id_version)
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
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialActiveEnergyDelivered(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "partial active energy delivered", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergyDelivered(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "total active energy delivered", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialActiveEnergyDeliveredPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"partial active energy delivered phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_partial_phase(
            self._modbus_index, self.__phase
        )

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            # Assumption, documentation actually doesn't list these.
            FeatureClass.A1, FeatureClass.F1, FeatureClass.F3,
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
            FeatureClass.R1
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergyDeliveredPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"total active energy delivered phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_total_phase(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            # Assumption, documentation actually doesn't list these.
            FeatureClass.A1, FeatureClass.F1, FeatureClass.F3,
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
            FeatureClass.R1
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialActiveEnergyReceived(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "partial active energy received", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergyReceived(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "total active energy received", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialActiveEnergyReceivedPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"partial active energy received phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_partial_phase(
            self._modbus_index, self.__phase
        )

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            # Assumption, documentation actually doesn't list these.
            FeatureClass.A1, FeatureClass.F1, FeatureClass.F3,
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
            FeatureClass.R1
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalActiveEnergyReceivedPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"total active energy received phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_total_phase(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            # Assumption, documentation actually doesn't list these.
            FeatureClass.A1, FeatureClass.F1, FeatureClass.F3,
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
            FeatureClass.R1
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialActiveEnergyDeliveredAndReceived(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "partial energy delivered and received", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_plus_received_partial(self._modbus_index)
        self._attr_last_reset = self._client.tag_load_operating_time_start(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialReactiveEnergyDelivered(WirelessDeviceEntity, SensorEntity):
    # TODO lobby for Reactive-energy: https://github.com/home-assistant/architecture/discussions/724
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "partial reactive energy delivered", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL,
                                 FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalReactiveEnergyDelivered(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "total reactive energy delivered", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialReactiveEnergyDeliveredPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"partial reactive energy delivered phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_partial_phase(
            self._modbus_index, self.__phase
        )

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL,
                                 # Assumption, documentation actually doesn't list these.
                                 FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalReactiveEnergyDeliveredPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"total reactive energy delivered phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_total_phase(
            self._modbus_index, self.__phase
        )

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL,
                                 # Assumption, documentation actually doesn't list these.
                                 FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialReactiveEnergyReceived(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "partial reactive energy received", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL,
                                 FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalReactiveEnergyReceived(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "total reactive energy received", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL,
            # Documentation implies only the resettable variant would exist, not this one. Wtf?
            FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
            FeatureClass.R1
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialReactiveEnergyReceivedPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"partial reactive energy received phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_partial_phase(
            self._modbus_index, self.__phase
        )

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL,
                                 # Assumption, documentation actually doesn't list these.
                                 FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalReactiveEnergyReceivedPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"total reactive energy received phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_total_phase(
            self._modbus_index, self.__phase
        )

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL,
                                 # Assumption, documentation actually doesn't list these.
                                 FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialApparentEnergy(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "partial apparent energy", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_partial(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalApparentEnergy(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "total apparent energy", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagPartialApparentEnergyPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"partial apparent energy phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_partial_phase(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTotalApparentEnergyPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"total apparent energy phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_total_phase(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagCurrent(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = "A"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"current {phase.name}", unique_id_version)
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
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagCurrentNeutral(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = "A"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"current neutral", unique_id_version)

        self._attr_extra_state_attributes = {
            "Rated current": client.tag_rated_current(modbus_index)
        }

    async def async_update(self):
        self._attr_native_value = self._client.tag_current_neutral(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagVoltage(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, line: LineVoltage, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"voltage {line.name}", unique_id_version)
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
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagFrequency(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_native_unit_of_measurement = "Hz"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"frequency", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_ac_frequency(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3,
                                 FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagTemperature(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"temperature", unique_id_version)

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
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]

    @staticmethod
    def supports_firmware_version(firmware_version: str) -> bool:
        import re
        major_version = re.sub(r'[^0-9.]', '', firmware_version).split('.')[0]
        return int(major_version) >= 4


class PowerTagActivePower(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "active power", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_active_total(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagActivePowerPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, f"active power phase {phase}", unique_id_version)
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_active(self._modbus_index, self.__phase)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.P1, FeatureClass.F1, FeatureClass.F3, FeatureClass.FL,
                                 FeatureClass.M0, FeatureClass.M1, FeatureClass.M2, FeatureClass.M3, FeatureClass.R1,
                                 FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagDemandActivePower(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "demand active power", unique_id_version)

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
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class EnvTagBatteryVoltage(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "battery voltage", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.env_battery_voltage(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.PANEL_SERVER]


class EnvTagTemperature(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "temperature", unique_id_version)
        self._attr_extra_state_attributes = {
            "Minimum measurable temperature (°C)": client.env_temperature_minimum(modbus_index),
            "Maximum measurable temperature (°C)": client.env_temperature_maximum(modbus_index)
        }

    async def async_update(self):
        self._attr_native_value = self._client.env_temperature(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.TEMP0, FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.PANEL_SERVER]


class EnvTagHumidity(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "humidity", unique_id_version)
        self._attr_extra_state_attributes = {
            "Minimum measurable humidity (%)": client.env_humidity_minimum(modbus_index) * 100,
            "Maximum measurable humidity (%)": client.env_humidity_maximum(modbus_index) * 100
        }

    async def async_update(self):
        self._attr_native_value = self._client.env_humidity(self._modbus_index) * 100

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.PANEL_SERVER]


class EnvTagCO2(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.CO2
    _attr_native_unit_of_measurement = "ppm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "CO2", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.env_co2(self._modbus_index) * 1000

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.PANEL_SERVER]


class DeviceRssiTag(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "RSSI in tag", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_rssi_inside_tag(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Minimum": self._client.tag_radio_rssi_minimum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C,
                                 FeatureClass.TEMP0, FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class DeviceRssiGateway(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "RSSI in gateway", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_rssi_inside_gateway(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Minimum": self._client.tag_radio_rssi_minimum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C,
                                 FeatureClass.TEMP0, FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class DeviceLqiTag(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "LQI in tag", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_lqi_tag(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Minimum": self._client.tag_radio_lqi_minimum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C,
                                 FeatureClass.TEMP0, FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class DeviceLqiGateway(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "LQI in gateway", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_lqi_gateway(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Minimum": self._client.tag_radio_lqi_minimum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C,
                                 FeatureClass.TEMP0, FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class DevicePerTag(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "packet error rate in tag", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_per_tag(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Maximum": self._client.tag_radio_per_maximum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C,
                                 FeatureClass.TEMP0, FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class DevicePerGateway(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "packet error rate in gateway", unique_id_version)

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_per_gateway(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Maximum": self._client.tag_radio_per_maximum(self._modbus_index)
        }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C,
                                 FeatureClass.TEMP0, FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]
