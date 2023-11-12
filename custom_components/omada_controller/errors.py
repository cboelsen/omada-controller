"""Errors for the Omada Controller component."""
from homeassistant.exceptions import HomeAssistantError


class CannotConnect(HomeAssistantError):
    """Unable to connect to the controller."""


class LoginError(HomeAssistantError):
    """Component got logged out."""
