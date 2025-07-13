#!/usr/bin/env python3
"""
Script de prueba para demostrar el formato de comandos de bypass
"""

def build_bypass_string(zones: list[int], code: str = "") -> str:
    """Build bypass string for the given zones."""
    if not zones:
        return ""
    
    # Nuevo formato: código + 6 + zonas a bypass + *
    # Las zonas nunca deben tener ceros a la izquierda (1, no 01; 11, no 011)
    zones_str = "".join([str(zone) for zone in zones])
    bypass_string = f"{code}6{zones_str}*"
    
    print(f"Código: '{code}', Zonas: {zones}, Resultado: '{bypass_string}'")
    return bypass_string

def test_bypass_formats():
    """Test various bypass scenarios"""
    print("Probando formatos de bypass:\n")
    
    # Escenarios de prueba
    test_cases = [
        # (zones, code, description)
        ([1], "1234", "Zona 1 con código 1234"),
        ([1, 2], "1234", "Zonas 1 y 2 con código 1234"),
        ([1, 11], "1234", "Zonas 1 y 11 con código 1234"),
        ([3, 5, 12], "1234", "Zonas 3, 5 y 12 con código 1234"),
        ([10, 11, 12], "1234", "Zonas 10, 11 y 12 con código 1234"),
        ([1], "", "Zona 1 sin código"),
        ([7, 8, 9], "", "Zonas 7, 8 y 9 sin código"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "1234", "Todas las zonas (1-12)"),
        
        # Casos con zonas de 2 dígitos
        ([15], "1234", "Zona 15 (2 dígitos)"),
        ([25, 30], "1234", "Zonas 25 y 30 (2 dígitos)"),
        ([5, 15, 25], "1234", "Zonas 5, 15 y 25 (mix 1-2 dígitos)"),
        ([99], "1234", "Zona 99 (2 dígitos máximo)"),
        
        # Casos con zonas de 3 dígitos
        ([100], "1234", "Zona 100 (3 dígitos)"),
        ([101], "1234", "Zona 101 (3 dígitos con cero en medio)"),
        ([105, 110], "1234", "Zonas 105 y 110 (3 dígitos)"),
        ([1, 50, 100], "1234", "Zonas 1, 50 y 100 (mix 1-2-3 dígitos)"),
        ([999], "1234", "Zona 999 (3 dígitos máximo)"),
        
        # Casos especiales con ceros
        ([1], "1234", "Zona 01 (entrada como 1, sin cero delante)"),
        ([10], "1234", "Zona 10 (termina en 0)"),
        ([20, 30, 40], "1234", "Zonas 20, 30, 40 (terminan en 0)"),
        ([100, 200, 300], "1234", "Zonas 100, 200, 300 (terminan en 00)"),
        ([101, 102, 103], "1234", "Zonas 101, 102, 103 (empiezan con 10)"),
        ([1, 10, 100], "1234", "Zonas 1, 10, 100 (potencias de 10)"),
        
        # Casos sin código
        ([15, 25], "", "Zonas 15 y 25 sin código"),
        ([100, 200], "", "Zonas 100 y 200 sin código"),
    ]
    
    for zones, code, description in test_cases:
        print(f"{description}:")
        build_bypass_string(zones, code)
        print()

if __name__ == "__main__":
    test_bypass_formats()
    
    print("\nEjemplos de comandos completos:")
    print("================================")
    print("Para bypass zona 01 (como 1) + armar away: '123461*' seguido de '12342'")
    print("Para bypass zona 1 + armar away: '123461*' seguido de '12342'")
    print("Para bypass zonas 1,11 + armar home: '12346111*' seguido de '12343'")
    print("Para bypass zonas 3,5,12 + armar away: '123463512*' seguido de '12342'")
    print("Para bypass zona 15 + armar away: '1234615*' seguido de '12342'")
    print("Para bypass zonas 1,50,100 + armar home: '12346150100*' seguido de '12343'")
    print("Para bypass zona 101 + armar away: '12346101*' seguido de '12342'")
