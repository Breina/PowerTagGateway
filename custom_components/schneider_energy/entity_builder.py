from .entities import gateway_device_info, tag_device_info, GatewayStatus, GatewayTime, PowerTagApparentPower, \
    PowerTagCurrent, PowerTagActivePower, PowerTagDemandActivePower, PowerTagTotalEnergy, PowerTagPartialEnergy, \
    PowerTagPowerFactor, PowerTagRssiTag, PowerTagRssiGateway, PowerTagLqiTag, PowerTagLqiGateway, PowerTagPerTag, \
    PowerTagPerGateway, PowerTagWirelessCommunicationValid, PowerTagRadioCommunicationValid, PowerTagResetPeakDemand, \
    PowerTagAlarmValid, PowerTagGetAlarm, phase_sequence_to_phases, PowerTagActivePowerPerPhase, \
    phase_sequence_to_line_voltages, PowerTagVoltage
from .schneider_modbus import SchneiderModbus

PRESENTATION_URL = "http://192.168.1.39"

client = SchneiderModbus("192.168.1.39")

entities = []

gateway_device = gateway_device_info(client, PRESENTATION_URL)

entities.append([
    GatewayStatus(client, gateway_device),
    GatewayTime(client, gateway_device)
])

for i in range(1, 100):
    modbus_address = client.modbus_address_of_node(1)
    if modbus_address is None:
        break

    tag_device = tag_device_info(client, modbus_address, PRESENTATION_URL, next(iter(gateway_device["identifiers"])))

    entities.append([
        PowerTagApparentPower(client, modbus_address, tag_device),
        PowerTagActivePower(client, modbus_address, tag_device),
        PowerTagDemandActivePower(client, modbus_address, tag_device),
        PowerTagTotalEnergy(client, modbus_address, tag_device),
        PowerTagPartialEnergy(client, modbus_address, tag_device),
        PowerTagPowerFactor(client, modbus_address, tag_device),
        PowerTagRssiTag(client, modbus_address, tag_device),
        PowerTagRssiGateway(client, modbus_address, tag_device),
        PowerTagLqiTag(client, modbus_address, tag_device),
        PowerTagLqiGateway(client, modbus_address, tag_device),
        PowerTagPerTag(client, modbus_address, tag_device),
        PowerTagPerGateway(client, modbus_address, tag_device),
        PowerTagWirelessCommunicationValid(client, modbus_address, tag_device),
        PowerTagRadioCommunicationValid(client, modbus_address, tag_device),
        PowerTagResetPeakDemand(client, modbus_address, tag_device),
        PowerTagAlarmValid(client, modbus_address, tag_device),
        PowerTagGetAlarm(client, modbus_address, tag_device)
    ])

    phase_sequence = client.tag_phase_sequence(modbus_address)

    for phase in phase_sequence_to_phases(phase_sequence):
        entities.append([
            PowerTagCurrent(client, modbus_address, tag_device, phase),
            PowerTagActivePowerPerPhase(client, modbus_address, tag_device, phase)
        ])

    for line_voltage in phase_sequence_to_line_voltages(phase_sequence):
            entities.append(PowerTagVoltage(client, modbus_address, tag_device, line_voltage))