"""Support for AlarmDecoder zone bypass switches and panel chime."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import AlarmDecoderConfigEntry
from .const import (
    OPTIONS_ARM,
    OPTIONS_ZONES,
    CONF_BYPASSABLE,
    CONF_ZONE_NAME,
    CONF_ZONE_TYPE,
    DEFAULT_ZONE_OPTIONS,
    SIGNAL_PANEL_MESSAGE,
)
from .entity import AlarmDecoderEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlarmDecoderConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AlarmDecoder zone switches and panel chime."""
    controller = entry.runtime_data.client
    zones = entry.options.get(OPTIONS_ZONES, DEFAULT_ZONE_OPTIONS)  # Igual que binary_sensor
    arm_options = entry.options.get(OPTIONS_ARM, {})
    alarm_code = arm_options.get("alarm_code", "")
    
    switches = []

    chime_switch = AlarmDecoderChimeSwitch(
        controller,
        entry.entry_id,
        alarm_code
    )
    switches.append(chime_switch)

    for zone_num in zones:
        zone_info = zones[zone_num]
        if zone_info.get(CONF_BYPASSABLE, False):
            switches.append(
                AlarmDecoderZoneSwitch(
                    controller,
                    int(zone_num),
                    zone_info,
                    entry.entry_id,
                )
            )

    if switches:
        async_add_entities(switches)


class AlarmDecoderZoneSwitch(AlarmDecoderEntity, SwitchEntity, RestoreEntity):
    """Representation of an AlarmDecoder zone switch for bypass control."""

    def __init__(
        self,
        controller,
        zone_number: int,
        zone_config: dict[str, Any],
        entry_id: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(controller)
        
        self._entry_id = entry_id
        self._zone_number = zone_number
        self._zone_config = zone_config
        
        # Usar números sin ceros delante para unique_id y nombre
        self._attr_unique_id = f"{entry_id}_{zone_number}_bypass"
        self._attr_icon = "mdi:shield-check"
        self._is_bypassed = False
        
        # Configurar nombre personalizado si existe, sino usar número de zona
        if zone_name := zone_config.get(CONF_ZONE_NAME):
            self._attr_name = f"{zone_name} Bypass"
        else:
            self._attr_name = f"Zone {zone_number} Bypass"
        
        # Definir translation_key para usar las traducciones
        self._attr_translation_key = "zone_bypass"
        self._attr_translation_placeholders = {"zone_number": str(zone_number)}
    
    @property
    def is_on(self) -> bool | None:
        """Return true if zone is marked for bypass."""
        return self._is_bypassed
    
    @property
    def zone_number(self) -> int:
        """Return the zone number."""
        return self._zone_number
    
    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        attrs = super().extra_state_attributes
        if attrs is None:
            attrs = {}
        else:
            attrs = dict(attrs)  # Crear una copia para evitar mutaciones
        
        attrs.update({
            "zone_number": self._zone_number,
            "zone_type": self._zone_config.get(CONF_ZONE_TYPE, "door_window"),
            "zone_name": self._zone_config.get(CONF_ZONE_NAME, f"Zone {self._zone_number}"),
            "marked_for_bypass": self._is_bypassed,
        })
        return attrs

    async def async_added_to_hass(self) -> None:
        """Restore bypass state on startup."""
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._is_bypassed = last_state.state == "on"
            self._attr_icon = "mdi:shield-off" if self._is_bypassed else "mdi:shield-check"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mark zone for bypass on next arming."""
        self._is_bypassed = True
        self._attr_icon = "mdi:shield-off"
        self.async_write_ha_state()
        _LOGGER.debug("Zone %s marked for bypass", self._zone_number)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unmark zone for bypass."""
        self._is_bypassed = False
        self._attr_icon = "mdi:shield-check"
        self.async_write_ha_state()
        _LOGGER.debug("Zone %s unmarked for bypass", self._zone_number)


class AlarmDecoderChimeSwitch(AlarmDecoderEntity, SwitchEntity):
    """Representation of an AlarmDecoder panel chime switch."""

    def __init__(
        self,
        controller,
        entry_id: str,
        code: str,
    ) -> None:
        """Initialize the chime switch."""
        super().__init__(controller)
        
        self._entry_id = entry_id
        self._code = code
        self._attr_unique_id = f"{entry_id}-panel-chime"
        self._attr_name = "Panel Chime"
        self._attr_icon = "mdi:bell-off"
        self._attr_translation_key = "panel_chime"
        self._is_on = False

    async def async_added_to_hass(self) -> None:
        """Register callback for panel messages."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_PANEL_MESSAGE, self._message_callback
            )
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if chime is enabled."""
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        attrs = super().extra_state_attributes
        if attrs is None:
            attrs = {}
        else:
            attrs = dict(attrs)
        
        attrs.update({
            "chime_enabled": self._is_on,
        })
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on chime (enable chime)."""
        if self._client:
            _LOGGER.debug("Turning on chime via alarm_toggle_chime service")
            # Use alarm_toggle_chime service with user code + "9"
            self._client.send(f"{self._code}9")
            self._is_on = True
            self._attr_icon = "mdi:bell-ring"
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off chime (disable chime)."""
        if self._client:
            _LOGGER.debug("Turning off chime via alarm_toggle_chime service")
            # Use alarm_toggle_chime service with user code + "9"
            self._client.send(f"{self._code}9")
            self._is_on = False
            self._attr_icon = "mdi:bell-off"
            self.async_write_ha_state()

    def _message_callback(self, message) -> None:
        """Handle incoming AlarmDecoder messages to update chime status."""
        if not hasattr(message, "raw") or not message.raw or message.raw[0] != "[":
            return

        new_state = getattr(message, "chime_on", None)
        if new_state is None:
            return

        if new_state != self._is_on:
            _LOGGER.debug("Chime state changed from message: %s", new_state)
            self._is_on = new_state
            self._attr_icon = "mdi:bell-ring" if new_state else "mdi:bell-off"
            if self.hass and self.hass.loop.is_running():
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)