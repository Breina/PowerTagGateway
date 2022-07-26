"""Platform for Schneider Energy."""
from enum import Enum

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_CLIENT, DOMAIN, TAG_DOMAIN, GATEWAY_DOMAIN
from .entity_base import gateway_device_info, tag_device_info
from .schneider_modbus import SchneiderModbus, Phase, LineVoltage, PhaseSequence, ProductType

PLATFORMS: list[str] = ["sensor"]


def phase_sequence_to_phases(phase_sequence: PhaseSequence) -> [Phase]:
    return {
        PhaseSequence.A: [Phase.A],
        PhaseSequence.B: [Phase.B],
        PhaseSequence.C: [Phase.C],
        PhaseSequence.ABC: [Phase.A, Phase.B, Phase.C],
        PhaseSequence.ACB: [Phase.A, Phase.C, Phase.B],
        PhaseSequence.BAC: [Phase.B, Phase.A, Phase.C],
        PhaseSequence.BCA: [Phase.B, Phase.C, Phase.A],
        PhaseSequence.CAB: [Phase.C, Phase.A, Phase.B],
        PhaseSequence.CBA: [Phase.C, Phase.B, Phase.A]
    }[phase_sequence]


class FeatureClass(Enum):
    A1 = [ProductType.A9MEM1520, ProductType.A9MEM1521, ProductType.A9MEM1522, ProductType.A9MEM1541,
          ProductType.A9MEM1542]
    A2 = [ProductType.A9MEM1540, ProductType.A9MEM1543]
    P1 = [ProductType.A9MEM1561, ProductType.A9MEM1562, ProductType.A9MEM1563, ProductType.A9MEM1571,
          ProductType.A9MEM1572]
    F1 = [ProductType.A9MEM1560, ProductType.A9MEM1570]
    F2 = [ProductType.A9MEM1573]
    F3 = [ProductType.A9MEM1564, ProductType.A9MEM1574]


def has_neutral(product_type: ProductType) -> bool:
    feature_class = [fc for fc in FeatureClass if product_type in fc.value][0]
    return feature_class in [FeatureClass.A2, FeatureClass.F2]


def phase_sequence_to_line_voltages(phase_sequence: PhaseSequence, neutral: bool) -> [LineVoltage]:
    if phase_sequence in [PhaseSequence.A, PhaseSequence.B, PhaseSequence.C]:
        if not neutral:
            return []
        return {
            PhaseSequence.A: [LineVoltage.A_N],
            PhaseSequence.B: [LineVoltage.B_N],
            PhaseSequence.C: [LineVoltage.C_N]
        }[phase_sequence]
    else:
        return [LineVoltage.A_N, LineVoltage.B_N, LineVoltage.C_N] if neutral \
            else [LineVoltage.A_B, LineVoltage.B_C, LineVoltage.C_A]


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PowerTag Link Gateway from a config entry."""

    data = hass.data[DOMAIN][config_entry.entry_id]

    client = data[CONF_CLIENT]
    presentation_url = data[CONF_INTERNAL_URL]

    entities = []

    gateway_device = gateway_device_info(client, presentation_url)

    # entities.append(GatewayTime(client, gateway_device))

    for i in range(1, 100):
        modbus_address = client.modbus_address_of_node(1)
        if modbus_address is None:
            break

        tag_device = tag_device_info(
            client, modbus_address, presentation_url, next(iter(gateway_device["identifiers"]))
        )

        entities.append([
            PowerTagApparentPower(client, modbus_address, tag_device),
            PowerTagActivePower(client, modbus_address, tag_device),
            PowerTagDemandActivePower(client, modbus_address, tag_device),
            PowerTagTotalEnergy(client, modbus_address, tag_device),
            PowerTagPartialEnergy(client, modbus_address, tag_device),
            PowerTagPowerFactor(client, modbus_address, tag_device),
            # PowerTagRssiTag(client, modbus_address, tag_device),
            # PowerTagRssiGateway(client, modbus_address, tag_device),
            # PowerTagLqiTag(client, modbus_address, tag_device),
            # PowerTagLqiGateway(client, modbus_address, tag_device),
            # PowerTagPerTag(client, modbus_address, tag_device),
            # PowerTagPerGateway(client, modbus_address, tag_device)
        ])

        phase_sequence = client.tag_phase_sequence(modbus_address)
        neutral = has_neutral(client.tag_product_type(modbus_address))

        for phase in phase_sequence_to_phases(phase_sequence):
            entities.append(PowerTagCurrent(client, modbus_address, tag_device, phase))
            if neutral:
                PowerTagActivePowerPerPhase(client, modbus_address, tag_device, phase)

        for line_voltage in phase_sequence_to_line_voltages(phase_sequence, neutral):
            entities.append(PowerTagVoltage(client, modbus_address, tag_device, line_voltage))

    async_add_entities(entities, update_before_add=False)


class GatewayEntity(SensorEntity):
    def __init__(self, client: SchneiderModbus, tag_device: DeviceInfo, sensor_name: str):
        self._client = client

        self._attr_device_info = tag_device
        self._attr_name = f"{tag_device['name']} {sensor_name}"

        serial = client.serial_number()
        self._attr_unique_id = f"{GATEWAY_DOMAIN}{serial}{sensor_name}"


class PowerTagEntity(SensorEntity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, entity_name: str):
        self._client = client
        self._modbus_index = modbus_index

        self._attr_device_info = tag_device
        self._attr_name = f"{tag_device['name']} {entity_name}"

        serial = client.tag_serial_number(modbus_index)
        self._attr_unique_id = f"{TAG_DOMAIN}{serial}{entity_name}"


class GatewayTime(GatewayEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, client: SchneiderModbus, tag_device: DeviceInfo):
        super().__init__(client, tag_device, "datetime")

    async def async_update(self):
        self._attr_native_value = self._client.date_time()


class PowerTagApparentPower(PowerTagEntity):
    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_native_unit_of_measurement = "VA"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "apparent power")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_apparent_total(self._modbus_index)


class PowerTagCurrent(PowerTagEntity):
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


class PowerTagVoltage(PowerTagEntity):
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, line: LineVoltage):
        super().__init__(client, modbus_index, tag_device, f"voltage {line.name}")
        self.__line = line

        self._attr_extra_state_attributes = {
            "Rated voltage": client.tag_rated_voltage(modbus_index)
        }

    async def async_update(self):
        self._attr_native_value = self._client.tag_voltage(self._modbus_index, self.__line)


class PowerTagActivePower(PowerTagEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "active power")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_active_total(self._modbus_index)


class PowerTagActivePowerPerPhase(PowerTagEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"active power phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_active(self._modbus_index, self.__phase)


class PowerTagDemandActivePower(PowerTagEntity):
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


class PowerTagTotalEnergy(PowerTagEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total energy")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_total(self._modbus_index)


class PowerTagPartialEnergy(PowerTagEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial energy")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_partial(self._modbus_index)
        self._attr_last_reset = self._client.tag_load_operating_time_start(self._modbus_index)


class PowerTagPowerFactor(PowerTagEntity):
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "power factor")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_factor_total(self._modbus_index)


class PowerTagRssiTag(PowerTagEntity):
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


class PowerTagRssiGateway(PowerTagEntity):
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


class PowerTagLqiTag(PowerTagEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "LQI in tag")

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_lqi_tag(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Minimum": self._client.tag_radio_lqi_minimum(self._modbus_index)
        }


class PowerTagLqiGateway(PowerTagEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "LQI in gateway")

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_lqi_gateway(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Minimum": self._client.tag_radio_lqi_minimum(self._modbus_index)
        }


class PowerTagPerTag(PowerTagEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "packet error rate in tag")

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_per_tag(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Maximum": self._client.tag_radio_per_maximum(self._modbus_index)
        }


class PowerTagPerGateway(PowerTagEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "packet error rate in gateway")

    async def async_update(self):
        self._attr_native_value = self._client.tag_radio_per_gateway(self._modbus_index)
        self._attr_extra_state_attributes = {
            "Maximum": self._client.tag_radio_per_maximum(self._modbus_index)
        }
