import re
from enum import Enum, auto

from homeassistant.exceptions import IntegrationError


class FeatureClass(Enum):
    A1 = auto()
    A2 = auto()
    P1 = auto()
    F1 = auto()
    F2 = auto()
    F3 = auto()
    FL = auto()
    M0 = auto()
    M1 = auto()
    M2 = auto()
    M3 = auto()
    R1 = auto()
    C = auto()
    TEMP0 = auto()
    TEMP1 = auto()
    CO2 = auto()


class UnknownDevice(IntegrationError):
    pass


def from_commercial_reference(commercial_reference: str) -> FeatureClass:
    for regex, result in {
        '^A9MEM1520|A9MEM1521|A9MEM1522|A9MEM1541|A9MEM1542|PLTQO.|PLTE60.$': FeatureClass.A1,
        '^A9MEM1540|A9MEM1543$': FeatureClass.A2,
        '^A9MEM1561|A9MEM1562|A9MEM1563|A9MEM1571|A9MEM1572$': FeatureClass.P1,
        '^A9MEM1560|A9MEM1570$': FeatureClass.F1,
        '^A9MEM1573$': FeatureClass.F2,
        '^A9MEM1564|A9MEM1574$': FeatureClass.F3,
        '^A9MEM1580$': FeatureClass.FL,
        '^LV434020$': FeatureClass.M0,
        '^LV434021$': FeatureClass.M1,
        '^LV434022$': FeatureClass.M2,
        '^LV434023$': FeatureClass.M3,
        '^A9MEM1590|A9MEM1591|A9MEM1592|A9MEM1593|PLTR.$': FeatureClass.R1,
        '^A9TAA....|A9TAB....|A9TDEC...|A9TDFC...|A9TDFD...|A9TPDD...|A9TPED...|A9TYAE...|A9TYBE...$': FeatureClass.C,
        '^EMS59440$': FeatureClass.TEMP0,
        '^SED-TRH-G-5045|ZBRTT1|ESST010B0400|A9XST114|EMS59443$': FeatureClass.TEMP1,
        '^SED-CO2-G-5045$': FeatureClass.CO2
    }.items():
        if re.match(regex, commercial_reference):
            return result

    raise UnknownDevice(f"Unsupported commercial reference: {commercial_reference}")


def from_wireless_device_type_code(code: int) -> FeatureClass:
    try:
        commercial_reference = {
            41: "A9MEM1520",
            42: "A9MEM1521",
            43: "A9MEM1522",
            44: "A9MEM1540",
            45: "A9MEM1541",
            46: "A9MEM1542",
            81: "A9MEM1560",
            82: "A9MEM1561",
            83: "A9MEM1562",
            84: "A9MEM1563",
            85: "A9MEM1570",
            86: "A9MEM1571",
            87: "A9MEM1572",
            92: "LV434020",
            93: "LV434021",
            94: "LV434022",
            95: "LV434023",
            96: "A9MEM1543",
            97: "A9XMC2D3",
            98: "A9XMC1D3",
            101: "A9MEM1564",
            102: "A9MEM1573",
            103: "A9MEM1574",
            104: "A9MEM1590",
            105: "A9MEM1591",
            106: "A9MEM1592",
            107: "A9MEM1593",
            121: "A9MEM1580",
            170: "A9XMWRD",
            171: "SMT10020"
        }[code]
    except KeyError:
        raise UnknownDevice(f"Unknown device code: {code}."
                            f" Please create a GitHub issue mentioning this device's code and commercial reference.")

    return from_commercial_reference(commercial_reference)
