"""Support for AlarmDecoder zone states and diagnostic sensors."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AlarmDecoderConfigEntry
from .const import (
    CONF_RELAY_ADDR,
    CONF_RELAY_CHAN,
    CONF_ZONE_LOOP,
    CONF_ZONE_NAME,
    CONF_ZONE_NUMBER,
    CONF_ZONE_RFID,
    CONF_ZONE_TYPE,
    DEFAULT_ZONE_OPTIONS,
    OPTIONS_ZONES,
    SIGNAL_PANEL_MESSAGE,
    SIGNAL_REL_MESSAGE,
    SIGNAL_RFX_MESSAGE,
    SIGNAL_ZONE_FAULT,
    SIGNAL_ZONE_RESTORE,
)
from .entity import AlarmDecoderEntity

_LOGGER = logging.getLogger(__name__)

ATTR_RF_BIT0 = "rf_bit0"
ATTR_RF_LOW_BAT = "rf_low_battery"
ATTR_RF_SUPERVISED = "rf_supervised"
ATTR_RF_BIT3 = "rf_bit3"
ATTR_RF_LOOP3 = "rf_loop3"
ATTR_RF_LOOP2 = "rf_loop2"
ATTR_RF_LOOP4 = "rf_loop4"
ATTR_RF_LOOP1 = "rf_loop1"

PANEL_DIAGNOSTICS = [
    ("ac_power", "AC Power", "power", "mdi:power-plug"),
    ("battery_low", "Battery Low", "battery", "mdi:battery-alert"),
    ("ready", "Ready", None, "mdi:shield-check"),
    ("check_zone", "Check Zone", "problem", "mdi:alert-circle"),
    ("chime_on", "Chime", None, "mdi:bell-ring"),
    ("programming_mode", "Programming Mode", None, "mdi:cog"),
    ("entry_delay_off", "Entry Delay Off", None, "mdi:timer-off"),
    ("zone_bypassed", "Zone Bypassed", None, "mdi:shield-half-full"),
    ("alarm_event_occurred", "Alarm Event", "problem", "mdi:alarm-bell"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlarmDecoderConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up for AlarmDecoder binary sensors."""
    client = entry.runtime_data.client
    serial = client.serial_number
    zones = entry.options.get(OPTIONS_ZONES, DEFAULT_ZONE_OPTIONS)

    entities: list[BinarySensorEntity] = []

    # Zone sensors
    for zone_num in zones:
        zone_info = zones[zone_num]
        zone_type = zone_info[CONF_ZONE_TYPE]
        zone_name = zone_info[CONF_ZONE_NAME]
        zone_rfid = zone_info.get(CONF_ZONE_RFID)
        zone_loop = zone_info.get(CONF_ZONE_LOOP)
        relay_addr = zone_info.get(CONF_RELAY_ADDR)
        relay_chan = zone_info.get(CONF_RELAY_CHAN)
        entities.append(
            AlarmDecoderBinarySensor(
                client,
                zone_num,
                zone_name,
                zone_type,
                zone_rfid,
                zone_loop,
                relay_addr,
                relay_chan,
            )
        )

    # Panel-level diagnostic sensors
    for attr, name, device_class, icon in PANEL_DIAGNOSTICS:
        entities.append(
            PanelDiagnosticSensor(
                client=client,
                unique_id=f"{serial}-diag-{attr}",
                name=name,
                attribute=attr,
                device_class=device_class,
                icon=icon,
            )
        )

    # Zone RF diagnostic sensors (only for zones with RFID)
    for zone_num, zone_info in zones.items():
        zone_rfid = zone_info.get(CONF_ZONE_RFID)
        if not zone_rfid:
            continue
        zone_name = zone_info.get(CONF_ZONE_NAME, f"Zone {zone_num}")
        entities.append(
            ZoneRfDiagnosticSensor(
                client=client,
                unique_id=f"{serial}-zone-{zone_num}-rf-low-battery",
                name=f"{zone_name} RF Low Battery",
                zone_number=int(zone_num),
                zone_rfid=zone_rfid,
                device_class="battery",
                attribute="rf_low_battery",
                icon="mdi:battery-alert",
            )
        )
        entities.append(
            ZoneRfDiagnosticSensor(
                client=client,
                unique_id=f"{serial}-zone-{zone_num}-rf-supervised",
                name=f"{zone_name} RF Supervised",
                zone_number=int(zone_num),
                zone_rfid=zone_rfid,
                device_class=None,
                attribute="rf_supervised",
                icon="mdi:eye-check",
            )
        )

    # Panel delay sensor (exit/entry delay detection)
    entities.append(
        PanelDelaySensor(
            client=client,
            unique_id=f"{serial}-diag-panel-delay",
            name="Panel Delay",
        )
    )

    async_add_entities(entities)


class AlarmDecoderBinarySensor(AlarmDecoderEntity, BinarySensorEntity):
    """Representation of an AlarmDecoder binary sensor."""

    _attr_should_poll = False

    def __init__(
        self,
        client,
        zone_number,
        zone_name,
        zone_type,
        zone_rfid,
        zone_loop,
        relay_addr,
        relay_chan,
    ):
        """Initialize the binary_sensor."""
        super().__init__(client)
        self._attr_unique_id = f"{client.serial_number}-zone-{zone_number}"
        self._zone_number = int(zone_number)
        self._zone_type = zone_type
        self._attr_name = zone_name
        self._attr_is_on = False
        self._rfid = zone_rfid
        self._loop = zone_loop
        self._relay_addr = relay_addr
        self._relay_chan = relay_chan
        self._attr_device_class = zone_type
        self._attr_extra_state_attributes = {
            CONF_ZONE_NUMBER: self._zone_number,
        }

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_ZONE_FAULT, self._fault_callback)
        )

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_ZONE_RESTORE, self._restore_callback
            )
        )

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_RFX_MESSAGE, self._rfx_message_callback
            )
        )

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_REL_MESSAGE, self._rel_message_callback
            )
        )

    def _fault_callback(self, zone):
        """Update the zone's state, if needed."""
        if zone is None or int(zone) == self._zone_number:
            # Skip KPM fault if zone has RFID - use RFX loop instead
            if self._rfid and self._loop:
                return
            self._attr_is_on = True
            self.hass.loop.call_soon_threadsafe(lambda: self.async_write_ha_state())

    def _restore_callback(self, zone):
        """Update the zone's state, if needed."""
        if zone is None or int(zone) == self._zone_number:
            # Skip KPM restore if zone has RFID - use RFX loop instead
            if self._rfid and self._loop:
                return
            self._attr_is_on = False
            self.hass.loop.call_soon_threadsafe(lambda: self.async_write_ha_state())

    def _rfx_message_callback(self, message):
        """Update RF state from RFX message using loop for open/close detection."""
        if not self._rfid or not message or message.serial_number != self._rfid:
            return

        rfstate = message.value
        if rfstate is None:
            return

        # Use loop value for open/close detection
        if self._loop:
            loop_idx = int(self._loop) - 1
            if 0 <= loop_idx < len(message.loop):
                new_state = bool(message.loop[loop_idx])
                if self._attr_is_on != new_state:
                    self._attr_is_on = new_state

        # Update RF attributes
        attr = {CONF_ZONE_NUMBER: self._zone_number}
        if rfstate is not None:
            attr[ATTR_RF_BIT0] = bool(rfstate & 0x01)
            attr[ATTR_RF_LOW_BAT] = bool(rfstate & 0x02)
            attr[ATTR_RF_SUPERVISED] = bool(rfstate & 0x04)
            attr[ATTR_RF_BIT3] = bool(rfstate & 0x08)
            attr[ATTR_RF_LOOP3] = bool(rfstate & 0x10)
            attr[ATTR_RF_LOOP2] = bool(rfstate & 0x20)
            attr[ATTR_RF_LOOP4] = bool(rfstate & 0x40)
            attr[ATTR_RF_LOOP1] = bool(rfstate & 0x80)
        self._attr_extra_state_attributes = attr
        self.hass.loop.call_soon_threadsafe(lambda: self.async_write_ha_state())

    def _rel_message_callback(self, message):
        """Update relay / expander state."""

        if self._relay_addr == message.address and self._relay_chan == message.channel:
            _LOGGER.debug(
                "%s %d:%d value:%d",
                "Relay" if message.type == message.RELAY else "ZoneExpander",
                message.address,
                message.channel,
                message.value,
            )
            self._attr_is_on = bool(message.value)
            self.hass.loop.call_soon_threadsafe(lambda: self.async_write_ha_state())


class PanelDiagnosticSensor(AlarmDecoderEntity, BinarySensorEntity):
    """Diagnostic binary sensor for panel-level status (AC power, battery, etc.)."""

    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        client,
        unique_id: str,
        name: str,
        attribute: str,
        device_class: str | None,
        icon: str | None = None,
    ) -> None:
        """Initialize the diagnostic sensor."""
        super().__init__(client)
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attribute = attribute

    async def async_added_to_hass(self) -> None:
        """Register callback for panel messages."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_PANEL_MESSAGE, self._message_callback
            )
        )

    def _message_callback(self, message) -> None:
        """Update state from panel message."""
        if not hasattr(message, "raw") or not message.raw or message.raw[0] != "[":
            return
        # battery_low only updates from panel status messages
        if self._attribute == "battery_low":
            if not message.text or "**" not in message.text:
                return
        new_state = getattr(message, self._attribute, None)
        if new_state is None:
            return
        if self._attr_is_on != new_state:
            self._attr_is_on = new_state
            self.hass.loop.call_soon_threadsafe(lambda: self.async_write_ha_state())


class ZoneRfDiagnosticSensor(AlarmDecoderEntity, BinarySensorEntity):
    """Diagnostic binary sensor for per-zone RF status."""

    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        client,
        unique_id: str,
        name: str,
        zone_number: int,
        zone_rfid: str,
        attribute: str,
        device_class: str | None,
        icon: str | None = None,
    ) -> None:
        """Initialize the RF diagnostic sensor."""
        super().__init__(client)
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._zone_number = zone_number
        self._rfid = zone_rfid
        self._attribute = attribute

    async def async_added_to_hass(self) -> None:
        """Register callback for RFX messages."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_RFX_MESSAGE, self._rfx_message_callback
            )
        )

    def _rfx_message_callback(self, message) -> None:
        """Update state from RF message."""
        if not message or message.serial_number != self._rfid:
            return

        rfstate = message.value
        if rfstate is None:
            return

        if self._attribute == "rf_low_battery":
            new_state = bool(rfstate & 0x02)
        elif self._attribute == "rf_supervised":
            new_state = bool(rfstate & 0x04)
        else:
            return

        if self._attr_is_on != new_state:
            self._attr_is_on = new_state
            self.hass.loop.call_soon_threadsafe(lambda: self.async_write_ha_state())


class PanelDelaySensor(AlarmDecoderEntity, BinarySensorEntity):
    """Diagnostic sensor for panel delay states (exit/entry delay).

    Detects delay periods by tracking state transitions:
    - Exit delay: ready=True but not yet armed (user entering code)
    - Entry delay: armed but ready=False (zone opened while armed)
    """

    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = "safety"
    _attr_icon = "mdi:timer-sand"

    def __init__(self, client, unique_id: str, name: str) -> None:
        """Initialize the delay sensor."""
        super().__init__(client)
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._armed = False
        self._ready = True

    async def async_added_to_hass(self) -> None:
        """Register callback for panel messages."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_PANEL_MESSAGE, self._message_callback
            )
        )

    def _message_callback(self, message) -> None:
        """Update delay state from panel message."""
        if not hasattr(message, "raw") or not message.raw or message.raw[0] != "[":
            return
        self._armed = message.armed_away or message.armed_home
        self._ready = message.ready

        # Exit delay: ready=True but not yet armed (user is entering code)
        # Entry delay: armed but ready=False (zone opened while armed)
        in_delay = (self._ready and not self._armed) or (
            self._armed and not self._ready
        )

        # Determine delay type for attributes
        delay_type = "none"
        if self._ready and not self._armed:
            delay_type = "exit"
        elif self._armed and not self._ready:
            delay_type = "entry"

        attrs = {
            "delay_type": delay_type,
            "armed": self._armed,
            "ready": self._ready,
        }

        if self._attr_is_on != in_delay or self._attr_extra_state_attributes != attrs:
            self._attr_is_on = in_delay
            self._attr_extra_state_attributes = attrs
            self.hass.loop.call_soon_threadsafe(lambda: self.async_write_ha_state())
