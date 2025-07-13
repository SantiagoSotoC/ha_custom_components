#!/usr/bin/env python3
"""
Prueba manual de las traducciones para verificar el output visual
"""

import json
from pathlib import Path


def test_visual_translations():
    """Prueba visual de las traducciones"""
    
    print("🔍 PRUEBA VISUAL DE TRADUCCIONES")
    print("=" * 50)
    
    # Cargar archivos
    en_file = Path("custom_components/custom_alarmdecoder/translations/en.json")
    es_file = Path("custom_components/custom_alarmdecoder/translations/es.json")
    
    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)
    
    with open(es_file, 'r', encoding='utf-8') as f:
        es_data = json.load(f)
    
    # Probar traducciones de switches de bypass
    print("\n🔧 SWITCHES DE BYPASS:")
    print("-" * 30)
    
    zones_to_test = ["1", "05", "15", "100"]
    
    for zone in zones_to_test:
        processed_zone = str(int(zone))  # Simular procesamiento del componente
        
        en_name = en_data["entity"]["switch"]["zone_bypass"]["name"].format(zone_number=processed_zone)
        es_name = es_data["entity"]["switch"]["zone_bypass"]["name"].format(zone_number=processed_zone)
        
        print(f"Zona {zone:>3} → EN: '{en_name}' | ES: '{es_name}'")
    
    # Probar descripciones del config flow
    print("\n⚙️  CONFIG FLOW:")
    print("-" * 30)
    
    test_zone = "15"
    en_desc = en_data["options"]["step"]["zone_details"]["description"].format(zone_number=test_zone)
    es_desc = es_data["options"]["step"]["zone_details"]["description"].format(zone_number=test_zone)
    
    print(f"EN: {en_desc}")
    print(f"ES: {es_desc}")
    
    # Probar títulos principales
    print("\n📋 TÍTULOS PRINCIPALES:")
    print("-" * 30)
    
    sections = [
        ("config.step.protocol.title", "Título de configuración de protocolo"),
        ("options.step.arm_settings.title", "Título de configuración de armado"),
        ("options.step.zone_details.data.bypassable", "Opción de bypass"),
    ]
    
    for path, description in sections:
        keys = path.split(".")
        
        # Navegar por las claves anidadas
        en_value = en_data
        es_value = es_data
        
        for key in keys:
            en_value = en_value[key]
            es_value = es_value[key]
        
        print(f"{description}:")
        print(f"  EN: {en_value}")
        print(f"  ES: {es_value}")
        print()
    
    # Probar servicios
    print("\n🔧 SERVICIOS:")
    print("-" * 30)
    
    services = ["alarm_keypress", "alarm_toggle_chime"]
    
    for service in services:
        en_service = en_data["services"][service]
        es_service = es_data["services"][service]
        
        print(f"Servicio: {service}")
        print(f"  EN: {en_service['name']} - {en_service['description']}")
        print(f"  ES: {es_service['name']} - {es_service['description']}")
        print()
    
    # Probar mensajes de error
    print("\n❌ MENSAJES DE ERROR:")
    print("-" * 30)
    
    errors = [
        ("config.error.cannot_connect", "Error de conexión"),
        ("options.error.relay_inclusive", "Error de configuración de relé"),
    ]
    
    for path, description in errors:
        keys = path.split(".")
        
        en_value = en_data
        es_value = es_data
        
        for key in keys:
            en_value = en_value[key]
            es_value = es_value[key]
        
        print(f"{description}:")
        print(f"  EN: {en_value}")
        print(f"  ES: {es_value}")
        print()
    
    # Probar estados del panel de alarma
    print("\n🚨 ESTADOS DEL PANEL DE ALARMA:")
    print("-" * 30)
    
    states = ["disarmed", "armed_away", "armed_home", "triggered"]
    
    for state in states:
        en_state = en_data["entity"]["alarm_control_panel"]["state"][state]
        es_state = es_data["entity"]["alarm_control_panel"]["state"][state]
        
        print(f"Estado '{state}':")
        print(f"  EN: {en_state}")
        print(f"  ES: {es_state}")
        print()
    
    print("✅ PRUEBA VISUAL COMPLETADA")


def simulate_ui_flow():
    """Simula el flujo de UI con las traducciones"""
    
    print("\n🎭 SIMULACIÓN DE FLUJO DE UI")
    print("=" * 50)
    
    en_file = Path("custom_components/custom_alarmdecoder/translations/en.json")
    es_file = Path("custom_components/custom_alarmdecoder/translations/es.json")
    
    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)
    
    with open(es_file, 'r', encoding='utf-8') as f:
        es_data = json.load(f)
    
    # Simular configuración de zona con bypass
    print("\n📝 CONFIGURACIÓN DE ZONA CON BYPASS:")
    print("-" * 40)
    
    zone_number = "5"
    
    # Inglés
    print("INGLÉS:")
    print(f"Título: {en_data['options']['step']['zone_details']['title']}")
    print(f"Descripción: {en_data['options']['step']['zone_details']['description'].format(zone_number=zone_number)}")
    print(f"Campo 'Nombre de zona': {en_data['options']['step']['zone_details']['data']['zone_name']}")
    print(f"Campo 'Permitir Bypass': {en_data['options']['step']['zone_details']['data']['bypassable']}")
    
    print("\nESPAÑOL:")
    print(f"Título: {es_data['options']['step']['zone_details']['title']}")
    print(f"Descripción: {es_data['options']['step']['zone_details']['description'].format(zone_number=zone_number)}")
    print(f"Campo 'Nombre de zona': {es_data['options']['step']['zone_details']['data']['zone_name']}")
    print(f"Campo 'Permitir Bypass': {es_data['options']['step']['zone_details']['data']['bypassable']}")
    
    # Simular switch creado
    print(f"\n🔀 SWITCH CREADO PARA ZONA {zone_number}:")
    print("-" * 40)
    
    en_switch_name = en_data["entity"]["switch"]["zone_bypass"]["name"].format(zone_number=zone_number)
    es_switch_name = es_data["entity"]["switch"]["zone_bypass"]["name"].format(zone_number=zone_number)
    
    print(f"EN: entity_id: switch.zone_{zone_number}_bypass | name: '{en_switch_name}'")
    print(f"ES: entity_id: switch.zone_{zone_number}_bypass | name: '{es_switch_name}'")
    
    print("\n✅ SIMULACIÓN COMPLETADA")


if __name__ == "__main__":
    test_visual_translations()
    simulate_ui_flow()
