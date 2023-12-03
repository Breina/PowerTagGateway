import logging
import uuid

import requests
from homeassistant.core import HomeAssistant
from requests import Response
from wsdiscovery import QName
from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
from wsdiscovery.service import Service

NAMESPACE_SCHNEIDER = "http://www.schneider-electric.com"
NAMESPACE_SCHNEIDER_CYBERSECURITY = "http://www.schneider-electric.com/CyberSecurity"

LOCAL_NAME_GATEWAY_SERVER = "GatewayServer"
LOCAL_NAME_PANEL_SERVER = "EcoStruxurePanelServer"

_LOGGER = logging.getLogger(__name__)

template = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">
    <soap:Header>
        <wsa:To>{{To}}</wsa:To>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2004/09/transfer/Get</wsa:Action>
        <wsa:MessageID>urn:uuid:{{MessageID}}</wsa:MessageID>
        <wsa:ReplyTo>
            <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
        </wsa:ReplyTo>
        <wsa:From>
            <wsa:Address>urn:uuid:{{OurID}}</wsa:Address>
        </wsa:From>
    </soap:Header>
    <soap:Body/>
</soap:Envelope>"""


def dpws_discovery() -> list[Service]:
    """Search a Link Gateway from the network"""
    _LOGGER.info("Attempting to discover EnergyTag Gateway")

    wsd = WSDiscovery()
    wsd.start()
    services = wsd.searchServices(types=[QName(NAMESPACE_SCHNEIDER, LOCAL_NAME_GATEWAY_SERVER)])
    wsd.stop()
    return services


class Soapy:
    def __init__(self, service: Service, hass=HomeAssistant):
        message_id = uuid.uuid4()
        our_id = uuid.uuid4()

        self.get_device = template \
            .replace("{{To}}", service.getEPR()) \
            .replace("{{MessageID}}", str(message_id)) \
            .replace("{{OurID}}", str(our_id))
        self.hass = hass
        self.address = service.getXAddrs()[0]
        self.service = service

    def address(self):
        return self.service.getXAddrs()[0]

    def is_panel_server(self) -> bool:
        schneiderCyberSecurity = [type for type in self.service.getTypes() if
                                  type.getNamespace() == NAMESPACE_SCHNEIDER_CYBERSECURITY]
        if not schneiderCyberSecurity:
            return False

        return schneiderCyberSecurity[0].getLocalname() == LOCAL_NAME_PANEL_SERVER

    async def transfer_get(self) -> Response:
        return await self.hass.async_add_executor_job(self.fetch_device)

    def fetch_device(self):
        return requests.post(self.address, data=self.get_device)
