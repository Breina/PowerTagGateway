# EcoStruxure PowerTag Link Gateway

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

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

![Overview of a PowerTag device](images/Features_PowerTag.png)
![Example of a specific sensor](images/Features_Sensor.png)

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

#### Possible integrations

> **Warning**
>
> The following PowerTags are not yet supported, but are compatible with the Link Gateway.
> If integration is desired, please [create an issue](https://github.com/Breina/PowerTagGateway/issues) requesting it as an additional feature.
> 
> As it is not practical to integrate a device one doesn't have, consider sending the PowerTag to a maintainer of this project.

* A9MEM1580
* A9MEM1590, A9MEM1591, A9MEM1592, A9MEM1593
* LV434020, LV434021, LV434022, LV434023
* A9XMC1D3, A9XMC2D3
* SMT10020
* A9XMWRD


# Installation

## Preparation

It is assumed that you have configured your gateway and all of its powertags.

A hard requirement for this integration to work is the modbus TCP service to be enabled, which it is by default.
To check whether this is the case, open the device's configuration webpage through navigating to its IP address in your web browser.

Navigate to _SETTINGS_ > _IP NETWORK SERVICES_

![The IP services configuration](images/Web_config.png)

Check that the _MODBUS TCP_ service is enabled.
Its port is set to 502 by default, if you diverge from this, **please keep your port number in mind for later**.

To make your life easier later, it's also recommended to enable the _DISCOVERY_ service, its port doesn't matter.

## Installation

### HACS

> **Note**
> 
> This integration requires [HACS](https://github.com/hacs/integration) to be installed

1. Open HACS
2. _+ EXPLORE & DOWNLOAD REPOSITORIES_
3. Find _EcoStruxure PowerTag Link Gateway_ in this list
4. _DOWNLOAD THIS REPOSITORY WITH HACS_
5. _DOWNLOAD_
6. Restart Home Assistant (_Settings_ > _System_ > _RESTART_)

### Integration

 1. Navigate to the integrations page: _Settings_ > _Devices & Services_
 2. _+ ADD INTEGRATION_
 3. Select _PowerTag Link Gateway_ in this selection window
 4. **Search the network?** If the *DISCOVERY* service is enabled, the *Discover automatically* option can be checked. 
    Otherwise, move on to the next step.
    1. If the discovery was successful, the next step will present you with the gateways which were discovered.
       Select one or choose to set the host address manually.
 5. Enter the host address (without `http://`) and the modbus TCP port (default 502) of your gateway.
 6. If successful, you can now select to which areas the new devices belong.
    All entities are now created.

### Adding to the energy dashboard

![Monitor individual devices](images/Features_Energy_panel.png)

 1. Navigate to the energy configuration page: _Settings_ > _Dashboards_ > _Energy_
 2. Depending on where you added your PowerTags, press _ADD DEVICE_ or _ADD_SOLAR_PRODUCTION_.
 3. Select the PowerTag entity you want to add (ends with _'total energy'_)
 4. _SAVE_