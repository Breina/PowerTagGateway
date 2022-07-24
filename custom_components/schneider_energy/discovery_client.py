# from PyWSD import wsd_discovery__structures, wsd_discovery__operations
#
# devices = wsd_discovery__operations.get_devices(cache=False, probe_timeout=3)
# for device in devices:
#     print(device)
#
# devices = wsd_discovery__operations.wsd_probe(probe_timeout=3)
# for device in devices:
#     print(device)
import uuid
from urllib.parse import urlparse

import requests
from wsdiscovery import QName, Scope
from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery

# Define type, scope & address of service

# Discover it (along with any other service out there)
wsd = WSDiscovery()
wsd.start()
services = wsd.searchServices(types=[QName("http://www.schneider-electric.com", "GatewayServer")])
wsd.stop()
for service in services:
    address = service.getXAddrs()[0]
    url = urlparse(address)

    messageId = uuid.uuid4()
    ourId = uuid.uuid4()
    with open("../templates/transfer_get.xml") as transfer_get:
        get_device = transfer_get.read()\
            .replace("{{To}}", service.getEPR()) \
            .replace("{{MessageID}}", str(messageId)) \
            .replace("{{OurID}}", str(ourId))

    result = requests.post(address, data=get_device)
    if result.status_code != 200:
        continue

