#!/usr/bin/env python3
"""
Pruebas pytest para el formato de comandos de bypass
"""

import pytest


def build_bypass_string(zones: list[int], code: str = "") -> str:
    """Build bypass string for the given zones."""
    if not zones:
        return ""
    
    # Nuevo formato: código + 6 + zonas a bypass + *
    # Las zonas nunca deben tener ceros a la izquierda (1, no 01; 11, no 011)
    zones_str = "".join([str(zone) for zone in zones])
    bypass_string = f"{code}6{zones_str}*"
    
    return bypass_string


class TestBypassFormat:
    """Test cases for bypass command format"""
    
    def test_single_digit_zones(self):
        """Test single digit zones"""
        assert build_bypass_string([1], "1234") == "123461*"
        assert build_bypass_string([5], "1234") == "123465*"
        assert build_bypass_string([9], "1234") == "123469*"
    
    def test_zone_01_as_integer_1(self):
        """Test that zone 01 is handled as 1 (no leading zero)"""
        # En el sistema real, "01" se convierte a int(1)
        assert build_bypass_string([1], "1234") == "123461*"
        # Verificar que NO se genera con cero delante
        assert build_bypass_string([1], "1234") != "123460*"
        assert build_bypass_string([1], "1234") != "12346010*"
    
    def test_multiple_single_digit_zones(self):
        """Test multiple single digit zones"""
        assert build_bypass_string([1, 2], "1234") == "1234612*"
        assert build_bypass_string([1, 5, 9], "1234") == "12346159*"
        assert build_bypass_string([7, 8, 9], "") == "6789*"
    
    def test_two_digit_zones(self):
        """Test two digit zones"""
        assert build_bypass_string([10], "1234") == "1234610*"
        assert build_bypass_string([15], "1234") == "1234615*"
        assert build_bypass_string([25, 30], "1234") == "123462530*"
        assert build_bypass_string([99], "1234") == "1234699*"
    
    def test_three_digit_zones(self):
        """Test three digit zones"""
        assert build_bypass_string([100], "1234") == "12346100*"
        assert build_bypass_string([101], "1234") == "12346101*"
        assert build_bypass_string([105, 110], "1234") == "12346105110*"
        assert build_bypass_string([999], "1234") == "12346999*"
    
    def test_mixed_digit_zones(self):
        """Test mixed digit zones"""
        assert build_bypass_string([1, 11], "1234") == "12346111*"
        assert build_bypass_string([3, 5, 12], "1234") == "123463512*"
        assert build_bypass_string([1, 50, 100], "1234") == "12346150100*"
        assert build_bypass_string([5, 15, 25], "1234") == "1234651525*"
    
    def test_zones_ending_with_zero(self):
        """Test zones ending with zero"""
        assert build_bypass_string([10], "1234") == "1234610*"
        assert build_bypass_string([20, 30, 40], "1234") == "12346203040*"
        assert build_bypass_string([100, 200, 300], "1234") == "12346100200300*"
    
    def test_zones_with_internal_zeros(self):
        """Test zones with zeros in the middle"""
        assert build_bypass_string([101, 102, 103], "1234") == "12346101102103*"
        assert build_bypass_string([105], "1234") == "12346105*"
        assert build_bypass_string([1010], "1234") == "123461010*"
    
    def test_no_code_scenarios(self):
        """Test bypass without security code"""
        assert build_bypass_string([1], "") == "61*"
        assert build_bypass_string([15, 25], "") == "61525*"
        assert build_bypass_string([100, 200], "") == "6100200*"
        assert build_bypass_string([7, 8, 9], "") == "6789*"
    
    def test_empty_zones(self):
        """Test empty zones list"""
        assert build_bypass_string([], "1234") == ""
        assert build_bypass_string([], "") == ""
    
    def test_large_zone_list(self):
        """Test many zones at once"""
        zones = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        expected = "12346123456789101112*"
        assert build_bypass_string(zones, "1234") == expected
    
    def test_powers_of_ten(self):
        """Test zones that are powers of 10"""
        assert build_bypass_string([1, 10, 100], "1234") == "12346110100*"
        assert build_bypass_string([1, 10, 100, 1000], "1234") == "123461101001000*"
    
    def test_no_leading_zeros_guarantee(self):
        """Ensure no leading zeros are ever added"""
        test_cases = [
            ([1], "1234", "123461*"),
            ([5], "1234", "123465*"),
            ([10], "1234", "1234610*"),
            ([15], "1234", "1234615*"),
            ([100], "1234", "12346100*"),
            ([101], "1234", "12346101*"),
        ]
        
        for zones, code, expected in test_cases:
            result = build_bypass_string(zones, code)
            assert result == expected
            # Verificar que no hay patrones de ceros delante
            assert "601*" not in result  # No 01
            assert "605*" not in result  # No 05
            assert "6010*" not in result  # No 010
            assert "6015*" not in result  # No 015
            assert "60100*" not in result  # No 0100
            assert "60101*" not in result  # No 0101


@pytest.mark.parametrize("zones,code,expected", [
    # Casos básicos
    ([1], "1234", "123461*"),
    ([1, 2], "1234", "1234612*"),
    ([1, 11], "1234", "12346111*"),
    
    # Casos especiales de zona 01
    ([1], "1234", "123461*"),  # zona "01" como int 1
    ([1], "", "61*"),          # zona "01" sin código
    
    # Casos de 2 dígitos
    ([15], "1234", "1234615*"),
    ([25, 30], "1234", "123462530*"),
    
    # Casos de 3 dígitos
    ([100], "1234", "12346100*"),
    ([101], "1234", "12346101*"),
    
    # Casos mixtos
    ([1, 50, 100], "1234", "12346150100*"),
    ([3, 5, 12], "1234", "123463512*"),
])
def test_bypass_format_parametrized(zones, code, expected):
    """Parametrized tests for various bypass scenarios"""
    assert build_bypass_string(zones, code) == expected


def test_real_world_scenarios():
    """Test real-world usage scenarios"""
    # Scenario 1: Single zone bypass for maintenance
    assert build_bypass_string([5], "1234") == "123465*"
    
    # Scenario 2: Multiple zones for party mode
    assert build_bypass_string([1, 2, 3], "1234") == "12346123*"
    
    # Scenario 3: High-numbered zones in commercial systems
    assert build_bypass_string([150, 151, 152], "1234") == "12346150151152*"
    
    # Scenario 4: Mixed zone types
    assert build_bypass_string([5, 25, 125], "1234") == "12346525125*"


if __name__ == "__main__":
    # Ejecutar las pruebas si se ejecuta directamente
    pytest.main([__file__, "-v"])
