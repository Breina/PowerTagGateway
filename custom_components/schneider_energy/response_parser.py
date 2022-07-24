import re

response = """<?xml version="1.0" encoding="utf-8" ?>
<s12:Envelope xmlns:s12="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">
    <s12:Header>
        <wsa:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:To>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2004/09/transfer/GetResponse</wsa:Action>
        <wsa:RelatesTo>urn:uuid:c798c794-a65b-45b2-b066-448adfafd2ce</wsa:RelatesTo>
    </s12:Header>
    <s12:Body>
        <mex:Metadata xmlns:mex="http://schemas.xmlsoap.org/ws/2004/09/mex">
            <mex:MetadataSection Dialect="http://schemas.xmlsoap.org/ws/2006/02/devprof/ThisModel">
                <dp:ThisModel xmlns:dp="http://schemas.xmlsoap.org/ws/2006/02/devprof">
                    <dp:Manufacturer>Schneider Electric</dp:Manufacturer>
                    <dp:ManufacturerUrl>http://www.schneider-electric.com</dp:ManufacturerUrl>
                    <dp:ModelName>Acti9 PowerTag Link HD</dp:ModelName>
                    <dp:ModelNumber>A9XMWD100</dp:ModelNumber>
                    <dp:ModelUrl>http://www.schneider-electric.com</dp:ModelUrl>
                    <dp:PresentationUrl>http://192.168.1.39/</dp:PresentationUrl>
                </dp:ThisModel>
            </mex:MetadataSection>
            <mex:MetadataSection Dialect="http://schemas.xmlsoap.org/ws/2006/02/devprof/ThisDevice">
                <dp:ThisDevice xmlns:dp="http://schemas.xmlsoap.org/ws/2006/02/devprof">
                    <dp:FriendlyName>Pries</dp:FriendlyName>
                    <dp:FirmwareVersion>002.001.005</dp:FirmwareVersion>
                    <dp:SerialNumber>RN212667091</dp:SerialNumber>
                </dp:ThisDevice>
            </mex:MetadataSection>
        </mex:Metadata>
    </s12:Body>
</s12:Envelope>"""


# manufacturer = re.findall("<.*:Manufacturer>(.*)</.*:Manufacturer>", response)[0]

def find_tag(tag, source):
    return next(re.finditer(f"<.*:{tag}>(.*)</.*:{tag}>", source)).group(1)


manufacturer = find_tag("Manufacturer", response)
manufacturer_url = find_tag("ManufacturerUrl", response)
model_name = find_tag("ModelName", response)
model_number = find_tag("ModelNumber", response)
model_url = find_tag("ModelUrl", response)
presentation_url = find_tag("PresentationUrl", response)
friendly_name = find_tag("FriendlyName", response)
firmware_version = find_tag("FirmwareVersion", response)
serial_number = find_tag("SerialNumber", response)

print(manufacturer)