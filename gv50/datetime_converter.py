#!/usr/bin/env python3
"""
Conversor de data/hora do dispositivo GV50
Formato: YYYYMMDDHHMMSS -> datetime
"""

from datetime import datetime
from typing import Optional
import re

def convert_device_timestamp(device_timestamp: str) -> Optional[datetime]:
    """
    Converte timestamp do dispositivo GV50 para datetime
    
    Formato esperado: YYYYMMDDHHMMSS (14 dígitos)
    Exemplo: "20250727120605" -> 2025-07-27 12:06:05
    
    Args:
        device_timestamp: String com timestamp do dispositivo
        
    Returns:
        datetime object ou None se conversão falhar
    """
    try:
        if not device_timestamp or len(device_timestamp) < 4:
            return None
            
        # Extrair e limpar timestamp
        timestamp_clean = device_timestamp.strip()
        
        # GTSTT pode ter timestamp "0000" - tratar como inválido
        if timestamp_clean == "0000" or timestamp_clean == "":
            return None
            
        # Verificar se tem pelo menos 14 dígitos para timestamp completo
        if len(timestamp_clean) < 14:
            return None
            
        # Extrair componentes
        year = int(timestamp_clean[0:4])
        month = int(timestamp_clean[4:6])
        day = int(timestamp_clean[6:8])
        hour = int(timestamp_clean[8:10])
        minute = int(timestamp_clean[10:12])
        second = int(timestamp_clean[12:14])
        
        # Validar valores
        if not (1900 <= year <= 2100):
            return None
        if not (1 <= month <= 12):
            return None
        if not (1 <= day <= 31):
            return None
        if not (0 <= hour <= 23):
            return None
        if not (0 <= minute <= 59):
            return None
        if not (0 <= second <= 59):
            return None
            
        # Criar datetime
        converted_dt = datetime(year, month, day, hour, minute, second)
        return converted_dt
        
    except (ValueError, IndexError, TypeError) as e:
        print(f"Erro convertendo timestamp '{device_timestamp}': {e}")
        return None

def format_device_timestamp(device_timestamp: str) -> str:
    """
    Formatar timestamp do dispositivo para string legível
    
    Args:
        device_timestamp: String com timestamp do dispositivo
        
    Returns:
        String formatada ou timestamp original se conversão falhar
    """
    converted = convert_device_timestamp(device_timestamp)
    if converted:
        return converted.strftime("%Y-%m-%d %H:%M:%S")
    return device_timestamp

def test_converter():
    """Testar conversor com exemplos"""
    test_cases = [
        "20250727120605",  # Válido
        "20250727120000",  # Válido
        "2025072712",      # Muito curto
        "invalid",         # Inválido
        "",                # Vazio
        "20251301120605",  # Mês inválido
        "20250732120605",  # Dia inválido
        "20250727250605",  # Hora inválida
    ]
    
    print("🧪 TESTE DO CONVERSOR DE DATA:")
    for test in test_cases:
        result = convert_device_timestamp(test)
        formatted = format_device_timestamp(test)
        print(f"  '{test}' -> {result} -> '{formatted}'")

if __name__ == "__main__":
    test_converter()