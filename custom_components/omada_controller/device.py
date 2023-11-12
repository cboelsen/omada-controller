"""Network client device class."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.util import slugify

from .const import ATTR_DEVICE_TRACKER


class Device:
    """Represents a network device."""

    def __init__(self, mac: str, params: dict[str, Any]) -> None:
        """Initialize the network device."""
        self._mac = mac
        self._params = params
        self._attrs: dict[str, Any] = {}
        self.connected: bool = True
        self._set_last_seen(params)

    def _set_last_seen(self, params: dict[str, Any]) -> None:
        timestamp: int | None = params.get("lastSeen")
        if timestamp:
            self._last_seen = datetime.utcfromtimestamp(timestamp / 1000.0)

    @property
    def name(self) -> str:
        """Return device name."""
        return str(self._params.get("name", self.mac))

    @property
    def ip_address(self) -> str | None:
        """Return device primary ip address."""
        return self._params.get("ip")

    @property
    def mac(self) -> str:
        """Return device mac."""
        return self._mac

    @property
    def last_seen(self) -> datetime | None:
        """Return device last seen."""
        return self._last_seen

    @property
    def attrs(self) -> dict[str, Any]:
        """Return device attributes."""
        for attr in ATTR_DEVICE_TRACKER:
            if attr in self._params:
                self._attrs[slugify(attr)] = self._params[attr]
        return self._attrs

    def update(self, params: dict[str, Any]) -> None:
        """Update Device params."""
        self._params = params
        self._set_last_seen(params)
        self.connected = True
