"""Platform for Schneider Energy."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_CLIENT, DOMAIN
from .entity_base import gateway_device_info, tag_device_info, has_neutral, \
    phase_sequence_to_phases, phase_sequence_to_line_voltages, GatewayEntity, PowerTagEntity, is_m, is_r
from .schneider_modbus import SchneiderModbus, Phase, LineVoltage, PhaseSequence, PowerFactorSignConvention

PLATFORMS: list[str] = ["sensor"]

log = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PowerTag Link Gateway from a config entry."""

    data = hass.data[DOMAIN][config_entry.entry_id]

    client = data[CONF_CLIENT]
    presentation_url = data[CONF_INTERNAL_URL]

    entities = []

    gateway_device = gateway_device_info(client, presentation_url)

    entities.append(GatewayTime(client, gateway_device))

    for i in range(1, 100):
        modbus_address = client.modbus_address_of_node(i)
        if modbus_address is None:
            break

        tag_device = tag_device_info(
            client, modbus_address, presentation_url, next(iter(gateway_device["identifiers"]))
        )

        entities.extend([
            PowerTagApparentPower(client, modbus_address, tag_device),
            PowerTagActivePower(client, modbus_address, tag_device),
            PowerTagPartialEnergy(client, modbus_address, tag_device),
            PowerTagPowerFactor(client, modbus_address, tag_device),
            PowerTagRssiTag(client, modbus_address, tag_device),
            PowerTagRssiGateway(client, modbus_address, tag_device),
            PowerTagLqiTag(client, modbus_address, tag_device),
            PowerTagLqiGateway(client, modbus_address, tag_device),
            PowerTagPerTag(client, modbus_address, tag_device),
            PowerTagPerGateway(client, modbus_address, tag_device)
        ])

        product_type = client.tag_product_type(modbus_address)
        neutral = has_neutral(product_type)

        class_m = is_m(product_type)
        class_r = is_r(product_type)

        if class_m or class_r:
            entities.extend([
                PowerTagReactivePower(client, modbus_address, tag_device),
                PowerTagFrequency(client, modbus_address, tag_device),
                PowerTagTemperature(client, modbus_address, tag_device),
            ])
        else:
            entities.extend([
                PowerTagTotalActiveEnergy(client, modbus_address, tag_device),
            ])

        if class_r:
            entities.extend([
                PowerTagCurrentNeutral(client, modbus_address, tag_device),
                PowerTagPartialActiveEnergyDelivered(client, modbus_address, tag_device),
                PowerTagTotalActiveEnergyDelivered(client, modbus_address, tag_device),
                PowerTagPartialActiveEnergyReceived(client, modbus_address, tag_device),
                PowerTagTotalActiveEnergyReceived(client, modbus_address, tag_device),
                PowerTagPartialReactiveEnergyDelivered(client, modbus_address, tag_device),
                PowerTagTotalReactiveEnergyDelivered(client, modbus_address, tag_device),
                PowerTagPartialReactiveEnergyReceived(client, modbus_address, tag_device),
                PowerTagTotalReactiveEnergyReceived(client, modbus_address, tag_device),
                PowerTagPartialApparentEnergy(client, modbus_address, tag_device),
                PowerTagTotalApparentEnergy(client, modbus_address, tag_device),
            ])

        if not class_m:
            entities.extend([
                PowerTagDemandActivePower(client, modbus_address, tag_device),
            ])

        phase_sequence = client.tag_phase_sequence(modbus_address)
        if phase_sequence == PhaseSequence.INVALID:
            log.warning(f"The phase sequence of {tag_device['name']} was not defined."
                        f"Skipping adding phase-specific entities...")

        for phase in phase_sequence_to_phases(phase_sequence):
            entities.append(PowerTagCurrent(client, modbus_address, tag_device, phase))

            if neutral:
                entities.append(PowerTagActivePowerPerPhase(client, modbus_address, tag_device, phase))

            if class_m:
                entities.extend([
                    PowerTagTotalActiveEnergyDeltaPerPhase(client, modbus_address, tag_device, phase),
                ])

            if class_r:
                entities.extend([
                    PowerTagReactivePowerPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagApparentPowerPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagPowerFactorPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagPartialActiveEnergyDeliveredPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagTotalActiveEnergyDeliveredPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagPartialActiveEnergyReceivedPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagTotalActiveEnergyReceivedPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagPartialReactiveEnergyDeliveredPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagTotalReactiveEnergyDeliveredPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagPartialReactiveEnergyReceivedPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagTotalReactiveEnergyReceivedPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagPartialApparentEnergyPerPhase(client, modbus_address, tag_device, phase),
                    PowerTagTotalApparentEnergyPerPhase(client, modbus_address, tag_device, phase),
                ])

        for line_voltage in phase_sequence_to_line_voltages(phase_sequence, neutral):
            entities.append(PowerTagVoltage(client, modbus_address, tag_device, line_voltage))

    async_add_entities(entities, update_before_add=False)


class GatewayTime(GatewayEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, client: SchneiderModbus, tag_device: DeviceInfo):
        super().__init__(client, tag_device, "datetime")

    async def async_update(self):
        self._attr_native_value = self._client.date_time()


class PowerTagApparentPower(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_native_unit_of_measurement = "VA"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "apparent power")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_apparent_total(self._modbus_index)


class PowerTagApparentPowerPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "VA"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"apparent power phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_apparent(self._modbus_index, self.__phase)


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


class PowerTagVoltage(PowerTagEntity, SensorEntity):
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


class PowerTagActivePower(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "active power")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_active_total(self._modbus_index)


class PowerTagActivePowerPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"active power phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_active(self._modbus_index, self.__phase)


class PowerTagReactivePower(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "VAR"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "reactive power")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_reactive_total(self._modbus_index)


class PowerTagReactivePowerPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "VAR"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, f"reactive power phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_reactive(self._modbus_index, self.__phase)


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


class PowerTagTotalActiveEnergy(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total active energy")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_plus_received_total(self._modbus_index)


class PowerTagTotalActiveEnergyDeltaPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, "total active energy delivered")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delta(self._modbus_index, self.__phase)


class PowerTagPartialActiveEnergyDelivered(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial active energy delivered")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_partial(self._modbus_index)


class PowerTagTotalActiveEnergyDelivered(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total active energy delivered")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_total(self._modbus_index)


class PowerTagPartialActiveEnergyReceived(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial active energy received")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_partial(self._modbus_index)


class PowerTagTotalActiveEnergyReceived(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total active energy received")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_total(self._modbus_index)


class PowerTagPartialActiveEnergyDeliveredPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, "partial active energy delivered phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_partial_phase(
            self._modbus_index, self.__phase
        )


class PowerTagTotalActiveEnergyDeliveredPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, "total active energy delivered phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_total_phase(self._modbus_index, self.__phase)


class PowerTagPartialActiveEnergyReceivedPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, "partial active energy received phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_partial_phase(
            self._modbus_index, self.__phase
        )


class PowerTagTotalActiveEnergyReceivedPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, "total active energy received phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_received_total_phase(self._modbus_index, self.__phase)


class PowerTagPartialReactiveEnergyDelivered(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial reactive energy delivered")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_partial(self._modbus_index)


class PowerTagTotalReactiveEnergyDelivered(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total reactive energy delivered")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_total(self._modbus_index)


class PowerTagPartialReactiveEnergyReceived(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial reactive energy received")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_partial(self._modbus_index)


class PowerTagTotalReactiveEnergyReceived(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total reactive energy received")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_total(self._modbus_index)


class PowerTagPartialReactiveEnergyDeliveredPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, "partial reactive energy delivered phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_partial_phase(
            self._modbus_index, self.__phase
        )


class PowerTagTotalReactiveEnergyDeliveredPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, "total reactive energy delivered phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_delivered_total_phase(self._modbus_index, self.__phase)


class PowerTagPartialReactiveEnergyReceivedPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, "partial reactive energy received phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_partial_phase(
            self._modbus_index, self.__phase
        )


class PowerTagTotalReactiveEnergyReceivedPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, "total reactive energy received phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_reactive_received_total_phase(self._modbus_index, self.__phase)


class PowerTagPartialApparentEnergy(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial apparent energy")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_partial(self._modbus_index)


class PowerTagTotalApparentEnergy(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total apparent energy")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_total(self._modbus_index)


class PowerTagPartialApparentEnergyPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, "partial apparent energy phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_partial_phase(self._modbus_index, self.__phase)


class PowerTagTotalApparentEnergyPerPhase(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, phase: Phase):
        super().__init__(client, modbus_index, tag_device, "total apparent energy phase {phase}")
        self.__phase = phase

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_apparent_total_phase(self._modbus_index, self.__phase)


class PowerTagPartialEnergy(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial energy")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_delivered_plus_received_partial(self._modbus_index)
        self._attr_last_reset = self._client.tag_load_operating_time_start(self._modbus_index)


class PowerTagPowerFactor(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "power factor")

        product_type = client.tag_product_type(self._modbus_index)
        if is_r(product_type):
            convention = client.tag_power_factor_sign_convention(self._modbus_index)
            if convention != PowerFactorSignConvention.INVALID:
                self._attr_extra_state_attributes = {
                    "Power factor sign convention": convention
                }

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_factor_total(self._modbus_index)


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


class PowerTagFrequency(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_native_unit_of_measurement = "Hz"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, f"frequency")

    async def async_update(self):
        self._attr_native_value = self._client.tag_ac_frequency(self._modbus_index)


class PowerTagTemperature(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "C"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, f"temperature")

    async def async_update(self):
        self._attr_native_value = self._client.tag_device_temperature(self._modbus_index)


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
