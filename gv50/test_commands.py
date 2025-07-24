#!/usr/bin/env python3
"""
Script para testar comandos da tabela Vehicle
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from database import db_manager
from message_handler import message_handler
from models import Vehicle

def test_vehicle_creation():
    """Testa criação de veículo com nova estrutura"""
    print("=== TESTE: Criação de Veículo ===")
    
    test_imei = "865083030056741"
    
    # Criar veículo de teste
    vehicle = Vehicle(
        IMEI=test_imei,
        dsplaca="ABC1234",
        dsmodelo="GV50",
        ignicao=False,
        bloqueado=False,
        bateriavoltagem=12.5,
        bateriabaixa=False,
        tsusermanu=datetime.utcnow()
    )
    
    # Salvar no banco
    success = db_manager.upsert_vehicle(vehicle)
    print(f"✓ Veículo criado: {success}")
    
    # Verificar se foi salvo
    saved_vehicle = db_manager.get_vehicle_by_imei(test_imei)
    if saved_vehicle:
        print(f"✓ Veículo encontrado: IMEI={saved_vehicle['IMEI']}, placa={saved_vehicle.get('dsplaca')}")
        return True
    else:
        print("❌ Veículo não encontrado")
        return False

def test_blocking_commands():
    """Testa comandos de bloqueio"""
    print("\n=== TESTE: Comandos de Bloqueio ===")
    
    test_imei = "865083030056741"
    
    # Definir comando de bloqueio
    message_handler.set_blocking_command(test_imei, True)
    print("✓ Comando de bloqueio definido")
    
    # Verificar comando pendente
    vehicle = db_manager.get_vehicle_by_imei(test_imei)
    if vehicle and vehicle.get('comandobloqueo') == True:
        print("✓ Comando de bloqueio pendente confirmado")
    else:
        print("❌ Comando de bloqueio não encontrado")
        return False
    
    # Simular resposta do dispositivo (executar comando)
    message_handler.update_vehicle_blocking(test_imei, True)
    print("✓ Comando de bloqueio executado")
    
    # Verificar status final
    vehicle = db_manager.get_vehicle_by_imei(test_imei)
    if vehicle:
        blocked = vehicle.get('bloqueado')
        pending_cmd = vehicle.get('comandobloqueo')
        print(f"✓ Status final: bloqueado={blocked}, comando_pendente={pending_cmd}")
        return blocked == True and pending_cmd is None
    
    return False

def test_ignition_update():
    """Testa atualização de ignição"""
    print("\n=== TESTE: Atualização de Ignição ===")
    
    test_imei = "865083030056741"
    
    # Ligar ignição
    message_handler.update_vehicle_ignition(test_imei, True)
    print("✓ Ignição ligada")
    
    # Verificar status
    vehicle = db_manager.get_vehicle_by_imei(test_imei)
    if vehicle and vehicle.get('ignicao') == True:
        print("✓ Status de ignição confirmado: LIGADA")
    else:
        print("❌ Status de ignição não atualizado")
        return False
    
    # Desligar ignição
    message_handler.update_vehicle_ignition(test_imei, False)
    print("✓ Ignição desligada")
    
    # Verificar status final
    vehicle = db_manager.get_vehicle_by_imei(test_imei)
    if vehicle and vehicle.get('ignicao') == False:
        print("✓ Status de ignição confirmado: DESLIGADA")
        return True
    else:
        print("❌ Status de ignição não atualizado")
        return False

def test_battery_monitoring():
    """Testa monitoramento de bateria"""
    print("\n=== TESTE: Monitoramento de Bateria ===")
    
    test_imei = "865083030056741"
    
    # Simular bateria baixa
    vehicle = Vehicle(
        IMEI=test_imei,
        bateriavoltagem=9.5,  # Bateria crítica
        bateriabaixa=True,
        ultimoalertabateria=datetime.utcnow(),
        tsusermanu=datetime.utcnow()
    )
    
    success = db_manager.upsert_vehicle(vehicle)
    print(f"✓ Bateria baixa simulada: {success}")
    
    # Verificar alerta
    saved_vehicle = db_manager.get_vehicle_by_imei(test_imei)
    if saved_vehicle:
        voltage = saved_vehicle.get('bateriavoltagem')
        low_battery = saved_vehicle.get('bateriabaixa')
        alert_time = saved_vehicle.get('ultimoalertabateria')
        
        print(f"✓ Status bateria: {voltage}V, baixa={low_battery}, alerta={alert_time}")
        return voltage == 9.5 and low_battery == True
    
    return False

def test_ip_change_command():
    """Testa comando de troca de IP"""
    print("\n=== TESTE: Comando Troca IP ===")
    
    test_imei = "865083030056741"
    
    # Definir comando de troca de IP
    message_handler.set_ip_change_command(test_imei)
    print("✓ Comando de troca IP definido")
    
    # Verificar comando pendente
    vehicle = db_manager.get_vehicle_by_imei(test_imei)
    if vehicle and vehicle.get('comandotrocarip') == True:
        print("✓ Comando de troca IP pendente confirmado")
        return True
    else:
        print("❌ Comando de troca IP não encontrado")
        return False

def main():
    """Executa todos os testes"""
    print("╔══════════════════════════════════════╗")
    print("║        TESTE DE COMANDOS GV50        ║")
    print("╚══════════════════════════════════════╝")
    
    tests = [
        ("Criação de Veículo", test_vehicle_creation),
        ("Comandos de Bloqueio", test_blocking_commands),
        ("Atualização de Ignição", test_ignition_update),
        ("Monitoramento de Bateria", test_battery_monitoring),
        ("Comando Troca IP", test_ip_change_command)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERRO em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "="*50)
    print("RESUMO DOS TESTES:")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✓ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:25} | {status}")
        if result:
            passed += 1
    
    print("="*50)
    print(f"TOTAL: {passed}/{len(tests)} testes passaram")
    
    if passed == len(tests):
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM")

if __name__ == "__main__":
    main()