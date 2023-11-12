"""Config flow for Omada Controller."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DETECTION_TIME,
    DEFAULT_DETECTION_TIME,
    DEFAULT_NAME,
    DOMAIN,
)
from .errors import CannotConnect, LoginError
from .controller import OmadaController


class OmadaControllerFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a OmadaController config flow."""

    VERSION = 1
    _reauth_entry: config_entries.ConfigEntry | None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OmadaControllerOptionsFlowHandler:
        """Get the options flow for this handler."""
        return OmadaControllerOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            self._async_abort_entries_match({CONF_URL: user_input[CONF_URL]})

            try:
                api = await self.hass.async_add_executor_job(lambda: OmadaController(user_input))
                await self.hass.async_add_executor_job(api.login)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except LoginError:
                errors[CONF_USERNAME] = "invalid_auth"
                errors[CONF_PASSWORD] = "invalid_auth"

            if not errors:
                return self.async_create_entry(
                    title=f"{DEFAULT_NAME} ({user_input[CONF_URL]})", data=user_input
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_URL): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_VERIFY_SSL, default=False): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, data: Mapping[str, Any]) -> FlowResult:
        """Perform reauth upon an API authentication error."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Confirm reauth dialog."""
        errors = {}
        assert self._reauth_entry
        if user_input is not None:
            user_input = {**self._reauth_entry.data, **user_input}
            try:
                api = await self.hass.async_add_executor_job(lambda: OmadaController(user_input))
                await self.hass.async_add_executor_job(api.login)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except LoginError:
                errors[CONF_PASSWORD] = "invalid_auth"

            if not errors:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data=user_input,
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            description_placeholders={
                CONF_USERNAME: self._reauth_entry.data[CONF_USERNAME]
            },
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )


class OmadaControllerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle OmadaController options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize OmadaController options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the OmadaController options."""
        return await self.async_step_device_tracker()

    async def async_step_device_tracker(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the device tracker options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_DETECTION_TIME,
                default=self.config_entry.options.get(
                    CONF_DETECTION_TIME, DEFAULT_DETECTION_TIME
                ),
            ): int,
        }

        return self.async_show_form(
            step_id="device_tracker", data_schema=vol.Schema(options)
        )
