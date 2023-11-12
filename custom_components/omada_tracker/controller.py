import logging
import requests

from datetime import timedelta
from typing import Any
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_DETECTION_TIME, DEFAULT_DETECTION_TIME, DOMAIN, NAME
from .device import Device
from .errors import CannotConnect, LoginError

_LOGGER = logging.getLogger(__name__)


class OmadaController:
    """Wrapper around the API on TP-Link's Omada Controller."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry
        self.url: str = self.config_entry.data[CONF_URL]
        self.token: str | None = None
        self.site_id: str | None = None
        self.headers: dict[str, str] = {"Content-Type": "application/json"}
        self.session: requests.Session = requests.Session()
        self.session.verify = self.config_entry.data[CONF_VERIFY_SSL]
        self.sites: dict[str, str] = {}
        self.controller_id: str = ""

    def get_info(self) -> dict[str, Any]:
        """Get controller info."""
        try:
            return self.session.get(f"{self.url}/api/info").json()["result"]
        except Exception as error:
            _LOGGER.error("Omada Controller %s error: %s", self.url, error)
            raise CannotConnect from error

    def login(self) -> None:
        """Log into the API annd collecto the authentication token."""
        url = f"{self.url}/api/v2/login"
        username: str = self.config_entry.data[CONF_USERNAME]
        password: str = self.config_entry.data[CONF_PASSWORD]
        data: dict[str, str] = {"username": username, "password": password}
        try:
            response = self.session.post(url, json=data, headers=self.headers).json()
        except Exception as error:
            _LOGGER.error("Omada Controller %s error: %s", self.url, error)
            raise CannotConnect from error
        error_code: int = response["errorCode"]
        if error_code != 0:
            _LOGGER.error("Omada Controller %s login error - errorCode: %s", self.url, error_code)
            raise LoginError
        self.token = response["result"]["token"]
        self.headers["Csrf-Token"] = self.token

        url = f"{self.url}/{self.controller_id}/api/v2/loginStatus?token={self.token}"
        try:
            self.session.get(url, headers=self.headers).json()
        except requests.exceptions.JSONDecodeError as error:
            _LOGGER.error("Omada Controller %s login error", self.url)
            raise LoginError from error

        url = (
            f"{self.url}/{self.controller_id}/api/v2/users/current"
            "?token={self.token}&currentPage=1&currentPageSize=1000"
        )
        try:
            user_response = self.session.get(url, headers=self.headers).json()
        except Exception as error:
            _LOGGER.error("Omada Controller %s error: %s", self.url, error)
            raise CannotConnect from error
        self.sites = {s["name"]: s["key"] for s in user_response["result"]["privilege"]["sites"]}

    def get_clients_at_site(self, site_name) -> list[dict[str, str]]:
        """Return the list of clients at the givven site."""
        site_id = self.sites[site_name]
        url = (
            f"{self.url}/{self.controller_id}/api/v2/sites/{site_id}/clients"
            "?token={self.token}&currentPage=1&currentPageSize=1000&filters.active=true"
        )
        try:
            return self.session.get(url, headers=self.headers).json()["result"]["data"]
        except Exception as error:
            _LOGGER.error("Omada Controller %s error: %s", self.url, error)
            raise CannotConnect from error

    def get_all_clients(self) -> list[dict[str, str]]:
        """Return a list of all clients on this controller."""
        clients = []
        for site in self.sites:
            clients += self.get_clients_at_site(site)
        return clients


class OmadaControllerData:
    """Tracks the devices attached to the sites managed by the Omada Controller."""

    def __init__(self, api: OmadaController) -> None:
        self.api = api
        self.devices: dict[str, Device] = {}
        self.hostname: str = urlparse(api.url).netloc
        self.model: str = ""
        self.firmware: str = ""
        self.serial_number: str = ""

    def get_controller_details(self) -> None:
        """Get what little details can be retrieved about the controller."""
        info = self.api.get_info()
        self.api.controller_id = info["omadacId"]
        self.model: str = info["type"]
        self.firmware: str = info["controllerVer"]
        self.serial_number: str = self.api.controller_id

    def update_devices(self):
        """Update the state for the devices tracked here."""
        try:
            clients = self.api.get_all_clients()
        except CannotConnect as err:
            raise UpdateFailed from err
        except LoginError as err:
            raise ConfigEntryAuthFailed from err

        for device in self.devices.values():
            device.connected = False

        for client in clients:
            mac = client["mac"]
            if mac in self.devices:
                self.devices[mac].update(client)
            else:
                self.devices[mac] = Device(mac, client)


class OmadaControllerDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Omada Controller Hub Object."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: OmadaController,
    ) -> None:
        """Initialize the Omada Controller Client."""
        self.hass = hass
        self.config_entry: ConfigEntry = config_entry
        self._oc_data = OmadaControllerData(api)
        conf_name = self.config_entry.data[NAME]
        super().__init__(
            self.hass,
            _LOGGER,
            name=f"{DOMAIN} - {conf_name}",
            update_interval=timedelta(seconds=10),
        )

    @property
    def host(self) -> str:
        """Return the host of this hub."""
        return self.hostname

    @property
    def hostname(self) -> str:
        """Return the hostname of the hub."""
        return self._oc_data.hostname

    @property
    def model(self) -> str:
        """Return the model of the hub."""
        return self._oc_data.model

    @property
    def firmware(self) -> str:
        """Return the firmware of the hub."""
        return self._oc_data.firmware

    @property
    def serial_num(self) -> str:
        """Return the serial number of the hub."""
        return self._oc_data.serial_number

    @property
    def option_detection_time(self) -> timedelta:
        """Config entry option defining number of seconds from last seen to away."""
        return timedelta(
            seconds=self.config_entry.options.get(
                CONF_DETECTION_TIME, DEFAULT_DETECTION_TIME
            )
        )

    @property
    def api(self) -> OmadaControllerData:
        """Represent Omada Controller data object."""
        return self._oc_data

    async def update_method(self) -> None:
        """Update devices information."""
        await self.hass.async_add_executor_job(self._oc_data.update_devices)
