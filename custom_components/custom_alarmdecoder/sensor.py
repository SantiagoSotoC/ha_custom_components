"""Support for AlarmDecoder sensors (Panel Display per Keypad + Event History)."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers import entity_registry as er

from . import AlarmDecoderConfigEntry
from .const import (
    CONF_KEYPADS,
    OPTIONS_KEYPADS,
    SIGNAL_PANEL_MESSAGE,
    SIGNAL_ZONE_FAULT,
    SIGNAL_ZONE_RESTORE,
    SIGNAL_RFX_MESSAGE,
)
from .entity import AlarmDecoderEntity

_LOGGER = logging.getLogger(__name__)

MAX_EVENTS = 50


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlarmDecoderConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up for AlarmDecoder sensors — one per keypad."""
    client = entry.runtime_data.client
    serial = client.serial_number

    # Keypads: prefer options, fallback to data for backwards compatibility
    keypads = entry.options.get(OPTIONS_KEYPADS, entry.data.get(CONF_KEYPADS, []))

    # Remove entities for keypads that no longer exist
    entity_reg = er.async_get(hass)
    prefix = f"{serial}-display-"
    for entity_id, entity in list(entity_reg.entities.items()):
        if (
            entity.config_entry_id == entry.entry_id
            and entity.domain == "sensor"
            and entity.unique_id.startswith(prefix)
        ):
            addr = entity.unique_id[len(prefix):]
            try:
                if int(addr) not in keypads:
                    entity_reg.async_remove(entity_id)
                    _LOGGER.debug("Removed stale sensor entity %s", entity_id)
            except ValueError:
                pass

    if not keypads:
        return

    entities: list[SensorEntity] = [
        AlarmDecoderSensor(
            client=client,
            address=address,
        )
        for address in keypads
    ]

    # Add event history sensor
    entities.append(
        EventHistorySensor(
            client=client,
            unique_id=f"{serial}-event-history",
            name="Alarm Event History",
        )
    )

    async_add_entities(entities)


class AlarmDecoderSensor(AlarmDecoderEntity, SensorEntity):
    """Representation of an AlarmDecoder keypad display."""

    _attr_should_poll = False

    def __init__(self, client, address: int) -> None:
        """Initialize the sensor."""
        super().__init__(client)
        self._address = address
        self._attr_unique_id = f"{client.serial_number}-display-{address}"
        self._attr_name = f"Keypad {address} Display"

    async def async_added_to_hass(self) -> None:
        """Register callback."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_PANEL_MESSAGE, self._message_callback
            )
        )

    @staticmethod
    def _extract_keypad_addresses(message) -> list[int]:
        """Extract target keypad addresses from a panel message."""
        if message.raw[0] != "[":
            return []
        raw = message.raw[28:58]
        raw = bin(int(raw, 16))[2:]
        raw = str(raw[8:40])
        byte0 = raw[0:8][::-1]
        byte1 = raw[8:16][::-1]
        byte2 = raw[16:24][::-1]
        byte3 = raw[24:35][::-1]
        sorted_bin = byte0 + byte1 + byte2 + byte3
        return [i for i in range(len(sorted_bin)) if sorted_bin[i] == "1"]

    def _message_callback(self, message) -> None:
        """Update display text for this keypad."""
        keypads = self._extract_keypad_addresses(message)
        if self._address not in keypads:
            return

        if self._attr_native_value != message.text:
            self._attr_native_value = message.text
            self.hass.loop.call_soon_threadsafe(lambda: self.async_write_ha_state())


class EventHistorySensor(AlarmDecoderEntity, SensorEntity):
    """Sensor that tracks alarm events (arm, disarm, fault, restore)."""

    _attr_should_poll = False
    _attr_icon = "mdi:history"

    def __init__(self, client, unique_id: str, name: str) -> None:
        """Initialize the event history sensor."""
        super().__init__(client)
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._events: list[dict[str, Any]] = []
        self._attr_native_value = "Sin eventos"
        self._attr_extra_state_attributes = {"events": []}

    async def async_added_to_hass(self) -> None:
        """Register callbacks for all event signals."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_PANEL_MESSAGE, self._panel_callback
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_ZONE_FAULT, self._fault_callback
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_ZONE_RESTORE, self._restore_callback
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_RFX_MESSAGE, self._rfx_callback
            )
        )

    def _add_event(self, event_type: str, details: str) -> None:
        """Add an event to history."""
        now = datetime.now()
        event = {
            "timestamp": now.isoformat(),
            "type": event_type,
            "details": details,
        }
        self._events.insert(0, event)
        if len(self._events) > MAX_EVENTS:
            self._events = self._events[:MAX_EVENTS]

        self._attr_native_value = f"{event_type}: {details}"
        self._attr_extra_state_attributes = {
            "events": self._events,
            "total_events": len(self._events),
        }
        self.hass.loop.call_soon_threadsafe(lambda: self.async_write_ha_state())

    def _panel_callback(self, message) -> None:
        """Handle panel messages for arm/disarm/chime events."""
        if not hasattr(message, "raw") or not message.raw or message.raw[0] != "[":
            return

        text = message.text if message.text else ""

        # Detect arm/disarm events from bitfield
        if hasattr(message, "armed_away"):
            if message.armed_away:
                self._add_event("ARM_AWAY", "Alarma armada (salida)")
            elif message.armed_home:
                self._add_event("ARM_HOME", "Alarma armada (estancia)")
            elif not message.armed_away and not message.armed_home:
                # Check if was previously armed (disarm event)
                pass

        # Detect chime
        if hasattr(message, "chime_on") and message.chime_on:
            self._add_event("CHIME", "Chime activado")

        # Detect zone bypass
        if hasattr(message, "zone_bypassed") and message.zone_bypassed:
            self._add_event("BYPASS", "Zona en bypass")

        # Detect alarm triggered
        if hasattr(message, "alarm_event_occurred") and message.alarm_event_occurred:
            self._add_event("ALARM", "Alarma disparada")

        # Detect ready state changes
        if hasattr(message, "ready"):
            if message.ready:
                self._add_event("READY", "Panel listo")
            else:
                self._add_event("NOT_READY", "Panel no listo")

        # Detect programming mode
        if hasattr(message, "programming_mode") and message.programming_mode:
            self._add_event("PROGRAMMING", "Modo programación")

    def _fault_callback(self, zone) -> None:
        """Handle zone fault events."""
        if zone is not None:
            self._add_event("FAULT", f"Zona {int(zone)} abierta")
        else:
            self._add_event("FAULT", "Zona desconocida abierta")

    def _restore_callback(self, zone) -> None:
        """Handle zone restore events."""
        if zone is not None:
            self._add_event("RESTORE", f"Zona {int(zone)} cerrada")
        else:
            self._add_event("RESTORE", "Zona desconocida cerrada")

    def _rfx_callback(self, message) -> None:
        """Handle RF events."""
        if message and hasattr(message, "serial_number"):
            serial = message.serial_number
            if hasattr(message, "battery") and message.battery:
                self._add_event("RF_BATTERY", f"Sensor {serial} batería baja")
            if hasattr(message, "supervision") and not message.supervision:
                self._add_event("RF_SUPERVISION", f"Sensor {serial} sin supervisión")
