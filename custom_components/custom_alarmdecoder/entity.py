"""Support for AlarmDecoder-based alarm control panels entity."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class AlarmDecoderEntity(Entity):
    """Define a base AlarmDecoder entity."""

    _attr_has_entity_name = True

    def __init__(self, client, device_name=None, device_identifier=None):
        """Initialize the alarm decoder entity."""
        self._client = client
        
        # If device_name and device_identifier are provided, create a sub-device
        if device_name and device_identifier:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, device_identifier)},
                name=device_name,
                manufacturer="NuTech",
                model="Zone",
                via_device=(DOMAIN, client.serial_number),
            )
        else:
            # Main device (alarm panel)
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, client.serial_number)},
                name="AlarmDecoder Panel",
                manufacturer="NuTech",
                model="AlarmDecoder",
                serial_number=client.serial_number,
                sw_version=client.version_number,
            )
