import uuid

import requests
from homeassistant.core import HomeAssistant
from requests import Response
from wsdiscovery.service import Service

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

    async def transfer_get(self) -> Response:
        return await self.hass.async_add_executor_job(self.fetch_device)

    def fetch_device(self):
        return requests.post(self.address, data=self.get_device)
