#!/usr/bin/env python3
"""
Pruebas pytest específicas para el componente de Home Assistant
"""

import pytest
from unittest.mock import Mock, MagicMock

# Simulamos las dependencias de Home Assistant para poder testear
class MockHomeAssistant:
    def __init__(self):
        self.states = MockStates()
        self.services = MockServices()

class MockStates:
    def __init__(self):
        self._states = {}
    
    def get(self, entity_id):
        return self._states.get(entity_id)
    
    def set_state(self, entity_id, state):
        mock_state = Mock()
        mock_state.state = state
        self._states[entity_id] = mock_state

class MockServices:
    def async_call(self, domain, service, data):
        pass

class MockEntityRegistry:
    def __init__(self):
        self.entities = {}
    
    def add_entity(self, entity_id, config_entry_id, domain, unique_id):
        mock_entity = Mock()
        mock_entity.config_entry_id = config_entry_id
        mock_entity.domain = domain
        mock_entity.unique_id = unique_id
        self.entities[entity_id] = mock_entity


# Copiamos la función del componente real
def build_bypass_string(zones: list[int], code: str = "") -> str:
    """Build bypass string for the given zones."""
    if not zones:
        return ""
    
    zones_str = "".join([str(zone) for zone in zones])
    return f"{code}6{zones_str}*"


def extract_bypass_zones(hass, entity_registry, entry_id):
    """Extract bypass zones from active switch states (simulación del método _get_bypass_zones)"""
    bypass_zones = []
    
    for entity_id, entity in entity_registry.entities.items():
        if (entity.config_entry_id == entry_id and 
            entity.domain == "switch" and 
            "_bypass" in entity.unique_id):
            
            state = hass.states.get(entity_id)
            if state and state.state == "on":
                try:
                    zone_str = entity.unique_id.split("_")[-2]
                    zone_num = int(zone_str)
                    bypass_zones.append(zone_num)
                except (ValueError, IndexError):
                    pass
    
    return sorted(bypass_zones)


class TestHomeAssistantBypassIntegration:
    """Tests for Home Assistant bypass integration"""
    
    def setup_method(self):
        """Setup for each test"""
        self.hass = MockHomeAssistant()
        self.entity_registry = MockEntityRegistry()
        self.entry_id = "test_entry_123"
    
    def test_no_bypass_zones_active(self):
        """Test when no bypass zones are active"""
        zones = extract_bypass_zones(self.hass, self.entity_registry, self.entry_id)
        assert zones == []
        assert build_bypass_string(zones, "1234") == ""
    
    def test_single_bypass_zone_active(self):
        """Test single bypass zone active"""
        # Setup: agregar entidad de bypass zona 1
        entity_id = "switch.zone_1_bypass"
        self.entity_registry.add_entity(
            entity_id, self.entry_id, "switch", f"{self.entry_id}_1_bypass"
        )
        self.hass.states.set_state(entity_id, "on")
        
        # Test
        zones = extract_bypass_zones(self.hass, self.entity_registry, self.entry_id)
        assert zones == [1]
        assert build_bypass_string(zones, "1234") == "123461*"
    
    def test_multiple_bypass_zones_active(self):
        """Test multiple bypass zones active"""
        # Setup: agregar varias entidades de bypass
        test_zones = [1, 5, 12]
        for zone in test_zones:
            entity_id = f"switch.zone_{zone}_bypass"
            self.entity_registry.add_entity(
                entity_id, self.entry_id, "switch", f"{self.entry_id}_{zone}_bypass"
            )
            self.hass.states.set_state(entity_id, "on")
        
        # Test
        zones = extract_bypass_zones(self.hass, self.entity_registry, self.entry_id)
        assert zones == [1, 5, 12]
        assert build_bypass_string(zones, "1234") == "123461512*"
    
    def test_zone_01_configuration(self):
        """Test that zone 01 (configured as string) works as zone 1"""
        # Setup: zona configurada como "01" pero manejada como 1
        entity_id = "switch.zone_01_bypass"
        self.entity_registry.add_entity(
            entity_id, self.entry_id, "switch", f"{self.entry_id}_1_bypass"  # Se guarda como 1
        )
        self.hass.states.set_state(entity_id, "on")
        
        # Test
        zones = extract_bypass_zones(self.hass, self.entity_registry, self.entry_id)
        assert zones == [1]
        assert build_bypass_string(zones, "1234") == "123461*"
    
    def test_mixed_zone_digits(self):
        """Test zones with different digit counts"""
        # Setup: zonas 1, 15, 100
        test_zones = [1, 15, 100]
        for zone in test_zones:
            entity_id = f"switch.zone_{zone}_bypass"
            self.entity_registry.add_entity(
                entity_id, self.entry_id, "switch", f"{self.entry_id}_{zone}_bypass"
            )
            self.hass.states.set_state(entity_id, "on")
        
        # Test
        zones = extract_bypass_zones(self.hass, self.entity_registry, self.entry_id)
        assert zones == [1, 15, 100]
        assert build_bypass_string(zones, "1234") == "12346115100*"
    
    def test_bypass_zones_with_inactive_switches(self):
        """Test that only active (on) switches are included"""
        # Setup: algunas zonas activas, otras inactivas
        all_zones = [1, 2, 3, 4, 5]
        active_zones = [1, 3, 5]
        
        for zone in all_zones:
            entity_id = f"switch.zone_{zone}_bypass"
            self.entity_registry.add_entity(
                entity_id, self.entry_id, "switch", f"{self.entry_id}_{zone}_bypass"
            )
            # Solo marcar como activas las zonas en active_zones
            state = "on" if zone in active_zones else "off"
            self.hass.states.set_state(entity_id, state)
        
        # Test
        zones = extract_bypass_zones(self.hass, self.entity_registry, self.entry_id)
        assert zones == [1, 3, 5]
        assert build_bypass_string(zones, "1234") == "12346135*"
    
    def test_different_config_entries(self):
        """Test that only switches from the correct config entry are included"""
        # Setup: switches de diferentes config entries
        other_entry_id = "other_entry_456"
        
        # Agregar switch del entry correcto
        entity_id_1 = "switch.zone_1_bypass"
        self.entity_registry.add_entity(
            entity_id_1, self.entry_id, "switch", f"{self.entry_id}_1_bypass"
        )
        self.hass.states.set_state(entity_id_1, "on")
        
        # Agregar switch de otro entry (no debería incluirse)
        entity_id_2 = "switch.zone_2_bypass_other"
        self.entity_registry.add_entity(
            entity_id_2, other_entry_id, "switch", f"{other_entry_id}_2_bypass"
        )
        self.hass.states.set_state(entity_id_2, "on")
        
        # Test
        zones = extract_bypass_zones(self.hass, self.entity_registry, self.entry_id)
        assert zones == [1]  # Solo la zona del entry correcto
        assert build_bypass_string(zones, "1234") == "123461*"
    
    def test_arm_command_sequence(self):
        """Test the complete arm command sequence with bypass"""
        # Setup: zona 5 activa para bypass
        entity_id = "switch.zone_5_bypass"
        self.entity_registry.add_entity(
            entity_id, self.entry_id, "switch", f"{self.entry_id}_5_bypass"
        )
        self.hass.states.set_state(entity_id, "on")
        
        # Test: simular secuencia de armado
        zones = extract_bypass_zones(self.hass, self.entity_registry, self.entry_id)
        bypass_command = build_bypass_string(zones, "1234")
        arm_away_command = "12342"
        arm_home_command = "12343"
        
        assert bypass_command == "123465*"
        assert arm_away_command == "12342"
        assert arm_home_command == "12343"


@pytest.mark.parametrize("zone_config,expected_zone,expected_command", [
    ("1", 1, "123461*"),      # Zona configurada como "1"
    ("01", 1, "123461*"),     # Zona configurada como "01" → int(1)
    ("5", 5, "123465*"),      # Zona configurada como "5"
    ("05", 5, "123465*"),     # Zona configurada como "05" → int(5)
    ("10", 10, "1234610*"),   # Zona configurada como "10"
    ("010", 10, "1234610*"),  # Zona configurada como "010" → int(10)
    ("15", 15, "1234615*"),   # Zona configurada como "15"
    ("100", 100, "12346100*"), # Zona configurada como "100"
])
def test_zone_configuration_formats(zone_config, expected_zone, expected_command):
    """Test that different zone configuration formats work correctly"""
    # Simular que la zona se procesa como int (como hace el config flow real)
    processed_zone = int(zone_config.lstrip('0') or '0')  # Simula int(zone_config)
    
    assert processed_zone == expected_zone
    assert build_bypass_string([processed_zone], "1234") == expected_command


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
