# AlarmDecoder Custom Integration for Home Assistant

This is a custom component for integrating AlarmDecoder with Home Assistant, allowing support for multiple alarm panels (keypads) based on their address.

🛠️ This is a **modified version** of the official Home Assistant AlarmDecoder integration, intended to support additional features such as multi-keypad handling and automatic zone bypass.

---

## Status

⚠️ **Under development** – This integration is currently **not functional** and still a work in progress.

---

## Planned Features

- Support for multiple alarm panels (keypads).
- Message filtering per panel based on keypad address.
- Custom services for alarm control.
- Full integration with Home Assistant.

---

## Upcoming Features

### Zone Bypass

This integration will support automatic bypassing by creating individual entities for each configurable zone.

- Each bypassable zone will have its own Home Assistant entity (e.g., `switch`).
- These entities will allow manual toggle of bypass status from the UI.
- The integration will send the corresponding bypass commands to the panel on arming.
- When arming the system, active bypass settings will be respected automatically.
- The configuration flow will allow selecting which zones support bypass.

This enables a more dynamic and user-friendly way to manage zone bypasses in Home Assistant.

---

## Installation

There is no installable release yet. Installation instructions or packages will be provided soon.

---

## Usage

- Configure the keypad addresses through the configuration UI.
- Add the integration via Home Assistant.
- Each keypad will appear as a separate alarm control panel entity.

---

## Contributing

Contributions and suggestions are welcome. This project is maintained independently and not officially supported by the Home Assistant team.

---

## License

This project is open source and licensed under the **Apache License 2.0**, same as Home Assistant.
