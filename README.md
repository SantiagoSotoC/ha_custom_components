# AlarmDecoder Custom Integration for Home Assistant

This is a custom component for integrating AlarmDecoder with Home Assistant, allowing support for multiple alarm panels (keypads) based on their address.

🛠️ This is a **modified version** of the official Home Assistant AlarmDecoder integration that now uses **YAML configuration** instead of UI configuration.

---

## Installation and Configuration

### YAML Configuration

This integration is now configured via YAML in your `configuration.yaml` file. Add the following configuration:

```yaml
custom_alarmdecoder:
  protocol: socket # or "serial"
  host: 192.168.1.100 # for socket protocol
  port: 10000 # for socket protocol
  # device_path: /dev/ttyUSB0  # for serial protocol
  # device_baudrate: 115200  # for serial protocol
  auto_bypass: false
  code_arm_required: true
  keypads: [0, 1] # List of keypad addresses
  zones:
    1:
      name: "Front Door"
      type: "door"
      bypassable: true
    2:
      name: "Back Door"
      type: "door"
      bypassable: true
    3:
      name: "Living Room Motion"
      type: "motion"
      bypassable: true
      rfid: 1
      loop: 1
    10:
      name: "Kitchen Window"
      type: "window"
      bypassable: false
```

### Configuration Options

#### Main Configuration

- **protocol**: `socket` or `serial`
- **host**: IP address (required for socket protocol)
- **port**: Port number (required for socket protocol)
- **device_path**: Serial device path (required for serial protocol)
- **device_baudrate**: Baud rate (optional for serial protocol, default: 115200)
- **auto_bypass**: Enable automatic bypass of faulted zones (default: false)
- **code_arm_required**: Require code for arming (default: true)
- **keypads**: List of keypad addresses (default: [0])

#### Zone Configuration

Each zone is defined by its number (1-999) and can have the following properties:

- **name**: Display name for the zone (required)
- **type**: Zone type (optional, default: "window")
  - Available types: `door`, `window`, `motion`, `smoke`, `glass`, `co`, `flood`, `gas`, `heat`, `medical`, `freeze`, `generic`
- **bypassable**: Whether the zone can be bypassed (optional, default: false)
- **rfid**: RFID address (optional)
- **loop**: Loop number (optional)

### Basic Setup

After adding the YAML configuration:

1. Restart Home Assistant
2. Go to **Settings** → **Devices & Services**
3. Click **Add Integration**
4. Search for **AlarmDecoder**
5. Follow the setup wizard to configure basic connection settings

The zones and advanced settings will be read from your YAML configuration.

---

## Status

✅ **Functional** – This integration is currently **working** with YAML configuration.

### Current Limitations

- **Single partition support only**: Currently supports one partition (default partition)
- **Default partition messages**: All alarm messages are sent from the default partition address

### Compatibility

⚠️ **Honeywell Panels Only** – This version has been **tested only with Honeywell panels** and specifically with a **Honeywell Vista 48LA** panel. DSC panel compatibility has not been tested and may not work correctly.

**Tested Hardware:**

- ✅ **Honeywell Vista 48LA** (Fully tested and working)
- ❓ **DSC Panels** (Not tested - compatibility unknown)

---

## Current Features

### ✅ Zone Bypass System

- **Individual bypass switches**: Each configurable zone has its own Home Assistant switch entity
- **Manual bypass control**: Toggle bypass status for individual zones from the UI
- **Automatic bypass commands**: System sends proper bypass commands when arming
- **Auto-bypass support**: Automatic bypass of zones with faults during arming
- **Bypass command format**: `code + 6 + zones + *` for manual bypass, `code + 6 + #` for auto-bypass

### ✅ Alarm Control

- **Arm Away/Home**: Full support with bypass integration
- **Disarm**: Standard disarm functionality
- **Custom keypresses**: Send custom commands to the alarm panel
- **Toggle chime**: Control panel chime settings

### ✅ Configuration

- **Zone configuration**: Add, edit, and remove zones through the UI
- **Bypass settings**: Configure which zones support bypass
- **Zone types**: Support for different zone types (door/window, motion, etc.)
- **Multi-language support**: Full Spanish and English translations

### ✅ Zone Management

- **Zone numbering**: Supports zones 1-999 without leading zeros
- **Zone deletion**: Proper zone removal handling
- **Zone editing**: Edit existing zone configurations

---

## Hardware Requirements

### Supported Panels

- **Honeywell Vista Series**: ✅ Tested and working
  - **Vista 48LA**: ✅ Fully tested
  - **Other Vista models**: Likely compatible but not specifically tested

### Unsupported/Untested Panels

- **DSC Panels**: ❓ Not tested - may require command format modifications
- **Other manufacturers**: ❓ Unknown compatibility

### AlarmDecoder Hardware

- Any AlarmDecoder device (AD2USB, AD2Serial, AD2PI, etc.)
- Connected to a compatible Honeywell panel

---

## Planned Features (Future Releases)

- **Multi-partition support**: Support for multiple alarm partitions
- **Partition-specific messages**: Messages routed to specific partition addresses
- **Advanced keypad handling**: Full multi-keypad address support
- **DSC panel support**: Testing and compatibility for DSC panels

---

## Configuration

### Basic Setup

1. Go to Settings > Devices & Services
2. Click "Add Integration" and search for "AlarmDecoder"
3. Configure your AlarmDecoder connection details
4. Set up zones and their bypass capabilities

### Zone Bypass Configuration

1. In the integration options, select "Configure Zones"
2. For each zone:
   - Enter zone name and type
   - Enable "Allow Bypass" for zones you want to control
   - Configure zone-specific settings (RFID loop, relay settings, etc.)

### Usage Examples

#### Manual Zone Bypass

```yaml
# Example: Bypass zone 1 and 5, then arm away
service: switch.turn_on
target:
  entity_id:
    - switch.zone_1_bypass
    - switch.zone_5_bypass

# Then arm the system - bypasses will be applied automatically
service: alarm_control_panel.alarm_arm_away
target:
  entity_id: alarm_control_panel.alarmdecoder
data:
  code: "1234"
```

#### Auto-Bypass

Enable "Auto-bypass on arm" in the integration options to automatically bypass zones with faults when arming.

---

## Command Reference

### Bypass Commands (Honeywell Format)

- **Manual bypass**: `code + 6 + zones + *` (e.g., `123461520*` for zones 1, 5, 20)
- **Auto bypass**: `code + 6 + #` (e.g., `12346#` for automatic fault bypass)

### Arm Commands (Honeywell Format)

- **Arm Away**: `code + 2` (e.g., `12342`)
- **Arm Home**: `code + 3` (e.g., `12343`)
- **Disarm**: `code + 1` (e.g., `12341`)

**Note**: These command formats are specific to Honeywell panels. DSC panels may use different command sequences.

---

## Troubleshooting

### Panel Compatibility Issues

If you're using a DSC panel and commands aren't working:

1. Check your panel's manual for the correct bypass command format
2. Consider contributing DSC support by testing and reporting command formats

### Zone Deletion Issues

If you cannot delete a zone (e.g., zone 9 vs 09 formatting):

1. Try entering the zone number without leading zeros
2. Clear the zone name field completely to delete the zone

### RFID Loop Configuration

If you encounter type errors when editing zones with RFID loops:

1. Clear the RFID loop field
2. Re-enter the value
3. Save the configuration

---

## Contributing

Contributions and suggestions are welcome. This project is maintained independently and not officially supported by the Home Assistant team.

### Especially Needed

- **DSC Panel Testing**: If you have a DSC panel, testing and feedback would be greatly appreciated
- **Other Honeywell Models**: Testing with other Vista models would help expand compatibility

### Development Status

- **Zone bypass system**: ✅ Complete (Honeywell)
- **Single partition support**: ✅ Complete (Honeywell)
- **Multi-language support**: ✅ Complete
- **Multi-partition support**: 🔄 Planned
- **DSC panel support**: 🔄 Needs testing
- **Advanced keypad handling**: 🔄 Planned

---

## License

This project is open source and licensed under the **Apache License 2.0**, same as Home Assistant.

---

## Changelog

### Current Version

- ✅ Functional zone bypass system (Honeywell panels)
- ✅ Individual zone control switches
- ✅ Auto-bypass support for faulted zones
- ✅ Full Spanish/English translations
- ✅ Proper zone number formatting (no leading zeros)
- ✅ Configuration UI improvements
- ✅ Tested and working with Honeywell Vista 48LA
- ⚠️ Single partition support only (default partition)
- ⚠️ Honeywell panels only (DSC not tested)

### Known Issues

- Zone deletion may require entering numbers without leading zeros
- RFID loop editing may require field clearing/re-entry
- Multi-partition support not yet implemented
- DSC panel compatibility unknown

---

## Disclaimer

This integration has been developed and tested specifically with Honeywell Vista panels. While it may work with other panel types, compatibility is not guaranteed. Use at your own risk and always test thoroughly in a safe environment before deploying in production.
