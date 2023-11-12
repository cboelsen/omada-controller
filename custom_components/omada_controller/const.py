"""Constants used in the Mikrotik components."""
from datetime import timedelta
from typing import Final

DOMAIN: Final = "omada_controller"
DEFAULT_NAME: Final = "Omada Controller"
DEFAULT_DETECTION_TIME: Final = 300

ATTR_MANUFACTURER: Final = "TP-Link"
ATTR_VERSION: Final = "current-version"

SCAN_INTERVAL = timedelta(seconds=30)

CONF_DETECTION_TIME: Final = "detection_time"

###########################################
# From mikrotik module

NAME: Final = "name"
INFO: Final = "info"
IDENTITY: Final = "identity"
ARP: Final = "arp"

CAPSMAN: Final = "capsman"
DHCP: Final = "dhcp"
WIRELESS: Final = "wireless"
WIFIWAVE2: Final = "wifiwave2"
IS_WIRELESS: Final = "is_wireless"
IS_CAPSMAN: Final = "is_capsman"
IS_WIFIWAVE2: Final = "is_wifiwave2"


MIKROTIK_SERVICES: Final = {
    ARP: "/ip/arp/getall",
    CAPSMAN: "/caps-man/registration-table/getall",
    DHCP: "/ip/dhcp-server/lease/getall",
    IDENTITY: "/system/identity/getall",
    INFO: "/system/routerboard/getall",
    WIRELESS: "/interface/wireless/registration-table/getall",
    WIFIWAVE2: "/interface/wifiwave2/registration-table/print",
    IS_WIRELESS: "/interface/wireless/print",
    IS_CAPSMAN: "/caps-man/interface/print",
    IS_WIFIWAVE2: "/interface/wifiwave2/print",
}


ATTR_DEVICE_TRACKER: Final = [
    "apName",
    "ip",
    "name",
    "signalLevel",
    "snr",
    "ssid",
    "rxRate",
    "txRate",
    "uptime",
]
