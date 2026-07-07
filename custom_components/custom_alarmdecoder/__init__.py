"""Support for AlarmDecoder devices."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
import logging
import re
import threading
import time
from typing import TypeAlias

from adext import AdExt
from alarmdecoder.devices import SerialDevice, SocketDevice
from alarmdecoder.util import NoDeviceError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_PROTOCOL,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send
from homeassistant.helpers.event import async_call_later
from homeassistant.components import persistent_notification

from .const import (
    CONF_AUTO_DETECT_ZONES,
    CONF_DEVICE_BAUD,
    CONF_DEVICE_PATH,
    CONF_ENTRY_DELAY,
    CONF_NOTIFY_ARM,
    CONF_NOTIFY_DISARM,
    CONF_NOTIFY_TRIGGER,
    CONF_SCAN_PANEL,
    CONF_ZONE_NAME,
    CONF_ZONE_RFID,
    CONF_ZONE_TYPE,
    DEFAULT_ARM_OPTIONS,
    DEFAULT_AUTO_DETECT_ZONES,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_SCAN_PANEL,
    DEFAULT_ZONE_TYPE,
    OPTIONS_ARM,
    OPTIONS_ZONES,
    PROTOCOL_SERIAL,
    PROTOCOL_SOCKET,
    SIGNAL_AUI_MESSAGE,
    SIGNAL_PANEL_MESSAGE,
    SIGNAL_REL_MESSAGE,
    SIGNAL_RFX_MESSAGE,
    SIGNAL_ZONE_FAULT,
    SIGNAL_ZONE_RESTORE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
]

# Regex to extract zone number and name from panel text
# Matches: "ANULA 09  POSTI DORM PPAL" or "COMPROBAR 32  VENT BARBACOA 3"
_ZONE_TEXT_RE = re.compile(r"^(?:ANULA|COMPROBAR)\s+(\d{2})\s+(.+?)\s*$")

# AUI partition map
_PARTITION_MAP = {
    0: '31',  # partition 1
    1: '32',  # partition 2
    2: '33',
    3: '34',
    4: '35',
    5: '36',
    6: '37',
    7: '38',
    8: '39',
}

# Zone type map from AUI
_ZONE_TYPE_MAP = {
    '9': 'Supervised Fire',
    '00': 'Zone Not Used',
    '1': 'Entry/Exit #1 Burglary',
    '2': 'Entry/Exit #2 Burglary',
    '3': 'Perimeter Burglary',
    '4': 'Interior, Follower',
    '5': 'Trouble by Day/Alarm by Night',
    '6': '24-Hour Silent Alarm',
    '7': '24-Hour Audible Alarm',
    '8': '24-Hour Auxiliary Alarm',
    '10': 'Interior With Delay',
    '12': 'Monitor Zone',
    '14': 'Carbon Monoxide',
    '16': 'Fire w/Verify',
    '20': 'Arm-STAY',
    '21': 'Arm-AWAY',
    '22': 'Disarm',
    '23': 'No Alarm Response',
    '24': 'Silent Burglary',
    '27': 'Access Point',
    '28': 'Main Logic Board (MLB) Supervision',
    '29': 'Momentary on Exit',
    '77': 'KeySwitch',
    '81': 'AAV Monitor Zone',
    '90': 'Configurable',
    '91': 'Configurable',
}


def _ascii_to_hex(text: str) -> str:
    """Convert ASCII string to hex."""
    return ''.join(f'{ord(c):02x}' for c in text)


def _hex_to_ascii(hex_str: str) -> str:
    """Convert hex string to ASCII."""
    result = ''
    for i in range(0, len(hex_str), 2):
        result += chr(int(hex_str[i:i+2], 16))
    return result


def _dec_to_hex(num: int) -> str:
    """Convert decimal number to hex string with padding."""
    if num < 10:
        return _ascii_to_hex(f"00{num}")
    elif num < 100:
        return _ascii_to_hex(f"0{num}")
    else:
        return _ascii_to_hex(str(num))


def _get_aui_prefix(value: str) -> str:
    """Get AUI prefix from value."""
    return value[:2] if len(value) >= 2 else ''


def _get_hex_val(value: str, delimiter: str) -> str:
    """Get hex value after delimiter."""
    idx = value.find(delimiter)
    if idx == -1:
        return ''
    return value[idx + len(delimiter):]


def _parse_aui_message(prefix: str, value: str, state: str, partition_count: int = 0) -> dict | None:
    """Parse AUI message based on state."""
    if state == 'get_partition_count':
        # Response like: 0c020000000057fefefd3131
        if 'fefefd' not in value:
            return None
        hex_val = _get_hex_val(value, "fefefd")
        ascii_val = _hex_to_ascii(hex_val)
        return {'partition_count': ascii_val}

    if state == 'get_zone_data':
        # Response like: 17020000000057fefefeec380037003100534952454e41
        if 'fefefeec' not in value:
            return None
        hex_val = _get_hex_val(value, "fefefeec")
        if not hex_val:
            return None

        arr = hex_val.split("00")
        if len(arr) < 3:
            return None

        # Handle odd-length first element
        if arr[0] and len(arr[0]) % 2:
            arr[0] = hex_val[:len(arr[0])+1]
            arr[1] = arr[1][1:] if len(arr[1]) > 1 else ''

        address = _hex_to_ascii(arr[0]) if arr[0] else ''
        zone_type = _hex_to_ascii(arr[1]) if len(arr) > 1 and arr[1] else ''
        zone_device_type = _hex_to_ascii(arr[2]) if len(arr) > 2 and arr[2] else ''
        zone_name = _hex_to_ascii(arr[3]) if len(arr) > 3 and arr[3] else ''

        # Only accept valid zones (device type >= '1' in ASCII)
        device_type_hex = _ascii_to_hex(zone_device_type) if zone_device_type else ''
        if device_type_hex and int(device_type_hex, 16) >= 0x31:
            return {
                'address': address,
                'zone_type': zone_type,
                'zone_device_type': zone_device_type,
                'zone_name': zone_name,
            }
        return None

    return None


AlarmDecoderConfigEntry: TypeAlias = ConfigEntry["AlarmDecoderData"]


@dataclass
class AlarmDecoderData:
    """Runtime data for the AlarmDecoder class."""

    client: AdExt
    remove_update_listener: Callable[[], None]
    remove_stop_listener: Callable[[], None]
    restart: bool


async def async_setup_entry(
    hass: HomeAssistant, entry: AlarmDecoderConfigEntry
) -> bool:
    """Set up AlarmDecoder config flow."""
    undo_listener = entry.add_update_listener(_update_listener)

    ad_connection = entry.data
    protocol = ad_connection[CONF_PROTOCOL]

    def stop_alarmdecoder(event):
        """Handle the shutdown of AlarmDecoder."""
        if not entry.runtime_data:
            return
        _LOGGER.debug("Shutting down alarmdecoder")
        entry.runtime_data.restart = False
        controller.close()

    async def open_connection(now=None):
        """Open a connection to AlarmDecoder."""
        try:
            await hass.async_add_executor_job(controller.open, baud)
        except NoDeviceError:
            _LOGGER.debug("Failed to connect. Retrying in 5 seconds")
            async_call_later(hass, timedelta(seconds=5), open_connection)
            return
        _LOGGER.debug("Established a connection with the alarmdecoder")
        entry.runtime_data.restart = True

    def handle_closed_connection(event):
        """Restart after unexpected loss of connection."""
        if not entry.runtime_data.restart:
            return
        entry.runtime_data.restart = False
        _LOGGER.warning("AlarmDecoder unexpectedly lost connection")
        hass.add_job(open_connection)

    def handle_message(sender, message):
        """Handle message from AlarmDecoder."""
        dispatcher_send(hass, SIGNAL_PANEL_MESSAGE, message)

    def handle_rfx_message(sender, message):
        """Handle RFX message from AlarmDecoder."""
        dispatcher_send(hass, SIGNAL_RFX_MESSAGE, message)

    def zone_fault_callback(sender, zone):
        """Handle zone fault from AlarmDecoder."""
        dispatcher_send(hass, SIGNAL_ZONE_FAULT, zone)

    def zone_restore_callback(sender, zone):
        """Handle zone restore from AlarmDecoder."""
        dispatcher_send(hass, SIGNAL_ZONE_RESTORE, zone)

    def handle_rel_message(sender, message):
        """Handle relay or zone expander message from AlarmDecoder."""
        dispatcher_send(hass, SIGNAL_REL_MESSAGE, message)

    def auto_detect_zone(message):
        """Auto-detect zones from panel messages."""
        # Only process KPM messages (raw starts with "[")
        if not hasattr(message, "raw") or not message.raw or message.raw[0] != "[":
            return
        # Skip panel status messages (text starts with "**")
        if message.text and message.text.startswith("**"):
            return
        # Check if auto-detect is enabled (stored inside OPTIONS_ARM)
        arm_options = entry.options.get(OPTIONS_ARM, DEFAULT_ARM_OPTIONS)
        auto_detect = arm_options.get(CONF_AUTO_DETECT_ZONES, DEFAULT_AUTO_DETECT_ZONES)
        _LOGGER.debug(
            "Auto-detect check: arm_options=%s, auto_detect=%s",
            arm_options,
            auto_detect,
        )
        if not auto_detect:
            return
        # Extract zone info from text
        if not message.text:
            return
        match = _ZONE_TEXT_RE.match(message.text.strip())
        if not match:
            return
        zone_num = str(int(match.group(1)))
        zone_name = match.group(2).strip()
        # Check if zone already exists
        zones = entry.options.get(OPTIONS_ZONES, {})
        if zone_num in zones:
            return
        # Add new zone
        new_zone = {
            CONF_ZONE_NAME: f"{zone_num} - {zone_name}",
            CONF_ZONE_TYPE: DEFAULT_ZONE_TYPE,
            CONF_ENTRY_DELAY: DEFAULT_ENTRY_DELAY,
        }
        new_zones = {**zones, zone_num: new_zone}
        _LOGGER.info(
            "Auto-detected zone %s: '%s'. Reloading config entry.", zone_num, zone_name
        )

        def _update_entry():
            hass.config_entries.async_update_entry(
                entry, options={**entry.options, OPTIONS_ZONES: new_zones}
            )

        hass.loop.call_soon_threadsafe(_update_entry)

    # Track RF serials that have been notified
    _notified_rf_serials: set[str] = set()

    def notify_new_rf_sensor(rfx_message):
        """Notify when a new RF sensor is detected."""
        if not rfx_message or not rfx_message.serial_number:
            return

        serial = rfx_message.serial_number

        # Skip if already notified
        if serial in _notified_rf_serials:
            return

        # Check if serial exists in any zone config
        zones = entry.options.get(OPTIONS_ZONES, {})
        for zone_num, zone_config in zones.items():
            if zone_config.get(CONF_ZONE_RFID) == serial:
                return  # Already configured

        # New sensor detected - notify and track
        _notified_rf_serials.add(serial)
        _LOGGER.info(
            "RF Auto-Detect: New sensor detected with serial %s. "
            "Assign manually in zone configuration.",
            serial,
        )

        def _notify():
            persistent_notification.async_create(
                hass,
                title="Sensor RF nuevo detectado",
                message=(
                    f"Se detectó un sensor RF nuevo con serial **{serial}**.\n\n"
                    f"Debes asignarlo manualmente en la configuración de zonas "
                    f"del integration AlarmDecoder."
                ),
                notification_id=f"alarmdecoder_new_rf_{serial}",
            )

        hass.loop.call_soon_threadsafe(_notify)

    # AUI Scan Panel state
    class ScanState:
        """State for AUI panel scanning."""

        scanning = False
        partition_count = 0
        current_zone = 0
        current_partition = 0
        zones: list[dict] = []
        zone_addresses: list[str] = []

    scan_state = ScanState()

    def handle_aui_message_event(sender, message):
        """Handle AUI message from AlarmDecoder device event."""
        raw = str(message) if message else ''
        _LOGGER.debug("AUI Scan: on_aui_message event received: %s", raw[:100])
        
        if not scan_state.scanning:
            return

        if '!AUI:' not in raw:
            return

        # Extract the AUI value
        idx = raw.find('!AUI:')
        if idx == -1:
            return
        value = raw[idx + 5:]  # Remove '!AUI:' prefix
        prefix = _get_aui_prefix(value)

        _LOGGER.debug("AUI Scan: Processing AUI, prefix=%s, value=%s", prefix, value[:60])

        # Parse partition count response (prefix 0c with fefefd)
        if prefix == '0c' and 'fefefd' in value:
            result = _parse_aui_message(prefix, value, 'get_partition_count')
            if result:
                try:
                    scan_state.partition_count = int(result['partition_count'])
                    _LOGGER.info("AUI Scan: Found %d partitions", scan_state.partition_count)
                except (ValueError, TypeError):
                    _LOGGER.warning("AUI Scan: Invalid partition count: %s", result['partition_count'])

        # Parse zone data response (prefix 17 or similar with fefefeec)
        elif 'fefefeec' in value:
            result = _parse_aui_message(prefix, value, 'get_zone_data')
            if result:
                address = result['address']
                if address and address not in scan_state.zone_addresses:
                    zone_name = result['zone_name'] if result['zone_name'] else f"Zone {address}"
                    zone_data = {
                        'address': address,
                        'zone_name': zone_name,
                        'zone_type': result.get('zone_type', ''),
                    }
                    scan_state.zones.append(zone_data)
                    scan_state.zone_addresses.append(address)
                    _LOGGER.info(
                        "AUI Scan: Found zone %s - '%s'",
                        address,
                        zone_name,
                    )

    def _send_aui_command(command: str):
        """Send AUI command to AlarmDecoder."""
        if not entry.runtime_data or not entry.runtime_data.client:
            _LOGGER.warning("AUI Scan: Client not ready yet")
            return
        try:
            # K01| routes through AUI keypad at address 1
            full_command = f'K01|{command}\r\n'
            entry.runtime_data.client.send(full_command)
            _LOGGER.debug("AUI Scan: Sent command: %s", command)
        except Exception as e:
            _LOGGER.error("AUI Scan: Error sending command: %s", e)

    async def scan_panel_zones():
        """Scan panel for zones using AUI commands."""
        if scan_state.scanning:
            _LOGGER.warning("AUI Scan: Already scanning")
            return

        # Check if scan_panel is enabled
        arm_options = entry.options.get(OPTIONS_ARM, DEFAULT_ARM_OPTIONS)
        scan_enabled = arm_options.get(CONF_SCAN_PANEL, DEFAULT_SCAN_PANEL)
        if not scan_enabled:
            return

        scan_state.scanning = True
        scan_state.partition_count = 0
        scan_state.current_zone = 0
        scan_state.current_partition = 0
        scan_state.zones = []
        scan_state.zone_addresses = []

        _LOGGER.info("AUI Scan: Starting panel zone scan")

        try:
            # Step 1: Get partition count
            # Command: 00606b0c4361
            _send_aui_command('00606b0c4361\r\n')
            await hass.async_add_executor_job(time.sleep, 3)

            # If we didn't get partition count, default to 1
            if scan_state.partition_count == 0:
                scan_state.partition_count = 1
                _LOGGER.info("AUI Scan: Defaulting to 1 partition")

            # Step 2: Scan zones for each partition
            for partition_idx in range(scan_state.partition_count):
                partition_hex = _PARTITION_MAP.get(partition_idx, '31')
                _LOGGER.info("AUI Scan: Scanning partition %d (hex: %s)", partition_idx + 1, partition_hex)

                # Scan 48 zones per partition (standard Honeywell limit)
                for zone_num in range(48):
                    if not scan_state.scanning:
                        break

                    zone_hex = _dec_to_hex(zone_num)
                    # Command format: 006f620c4549f5{partition}fb4543f5{zone}fb436c
                    command = f'006f620c4549f5{partition_hex}fb4543f5{zone_hex}fb436c\r\n'
                    _send_aui_command(command)
                    await hass.async_add_executor_job(time.sleep, 1.5)

                if not scan_state.scanning:
                    break

            # Step 3: Create zones in config entry
            if scan_state.zones:
                zones = entry.options.get(OPTIONS_ZONES, {})
                new_zones = {**zones}

                for zone_data in scan_state.zones:
                    zone_num = str(int(zone_data['address']))
                    if zone_num not in new_zones:
                        new_zone = {
                            CONF_ZONE_NAME: f"{zone_num} - {zone_data['zone_name']}",
                            CONF_ZONE_TYPE: DEFAULT_ZONE_TYPE,
                            CONF_ENTRY_DELAY: DEFAULT_ENTRY_DELAY,
                        }
                        new_zones[zone_num] = new_zone
                        _LOGGER.info(
                            "AUI Scan: Adding zone %s - '%s'",
                            zone_num,
                            zone_data['zone_name'],
                        )

                # Update config entry
                def _update_zones():
                    hass.config_entries.async_update_entry(
                        entry, options={**entry.options, OPTIONS_ZONES: new_zones}
                    )

                hass.loop.call_soon_threadsafe(_update_zones)
                _LOGGER.info("AUI Scan: Scan complete. Found %d zones", len(scan_state.zones))
            else:
                _LOGGER.warning("AUI Scan: No zones found")

        except Exception as e:
            _LOGGER.error("AUI Scan: Error during scan: %s", e)
        finally:
            # Auto-uncheck the scan_panel option
            scan_state.scanning = False
            arm_options[CONF_SCAN_PANEL] = False

            def _disable_scan():
                hass.config_entries.async_update_entry(
                    entry, options={**entry.options, OPTIONS_ARM: arm_options}
                )

            hass.loop.call_soon_threadsafe(_disable_scan)
            _LOGGER.info("AUI Scan: Scan panel option disabled")

    baud = ad_connection.get(CONF_DEVICE_BAUD)
    if protocol == PROTOCOL_SOCKET:
        host = ad_connection[CONF_HOST]
        port = ad_connection[CONF_PORT]
        controller = AdExt(SocketDevice(interface=(host, port)))
    elif protocol == PROTOCOL_SERIAL:
        path = ad_connection[CONF_DEVICE_PATH]
        controller = AdExt(SerialDevice(interface=path))
    else:
        _LOGGER.error("Unsupported protocol: %s", protocol)
        return False

    controller.on_message += handle_message
    controller.on_rfx_message += handle_rfx_message
    controller.on_zone_fault += zone_fault_callback
    controller.on_zone_restore += zone_restore_callback
    controller.on_close += handle_closed_connection
    controller.on_expander_message += handle_rel_message

    # Bind AUI message event if available
    if hasattr(controller, 'on_aui_message'):
        controller.on_aui_message += handle_aui_message_event
        _LOGGER.debug("AUI Scan: Bound on_aui_message event handler")

    # Register auto-detect callback
    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_PANEL_MESSAGE, auto_detect_zone)
    )

    # Register RF sensor notification callback
    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_RFX_MESSAGE, notify_new_rf_sensor)
    )

    # Store last known state for notification tracking
    _last_alarm_state: dict[str, str] = {}

    def handle_alarm_state_change(event):
        """Handle state change event for alarm notifications."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if not new_state or not old_state:
            return

        entity_id = new_state.entity_id
        if not entity_id.startswith("alarm_control_panel."):
            return

        new_alarm_state = new_state.state
        old_alarm_state = old_state.state

        # Skip if state didn't change
        if new_alarm_state == old_alarm_state:
            return

        # Get notification settings from config entry
        arm_options = entry.options.get(OPTIONS_ARM, DEFAULT_ARM_OPTIONS)
        notify_arm = arm_options.get(CONF_NOTIFY_ARM, False)
        notify_disarm = arm_options.get(CONF_NOTIFY_DISARM, False)
        notify_trigger = arm_options.get(CONF_NOTIFY_TRIGGER, True)

        # Build notification message based on state change
        message = None
        title = "AlarmDecoder"

        if new_alarm_state == "triggered" and notify_trigger:
            message = f"ALARM TRIGGERED on {entity_id}"
        elif new_alarm_state == "armed_away" and notify_arm:
            message = f"System armed (Away) on {entity_id}"
        elif new_alarm_state == "armed_home" and notify_arm:
            message = f"System armed (Home) on {entity_id}"
        elif new_alarm_state == "disarmed" and notify_disarm:
            message = f"System disarmed on {entity_id}"

        if message:
            _LOGGER.info("Sending notification: %s", message)
            hass.async_create_task(
                hass.services.async_call(
                    "notify",
                    "mobile_app",
                    {
                        "title": title,
                        "message": message,
                    },
                    blocking=False,
                )
            )

    # Register state change listener for notifications
    entry.async_on_unload(
        hass.bus.async_listen("state_changed", handle_alarm_state_change)
    )

    remove_stop_listener = hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP, stop_alarmdecoder
    )

    entry.runtime_data = AlarmDecoderData(
        controller, undo_listener, remove_stop_listener, False
    )

    await open_connection()

    await controller.is_init()

    # Check if scan_panel is enabled and start scan
    arm_options = entry.options.get(OPTIONS_ARM, DEFAULT_ARM_OPTIONS)
    if arm_options.get(CONF_SCAN_PANEL, DEFAULT_SCAN_PANEL):
        _LOGGER.info("AUI Scan: Scan panel option is enabled, starting scan")

        async def _delayed_scan():
            """Wait for connection to be ready before starting scan."""
            # Wait for the connection to be established
            for _ in range(10):
                if entry.runtime_data and entry.runtime_data.client:
                    try:
                        # Test if client is ready
                        entry.runtime_data.client.send("")
                        break
                    except Exception:
                        pass
                await hass.async_add_executor_job(time.sleep, 1)
            await scan_panel_zones()

        hass.async_create_task(_delayed_scan())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: AlarmDecoderConfigEntry
) -> bool:
    """Unload a AlarmDecoder entry."""
    data = entry.runtime_data
    data.restart = False

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if not unload_ok:
        return False

    data.remove_update_listener()
    data.remove_stop_listener()
    await hass.async_add_executor_job(data.client.close)

    return True


async def _update_listener(hass: HomeAssistant, entry: AlarmDecoderConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("AlarmDecoder options updated: %s", entry.as_dict()["options"])
    await hass.config_entries.async_reload(entry.entry_id)
