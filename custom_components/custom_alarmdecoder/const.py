"""Constants for the AlarmDecoder component."""

CONF_ALARM_CODE = "alarm_code"
CONF_AUTO_BYPASS = "auto_bypass"
CONF_AUTO_DETECT_ZONES = "auto_detect_zones"
CONF_SCAN_PANEL = "scan_panel"
CONF_CODE_ARM_REQUIRED = "code_arm_required"
CONF_DEVICE_BAUD = "device_baudrate"
CONF_DEVICE_PATH = "device_path"
CONF_ENTRY_DELAY = "entry_delay"
CONF_RELAY_ADDR = "zone_relayaddr"
CONF_RELAY_CHAN = "zone_relaychan"
CONF_ZONE_LOOP = "zone_loop"
CONF_ZONE_NAME = "zone_name"
CONF_ZONE_NUMBER = "zone_number"
CONF_ZONE_RFID = "zone_rfid"
CONF_ZONE_TYPE = "zone_type"

DEFAULT_AUTO_BYPASS = False
DEFAULT_AUTO_DETECT_ZONES = False
DEFAULT_SCAN_PANEL = False
DEFAULT_CODE_ARM_REQUIRED = True
DEFAULT_DEVICE_BAUD = 115200
DEFAULT_DEVICE_HOST = "alarmdecoder"
DEFAULT_DEVICE_PATH = "/dev/ttyUSB0"
DEFAULT_DEVICE_PORT = 10000
DEFAULT_ENTRY_DELAY = True
DEFAULT_ZONE_TYPE = "window"
CONF_KEYPADS = "keypads"


DEFAULT_ARM_OPTIONS = {
    CONF_ALARM_CODE: "",
    CONF_AUTO_BYPASS: DEFAULT_AUTO_BYPASS,
    CONF_AUTO_DETECT_ZONES: DEFAULT_AUTO_DETECT_ZONES,
    CONF_CODE_ARM_REQUIRED: DEFAULT_CODE_ARM_REQUIRED,
    CONF_SCAN_PANEL: DEFAULT_SCAN_PANEL,
}
DEFAULT_ZONE_OPTIONS: dict = {}

DOMAIN = "custom_alarmdecoder"

OPTIONS_ARM = "arm_options"
OPTIONS_KEYPADS = "keypad_options"
OPTIONS_ZONES = "zone_options"

PROTOCOL_SERIAL = "serial"
PROTOCOL_SOCKET = "socket"

SIGNAL_PANEL_MESSAGE = "alarmdecoder.panel_message"
SIGNAL_REL_MESSAGE = "alarmdecoder.rel_message"
SIGNAL_RFX_MESSAGE = "alarmdecoder.rfx_message"
SIGNAL_AUI_MESSAGE = "alarmdecoder.aui_message"
SIGNAL_ZONE_FAULT = "alarmdecoder.zone_fault"
SIGNAL_ZONE_RESTORE = "alarmdecoder.zone_restore"

CONF_BYPASSABLE = "bypassable"
