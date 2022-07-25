from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.components.button import ButtonEntity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import Entity, DeviceInfo, EntityCategory

from .const import GATEWAY_DOMAIN, TAG_DOMAIN
from .schneider_modbus import SchneiderModbus, Phase, LineVoltage, PhaseSequence, LinkStatus


def gateway_device_info(client: SchneiderModbus, presentation_url: str) -> DeviceInfo:
    return DeviceInfo(
        configuration_url=presentation_url,
        identifiers={(GATEWAY_DOMAIN, client.serial_number())},
        hw_version=client.hardware_version(),
        sw_version=client.firmware_version(),
        manufacturer=client.manufacturer(),
        model=client.product_model(),
        name=client.name()
    )


def tag_device_info(client: SchneiderModbus, modbus_index: int, presentation_url: str,
                    gateway_identification: tuple[str, str]) -> DeviceInfo:
    return DeviceInfo(
        configuration_url=presentation_url,
        via_device=gateway_identification,
        identifiers={(GATEWAY_DOMAIN, client.serial_number()), (TAG_DOMAIN, client.tag_serial_number(modbus_index))},
        hw_version=client.tag_hardware_revision(modbus_index),
        sw_version=client.tag_firmware_revision(modbus_index),
        manufacturer=client.tag_vendor_name(modbus_index),
        model=client.tag_product_model(modbus_index),
        name=client.tag_name(modbus_index)
    )


def phase_sequence_to_phase(phase_sequence: PhaseSequence) -> [Phase]:
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


class GatewayEntity(Entity):
    def __init__(self, client: SchneiderModbus, tag_device: DeviceInfo, sensor_name: str):
        self._client = client

        self._attr_device_info = tag_device
        self._attr_name = f"{tag_device['name']} {sensor_name}"

        serial = client.serial_number()
        self._attr_unique_id = f"{TAG_DOMAIN}{serial}{sensor_name}"


class PowerTagEntity(Entity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, sensor_name: str):
        self._client = client
        self._modbus_index = modbus_index

        self._attr_device_info = tag_device
        self._attr_name = f"{tag_device['name']} {sensor_name}"

        serial = client.tag_serial_number(modbus_index)
        self._attr_unique_id = f"{TAG_DOMAIN}{serial}{sensor_name}"


class PowerTagApparentPower(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_native_unit_of_measurement = "VA"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "apparent power")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_apparent_total(self._modbus_index)


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


class PowerTagTotalEnergy(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "total energy")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_total(self._modbus_index)


class PowerTagPartialEnergy(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "partial energy")

    async def async_update(self):
        self._attr_native_value = self._client.tag_energy_active_partial(self._modbus_index)
        self._attr_last_reset = self._client.tag_load_operating_time_start(self._modbus_index)


class PowerTagPowerFactor(PowerTagEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "power factor")

    async def async_update(self):
        self._attr_native_value = self._client.tag_power_factor_total(self._modbus_index)


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


class PowerTagWirelessCommunicationValid(PowerTagEntity, BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "wireless communication valid")

    async def async_update(self):
        self._attr_is_on = self._client.tag_wireless_communication_valid(self._modbus_index)


class PowerTagRadioCommunicationValid(PowerTagEntity, BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "radio communication valid")

    async def async_update(self):
        self._attr_is_on = self._client.tag_radio_communication_valid(self._modbus_index)


class PowerTagResetPeakDemand(PowerTagEntity, ButtonEntity):
    def press(self) -> None:
        self.reset()

    async def async_press(self) -> None:
        self.reset()

    def reset(self):
        self._client.tag_reset_peak_demands(self._modbus_index)


class PowerTagAlarmValid(PowerTagEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "alarm valid")

    async def async_update(self):
        self._attr_is_on = not self._client.tag_is_alarm_valid(self._modbus_index)


class PowerTagGetAlarm(PowerTagEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "alarm valid")
        self.__product_range = self._client.tag_product_range(self._modbus_index)

    async def async_update(self):
        alarm = self._client.tag_get_alarm(self._modbus_index)
        self._attr_is_on = alarm.has_alarm

        if self.__product_range == "PowerTag":
            self._attr_extra_state_attributes = {
                "Voltage loss": alarm.alarm_voltage_loss,
                "Overcurrent at voltage loss": alarm.alarm_current_overload,
                "Overload 45%": alarm.alarm_overload_45_percent,
                "Loadcurrent loss": alarm.alarm_load_current_loss,
                "Overvoltage 120%": alarm.alarm_overvoltage,
                "Undervoltage 80%": alarm.alarm_undervoltage
            }
        elif self.__product_range == "HeatTag":
            self._attr_extra_state_attributes = {
                "Alarm": alarm.alarm_heattag_alarm,
                "Preventive maintenance on device": alarm.alarm_heattag_maintenance,
                "Device replacement": alarm.alarm_heattag_replacement
            }


class GatewayStatus(GatewayEntity, BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, client: SchneiderModbus, tag_device: DeviceInfo):
        super().__init__(client, tag_device, "status")

    async def async_update(self):
        status = self._client.status()
        self._attr_is_on = status == LinkStatus.OPERATING

        self._attr_extra_state_attributes["status"] = {
            LinkStatus.OPERATING: "Operating",
            LinkStatus.START_UP: "Starting up",
            LinkStatus.DOWNGRADED: "Downgraded",
            LinkStatus.E2PROM_ERROR: "E2PROM error",
            LinkStatus.FLASH_ERROR: "Flash error",
            LinkStatus.RAM_ERROR: "RAM error",
            LinkStatus.GENERAL_FAILURE: "General failure"
        }[status]


class GatewayTime(GatewayEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "datetime")

    async def async_update(self):
        self._attr_native_value = self._client.date_time()
