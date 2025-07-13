"""Support for AlarmDecoder zone bypass switches."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AlarmDecoderConfigEntry
from .const import DOMAIN, OPTIONS_ZONES, CONF_BYPASSABLE
from .entity import AlarmDecoderEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlarmDecoderConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AlarmDecoder zone switches."""
    controller = entry.runtime_data.client
    zones = entry.options.get(OPTIONS_ZONES, {})  # Obtener de options
    
    switches = []
    
    # Crear switches solo para zonas que soporten bypass
    for zone_number, zone_config in zones.items():
        if zone_config.get(CONF_BYPASSABLE, False):
            switch = AlarmDecoderZoneSwitch(
                controller,
                int(zone_number),
                zone_config,
                entry.entry_id
            )
            switches.append(switch)
    
    if switches:
        async_add_entities(switches)


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
        super().__init__(controller, entry_id)
        
        self._zone_number = zone_number
        self._zone_config = zone_config
        self._attr_name = f"Zone {zone_number} Bypass"
        self._attr_unique_id = f"{entry_id}_{zone_number}_bypass"
        self._is_bypassed = False
        
        # Configurar nombre personalizado si existe
        if zone_name := zone_config.get("name"):
            self._attr_name = f"{zone_name} Bypass"
    
    
    @property
    def is_on(self) -> bool:
        """Return true if zone is marked for bypass."""
        return self._is_bypassed
    
    @property
    def zone_number(self) -> int:
        """Return the zone number."""
        return self._zone_number
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = super().extra_state_attributes
        if attrs is None:
            attrs = {}
        else:
            attrs = dict(attrs)  # Crear una copia para evitar mutaciones
        
        attrs.update({
            "zone_number": self._zone_number,
            "zone_type": self._zone_config.get("type", "door_window"),
            "zone_name": self._zone_config.get("name", f"Zone {self._zone_number}"),
            "marked_for_bypass": self._is_bypassed,
        })
        return attrs
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mark zone for bypass on next arming."""
        self._is_bypassed = True
        self.async_write_ha_state()
        _LOGGER.debug("Zone %s marked for bypass", self._zone_number)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unmark zone for bypass."""
        self._is_bypassed = False
        self.async_write_ha_state()
        _LOGGER.debug("Zone %s unmarked for bypass", self._zone_number)
    
    def reset_bypass_state(self) -> None:
        """Reset bypass state after arming/disarming."""
        if self._is_bypassed:
            self._is_bypassed = False
            self.async_schedule_update_ha_state()
    
    def _message_callback(self, message) -> None:
        """Handle incoming AlarmDecoder messages to update bypass status."""
        # No procesamos mensajes del panel para estos switches
        # Solo mantienen el estado local para construcción de comandos
        pass