from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from .const import DOMAIN
import uuid
import logging
from .config_schema import PERIODS_SCHEMA, USER_SCHEMA
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register("baxi_power-meter")
class BaxiPowerMeterFlowHandler(config_entries.ConfigFlow, domain="baxi_power-meter"):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self._data = {}
        self._config_complete = False
        self._unique_id = str(uuid.uuid4())

    async def async_step_import(self, data=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="configuration.yaml", data={})

    async def async_step_user(self, user_input=None):
        self._errors = {}

        _LOGGER.debug("user_input= %s", user_input)
        if user_input:
            self._data.update(user_input)
            return await self._show_config_form_periods()

        return await self._show_config_form_user()

    async def _show_config_form_user(self):
        """Show form for config flow"""
        _LOGGER.info("Show user form")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(USER_SCHEMA),
            errors=self._errors,
        )

    async def async_step_periods(self, user_input=None):
        self._data.update(user_input)
        return self.async_create_entry(title=user_input.get(CONF_NAME), data=self._data)

    async def _show_config_form_periods(self):
        """Show form for config flow"""
        _LOGGER.info("Show periods form")
        self._config_complete = True
        return self.async_show_form(
            step_id="periods",
            data_schema=vol.Schema(PERIODS_SCHEMA),
            errors=self._errors,
        )
