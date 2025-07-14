"""Support for AlarmDecoder zone bypass switches."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AlarmDecoderConfigEntry
from .const import (
    DOMAIN, 
    OPTIONS_ZONES, 
    CONF_BYPASSABLE,
    CONF_ZONE_NAME,
    CONF_ZONE_TYPE,   
    DEFAULT_ZONE_OPTIONS
)
from .entity import AlarmDecoderEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlarmDecoderConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AlarmDecoder zone switches."""
    controller = entry.runtime_data.client
    zones = entry.options.get(OPTIONS_ZONES, DEFAULT_ZONE_OPTIONS)  # Same as binary_sensor
    
    # Temporary debug
    _LOGGER.error(f"DEBUG SWITCH: Zones data: {zones}")
    
    switches = []
    
    # Use same structure as binary_sensor
    for zone_num in zones:
        zone_info = zones[zone_num]  # Change zone_config to zone_info
        _LOGGER.error(f"DEBUG SWITCH: Zone {zone_num} info: {zone_info}")
        
        # Check if zone is bypassable using constant
        if zone_info.get(CONF_BYPASSABLE, False):
            _LOGGER.error(f"DEBUG SWITCH: Creating switch for zone {zone_num}")
            switch = AlarmDecoderZoneSwitch(
                controller,
                int(zone_num),
                zone_info,  # Pass zone_info instead of zone_config
                entry.entry_id
            )
            switches.append(switch)
        else:
            _LOGGER.error(f"DEBUG SWITCH: Zone {zone_num} not bypassable")
    
    _LOGGER.error(f"DEBUG SWITCH: Total switches created: {len(switches)}")
    
    if switches:
        async_add_entities(switches)
    else:
        _LOGGER.error("DEBUG SWITCH: No switches to add")


class AlarmDecoderZoneSwitch(AlarmDecoderEntity, SwitchEntity):
    """Representation of an AlarmDecoder zone switch for bypass control."""

    def __init__(
        self,
        controller,
        zone_number: int,
        zone_config: dict[str, Any],
        entry_id: str,
    ) -> None:
        """Initialize the switch."""
        # Create sub-device for zone (same as binary_sensor)
        zone_name = zone_config.get(CONF_ZONE_NAME, f"Zone {zone_number}")
        device_name = f"Zone {zone_number} - {zone_name}"
        device_identifier = f"{controller.serial_number}-zone-{zone_number}"
        super().__init__(controller, device_name, device_identifier)
        
        self._entry_id = entry_id
        self._zone_number = zone_number
        self._zone_config = zone_config
        
        # Use numbers without leading zeros for unique_id
        self._attr_unique_id = f"{controller.serial_number}-zone-{zone_number}-bypass"
        self._attr_icon = "mdi:shield-check"
        self._is_bypassed = False
        self._attr_is_on = False  # Initialize switch state
        
        # Simple name since device provides context
        self._attr_name = "Bypass"
        
        # Define translation_key to use translations
        self._attr_translation_key = "zone_bypass"
        self._attr_translation_placeholders = {"zone_number": str(zone_number)}
        
        # Configure additional attributes
        self._attr_extra_state_attributes = {
            "zone_number": self._zone_number,
            "zone_type": zone_config.get(CONF_ZONE_TYPE, "door_window"),
            "zone_name": zone_config.get(CONF_ZONE_NAME, f"Zone {zone_number}"),
            "marked_for_bypass": False,
        }

    @property
    def zone_number(self) -> int:
        """Return the zone number."""
        return self._zone_number
    
    def _update_bypass_state(self) -> None:
        """Update the bypass state and related attributes."""
        self._attr_is_on = self._is_bypassed
        if self._attr_extra_state_attributes:
            self._attr_extra_state_attributes["marked_for_bypass"] = self._is_bypassed

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mark zone for bypass on next arming."""
        self._is_bypassed = True
        self._attr_icon = "mdi:shield-off"
        self._update_bypass_state()
        self.async_write_ha_state()
        _LOGGER.debug("Zone %s marked for bypass", self._zone_number)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unmark zone for bypass."""
        self._is_bypassed = False
        self._attr_icon = "mdi:shield-check"
        self._update_bypass_state()
        self.async_write_ha_state()
        _LOGGER.debug("Zone %s unmarked for bypass", self._zone_number)
    
    def reset_bypass_state(self) -> None:
        """Reset bypass state after arming/disarming."""
        if self._is_bypassed:
            self._is_bypassed = False
            self._attr_icon = "mdi:shield-check"
            self.async_schedule_update_ha_state()
    
    def _message_callback(self, message) -> None:
        """Handle incoming AlarmDecoder messages to update bypass status."""
        # We don't process panel messages for these switches
        # They only maintain local state for command construction
        pass