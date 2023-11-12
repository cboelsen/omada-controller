"""Support for Omada Controllers as device tracker."""
from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import (
    DOMAIN as DEVICE_TRACKER,
    ScannerEntity,
    SourceType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import homeassistant.util.dt as dt_util

from .const import DOMAIN
from .controller import Device, OmadaControllerDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker for Omada Controller component."""
    coordinator: OmadaControllerDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    tracked: dict[str, OmadaControllerEntity] = {}

    # registry = er.async_get(hass)

    # # Restore clients that is not a part of active clients list.
    # for entity in registry.entities.values():
    #     if (
    #         entity.config_entry_id == config_entry.entry_id
    #         and entity.domain == DEVICE_TRACKER
    #     ):
    #         if entity.unique_id in coordinator.api.devices:
    #             continue
    #         coordinator.api.restore_device(entity.unique_id)

    @callback
    def update_hub() -> None:
        """Update the status of the device."""
        update_items(coordinator, async_add_entities, tracked)

    config_entry.async_on_unload(coordinator.async_add_listener(update_hub))

    update_hub()


@callback
def update_items(
    coordinator: OmadaControllerDataUpdateCoordinator,
    async_add_entities: AddEntitiesCallback,
    tracked: dict[str, OmadaControllerEntity],
) -> None:
    """Update tracked device state from the hub."""
    new_tracked: list[OmadaControllerEntity] = []
    for mac, device in coordinator.api.devices.items():
        if mac not in tracked:
            tracked[mac] = OmadaControllerEntity(device, coordinator)
            new_tracked.append(tracked[mac])

    async_add_entities(new_tracked)


class OmadaControllerEntity(
    CoordinatorEntity[OmadaControllerDataUpdateCoordinator], ScannerEntity
):
    """Representation of network device."""

    def __init__(
        self, device: Device, coordinator: OmadaControllerDataUpdateCoordinator
    ) -> None:
        """Initialize the tracked device."""
        super().__init__(coordinator)
        self.device = device
        self._attr_name = device.name
        self._attr_unique_id = device.mac

    @property
    def is_connected(self) -> bool:
        """Return true if the client is connected to the network."""
        return self.device.connected

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the client."""
        return SourceType.ROUTER

    @property
    def hostname(self) -> str:
        """Return the hostname of the client."""
        return self.device.name

    @property
    def mac_address(self) -> str:
        """Return the mac address of the client."""
        return self.device.mac

    @property
    def ip_address(self) -> str | None:
        """Return the mac address of the client."""
        return self.device.ip_address

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device state attributes."""
        return self.device.attrs