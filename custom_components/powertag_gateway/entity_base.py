from homeassistant.helpers.entity import Entity, DeviceInfo

from .const import GATEWAY_DOMAIN, TAG_DOMAIN
from .schneider_modbus import SchneiderModbus


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
        identifiers={(TAG_DOMAIN, client.tag_serial_number(modbus_index))},
        hw_version=client.tag_hardware_revision(modbus_index),
        sw_version=client.tag_firmware_revision(modbus_index),
        manufacturer=client.tag_vendor_name(modbus_index),
        model=client.tag_product_model(modbus_index),
        name=client.tag_name(modbus_index)
    )


class GatewayEntity(Entity):
    def __init__(self, client: SchneiderModbus, tag_device: DeviceInfo, sensor_name: str):
        self._client = client

        self._attr_device_info = tag_device
        self._attr_name = f"{tag_device['name']} {sensor_name}"

        serial = client.serial_number()
        self._attr_unique_id = f"{TAG_DOMAIN}{serial}{sensor_name}"


class PowerTagEntity(Entity):
    def __init__(self, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, entity_name: str):
        self._client = client
        self._modbus_index = modbus_index

        self._attr_device_info = tag_device
        self._attr_name = f"{tag_device['name']} {entity_name}"

        serial = client.tag_serial_number(modbus_index)
        self._attr_unique_id = f"{TAG_DOMAIN}{serial}{entity_name}"
