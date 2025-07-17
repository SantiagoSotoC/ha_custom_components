# AlarmDecoder Custom Integration for Home Assistant

This is a custom component for integrating AlarmDecoder with Home Assistant, allowing support for multiple alarm panels (keypads) based on their address.

🛠️ This is a **modified version** of the official Home Assistant AlarmDecoder integration that now uses **YAML configuration** instead of UI configuration.

---

## Installation and Configuration

## Configuration Examples

### Basic Socket Configuration

```yaml
custom_alarmdecoder:
  protocol: socket
  host: 192.168.1.100
  port: 10000
  auto_bypass: false
  code_arm_required: true
  keypads: [0]
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
```

### Serial Configuration

```yaml
custom_alarmdecoder:
  protocol: serial
  device_path: /dev/ttyUSB0
  device_baudrate: 115200
  auto_bypass: false
  code_arm_required: true
  keypads: [0]
  zones:
    1:
      name: "Main Entrance"
      type: "door"
      bypassable: true
```

### Advanced Configuration with RF Devices

```yaml
custom_alarmdecoder:
  protocol: socket
  host: 192.168.1.100
  port: 10000
  auto_bypass: true # Automatically bypass faulted zones
  code_arm_required: false # No code required for arming
  keypads: [0, 16, 17] # Multiple keypads
  zones:
    # Wired zones
    1:
      name: "Front Door"
      type: "door"
      bypassable: true
    2:
      name: "Back Door"
      type: "door"
      bypassable: true
    3:
      name: "Garage Door"
      type: "door"
      bypassable: true

    # RF devices with RFID and loop
    10:
      name: "Living Room Motion"
      type: "motion"
      bypassable: true
      rfid: 0123456 # RF device serial number
      loop: 1 # Specific loop to monitor

    11:
      name: "Kitchen Smoke Detector"
      type: "smoke"
      bypassable: false # Safety device - cannot bypass
      rfid: 0987654
      loop: 1

    12:
      name: "Bedroom Window"
      type: "window"
      bypassable: true
      rfid: 1122334
      loop: 2

    # Glass break detector
    15:
      name: "Patio Glass Break"
      type: "glass"
      bypassable: true
      rfid: 5566778
      loop: 1

    # Environmental sensors
    20:
      name: "Basement Flood Sensor"
      type: "flood"
      bypassable: false
      rfid: 9988776
      loop: 1

    21:
      name: "CO Detector Kitchen"
      type: "co"
      bypassable: false
      rfid: 1357924
      loop: 1
```

### Home Security System Configuration

```yaml
custom_alarmdecoder:
  protocol: socket
  host: 192.168.1.50
  port: 10000
  auto_bypass: false
  code_arm_required: true
  keypads: [0, 16] # Main panel + wireless keypad
  zones:
    # Entry points
    1:
      name: "Front Door"
      type: "door"
      bypassable: true
    2:
      name: "Back Door"
      type: "door"
      bypassable: true
    3:
      name: "Garage Side Door"
      type: "door"
      bypassable: true

    # Windows
    10:
      name: "Living Room Window"
      type: "window"
      bypassable: true
    11:
      name: "Kitchen Window"
      type: "window"
      bypassable: true
    12:
      name: "Master Bedroom Window"
      type: "window"
      bypassable: true

    # Motion detectors
    20:
      name: "Hallway Motion"
      type: "motion"
      bypassable: true
      rfid: 1111111
      loop: 1
    21:
      name: "Living Room Motion"
      type: "motion"
      bypassable: true
      rfid: 2222222
      loop: 1

    # Safety devices (non-bypassable)
    30:
      name: "Smoke Detector"
      type: "smoke"
      bypassable: false
      rfid: 3333333
      loop: 1
    31:
      name: "CO Detector"
      type: "co"
      bypassable: false
      rfid: 4444444
      loop: 1
```

### Small Apartment Configuration

```yaml
custom_alarmdecoder:
  protocol: socket
  host: 192.168.1.100
  port: 10000
  auto_bypass: true
  code_arm_required: false
  keypads: [0]
  zones:
    1:
      name: "Apartment Door"
      type: "door"
      bypassable: true
    2:
      name: "Balcony Door"
      type: "door"
      bypassable: true
    3:
      name: "Motion Detector"
      type: "motion"
      bypassable: true
      rfid: 1234567
      loop: 1
```

### Business/Office Configuration

```yaml
custom_alarmdecoder:
  protocol: socket
  host: 192.168.100.50
  port: 10000
  auto_bypass: false
  code_arm_required: true
  keypads: [0, 16, 17, 18] # Multiple zones/areas
  zones:
    # Main entrance
    1:
      name: "Main Entrance"
      type: "door"
      bypassable: false # Main entrance cannot be bypassed

    # Secondary entrances
    2:
      name: "Back Entrance"
      type: "door"
      bypassable: true
    3:
      name: "Emergency Exit"
      type: "door"
      bypassable: true

    # Office areas
    10:
      name: "Reception Motion"
      type: "motion"
      bypassable: true
      rfid: 1001001
      loop: 1
    11:
      name: "Office Area Motion"
      type: "motion"
      bypassable: true
      rfid: 1001002
      loop: 1

    # Server room (high security)
    20:
      name: "Server Room Door"
      type: "door"
      bypassable: false
    21:
      name: "Server Room Motion"
      type: "motion"
      bypassable: false
      rfid: 2002002
      loop: 1

    # Safety systems
    30:
      name: "Fire Detection"
      type: "smoke"
      bypassable: false
      rfid: 3003003
      loop: 1
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

## Configuration Reference

### Protocol Options

#### Socket Protocol (TCP/IP)

```yaml
custom_alarmdecoder:
  protocol: socket
  host: 192.168.1.100 # IP address of AlarmDecoder device
  port: 10000 # Port number (default: 10000)
```

#### Serial Protocol (USB/RS232)

```yaml
custom_alarmdecoder:
  protocol: serial
  device_path: /dev/ttyUSB0 # Serial device path
  device_baudrate: 115200 # Baud rate (default: 115200)
```

### Advanced Options

#### Auto Bypass

- `auto_bypass: true` - Automatically bypass faulted zones when arming
- `auto_bypass: false` - Require manual bypass of faulted zones (default)

#### Code Requirements

- `code_arm_required: true` - Require alarm code for arming (default)
- `code_arm_required: false` - Allow arming without code

#### Multiple Keypads

```yaml
keypads: [0]          # Single keypad (default)
keypads: [0, 16, 17]  # Multiple keypads by address
```

Common keypad addresses:

- `0` - Main panel
- `16-31` - Wireless keypads (6160RF, 6150RF)
- `1-8` - Hardwired keypads

### Zone Types and Usage

#### Entry/Exit Zones

```yaml
zones:
  1:
    name: "Front Door"
    type: "door" # Entry/exit delay
    bypassable: true
```

#### Perimeter Protection

```yaml
zones:
  10:
    name: "Living Room Window"
    type: "window" # Instant alarm
    bypassable: true
  15:
    name: "Patio Glass"
    type: "glass" # Glass break detection
    bypassable: true
```

#### Interior Protection

```yaml
zones:
  20:
    name: "Hallway Motion"
    type: "motion" # Motion detection
    bypassable: true
```

#### Safety Devices (Non-Bypassable)

```yaml
zones:
  30:
    name: "Smoke Detector"
    type: "smoke" # Fire detection
    bypassable: false # Cannot be bypassed for safety
  31:
    name: "CO Detector"
    type: "co" # Carbon monoxide
    bypassable: false
  32:
    name: "Flood Sensor"
    type: "flood" # Water detection
    bypassable: false
```

#### Specialized Zones

```yaml
zones:
  40:
    name: "Panic Button"
    type: "medical" # Medical emergency
    bypassable: false
  41:
    name: "High Temp Sensor"
    type: "heat" # Heat detection
    bypassable: false
  42:
    name: "Freeze Sensor"
    type: "freeze" # Low temperature
    bypassable: false
  43:
    name: "Gas Detector"
    type: "gas" # Gas leak detection
    bypassable: false
```

### RF Device Configuration

#### Basic RF Zone

```yaml
zones:
  50:
    name: "Wireless Motion"
    type: "motion"
    bypassable: true
    rfid: 1234567 # 7-digit RF device serial number
    loop: 1 # Loop number (1-4)
```

#### Multi-Loop RF Device

```yaml
zones:
  51:
    name: "4-Zone RF Receiver"
    type: "generic"
    bypassable: true
    rfid: 9876543
    loop: 1 # Monitor only loop 1
  52:
    name: "Same Device Loop 2"
    type: "motion"
    bypassable: true
    rfid: 9876543 # Same device
    loop: 2 # Different loop
```

#### RF Device with Supervision

```yaml
zones:
  55:
    name: "Supervised Motion"
    type: "motion"
    bypassable: true
    rfid: 5555555
    loop: 1
    # Device will report battery status and supervision
```

### Real-World Examples

#### Typical Home Setup

- **Zones 1-9**: Doors and main entry points
- **Zones 10-19**: Windows and perimeter
- **Zones 20-29**: Interior motion detectors
- **Zones 30-39**: Safety devices (smoke, CO)
- **Zones 40+**: RF devices and specialized sensors

#### Zone Numbering Best Practices

```yaml
zones:
  # Entry points (1-9)
  1: { name: "Front Door", type: "door", bypassable: true }
  2: { name: "Back Door", type: "door", bypassable: true }
  3: { name: "Garage Door", type: "door", bypassable: true }

  # Windows (10-19)
  10: { name: "Living Room Window", type: "window", bypassable: true }
  11: { name: "Kitchen Window", type: "window", bypassable: true }

  # Motion detectors (20-29)
  20: { name: "Hallway Motion", type: "motion", bypassable: true }
  21: { name: "Living Room Motion", type: "motion", bypassable: true }

  # Safety devices (30-39)
  30: { name: "Smoke Detector", type: "smoke", bypassable: false }
  31: { name: "CO Detector", type: "co", bypassable: false }

  # RF devices (40+)
  40:
    {
      name: "Wireless Motion",
      type: "motion",
      bypassable: true,
      rfid: 1234567,
      loop: 1,
    }
```
