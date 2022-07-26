"""Config flow for PowerTag Link Gateway"""

from __future__ import annotations

import logging
import re
import uuid
from urllib.parse import urlparse

import requests
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_DEVICE, CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from pymodbus.exceptions import ConnectionException
from wsdiscovery import QName
from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
from wsdiscovery.service import Service

from .const import (
    DEFAULT_MODBUS_PORT,
    SCHNEIDER_QNAME,
    SCHNEIDER_QNAME_GATEWAY,
    CONF_MANUAL_INPUT,
    DPWS_MODEL_NAME,
    DPWS_PRESENTATION_URL,
    DPWS_FRIENDLY_NAME,
    DPWS_SERIAL_NUMBER,
    CONF_CLIENT,
    DOMAIN
)
from .schneider_modbus import SchneiderModbus

_LOGGER = logging.getLogger(__name__)


class DiscoveredDevice:
    def __init__(self, content: str) -> None:
        self.model_name = find_tag(DPWS_MODEL_NAME, content)
        self.presentation_url = find_tag(DPWS_PRESENTATION_URL, content)
        self.friendly_name = find_tag(DPWS_FRIENDLY_NAME, content)
        self.serial_number = find_tag(DPWS_SERIAL_NUMBER, content)

        self.host = urlparse(self.presentation_url).hostname

        try:
            SchneiderModbus(self.host, DEFAULT_MODBUS_PORT, timeout=1).name()
            self.port = DEFAULT_MODBUS_PORT
        except ConnectionException:
            self.port = None


def find_tag(tag, source):
    return next(re.finditer(f"<.*:{tag}>(.*)</.*:{tag}>", source)).group(1)


def dpws_discovery() -> list[Service]:
    """Search a Link Gateway from the network"""
    _LOGGER.info("Attempting to discover EnergyTag Gateway")

    wsd = WSDiscovery()
    wsd.start()
    services = wsd.searchServices(types=[QName(SCHNEIDER_QNAME, SCHNEIDER_QNAME_GATEWAY)])
    wsd.stop()
    return services


async def async_discovery(hass: HomeAssistant) -> list[DiscoveredDevice]:
    """Return if there are devices that can be discovered."""
    services = await hass.async_add_executor_job(dpws_discovery)

    _LOGGER.info(f"Found {len(services)} candidates...")

    discovered_devices = []

    for service in services:
        address = service.getXAddrs()[0]

        message_id = uuid.uuid4()
        our_id = uuid.uuid4()
        with open("../templates/transfer_get.xml") as transfer_get:
            get_device = transfer_get.read() \
                .replace("{{To}}", service.getEPR()) \
                .replace("{{MessageID}}", str(message_id)) \
                .replace("{{OurID}}", str(our_id))

        result = requests.post(address, data=get_device)
        if result.status_code != 200:
            continue

        discovered_devices.append(DiscoveredDevice(result.text))

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

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle user flow."""
        if user_input:
            if user_input["auto"]:
                return await self.async_step_device()
            return await self.async_step_configure()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("auto", default=True): bool}),
        )

    async def async_step_device(self, user_input=None) -> FlowResult:
        """Handle WS-Discovery.

        Let user choose between discovered devices and manual configuration.
        If no device is found allow user to manually input configuration.
        """
        if user_input:
            if CONF_MANUAL_INPUT == user_input[CONF_DEVICE]:
                return await self.async_step_configure()

            for device in self.devices:
                name = f"{device.friendly_name}: {device.model_name} ({device.host})"
                if name == user_input[CONF_DEVICE]:
                    self.name = device.friendly_name
                    self.serial_number = device.serial_number
                    self.host = device.host
                    self.port = device.port
                    self.model_name = device.model_name
                    self.presentation_url = device.presentation_url
                    return await self.async_step_configure()

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
                step_id="device",
                data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(names)}),
            )

        return await self.async_step_configure()

    async def async_step_configure(self, user_input=None) -> FlowResult:
        """Device configuration."""
        errors = {}
        if user_input:
            self.host = user_input[CONF_HOST]
            self.port = user_input[CONF_PORT]
            try:
                return await self.async_step_connect()
            except ConnectionException:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="configure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self.host): str,
                    vol.Required(CONF_PORT, default=self.port): int,
                }
            ),
            errors=errors,
        )

    async def async_step_connect(self) -> FlowResult:
        """Connect to the PowerTag Link Gateway device."""

        try:
            if self.client is None:
                self.client = SchneiderModbus(self.host, self.port)
        except ConnectionException as e:
            _LOGGER.exception(e)
            return self.async_abort(reason="cannot_connect")

        if not self.serial_number:
            self.serial_number = self.client.serial_number()
        if not self.model_name:
            self.model_name = self.client.product_model()
        if not self.name:
            self.name = self.client.name()

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
                CONF_CLIENT: self.client,
                CONF_INTERNAL_URL: self.presentation_url,
            },
        )

    @staticmethod
    def construct_unique_id(model_name: str, serial_number: str) -> str:
        """Construct the unique id from the dpws discovery or user_step."""
        return f"{model_name}-{serial_number}"
