"""Config flow for AlarmDecoder (YAML only configuration)."""

from __future__ import annotations

import logging
from typing import Any

from adext import AdExt
from alarmdecoder.devices import SerialDevice, SocketDevice
from alarmdecoder.util import NoDeviceError
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PROTOCOL
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICE_BAUD,
    CONF_DEVICE_PATH,
    DEFAULT_DEVICE_BAUD,
    DEFAULT_DEVICE_HOST,
    DEFAULT_DEVICE_PATH,
    DEFAULT_DEVICE_PORT,
    DOMAIN,
    PROTOCOL_SERIAL,
    PROTOCOL_SOCKET,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PROTOCOL, default=PROTOCOL_SOCKET): vol.In(
            [PROTOCOL_SOCKET, PROTOCOL_SERIAL]
        ),
        vol.Optional(CONF_HOST, default=DEFAULT_DEVICE_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_DEVICE_PORT): int,
        vol.Optional(CONF_DEVICE_PATH, default=DEFAULT_DEVICE_PATH): str,
        vol.Optional(CONF_DEVICE_BAUD, default=DEFAULT_DEVICE_BAUD): int,
    }
)


class AlarmDecoderFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AlarmDecoder (basic setup only)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate basic connection
            try:
                await self._test_connection(user_input)
                return self.async_create_entry(title="AlarmDecoder", data=user_input)
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _test_connection(self, config: dict[str, Any]) -> None:
        """Test connection to AlarmDecoder."""
        protocol = config[CONF_PROTOCOL]

        if protocol == PROTOCOL_SOCKET:
            host = config[CONF_HOST]
            port = config[CONF_PORT]
            controller = AdExt(SocketDevice(interface=(host, port)))
        elif protocol == PROTOCOL_SERIAL:
            path = config[CONF_DEVICE_PATH]
            controller = AdExt(SerialDevice(interface=path))
        else:
            raise ValueError("Invalid protocol")

        try:
            # Try to open connection briefly to validate
            baud = config.get(CONF_DEVICE_BAUD)
            await self.hass.async_add_executor_job(controller.open, baud)
            await self.hass.async_add_executor_job(controller.close)
        except NoDeviceError as err:
            raise ConnectionError("Cannot connect to device") from err
