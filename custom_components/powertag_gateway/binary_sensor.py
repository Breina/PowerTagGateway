import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CONF_CLIENT, DOMAIN, UniqueIdVersion
from .device_features import FeatureClass
from .entity_base import WirelessDeviceEntity, GatewayEntity, setup_entities, gateway_device_info
from .schneider_modbus import SchneiderModbus, LinkStatus, PanelHealth, TypeOfGateway

_LOGGER = logging.getLogger(__name__)


def list_binary_sensors() -> list[type[WirelessDeviceEntity]]:
    return [
        PowerTagWirelessCommunicationValid,
        PowerTagRadioCommunicationValid,
        PowerTagAlarm,
        AmbientTagAlarm
    ]


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PowerTag Link Gateway from a config entry."""

    binary_sensors = list_binary_sensors()
    entities = setup_entities(hass, config_entry, binary_sensors)

    data = hass.data[DOMAIN][config_entry.entry_id]
    presentation_url = data[CONF_INTERNAL_URL]
    client = data[CONF_CLIENT]
    gateway_device = gateway_device_info(client, presentation_url)

    entities.extend([gateway_entity for gateway_entity
                     in [GatewayStatus(client, gateway_device), GatewayHealth(client, gateway_device)]
                     if gateway_entity.supports_gateway(client.type_of_gateway)
                     ])

    async_add_entities(entities, update_before_add=False)


class PowerTagWirelessCommunicationValid(WirelessDeviceEntity, BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "wireless communication valid", unique_id_version)

    async def async_update(self):
        self._attr_is_on = self._client.tag_wireless_communication_valid(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C,
                                 FeatureClass.TEMP0, FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagRadioCommunicationValid(WirelessDeviceEntity, BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "radio communication valid", unique_id_version)

    async def async_update(self):
        self._attr_is_on = self._client.tag_radio_communication_valid(self._modbus_index)

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C,
                                 FeatureClass.TEMP0, FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class PowerTagAlarm(WirelessDeviceEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "alarm info", unique_id_version)

    async def async_update(self):
        alarm = self._client.tag_get_alarm(self._modbus_index)

        if alarm.has_alarm != self._attr_is_on:
            self._attr_is_on = alarm.has_alarm
            self._attr_extra_state_attributes = {
                "Voltage loss": alarm.voltage_loss,
                "Current overload when voltage loss": alarm.current_overload_when_voltage_loss,
                "Current short-circuit": alarm.current_short_circuit,
                "Overload 45%": alarm.current_overload_45_percent,
                "Load current loss": alarm.load_current_loss,
                "Overvoltage 120%": alarm.overvoltage_120_percent,
                "Undervoltage 80%": alarm.undervoltage_80_percent,
                "Current 50%": alarm.current_50_percent,
                "Current 80%": alarm.current_80_percent
            }

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]


class AmbientTagAlarm(WirelessDeviceEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion):
        super().__init__(client, modbus_index, tag_device, "battery", unique_id_version)
        self.__product_range = self._client.tag_product_range(self._modbus_index)

    async def async_update(self):
        alarm = self._client.tag_get_alarm(self._modbus_index)
        self._attr_is_on = alarm.has_alarm

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.PANEL_SERVER]


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

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.SMARTLINK, TypeOfGateway.POWERTAG_LINK]


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

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.PANEL_SERVER]
