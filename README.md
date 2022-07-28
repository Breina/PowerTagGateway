# EcoStruxure PowerTag Link Gateway

An integration to fully integrate Schneider's PowerTag ecosystem into Home Assistant.
This will enable monitor electric circuits in great detail.

## Features

* **Current**: per phase and rated current
* **Voltage**: per phase, total and rated voltage
* **Power**: active, apparent and power factor
* **Energy**: partial (resettable) and total
* **Demand**: active power, maximum active power (resettable) and timestamp of maximum active power
* **Alarm**: current state and its reasons
* **Diagnostics**: gateway status, LQI, RSSI, packet loss, connectivity status

## Compatibility

### Gateways

* [A9XMWD20: Acti9 PowerTag Link](https://www.se.com/ww/en/product/A9XMWD20/acti9-powertag-link-wireless-to-modbus-tcp-ip-concentrator/)
* [A9XMWD100: Acti9 PowerTag Link HD](https://www.se.com/ww/en/product/A9XMWD100/acti9-powertag-link-hd-wireless-to-modbus-tcp-ip-concentrator/)

### PowerTags

* [A9MEM1520: PowerTag Monoconnect 63A 1P+Wire top and bottom](https://www.se.com/ww/en/product/A9MEM1520/energy-sensor-powertag-monoconnect-63a-1p+wire-top-and-bottom-position/)
* [A9MEM1521: PowerTag Monoconnect 63A 1P+N top position](https://www.se.com/ww/en/product/A9MEM1521/energy-sensor-powertag-monoconnect-63a-1p+n-top-position/)
* [A9MEM1522: PowerTag Monoconnect 63A 1P+N bottom position](https://www.se.com/ww/en/product/A9MEM1522/energy-sensor-powertag-monoconnect-63a-1p+n-bottom-position/)
* [A9MEM1540: PowerTag Monoconnect 63A 3P top and bottom position](https://www.se.com/ww/en/product/A9MEM1540/energy-sensor-powertag-monoconnect-63a-3p-top-and-bottom-position/)
* [A9MEM1541: PowerTag Monoconnect 63A 3P+N top position](https://se.com/ww/en/product/A9MEM1541/energy-sensor-powertag-monoconnect-63a-3p+n-top-position/)
* [A9MEM1542: PowerTag Monoconnect 63A 3P+N bottom position](https://www.se.com/ww/en/product/A9MEM1542/energy-sensor-powertag-monoconnect-63a-3p+n-bottom-position/)
* [A9MEM1543: PowerTag Monoconnect 230V LL 63A 3P top and bottom position](https://www.se.com/ww/en/product/A9MEM1543/energy-sensor-powertag-monoconnect-230v-ll-63a-3p-top-and-bottom-position/)
* [A9MEM1560: PowerTag Flex 230V 63A 1P+N top and bottom position](https://www.se.com/ww/en/product/A9MEM1560/energy-sensor-powertag-flex-230v-63a-1p+n-top-and-bottom-position/)
* [A9MEM1561: PowerTag phaseNeutral 63A 1P+N top position](https://www.se.com/ww/en/product/A9MEM1561/energy-sensor-powertag-phaseneutral-63a-1p+n-top-position/)
* [A9MEM1562: PowerTag phaseNeutral 63A 1P+N bottom position](https://www.se.com/ww/en/product/A9MEM1562/energy-sensor-powertag-phaseneutral-63a-1p+n-bottom-position/)
* [A9MEM1563: PowerTag PhaseNeutral 63A 1P+N bottom position for RCBO 18mm Slim](https://www.se.com/ww/en/product/A9MEM1563/energy-sensor-powertag-phaseneutral-63a-1p+n-bottom-position-for-rcbo-18mm-slim/)
* [A9MEM1564: PowerTag Flex 110V 63A 1P+N top and bottom position](https://www.se.com/ww/en/product/A9MEM1564/energy-sensor-powertag-flex-110v-63a-1p+n-top-and-bottom-position/)
* [A9MEM1570: PowerTag Flex 63A 3P+N top and bottom position](https://www.se.com/ww/en/product/A9MEM1570/energy-sensor-powertag-flex-63a-3p+n-top-and-bottom-position/)
* [A9MEM1571: PowerTag phaseNeutral 63A 3P+N top position](https://www.se.com/ww/en/product/A9MEM1571/energy-sensor-powertag-phaseneutral-63a-3p+n-top-position/)
* [A9MEM1572: PowerTag phaseNeutral 63A 3P+N bottom position](https://www.se.com/ww/en/product/A9MEM1572/energy-sensor-powertag-phaseneutral-63a-3p+n-bottom-position/)
* [A9MEM1573: PowerTag Flex 63A 3P top and bottom position](https://www.se.com/ww/en/product/A9MEM1573/energy-sensor-powertag-flex-63a-3p-top-and-bottom-position/)
* [A9MEM1574: PowerTag Flex 127/220V 63A 3P+N top and bottom position](https://www.se.com/ww/en/product/A9MEM1574/energy-sensor-powertag-flex-127-220v-63a-3p+n-top-and-bottom-position/)

> **Warning**
>
> Any PowerTags, HeatTags or control modules not mentioned here, although compatible with the gateway, are not supported by this integration.
> If integration is needed, please [create an issue](https://github.com/Breina/PowerTagGateway/issues) requesting it as an additional feature.