import inspect
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers import device_registry as dr

from . import UniqueIdVersion
from .const import CONF_CLIENT, DOMAIN, CONF_DEVICE_UNIQUE_ID_VERSION
from .const import GATEWAY_DOMAIN, TAG_DOMAIN
from .device_features import FeatureClass, from_commercial_reference, UnknownDevice, from_wireless_device_type_code
from .schneider_modbus import SchneiderModbus, Phase, LineVoltage, PhaseSequence, TypeOfGateway

_LOGGER = logging.getLogger(__name__)


def gateway_device_info(client: SchneiderModbus, presentation_url: str) -> DeviceInfo:
    serial = client.serial_number()
    return DeviceInfo(
        configuration_url=presentation_url,
        identifiers={(GATEWAY_DOMAIN, serial)},
        hw_version=client.hardware_version(),
        sw_version=client.firmware_version(),
        manufacturer=client.manufacturer(),
        model=client.product_code(),
        name=client.name(),
        serial_number=serial
    )


def tag_device_info(client: SchneiderModbus, modbus_index: int, presentation_url: str,
                    gateway_identification: tuple[str, str]) -> DeviceInfo:
    is_unreachable = client.tag_radio_lqi_gateway(modbus_index) is None
    serial_number = client.tag_serial_number(modbus_index)

    kwargs = {
        'configuration_url': presentation_url,
        'via_device': gateway_identification,
        'identifiers': {(TAG_DOMAIN, serial_number)},
        'serial_number': serial_number,
        'hw_version': client.tag_hardware_revision(modbus_index),
        'sw_version': client.tag_firmware_revision(modbus_index),
        'manufacturer': client.tag_vendor_name(modbus_index),
        'model': client.tag_product_model(modbus_index),
        'name': client.tag_name(modbus_index)
    }
    if not is_unreachable:
        kwargs['suggested_area'] = client.tag_usage(modbus_index).name

    if not is_unreachable and logging.DEBUG >= _LOGGER.level:
        position = client.tag_position(modbus_index)
        power_supply_type = client.tag_power_supply_type(modbus_index)
        rated_current = client.tag_rated_current(modbus_index)
        rated_voltage = client.tag_rated_voltage(modbus_index)
        circuit_diagnostic = client.tag_circuit_diagnostic(modbus_index)
        circuit = client.tag_circuit(modbus_index)
        product_code = client.tag_product_code(modbus_index)
        phase_sequence = client.tag_phase_sequence(modbus_index)
        family = client.tag_product_family(modbus_index)

        _LOGGER.debug(f"Found new device: name {kwargs['name']}, circuit {circuit}, rated voltage {rated_voltage}, "
                      f"rated current {rated_current}, position {position}, phase_sequence {phase_sequence}, "
                      f"family {family}, model {kwargs['model']}, product_code {product_code}, "
                      f" power_supply_type {power_supply_type}, circuit_diagnostic {circuit_diagnostic}, "
                      f"S/N {kwargs['serial_number']}")

    return DeviceInfo(kwargs)


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
        PhaseSequence.CBA: [Phase.C, Phase.B, Phase.A],
        PhaseSequence.INVALID: []
    }[phase_sequence]


def phase_sequence_to_line_voltages(phase_sequence: PhaseSequence, feature_class: FeatureClass) -> [LineVoltage]:
    has_neutral = feature_class not in [FeatureClass.A2, FeatureClass.F2]
    if phase_sequence is PhaseSequence.INVALID:
        return []
    elif phase_sequence in [PhaseSequence.A, PhaseSequence.B, PhaseSequence.C]:
        if not has_neutral:
            return []
        return {
            PhaseSequence.A: [LineVoltage.A_N],
            PhaseSequence.B: [LineVoltage.B_N],
            PhaseSequence.C: [LineVoltage.C_N]
        }[phase_sequence]
    else:
        return [LineVoltage.A_N, LineVoltage.B_N, LineVoltage.C_N] if has_neutral \
            else [LineVoltage.A_B, LineVoltage.B_C, LineVoltage.C_A]


class GatewayEntity(Entity):
    def __init__(self, client: SchneiderModbus, tag_device: DeviceInfo, sensor_name: str):
        self._client = client

        self._attr_device_info = tag_device
        self._attr_name = f"{tag_device['name']} {sensor_name}"

        serial = client.serial_number()
        self._attr_unique_id = f"{TAG_DOMAIN}{serial}{sensor_name}"

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        raise NotImplementedError()


class WirelessDeviceEntity(Entity):
    def __init__(self, client: SchneiderModbus, modbus_index: int,
                 tag_device: DeviceInfo, entity_name: str,
                 unique_id_version: UniqueIdVersion):

        self._client = client
        self._modbus_index = modbus_index

        self._attr_device_info = tag_device
        self._attr_name = f"{tag_device['name']} {entity_name}"

        serial = client.tag_serial_number(modbus_index)

        if unique_id_version == UniqueIdVersion.V1:
            self._attr_unique_id = f"{TAG_DOMAIN}{serial}{entity_name}{modbus_index}"
        else:
            self._attr_unique_id = f"{TAG_DOMAIN}{serial}{entity_name}"

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        raise NotImplementedError()

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        raise NotImplementedError()

    @staticmethod
    def supports_firmware_version(firmware_version: str) -> bool:
        return True


def collect_entities(client: SchneiderModbus, entities: list[Entity], feature_class: FeatureClass, modbus_address: int,
                     powertag_entity: type[WirelessDeviceEntity], tag_device: DeviceInfo, tag_phase_sequence: PhaseSequence, device_unique_id_version: UniqueIdVersion):
    params_raw = inspect.signature(powertag_entity.__init__).parameters
    params = [name for name in params_raw.items() if name[0] != "self" and name[0] != "kwargs"]
    args = []
    enumerate_param = None
    for param in params:
        typey = param[1].annotation
        if typey == SchneiderModbus:
            args.append(client)
        elif typey == DeviceInfo:
            args.append(tag_device)
        elif typey == int:
            assert param[0] == 'modbus_index'
            args.append(modbus_address)
        elif typey == FeatureClass:
            args.append(feature_class)
        elif typey == Phase:
            assert not enumerate_param
            phases = phase_sequence_to_phases(tag_phase_sequence)
            enumerate_param = (len(args), phases)
            args.append(None)
        elif typey == LineVoltage:
            assert not enumerate_param
            enumerate_param = (len(args), phase_sequence_to_line_voltages(tag_phase_sequence, feature_class))
            args.append(None)
        elif typey == UniqueIdVersion:
            args.append(device_unique_id_version)
        else:
            raise AssertionError("Dev fucked up, please create a GitHub issue. :(")
    if enumerate_param:
        arg_index, enumerated_param = enumerate_param
        for phase in enumerated_param:
            args[arg_index] = phase
            entities.append(powertag_entity(*args))

    else:
        entities.append(powertag_entity(*args))


def setup_entities(hass: HomeAssistant, config_entry: ConfigEntry, powertag_entities: list[type[WirelessDeviceEntity]]):
    data = hass.data[DOMAIN][config_entry.entry_id]
    client = data[CONF_CLIENT]
    presentation_url = data[CONF_INTERNAL_URL]
    device_unique_id_version = data[CONF_DEVICE_UNIQUE_ID_VERSION]

    entities = []
    gateway_device = gateway_device_info(client, presentation_url)
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers=gateway_device["identifiers"],
        manufacturer=gateway_device.get("manufacturer"),
        model=gateway_device.get("model"),
        name=gateway_device.get("name"),
        sw_version=gateway_device.get("sw_version"),
        hw_version=gateway_device.get("hw_version"),
        configuration_url=gateway_device.get("configuration_url"),
        serial_number=gateway_device.get("serial_number"),
    )

    for i in range(1, 100):
        modbus_address = client.modbus_address_of_node(i)
        if modbus_address is None:
            break

        if client.type_of_gateway == TypeOfGateway.SMARTLINK:
            identifier = client.tag_product_identifier(modbus_address)
            if identifier is None:
                break

            _LOGGER.debug(f"Found device #{modbus_address} to have product wireless device type code {identifier}")

            try:
                feature_class = from_wireless_device_type_code(identifier)
            except UnknownDevice:
                _LOGGER.error(f"I don't know what this product identifier is: {identifier}, but we can fix this! :) "
                              f"Please create a GitHub issue and tell me model of the {modbus_address}th wireless "
                              f"device.")
                continue

        else:
            commercial_reference = client.tag_product_code(modbus_address)

            _LOGGER.debug(f"Device #{modbus_address} is {commercial_reference}")

            try:
                feature_class = from_commercial_reference(commercial_reference)
            except UnknownDevice:
                _LOGGER.error(f"Unsupported wireless device: {commercial_reference}, "
                              f"to request support, please create a GitHub issue for this device.")
                continue

        if client.type_of_gateway is not TypeOfGateway.SMARTLINK:
            is_disabled = client.tag_radio_lqi_gateway(modbus_address) is None
            if is_disabled:
                _LOGGER.warning(f"The device {client.tag_name(modbus_address)} is not reachable; will ignore this one.")
                continue

        tag_device = tag_device_info(
            client, modbus_address, presentation_url, next(iter(gateway_device["identifiers"]))
        )
        device_name = tag_device['name']

        tag_phase_sequence = client.tag_phase_sequence(modbus_address)
        if not tag_phase_sequence:
            _LOGGER.warning(f"The phase sequence of {device_name} was not defined."
                            f"Skipping adding phase-specific entities...")

        for powertag_entity in [
            entity for entity in powertag_entities
            if entity.supports_feature_set(feature_class)
               and entity.supports_gateway(client.type_of_gateway)
               and entity.supports_firmware_version(tag_device['sw_version'])
        ]:
            collect_entities(
                client, entities, feature_class, modbus_address,
                powertag_entity, tag_device, tag_phase_sequence,
                device_unique_id_version
            )

        _LOGGER.info(f"Done with device at address {modbus_address}: {device_name}")
    return entities
