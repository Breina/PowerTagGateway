import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_CLIENT, DOMAIN
from .entity_base import PowerTagEntity, tag_device_info, gateway_device_info, GatewayEntity, is_powertag
from .schneider_modbus import SchneiderModbus, LinkStatus, PanelHealth, TypeOfGateway

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

    if client.type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.SMARTLINK]:
        entities.append(GatewayStatus(client, gateway_device))
    else:
        entities.append(GatewayHealth(client, gateway_device))

    for i in range(1, 100):
        modbus_address = client.modbus_address_of_node(i)
        if modbus_address is None:
            break

        product_type = client.tag_product_type(modbus_address)
        if not product_type:
            break

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

        entities.extend([
            PowerTagWirelessCommunicationValid(client, modbus_address, tag_device),
            PowerTagRadioCommunicationValid(client, modbus_address, tag_device),
            PowerTagAlarmValid(client, modbus_address, tag_device),
            PowerTagGetAlarm(client, modbus_address, tag_device)
        ])

    async_add_entities(entities, update_before_add=False)


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


class PowerTagAlarmValid(PowerTagEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "alarm valid")

    async def async_update(self):
        self._attr_is_on = not self._client.tag_is_alarm_valid(self._modbus_index)


class PowerTagGetAlarm(PowerTagEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo):
        super().__init__(client, modbus_index, tag_device, "alarm info")
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
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        status = self._client.status()
        self._attr_is_on = status != LinkStatus.OPERATING

        self._attr_extra_state_attributes["status"] = {
            LinkStatus.OPERATING: "Operating",
            LinkStatus.START_UP: "Starting up",
            LinkStatus.DOWNGRADED: "Downgraded",
            LinkStatus.E2PROM_ERROR: "E2PROM error",
            LinkStatus.FLASH_ERROR: "Flash error",
            LinkStatus.RAM_ERROR: "RAM error",
            LinkStatus.GENERAL_FAILURE: "General failure"
        }[status]


class GatewayHealth(GatewayEntity, BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, client: SchneiderModbus, tag_device: DeviceInfo):
        super().__init__(client, tag_device, "health")
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        status = self._client.health()
        self._attr_is_on = status != PanelHealth.NOMINAL

        self._attr_extra_state_attributes["status"] = {
            PanelHealth.NOMINAL: "Nominal",
            PanelHealth.DEGRADED: "Degraded",
            PanelHealth.OUT_OF_ORDER: "Out of order"
        }[status]
