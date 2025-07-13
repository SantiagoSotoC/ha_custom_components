"""Support for AlarmDecoder-based alarm control panels (Honeywell/DSC)."""

from __future__ import annotations
import logging

import voluptuous as vol

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
    CodeFormat,
)
from homeassistant.const import ATTR_CODE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers import entity_registry as er

from . import AlarmDecoderConfigEntry
from .const import (
    CONF_AUTO_BYPASS,
    CONF_CODE_ARM_REQUIRED,
    DEFAULT_ARM_OPTIONS,
    OPTIONS_ARM,
    SIGNAL_PANEL_MESSAGE,
)
from .entity import AlarmDecoderEntity

_LOGGER = logging.getLogger(__name__)

SERVICE_ALARM_TOGGLE_CHIME = "alarm_toggle_chime"

SERVICE_ALARM_KEYPRESS = "alarm_keypress"
ATTR_KEYPRESS = "keypress"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlarmDecoderConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up for AlarmDecoder alarm panels."""
    options = entry.options
    arm_options = options.get(OPTIONS_ARM, DEFAULT_ARM_OPTIONS)

    keypads = entry.data.get("keypads")
    if not keypads:
        return  # No crear entidades si no hay keypads configurados

    entities = []
    for address in keypads:
        entities.append(
            AlarmDecoderAlarmPanel(
                client=entry.runtime_data.client,
                auto_bypass=arm_options[CONF_AUTO_BYPASS],
                code_arm_required=arm_options[CONF_CODE_ARM_REQUIRED],
                address=address,
                entry_id=entry.entry_id,  # Agregar entry_id
            )
        )
    async_add_entities(entities)

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_ALARM_TOGGLE_CHIME,
        {
            vol.Required(ATTR_CODE): cv.string,
        },
        "alarm_toggle_chime",
    )

    platform.async_register_entity_service(
        SERVICE_ALARM_KEYPRESS,
        {
            vol.Required(ATTR_KEYPRESS): cv.string,
        },
        "alarm_keypress",
    )


class AlarmDecoderAlarmPanel(AlarmDecoderEntity, AlarmControlPanelEntity):
    """Representation of an AlarmDecoder-based alarm panel."""

    _attr_name = "Alarm Panel"
    _attr_should_poll = False
    _attr_code_format = CodeFormat.NUMBER
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
    )

    def __init__(self, client, auto_bypass, code_arm_required, address, entry_id):
        """Initialize the alarm panel."""
        super().__init__(client)
        self._attr_unique_id = f"{client.serial_number}-panel"
        self._auto_bypass = auto_bypass
        self._attr_code_arm_required = code_arm_required
        self._address = address
        self._entry_id = entry_id

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_PANEL_MESSAGE, self._message_callback
            )
        )

    @staticmethod
    def extract_keypad_addresses_from_message(message):
        if message.raw[0] == "[":
            raw = message.raw[28:58]
            raw = bin(int(raw, 16))[2:]
            message_keypads_bin_unsorted = str(raw[8:40])
            byte0 = (message_keypads_bin_unsorted[0:8])[::-1]
            byte1 = (message_keypads_bin_unsorted[8:16])[::-1]
            byte2 = (message_keypads_bin_unsorted[16:24])[::-1]
            byte3 = (message_keypads_bin_unsorted[24:35])[::-1]
            message_keypads_bin_sorted = byte0 + byte1 + byte2 + byte3
            message_target_keypads = []
            for i in range(len(message_keypads_bin_sorted)):
                if message_keypads_bin_sorted[i] == "1":
                    message_target_keypads.append(i)
            return message_target_keypads
        return []

    def _message_callback(self, message):
        """Handle received messages."""
        keypads = self.extract_keypad_addresses_from_message(message)
        if self._address not in keypads:
            return  # Ignorar mensajes que no son para este keypad

        if message.alarm_sounding or message.fire_alarm:
            self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
        elif message.armed_away:
            self._attr_alarm_state = AlarmControlPanelState.ARMED_AWAY
        elif message.armed_home:
            self._attr_alarm_state = AlarmControlPanelState.ARMED_HOME
        else:
            self._attr_alarm_state = AlarmControlPanelState.DISARMED

        self._attr_extra_state_attributes = {
            "ac_power": message.ac_power,
            "alarm_event_occurred": message.alarm_event_occurred,
            "backlight_on": message.backlight_on,
            "battery_low": message.battery_low,
            "check_zone": message.check_zone,
            "chime": message.chime_on,
            "entry_delay_off": message.entry_delay_off,
            "programming_mode": message.programming_mode,
            "ready": message.ready,
            "zone_bypassed": message.zone_bypassed,
        }
        self.schedule_update_ha_state()

    def _get_bypass_zones(self) -> list[int]:
        """Get list of zones marked for bypass."""
        entity_reg = er.async_get(self.hass)
        bypass_zones = []
        
        # Buscar todos los switches de bypass activos en este config entry
        for entity_id, entity in entity_reg.entities.items():
            if (entity.config_entry_id == self._entry_id and 
                entity.domain == "switch" and 
                "_bypass" in entity.unique_id):
                
                # Obtener el estado actual del switch
                state = self.hass.states.get(entity_id)
                if state and state.state == "on":
                    # Extraer número de zona del unique_id: "entry_id_ZONENUMBER_bypass"
                    try:
                        zone_str = entity.unique_id.split("_")[-2]
                        zone_num = int(zone_str)  # Convertir a int para bypass_zones
                        bypass_zones.append(zone_num)
                        _LOGGER.debug("Zone %s marked for bypass", zone_num)
                    except (ValueError, IndexError):
                        _LOGGER.warning("Could not extract zone number from entity %s", entity_id)
        
        _LOGGER.debug("Total bypass zones found: %s", sorted(bypass_zones))
        return sorted(bypass_zones)
    
    def _build_bypass_string(self, zones: list[int], code: str = "") -> str:
        """Build bypass string for the given zones."""
        if not zones:
            return ""
        
        # Nuevo formato: código + 6 + zonas a bypass + *
        # Las zonas nunca deben tener ceros a la izquierda (1, no 01; 11, no 011)
        zones_str = "".join([str(zone) for zone in zones])
        bypass_string = f"{code}6{zones_str}*"
        
        _LOGGER.debug(
            "Building bypass string - Code: '%s', Zones: %s, Zones string: '%s', Final: '%s'",
            code, zones, zones_str, bypass_string
        )
        
        return bypass_string

    def alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        if code:
            self._client.send(f"{code!s}1")

    def alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        # Obtener zonas marcadas para bypass
        bypass_zones = self._get_bypass_zones()
        
        if bypass_zones:
            _LOGGER.info("Arming away with bypassed zones: %s", bypass_zones)
            # Enviar comando de bypass: código + 6 + zonas + *
            bypass_command = self._build_bypass_string(bypass_zones, code or "")
            _LOGGER.debug("Sending bypass command: '%s'", bypass_command)
            self._client.send(bypass_command)
            # Luego enviar comando de armado away
            self._client.arm_away(
                code=code,
                code_arm_required=self._attr_code_arm_required,
                auto_bypass=self._auto_bypass,
            )
        else:
            _LOGGER.debug("Arming away without bypasses using standard method")
            self._client.arm_away(
                code=code,
                code_arm_required=self._attr_code_arm_required,
                auto_bypass=self._auto_bypass,
            )


    def alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        # Obtener zonas marcadas para bypass
        bypass_zones = self._get_bypass_zones()
        
        if bypass_zones:
            _LOGGER.info("Arming home with bypassed zones: %s", bypass_zones)
            # Enviar comando de bypass: código + 6 + zonas + *
            bypass_command = self._build_bypass_string(bypass_zones, code or "")
            _LOGGER.debug("Sending bypass command: '%s'", bypass_command)
            self._client.send(bypass_command)
            # Luego enviar comando de armado home
            arm_command = f"{code or ''}3"
            _LOGGER.debug("Sending arm home command: '%s'", arm_command)
            self._client.arm_home(
                code=code,
                code_arm_required=self._attr_code_arm_required,
                auto_bypass=self._auto_bypass,
            )
        else:
            _LOGGER.debug("Arming home without bypasses using standard method")
            # Armado normal sin bypasses
            self._client.arm_home(
                code=code,
                code_arm_required=self._attr_code_arm_required,
                auto_bypass=self._auto_bypass,
            )

    def alarm_toggle_chime(self, code=None):
        """Send toggle chime command."""
        if code:
            self._client.send(f"{code!s}9")

    def alarm_keypress(self, keypress):
        """Send custom keypresses."""
        if keypress:
            self._client.send(keypress)
