#!/usr/bin/env python3
"""
Pruebas pytest para verificar las traducciones del componente AlarmDecoder
"""

import json
import pytest
from pathlib import Path


class TestTranslations:
    """Test cases for translation files"""
    
    def setup_method(self):
        """Setup for each test"""
        self.component_path = Path("custom_components/custom_alarmdecoder")
        self.strings_file = self.component_path / "strings.json"
        self.en_file = self.component_path / "translations" / "en.json"
        self.es_file = self.component_path / "translations" / "es.json"
    
    def test_json_files_are_valid(self):
        """Test that all JSON files have valid syntax"""
        # Test strings.json
        with open(self.strings_file, 'r', encoding='utf-8') as f:
            strings_data = json.load(f)
        assert isinstance(strings_data, dict)
        
        # Test en.json
        with open(self.en_file, 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        assert isinstance(en_data, dict)
        
        # Test es.json
        with open(self.es_file, 'r', encoding='utf-8') as f:
            es_data = json.load(f)
        assert isinstance(es_data, dict)
    
    def test_translation_keys_match(self):
        """Test that English and Spanish translations have the same keys"""
        with open(self.en_file, 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        
        with open(self.es_file, 'r', encoding='utf-8') as f:
            es_data = json.load(f)
        
        # Función para obtener todas las claves de forma recursiva
        def get_all_keys(d, prefix=""):
            keys = set()
            for key, value in d.items():
                current_key = f"{prefix}.{key}" if prefix else key
                keys.add(current_key)
                if isinstance(value, dict):
                    keys.update(get_all_keys(value, current_key))
            return keys
        
        en_keys = get_all_keys(en_data)
        es_keys = get_all_keys(es_data)
        
        # Verificar que tienen las mismas claves
        missing_in_spanish = en_keys - es_keys
        missing_in_english = es_keys - en_keys
        
        assert not missing_in_spanish, f"Keys missing in Spanish translation: {missing_in_spanish}"
        assert not missing_in_english, f"Keys missing in English translation: {missing_in_english}"
    
    def test_zone_number_interpolation(self):
        """Test that zone number interpolation works in translations"""
        with open(self.en_file, 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        
        with open(self.es_file, 'r', encoding='utf-8') as f:
            es_data = json.load(f)
        
        # Verificar interpolación en entity.switch.zone_bypass.name
        en_zone_name = en_data["entity"]["switch"]["zone_bypass"]["name"]
        es_zone_name = es_data["entity"]["switch"]["zone_bypass"]["name"]
        
        assert "{zone_number}" in en_zone_name
        assert "{zone_number}" in es_zone_name
        
        # Probar interpolación
        test_zone = "5"
        en_formatted = en_zone_name.format(zone_number=test_zone)
        es_formatted = es_zone_name.format(zone_number=test_zone)
        
        assert en_formatted == "Zone 5 Bypass"
        assert es_formatted == "Bypass Zona 5"
    
    def test_zone_details_interpolation(self):
        """Test zone details description interpolation"""
        with open(self.en_file, 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        
        with open(self.es_file, 'r', encoding='utf-8') as f:
            es_data = json.load(f)
        
        en_desc = en_data["options"]["step"]["zone_details"]["description"]
        es_desc = es_data["options"]["step"]["zone_details"]["description"]
        
        # Verificar que contienen la variable de interpolación
        assert "{zone_number}" in en_desc
        assert "{zone_number}" in es_desc
        
        # Probar interpolación
        test_zone = "10"
        en_formatted = en_desc.format(zone_number=test_zone)
        es_formatted = es_desc.format(zone_number=test_zone)
        
        assert "zone 10" in en_formatted.lower()
        assert "zona 10" in es_formatted.lower()
    
    def test_required_sections_exist(self):
        """Test that all required sections exist in both translations"""
        required_sections = [
            "config",
            "options", 
            "services",
            "entity"
        ]
        
        with open(self.en_file, 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        
        with open(self.es_file, 'r', encoding='utf-8') as f:
            es_data = json.load(f)
        
        for section in required_sections:
            assert section in en_data, f"Section '{section}' missing in English translation"
            assert section in es_data, f"Section '{section}' missing in Spanish translation"
    
    def test_bypass_specific_translations(self):
        """Test bypass-specific translation elements"""
        with open(self.en_file, 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        
        with open(self.es_file, 'r', encoding='utf-8') as f:
            es_data = json.load(f)
        
        # Verificar traducciones específicas de bypass
        en_bypassable = en_data["options"]["step"]["zone_details"]["data"]["bypassable"]
        es_bypassable = es_data["options"]["step"]["zone_details"]["data"]["bypassable"]
        
        assert en_bypassable == "Allow Bypass"
        assert es_bypassable == "Permitir Bypass"
        
        # Verificar auto_bypass
        en_auto_bypass = en_data["options"]["step"]["arm_settings"]["data"]["auto_bypass"]
        es_auto_bypass = es_data["options"]["step"]["arm_settings"]["data"]["auto_bypass"]
        
        assert "bypass" in en_auto_bypass.lower()
        assert "bypass" in es_auto_bypass.lower()
    
    def test_service_translations(self):
        """Test service name and description translations"""
        with open(self.en_file, 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        
        with open(self.es_file, 'r', encoding='utf-8') as f:
            es_data = json.load(f)
        
        # Verificar servicios
        services = ["alarm_keypress", "alarm_toggle_chime"]
        
        for service in services:
            assert service in en_data["services"]
            assert service in es_data["services"]
            
            # Verificar que tienen name y description
            assert "name" in en_data["services"][service]
            assert "name" in es_data["services"][service]
            assert "description" in en_data["services"][service]
            assert "description" in es_data["services"][service]
            
            # Verificar que las traducciones no están vacías
            assert len(en_data["services"][service]["name"]) > 0
            assert len(es_data["services"][service]["name"]) > 0
            assert len(en_data["services"][service]["description"]) > 0
            assert len(es_data["services"][service]["description"]) > 0
    
    def test_error_messages_translated(self):
        """Test that error messages are properly translated"""
        with open(self.en_file, 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        
        with open(self.es_file, 'r', encoding='utf-8') as f:
            es_data = json.load(f)
        
        # Verificar errores de config
        config_errors = ["cannot_connect", "unknown"]
        for error in config_errors:
            assert error in en_data["config"]["error"]
            assert error in es_data["config"]["error"]
        
        # Verificar errores de options
        option_errors = ["int", "loop_range", "loop_rfid", "relay_inclusive"]
        for error in option_errors:
            assert error in en_data["options"]["error"]
            assert error in es_data["options"]["error"]


@pytest.mark.parametrize("zone_number,expected_en,expected_es", [
    ("1", "Zone 1 Bypass", "Bypass Zona 1"),
    ("05", "Zone 5 Bypass", "Bypass Zona 5"),  # zona configurada como "05"
    ("15", "Zone 15 Bypass", "Bypass Zona 15"),
    ("100", "Zone 100 Bypass", "Bypass Zona 100"),
])
def test_zone_bypass_names(zone_number, expected_en, expected_es):
    """Test zone bypass name formatting for different zone numbers"""
    en_file = Path("custom_components/custom_alarmdecoder/translations/en.json")
    es_file = Path("custom_components/custom_alarmdecoder/translations/es.json")
    
    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)
    
    with open(es_file, 'r', encoding='utf-8') as f:
        es_data = json.load(f)
    
    en_template = en_data["entity"]["switch"]["zone_bypass"]["name"]
    es_template = es_data["entity"]["switch"]["zone_bypass"]["name"]
    
    # Simular procesamiento de zona (quitar ceros delante)
    processed_zone = str(int(zone_number))
    
    en_result = en_template.format(zone_number=processed_zone)
    es_result = es_template.format(zone_number=processed_zone)
    
    assert en_result == expected_en.replace(zone_number, processed_zone)
    assert es_result == expected_es.replace(zone_number, processed_zone)


def test_translation_completeness():
    """Test that translations cover all necessary UI elements"""
    strings_file = Path("custom_components/custom_alarmdecoder/strings.json")
    en_file = Path("custom_components/custom_alarmdecoder/translations/en.json")
    es_file = Path("custom_components/custom_alarmdecoder/translations/es.json")
    
    with open(strings_file, 'r', encoding='utf-8') as f:
        strings_data = json.load(f)
    
    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)
    
    with open(es_file, 'r', encoding='utf-8') as f:
        es_data = json.load(f)
    
    # Verificar que las traducciones cubren las entidades definidas en strings.json
    if "entity" in strings_data:
        assert "entity" in en_data, "Entity section missing in English translations"
        assert "entity" in es_data, "Entity section missing in Spanish translations"
        
        if "switch" in strings_data["entity"]:
            assert "switch" in en_data["entity"], "Switch entity missing in English"
            assert "switch" in es_data["entity"], "Switch entity missing in Spanish"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
