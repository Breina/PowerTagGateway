"""Config flow for PowerTag Link Gateway"""

from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_DEVICE, \
    CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from pymodbus.exceptions import ConnectionException

from . import UniqueIdVersion
from .const import (
    DEFAULT_MODBUS_PORT,
    CONF_MANUAL_INPUT,
    DPWS_MODEL_NAME,
    DPWS_PRESENTATION_URL,
    DPWS_FRIENDLY_NAME,
    DPWS_SERIAL_NUMBER,
    DOMAIN, CONF_TYPE_OF_GATEWAY, CONF_DEVICE_UNIQUE_ID_VERSION
)
from .schneider_modbus import SchneiderModbus, TypeOfGateway, LinkStatus, \
    PanelHealth
from .soap_communication import Soapy, dpws_discovery

_LOGGER = logging.getLogger(__name__)


class DiscoveredDevice:
    def __init__(self, content: str, type_of_gateway: TypeOfGateway) -> None:
        self.model_name = find_tag(DPWS_MODEL_NAME, content)
        self.presentation_url = find_tag(DPWS_PRESENTATION_URL, content)
        self.friendly_name = find_tag(DPWS_FRIENDLY_NAME, content)
        self.serial_number = find_tag(DPWS_SERIAL_NUMBER, content)
        self.host = urlparse(self.presentation_url).hostname
        self.type_of_gateway = type_of_gateway
        self.port = None

    @classmethod
    async def create(cls, content: str, type_of_gateway: TypeOfGateway):
        instance = cls(content, type_of_gateway)
        try:
            await SchneiderModbus.create(instance.host, instance.type_of_gateway, DEFAULT_MODBUS_PORT, timeout=1)
            instance.port = DEFAULT_MODBUS_PORT
        except ConnectionException:
            instance.port = None
        return instance


def find_tag(tag, source):
    return next(re.finditer(f"<.*:{tag}.*>(.*)</.*:{tag}>", source)).group(1)


async def async_discovery(hass: HomeAssistant) -> list[DiscoveredDevice]:
    """Return if there are devices that can be discovered."""
    services = await dpws_discovery(hass)

    _LOGGER.info(f"Found {len(services)} candidates...")
    for s in services:
        _LOGGER.info(s.getTypes())

    discovered_devices = []

    for service in services:
        soapy = Soapy(service, hass)
        type_of_gateway = TypeOfGateway.PANEL_SERVER if soapy.is_panel_server() else TypeOfGateway.POWERTAG_LINK
        result = await soapy.transfer_get()
        if result.status_code != 200:
            continue

        discovered_devices.append(DiscoveredDevice(result.text, type_of_gateway))

    if discovered_devices:
        _LOGGER.info(f"Found {[s.friendly_name for s in discovered_devices]}")
    else:
        _LOGGER.info(f"Didn't find anything. Discovery might be turned off or the server isn't reachable.")

    return discovered_devices


class PowerTagFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """PowerTag config flow."""

    VERSION = 1

    def __init__(self):
        """Initialize the ONVIF config flow."""
        self.device_id = None
        self.devices = []
        self.host = None
        self.port = DEFAULT_MODBUS_PORT
        self.client = None
        self.serial_number = None
        self.model_name = None
        self.presentation_url = None
        self.name = None
        self.type_of_gateway = TypeOfGateway.POWERTAG_LINK.value

        self.skip_degradation_warning = False
        self.status = None
        self.errors = {}

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle user flow."""
        return self.async_show_menu(
            step_id="user",
            menu_options={
                "discover": "Perform automatic DPWS discovery",
                "configure": "Manually configure",
            }
        )

    async def async_step_discover(self, user_input=None) -> FlowResult:
        """Handle WS-Discovery.

        Let user choose between discovered devices and manual configuration.
        If no device is found allow user to manually input configuration.
        """
        if user_input:
            if CONF_MANUAL_INPUT == user_input[CONF_DEVICE]:
                return await self.async_step_connect()

            for device in self.devices:
                name = f"{device.friendly_name}: {device.model_name} ({device.host})"
                if name == user_input[CONF_DEVICE]:
                    self.name = device.friendly_name
                    self.serial_number = await device.serial_number
                    self.host = device.host
                    self.port = device.port
                    self.type_of_gateway = device.type_of_gateway.value
                    self.model_name = device.model_name
                    self.presentation_url = device.presentation_url
                    return await self.async_step_connect()

        discovered_devices = await async_discovery(self.hass)
        for device in discovered_devices:
            if not any(
                    device.serial_number == entry.unique_id
                    for entry in self._async_current_entries()
            ):
                self.devices.append(device)

        if self.devices:
            names = [
                f"{device.friendly_name}: {device.model_name} ({device.host})" for device in self.devices
            ]

            names.append(CONF_MANUAL_INPUT)

            return self.async_show_form(
                step_id="discover",
                data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(names)}),
            )

        self.errors["base"] = "discovery"
        return await self.async_step_configure()

    async def async_step_configure(self, user_input=None) -> FlowResult:
        """Device configuration."""

        if user_input:
            self.errors = {}
            self.host = user_input[CONF_HOST]
            self.port = user_input[CONF_PORT]
            self.type_of_gateway = user_input[CONF_TYPE_OF_GATEWAY]
            try:
                return await self.async_step_connect()
            except Exception as e:
                logging.exception(e)
                self.errors["base"] = "connection_error"

        return self.async_show_form(
            step_id="configure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self.host): str,
                    vol.Required(CONF_PORT, default=self.port): cv.port,
                    vol.Required(CONF_TYPE_OF_GATEWAY, default=self.type_of_gateway):
                        vol.In([
                            TypeOfGateway.POWERTAG_LINK.value,
                            TypeOfGateway.SMARTLINK.value,
                            TypeOfGateway.PANEL_SERVER.value,
                        ])
                }
            ),
            errors=self.errors,
            last_step=True
        )

    async def async_step_degraded(self, _=None) -> FlowResult:
        return self.async_show_menu(
            step_id="degraded",
            menu_options={
                "continue": "Continue",
                "abort": "Abort",
            },
            description_placeholders={"status": self.status.name}
        )

    async def async_step_abort(self, _=None) -> FlowResult:
        return self.async_abort(reason="user_cancelled")

    async def async_step_continue(self, user_input=None) -> FlowResult:
        self.skip_degradation_warning = True
        return await self.async_step_connect(user_input)

    async def async_step_connect(self, user_input=None) -> FlowResult:
        """Connect to the PowerTag Link Gateway device."""
        type_of_gateway = [t for t in TypeOfGateway if t.value == self.type_of_gateway][0]

        logging.info("Setting up modbus client...")
        self.client = await SchneiderModbus.create(self.host, type_of_gateway, self.port)

        logging.info("Checking status...")
        if (((type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.SMARTLINK]) and self.client.status() != LinkStatus.OPERATING)
                or (type_of_gateway is TypeOfGateway.PANEL_SERVER and self.client.health() != PanelHealth.NOMINAL)):
            if not self.skip_degradation_warning:
                self.status = await self.client.status() if type_of_gateway is TypeOfGateway.POWERTAG_LINK else self.client.health()
                return await self.async_step_degraded()

        logging.info("Retrieving serial number...")
        if not self.serial_number:
            self.serial_number = await self.client.serial_number()

        logging.info("Retrieving model name...")
        if not self.model_name:
            self.model_name = await self.client.product_model()

        logging.info("Retrieving device name...")
        if not self.name:
            self.name = await self.client.name()

        logging.info("Got everything, continuing creation process...")
        if self.serial_number is not None:
            unique_id = self.construct_unique_id(self.model_name, self.serial_number)
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
        else:
            _LOGGER.error(
                "Could not get serial number of ip %s, unique_id's will not be available",
                self.host,
            )
            self._async_abort_entries_match({CONF_HOST: self.host, CONF_PORT: self.port})

        return self.async_create_entry(
            title=self.name,
            data={
                CONF_HOST: self.host,
                CONF_PORT: self.port,
                CONF_INTERNAL_URL: self.presentation_url,
                CONF_TYPE_OF_GATEWAY: self.type_of_gateway,
                CONF_DEVICE_UNIQUE_ID_VERSION: UniqueIdVersion.V2.value
            },
        )

    @staticmethod
    def construct_unique_id(model_name: str, serial_number: str) -> str:
        """Construct the unique id from the dpws discovery or user_step."""
        return f"{model_name}-{serial_number}"
