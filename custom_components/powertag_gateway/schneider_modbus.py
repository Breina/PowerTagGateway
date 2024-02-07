import enum
import logging
import math
from datetime import datetime

from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.pdu import ExceptionResponse

GATEWAY_SLAVE_ID = 255
SYNTHESIS_TABLE_SLAVE_ID_START = 247

log = logging.getLogger(__name__)


class Phase(enum.Enum):
    A = 0
    B = 2
    C = 4


class LineVoltage(enum.Enum):
    A_B = 0
    B_C = 2
    C_A = 4
    A_N = 8
    B_N = 10
    C_N = 12


class LinkStatus(enum.Enum):
    START_UP = 0b0001
    OPERATING = 0b0010
    DOWNGRADED = 0b0100
    GENERAL_FAILURE = 0b1000
    E2PROM_ERROR = 0b0010_0000_0000_1000
    RAM_ERROR = 0b0100_0000_0000_1000
    FLASH_ERROR = 0b1000_0000_0000_1000


class PanelHealth(enum.Enum):
    NOMINAL = 0
    DEGRADED = 1
    OUT_OF_ORDER = 2


class AlarmStatus:
    def __init__(self, bitmask: int):
        lower_mask = bitmask & 0b1111_1111

        self.has_alarm = lower_mask != 0
        self.alarm_voltage_loss = (lower_mask & 0b0000_0001) != 0
        self.alarm_current_overload = (lower_mask & 0b0000_0010) != 0
        # self.alarm_reserved = (lower_mask & 0b0000_0100) != 0
        self.alarm_overload_45_percent = (lower_mask & 0b0000_1000) != 0
        self.alarm_load_current_loss = (lower_mask & 0b0001_0000) != 0
        self.alarm_overvoltage = (lower_mask & 0b0010_0000) != 0
        self.alarm_undervoltage = (lower_mask & 0b0100_0000) != 0
        self.alarm_heattag_alarm = (lower_mask & 0b0001_0000_0000) != 0
        self.alarm_heattag_maintenance = (lower_mask & 0b0100_0000_0000) != 0
        self.alarm_heattag_replacement = (lower_mask & 0b1000_0000_0000) != 0


class DeviceUsage(enum.Enum):
    main_incomer = 1
    sub_head_of_group = 2
    heating = 3
    cooling = 4
    hvac = 5
    ventilation = 6
    lighting = 7
    office_equipment = 8
    cooking = 9
    food_refrigeration = 10
    elevators = 11
    computers = 12
    renewable_power_source = 13
    genset = 14
    compressed_air = 15
    vapor = 16
    machine = 17
    process = 18
    water_system_pumps = 19
    other_sockets = 20
    other = 21
    electrical_vehicle_charging_station = 22
    loads_associated_with_renewable_power_source = 23
    plug_loads = 24
    air_conditioning = 25
    domestic_hot_water = 26
    heating_air_conditioning = 27
    hot_sanitary_water = 28
    it = 29
    lighting_interior = 30
    lighting_exterior_and_park = 31
    mixed_usages = 32
    refrigeration = 33
    special_loads = 34
    total = 35
    transportation_system = 36
    water = 37
    INVALID = None


class PhaseSequence(enum.Enum):
    A = 1
    B = 2
    C = 3
    ABC = 4
    ACB = 5
    BCA = 6
    BAC = 7
    CAB = 8
    CBA = 9
    INVALID = None


class Position(enum.Enum):
    not_configured = 0
    top = 1
    bottom = 2
    not_applicable = 3
    INVALID = None


class ProductType(enum.Enum):
    A9MEM1520 = (41, 17200, "PowerTag M63 1P")
    A9MEM1521 = (42, 17201, "PowerTag M63 1P+N Top")
    A9MEM1522 = (43, 17202, "PowerTag M63 1P+N Bottom")
    A9MEM1540 = (44, 17203, "PowerTag M63 3P")
    A9MEM1541 = (45, 17204, "PowerTag M63 3P+N Top")
    A9MEM1542 = (46, 17205, "PowerTag M63 3P+N Bottom")
    A9MEM1560 = (81, 17206, "PowerTag F63 1P+N")
    A9MEM1561 = (82, 17207, "PowerTag P63 1P+N Top")
    A9MEM1562 = (83, 17208, "PowerTag P63 1P+N Bottom")
    A9MEM1563 = (84, 17209, "PowerTag P63 1P+N Bottom")
    A9MEM1570 = (85, 17209, "PowerTag F63 3P+N")
    A9MEM1571 = (86, 17211, "PowerTag P63 3P+N Top")
    A9MEM1572 = (87, 17212, "PowerTag P63 3P+N Bottom")
    LV434020 = (92, 17800, "PowerTag M250 3P")
    LV434021 = (93, 17801, "PowerTag M250 4P")
    LV434022 = (94, 17802, "PowerTag M630 3P")
    LV434023 = (95, 17803, "PowerTag M630 4P")
    A9MEM1543 = (96, 17213, "PowerTag M63 3P 230 V")
    A9XMC2D3 = (97, 17900, "PowerTag C 2DI 230 V")
    A9XMC1D3 = (98, 17901, "PowerTag C IO 230 V")
    A9MEM1564 = (101, 17215, "PowerTag F63 1P+N 110 V")
    A9MEM1573 = (102, 17214, "PowerTag F63 3P")
    A9MEM1574 = (103, 17216, "PowerTag F63 3P+N 110/230 V")
    A9MEM1590 = (104, 17969, "PowerTag R200")
    A9MEM1591 = (105, 17970, "PowerTag R600")
    A9MEM1592 = (106, 17971, "PowerTag R1000")
    A9MEM1593 = (107, 17972, "PowerTag R2000")
    A9MEM1580 = (121, 17980, "PowerTag F160")
    A9XMWRD = (170, 9150, "PowerTag Link display")
    SMT10020 = (171, 17350, "HeatTag sensor")


class PowerFactorSignConvention(enum.Enum):
    IEC = 0
    IEEE = 1
    INVALID = None


class ElectricalNetworkSystemType(enum.Enum):
    UNKNOWN = (0, "Unknown system type")
    PH3W = (3, "3PH3W")
    PH4W = (11, "3PH4W")
    INVALID = (None, "Invalid")


class TypeOfGateway(enum.Enum):
    PANEL_SERVER = "Panel server"
    POWERTAG_LINK = "Powertag Link"
    SMARTLINK = "Smartlink SI D"


class SchneiderModbus:
    def __init__(self, host, type_of_gateway: TypeOfGateway, port=502, timeout=5):
        log.info(f"Connecting Modbus TCP to {host}:{port}")
        self.client = ModbusTcpClient(host, port, timeout=timeout)
        self.client.connect()
        self.type_of_gateway = type_of_gateway
        if type_of_gateway is TypeOfGateway.POWERTAG_LINK:
            self.synthetic_slave_id = self.find_synthentic_table_slave_id()

    def find_synthentic_table_slave_id(self):
        for slave_id in range(SYNTHESIS_TABLE_SLAVE_ID_START, 1, -1):
            try:
                self.__read_int_16(0x0001, slave_id)
                return slave_id
            except ConnectionError:
                continue
        raise ConnectionError("Could not find synthetic slave ID")

    # Identification
    def hardware_version(self) -> str:
        """Gateway Hardware version
        valid for firmware version 001.008.007 and later.
        """
        if self.type_of_gateway == TypeOfGateway.SMARTLINK:
            return self.__read_string(0x006A, 3, GATEWAY_SLAVE_ID, 6)
        else:
            return self.__read_string(0x0050, 6, GATEWAY_SLAVE_ID, 11)

    def serial_number(self) -> str:
        """[S/N]: PP YY WW [D [nnnn]]
        • PP: Plant
        • YY: Year in decimal notation [05...99]
        • WW: Week in decimal notation [1...53]
        • D: Day of the week in decimal notation [1...7]
        • nnnn: Sequence of numbers [0001...10.00-0–1]
        """
        return self.__read_string(0x0064, 6, GATEWAY_SLAVE_ID, 11)

    def firmware_version(self) -> str:
        """valid for firmware version 001.008.007 and later."""
        if self.type_of_gateway == TypeOfGateway.SMARTLINK:
            return self.__read_string(0x006D, 3, GATEWAY_SLAVE_ID, 6)
        else:
            return self.__read_string(0x0078, 6, GATEWAY_SLAVE_ID, 11)

    # Status

    def status(self) -> LinkStatus:
        """PowerTag Link gateway status and diagnostic register"""
        assert self.type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.SMARTLINK]
        bitmap = self.__read_int_16(0x0070, GATEWAY_SLAVE_ID)
        try:
            return LinkStatus(bitmap)
        except Exception as e:
            logging.error(f"Could not map status, defaulting to GENERAL_FAILURE ({str(e)}")
            return LinkStatus.GENERAL_FAILURE

    def health(self) -> PanelHealth:
        """PowerTag Link gateway status and diagnostic register"""
        assert self.type_of_gateway == TypeOfGateway.PANEL_SERVER
        code = self.__read_int_16(0x009E, GATEWAY_SLAVE_ID)
        return PanelHealth(code)

    # Date and Time

    def date_time(self) -> datetime | None:
        """Indicates the year, month, day, hour, minute and millisecond on the PowerTag Link gateway."""
        return self.__read_date_time(0x0073, GATEWAY_SLAVE_ID)

    # Current Metering Data

    def tag_current(self, power_tag_index: int, phase: Phase) -> float | None:
        """RMS current on phase"""
        return self.__read_float_32(0xBB7 + phase.value, power_tag_index)

    def tag_current_neutral(self, power_tag_index: int) -> float | None:
        """RMS current on Neutral"""
        return self.__read_float_32(0xBBD, power_tag_index)

    # Voltage Metering Data

    def tag_voltage(self, power_tag_index: int, line_voltage: LineVoltage) -> float | None:
        """RMS phase-to-phase voltage"""
        return self.__read_float_32(0xBCB + line_voltage.value, power_tag_index)

    # Power Metering Data

    def tag_power_active(self, power_tag_index: int, phase: Phase) -> float | None:
        """Active power on phase"""
        return self.__read_float_32(0xBED + phase.value, power_tag_index)

    def tag_power_active_total(self, power_tag_index: int) -> float | None:
        """Total active power"""
        return self.__read_float_32(0xBF3, power_tag_index)

    def tag_power_reactive(self, power_tag_index: int, phase: Phase) -> float | None:
        """Reactive power on phase"""
        return self.__read_float_32(0xBF5 + phase.value, power_tag_index)

    def tag_power_reactive_total(self, power_tag_index: int) -> float | None:
        """Total reactive power"""
        return self.__read_float_32(0xBFB, power_tag_index)

    def tag_power_apparent(self, power_tag_index: int, phase: Phase) -> float | None:
        """Apparent power on phase"""
        return self.__read_float_32(0xBFD + phase.value, power_tag_index)

    def tag_power_apparent_total(self, power_tag_index: int) -> float | None:
        """Total apparent power (arithmetric)"""
        return self.__read_float_32(0xC03, power_tag_index)

    # Power Factor Metering Data

    def tag_power_factor(self, power_tag_index: int, phase: Phase) -> float | None:
        """Power factor on phase"""
        return self.__read_float_32(0xC05 + phase.value, power_tag_index)

    def tag_power_factor_total(self, power_tag_index: int) -> float | None:
        """Total power factor"""
        return self.__read_float_32(0xC0B, power_tag_index)

    def tag_power_factor_sign_convention(self, power_tag_index: int) -> PowerFactorSignConvention:
        """Power factor sign convention"""
        return PowerFactorSignConvention(self.__read_int_16(0xC0D, power_tag_index))

    # Frequency Metering Data

    def tag_ac_frequency(self, power_tag_index: int) -> float | None:
        """AC frequency"""
        return self.__read_float_32(0xC25, power_tag_index)

    # Device Temperature Metering Data

    def tag_device_temperature(self, power_tag_index: int) -> float | None:
        """Device internal temperature"""
        return self.__read_float_32(0xC3B, power_tag_index)

    # Energy Data – Legacy Zone

    def tag_energy_active_delivered_plus_received_total(self, power_tag_index: int) -> int | None:
        """Total active energy delivered + received (not resettable)"""
        return self.__read_int_64(0xC83, power_tag_index)

    def tag_energy_active_delta(self, power_tag_index: int, phase: Phase) -> int | None:
        """Active energy on phase delivered - received (not resettable)"""
        return self.__read_int_64(0xC8F + phase.value * 2, power_tag_index)

    def tag_energy_active_delivered_plus_received_partial(self, power_tag_index: int) -> int | None:
        """Partial active energy delivered + received (resettable)"""
        return self.__read_int_64(0xCB7, power_tag_index)

    def tag_reset_energy_active_partial(self, power_tag_index: int):
        """Set partial active energy counter. The value returns to zero by PowerTag Link gateway"""
        self.__write_int_64(0xCBB, power_tag_index, 1)

    def tag_reset_energy_active_delivered_partial(self, power_tag_index: int):
        """Set partial active energy delivered counter. The value returns to zero by PowerTag Link gateway"""
        self.__write_int_64(0xCC3, power_tag_index, 1)

    def tag_reset_energy_active_received_partial(self, power_tag_index: int):
        """Set partial active energy received counter. The value returns to zero by PowerTag Link gateway."""
        self.__write_int_64(0xCCB, power_tag_index, 1)

    def tag_reset_energy_reactive_delivered_partial(self, power_tag_index: int):
        """Set partial reactive energy delivered counter. The value returns to zero by PowerTag Link gateway."""
        self.__write_int_64(0xCD3, power_tag_index, 1)

    def tag_reset_energy_reactive_received_partial(self, power_tag_index: int):
        """Set partial reactive energy received counter. The value returns to zero by PowerTag Link gateway."""
        self.__write_int_64(0xCDB, power_tag_index, 1)

    # Energy Data – New Zone

    def tag_energy_active_delivered_partial(self, power_tag_index: int) -> int | None:
        """Active energy delivered (resettable)"""
        return self.__read_int_64(0x1390, power_tag_index)

    def tag_energy_active_delivered_total(self, power_tag_index: int) -> int | None:
        """Active energy delivered count positively (not resettable)"""
        return self.__read_int_64(0x1394, power_tag_index)

    def tag_energy_active_received_partial(self, power_tag_index: int) -> int | None:
        """Active energy received (resettable)"""
        return self.__read_int_64(0x1398, power_tag_index)

    def tag_energy_active_received_total(self, power_tag_index: int) -> int | None:
        """Active energy received count negatively (not resettable)"""
        return self.__read_int_64(0x139C, power_tag_index)

    def tag_energy_active_delivered_partial_phase(self, power_tag_index: int, phase: Phase) -> int | None:
        """Active energy on phase delivered (resettable)"""
        return self.__read_int_64(0x13B8 + phase.value * 0x14, power_tag_index)

    def tag_energy_active_delivered_total_phase(self, power_tag_index: int, phase: Phase) -> int | None:
        """Active energy on phase delivered (not resettable)"""
        return self.__read_int_64(0x13BC + phase.value * 0x14, power_tag_index)

    def tag_energy_active_received_partial_phase(self, power_tag_index: int, phase: Phase) -> int | None:
        """Active energy on phase received (resettable)"""
        return self.__read_int_64(0x13C0 + phase.value * 0x14, power_tag_index)

    def tag_energy_active_received_total_phase(self, power_tag_index: int, phase: Phase) -> int | None:
        """Active energy on phase received (not resettable)"""
        return self.__read_int_64(0x13C4 + phase.value * 0x14, power_tag_index)

    def tag_energy_reactive_delivered_partial(self, power_tag_index: int) -> int | None:
        """Reactive energy delivered (resettable)"""
        return self.__read_int_64(0x1438, power_tag_index)

    def tag_energy_reactive_delivered_total(self, power_tag_index: int) -> int | None:
        """Reactive energy delivered count positively (not resettable)"""
        return self.__read_int_64(0x143C, power_tag_index)

    def tag_energy_reactive_received_partial(self, power_tag_index: int) -> int | None:
        """Reactive energy received (resettable)"""
        return self.__read_int_64(0x1488, power_tag_index)

    def tag_energy_reactive_received_total(self, power_tag_index: int) -> int | None:
        """Reactive energy received count negatively (not resettable)"""
        return self.__read_int_64(0x144C, power_tag_index)

    def tag_energy_reactive_delivered_partial_phase(self, power_tag_index: int, phase: Phase) -> int | None:
        """Reactive energy on phase delivered (resettable)"""
        return self.__read_int_64(0x1470 + phase.value * 0x14, power_tag_index)

    def tag_energy_reactive_delivered_total_phase(self, power_tag_index: int, phase: Phase) -> int | None:
        """Reactive energy on phase delivered (not resettable)"""
        return self.__read_int_64(0x1474 + phase.value * 0x14, power_tag_index)

    def tag_energy_reactive_received_partial_phase(self, power_tag_index: int, phase: Phase) -> int | None:
        """Reactive energy on phase received (resettable)"""
        return self.__read_int_64(0x1478 + phase.value * 0x14, power_tag_index)

    def tag_energy_reactive_received_total_phase(self, power_tag_index: int, phase: Phase) -> int | None:
        """Reactive energy on phase received (not resettable)"""
        return self.__read_int_64(0x147C + phase.value * 0x14, power_tag_index)

    def tag_energy_apparent_partial(self, power_tag_index: int) -> int | None:
        """Apparent energy delivered + received (resettable)"""
        return self.__read_int_64(0x14F4, power_tag_index)

    def tag_energy_apparent_total(self, power_tag_index: int) -> int | None:
        """Apparent energy delivered + received (not resettable)"""
        return self.__read_int_64(0x14F8, power_tag_index)

    def tag_energy_apparent_partial_phase(self, power_tag_index: int, phase: Phase) -> int | None:
        """Apparent energy on phase (resettable)"""
        return self.__read_int_64(0x150C + phase.value * 0x14, power_tag_index)

    def tag_energy_apparent_total_phase(self, power_tag_index: int, phase: Phase) -> int | None:
        """Apparent energy on phase A (not resettable)"""
        return self.__read_int_64(0x1510 + phase.value * 0x14, power_tag_index)

    # Power Demand Data

    def tag_power_active_demand_total(self, power_tag_index: int) -> float | None:
        """Demand total active power"""
        return self.__read_float_32(0x0EB5, power_tag_index)

    def tag_power_active_power_demand_total_maximum(self, power_tag_index: int) -> float | None:
        """Maximum Demand total active power"""
        return self.__read_float_32(0x0EB9, power_tag_index)

    def tag_power_active_demand_total_maximum_timestamp(self, power_tag_index: int) -> datetime | None:
        """Maximum Demand total active power"""
        return self.__read_date_time(0x0EBB, power_tag_index)

    # Alarm

    def tag_is_alarm_valid(self, power_tag_index: int) -> bool | None:
        """Validity of the alarm bitmap"""
        return (self.__read_int_16(0xCE1, power_tag_index) & 0b1) != 0

    def tag_get_alarm(self, power_tag_index: int) -> AlarmStatus:
        """Alarms"""
        return AlarmStatus(self.__read_int_16(0xCE3, power_tag_index))

    def tag_current_at_voltage_loss(self, power_tag_index: int, phase: Phase) -> float | None:
        """RMS current on phase at voltage loss (last RMS current measured when voltage loss occurred)"""
        return self.__read_float_32(0xCE5 + phase.value, power_tag_index)

    # Load Operating Time

    def tag_load_operating_time(self, power_tag_index: int) -> int | None:
        """Load operating time counter."""
        return self.__read_int_32(0xCEB, power_tag_index)

    def tag_load_operating_time_active_power_threshold(self, power_tag_index: int) -> float | None:
        """Active power threshold for Load operating time counter. Counter starts above the threshold value."""
        return self.__read_float_32(0xCED, power_tag_index)

    def tag_load_operating_time_start(self, power_tag_index: int) -> datetime | None:
        """Date and time stamp of last Set or reset of Load operating time counter."""
        return self.__read_date_time(0xCEF, power_tag_index)

    # Configuration Registers

    def tag_name(self, power_tag_index: int) -> str | None:
        """User application name of the wireless device. The user can enter maximum 20 characters."""
        return self.__read_string(0x7918, 10, power_tag_index, 20)

    def tag_circuit(self, power_tag_index: int) -> str:
        """Circuit identifier of the wireless device. The user can enter maximum five characters."""
        return self.__read_string(0x7922, 3, power_tag_index, 5)

    def tag_usage(self, power_tag_index: int) -> DeviceUsage:
        """Indicates the usage of the wireless device."""
        return DeviceUsage(self.__read_int_16(0x7925, power_tag_index))

    def tag_phase_sequence(self, power_tag_index: int) -> PhaseSequence:
        """Phase sequence."""
        return PhaseSequence(self.__read_int_16(0x7926, power_tag_index))

    def tag_position(self, power_tag_index: int) -> Position:
        """Mounting position"""
        return Position(self.__read_int_16(0x7927, power_tag_index))

    def tag_circuit_diagnostic(self, power_tag_index: int) -> Position:
        """Circuit diagnostics"""
        return Position(self.__read_int_16(0x7928, power_tag_index))

    def tag_rated_current(self, power_tag_index: int) -> int | None:
        """Rated current of the protective device to the wireless device"""
        return self.__read_int_16(0x7929, power_tag_index)

    def tag_electrical_network_system_type(self, power_tag_index: int) -> ElectricalNetworkSystemType:
        code = self.__read_int_16(0x792A, power_tag_index)
        system_type = [e for e in ElectricalNetworkSystemType if e.value[0] == code]
        return system_type[0] if system_type else None

    def tag_rated_voltage(self, power_tag_index: int) -> float | None:
        """Rated voltage"""
        if self.type_of_gateway == TypeOfGateway.SMARTLINK:
            return None
        return self.__read_float_32(0x792B, power_tag_index)

    def tag_reset_peak_demands(self, power_tag_index: int):
        """Reset All Peak Demands"""
        self.__write_int_16(0x792E, power_tag_index, 1)

    def tag_power_supply_type(self, power_tag_index: int) -> Position:
        """Power supply type"""
        if self.type_of_gateway == TypeOfGateway.SMARTLINK:
            return Position.INVALID
        return Position(self.__read_int_16(0x792F, power_tag_index))

    # Device identification

    def tag_product_type(self, power_tag_index: int) -> ProductType | None:
        """Wireless device code type"""
        if self.type_of_gateway == TypeOfGateway.SMARTLINK:
            identifier = self.__read_int_16(0x7930, power_tag_index)
        else:
            identifier = self.__read_int_16(0x7937, power_tag_index)
        product_type = [p for p in ProductType if p.value[1] == identifier]
        return product_type[0] if product_type else None

    def tag_slave_address(self, power_tag_index: int) -> int | None:
        """Virtual Modbus server address"""
        return self.__read_int_16(0x7931, power_tag_index)

    def tag_rf_id(self, power_tag_index: int) -> int | None:
        """Wireless device Radio Frequency Identifier"""
        return self.__read_int_64(0x7932, power_tag_index)

    def tag_vendor_name(self, power_tag_index: int) -> str | None:
        """Vendor name"""
        return self.__read_string(0x7944, 16, power_tag_index, 32)

    def tag_product_code(self, power_tag_index: int) -> str | None:
        """Wireless device commercial reference"""
        if self.type_of_gateway is TypeOfGateway.SMARTLINK:
            return None
        return self.__read_string(0x7954, 16, power_tag_index, 32)

    def tag_firmware_revision(self, power_tag_index: int) -> str | None:
        """Firmware revision"""
        return self.__read_string(0x7964, 6, power_tag_index, 12)

    def tag_hardware_revision(self, power_tag_index: int) -> str | None:
        """Hardware revision"""
        return self.__read_string(0x796A, 6, power_tag_index, 12)

    def tag_serial_number(self, power_tag_index: int) -> str | None:
        """Serial number"""
        return self.__read_string(0x7970, 10, power_tag_index, 20)

    def tag_product_range(self, power_tag_index: int) -> str | None:
        """Product range"""
        return self.__read_string(0x797A, 8, power_tag_index, 16)

    def tag_product_model(self, power_tag_index: int) -> str | None:
        """Product model"""
        return self.__read_string(0x7982, 8, power_tag_index, 16)

    def tag_product_family(self, power_tag_index: int) -> str | None:
        """Product family"""
        if self.type_of_gateway is TypeOfGateway.SMARTLINK:
            return None
        return self.__read_string(0x798A, 8, power_tag_index, 16)

    # Diagnostic Data Registers

    def tag_radio_communication_valid(self, power_tag_index: int) -> bool:
        """Validity of the RF communication between PowerTag system and PowerTag Link gateway status."""
        return self.__read_int_16(0x79A8, power_tag_index) != 0

    def tag_wireless_communication_valid(self, power_tag_index: int) -> bool:
        """Communication status between PowerTag Link gateway and wireless devices."""
        return self.__read_int_16(0x79A9, power_tag_index) != 0

    def tag_radio_per_tag(self, power_tag_index: int) -> float | None:
        """Packet Error Rate (PER) of the device, received by PowerTag Link gateway"""
        return self.__read_float_32(0x79B4, power_tag_index)

    def tag_radio_rssi_inside_tag(self, power_tag_index: int) -> float | None:
        """RSSI of the device, received by PowerTag Link gateway"""
        return self.__read_float_32(0x79B6, power_tag_index)

    def tag_radio_lqi_tag(self, power_tag_index: int) -> int | None:
        """Link Quality Indicator (LQI) of the device, received by PowerTag Link gateway"""
        return self.__read_int_16(0x79B8, power_tag_index)

    def tag_radio_per_gateway(self, power_tag_index: int) -> float | None:
        """PER of gateway, calculated inside the PowerTag Link gateway"""
        return self.__read_float_32(0x79AF, power_tag_index)

    def tag_radio_rssi_inside_gateway(self, power_tag_index: int) -> float | None:
        """Radio Signal Strength Indicator (RSSI) of gateway, calculated inside the PowerTag Link gateway"""
        return self.__read_float_32(0x79B1, power_tag_index)

    def tag_radio_lqi_gateway(self, power_tag_index: int) -> float | None:
        """LQI of gateway, calculated insider the PowerTag Link gateway"""
        return self.__read_int_16(0x79B3, power_tag_index)

    def tag_radio_per_maximum(self, power_tag_index: int) -> float | None:
        """PER–Maximum value between device and gateway"""
        return self.__read_float_32(0x79B4, power_tag_index)

    def tag_radio_rssi_minimum(self, power_tag_index: int) -> float | None:
        """RSSI–Minimal value between device and gateway"""
        return self.__read_float_32(0x79B6, power_tag_index)

    def tag_radio_lqi_minimum(self, power_tag_index: int) -> float | None:
        """LQI–Minimal value between device and gateway"""
        return self.__read_int_16(0x79B8, power_tag_index)

    # Identification and Status Register

    def product_id(self) -> int | None:
        """Product ID of the synthesis table"""
        if self.type_of_gateway is TypeOfGateway.POWERTAG_LINK:
            return self.__read_int_16(0x0001, self.synthetic_slave_id)
        elif self.type_of_gateway is TypeOfGateway.PANEL_SERVER:
            return self.__read_int_16(0xF002, GATEWAY_SLAVE_ID)
        else:
            return None

    def manufacturer(self) -> str | None:
        """Product ID of the synthesis table"""
        if self.type_of_gateway is TypeOfGateway.POWERTAG_LINK:
            return self.__read_string(0x0002, 16, self.synthetic_slave_id, 32)
        elif self.type_of_gateway is TypeOfGateway.PANEL_SERVER:
            return self.__read_string(0x009F, 16, GATEWAY_SLAVE_ID, 32)
        elif self.type_of_gateway is TypeOfGateway.SMARTLINK:
            return "Schneider Electric"
        else:
            return None

    def product_code(self) -> str | None:
        """Commercial reference of the gateway"""
        if self.type_of_gateway is TypeOfGateway.POWERTAG_LINK:
            return self.__read_string(0x0012, 16, self.synthetic_slave_id, 32)
        elif self.type_of_gateway is TypeOfGateway.PANEL_SERVER:
            return self.__read_string(0x003C, 16, GATEWAY_SLAVE_ID, 32)
        elif self.type_of_gateway is TypeOfGateway.SMARTLINK:
            return "A9XMWA20"
        else:
            return None

    def product_range(self) -> str | None:
        """Product range of the gateway"""
        if self.type_of_gateway is TypeOfGateway.POWERTAG_LINK:
            return self.__read_string(0x0022, 8, self.synthetic_slave_id, 16)
        elif self.type_of_gateway is TypeOfGateway.PANEL_SERVER:
            return self.__read_string(0x000A, 16, GATEWAY_SLAVE_ID, 32)
        else:
            return "Unknown"

    def product_model(self) -> str | None:
        """Product model"""
        if self.type_of_gateway is TypeOfGateway.POWERTAG_LINK:
            return self.__read_string(0x002A, 8, self.synthetic_slave_id, 16)
        elif self.type_of_gateway is TypeOfGateway.PANEL_SERVER:
            return self.__read_string(0xF003, 16, GATEWAY_SLAVE_ID, 32)
        else:
            return "Smartlink SI D"

    def name(self) -> str | None:
        """Asset name"""
        if self.type_of_gateway is TypeOfGateway.POWERTAG_LINK:
            return self.__read_string(0x0032, 10, self.synthetic_slave_id, 20)
        elif self.type_of_gateway is TypeOfGateway.PANEL_SERVER:
            return self.__read_string(0x1605, 32, GATEWAY_SLAVE_ID, 64)
        else:
            return "Unknown"

    def product_vendor_url(self) -> str | None:
        """Vendor URL"""
        if self.type_of_gateway is TypeOfGateway.POWERTAG_LINK:
            return self.__read_string(0x003C, 17, self.synthetic_slave_id, 34)
        elif self.type_of_gateway is TypeOfGateway.PANEL_SERVER:
            return self.__read_string(0x002A, 17, GATEWAY_SLAVE_ID, 34)
        else:
            return "Unknown"

    # Wireless Configured Devices – 100 Devices

    def modbus_address_of_node(self, node_index: int) -> int | None:
        if self.type_of_gateway is TypeOfGateway.SMARTLINK:
            return 150 + node_index - 1
        elif self.type_of_gateway is TypeOfGateway.POWERTAG_LINK:
            return self.__read_int_16(0x012C + node_index - 1, self.synthetic_slave_id)
        else:
            return self.__read_int_16(0x01F8 + (node_index - 1) * 5, GATEWAY_SLAVE_ID)

    # Helper functions

    def __write(self, address: int, registers: list[int], slave_id: int):
        self.client.write_registers(address, registers, slave=slave_id)

    def __read(self, address: int, count: int, slave_id: int):
        response = self.client.read_holding_registers(address, count, slave=slave_id)
        if isinstance(response, ExceptionResponse):
            raise ConnectionError(str(response))
        return response.registers

    @staticmethod
    def decoder(registers):
        return BinaryPayloadDecoder.fromRegisters(
            registers, byteorder=Endian.BIG, wordorder=Endian.BIG
        )

    def __read_string(self, address: int, count: int, slave_id: int, string_length: int) -> str | None:
        registers = self.__read(address, count, slave_id)
        ascii_bytes = self.decoder(registers).decode_string(string_length)

        if all(c == '\x00' for c in ascii_bytes):
            return None

        filtered_ascii_bytes = bytes(filter(lambda b: b != 0, list(ascii_bytes)))
        return bytes.decode(filtered_ascii_bytes)

    def __write_string(self, address: int, slave_id: int, string: str):
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)
        builder.add_string(string.ljust(20, '\x00'))
        self.__write(address, builder.to_registers(), slave_id)

    def __read_float_32(self, address: int, slave_id: int) -> float | None:
        result = self.decoder(self.__read(address, 2, slave_id)).decode_32bit_float()
        return result if not math.isnan(result) else None

    def __read_int_16(self, address: int, slave_id: int) -> int | None:
        result = self.decoder(self.__read(address, 1, slave_id)).decode_16bit_uint()
        return result if result != 0xFFFF else None

    def __write_int_16(self, address: int, slave_id: int, value: int):
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)
        builder.add_16bit_uint(value)
        self.__write(address, builder.to_registers(), slave_id)

    def __read_int_32(self, address: int, slave_id: int) -> int | None:
        result = self.decoder(self.__read(address, 2, slave_id)).decode_32bit_uint()
        return result if result != 0x8000_0000 else None

    def __read_int_64(self, address: int, slave_id: int) -> int | None:
        result = self.decoder(self.__read(address, 4, slave_id)).decode_64bit_uint()
        return result if result != 0x8000_0000_0000_0000 else None

    def __write_int_64(self, address: int, slave_id: int, value: int):
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)
        builder.add_64bit_uint(value)
        self.__write(address, builder.to_registers(), slave_id)

    def __read_date_time(self, address: int, slave_id) -> datetime | None:
        d = self.decoder(self.__read(address, 4, slave_id))

        year_raw = d.decode_16bit_uint()
        year = (year_raw & 0b0111_1111) + 2000

        day_month = d.decode_16bit_uint()
        day = day_month & 0b0001_1111
        month = (day_month >> 8) & 0b0000_1111

        minute_hour = d.decode_16bit_uint()
        minute = minute_hour & 0b0011_1111
        hour = (minute_hour >> 8) & 0b0001_1111

        second_millisecond = d.decode_16bit_uint()
        second = math.floor(second_millisecond / 1000)
        millisecond = second_millisecond - second * 1000

        if year_raw == 0xFFFF and day_month == 0xFFFF and minute_hour == 0xFFFF and second_millisecond == 0xFFFF:
            return None

        return datetime(year, month, day, hour, minute, second, millisecond)

try:
    LinkStatus(232323)
except Exception as e:
    print(e)