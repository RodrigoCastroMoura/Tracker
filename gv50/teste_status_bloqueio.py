#!/usr/bin/env python3
"""
Teste: Status de bloqueio e comando de troca de IP
"""

import os
import socket
import time
from datetime import datetime

# Force correct configuration
os.environ['SERVER_PORT'] = '8000'
os.environ['DATABASE_NAME'] = 'track'

from database import db_manager
from message_handler import MessageHandler

def teste_status_bloqueio():
    """Testar se status de bloqueio muda corretamente"""
    print("=== TESTE: STATUS DE BLOQUEIO ===")
    
    imei_test = "865083030056741"
    handler = MessageHandler()
    
    # 1. Estado inicial - veículo desbloqueado
    print("1. Configurando estado inicial (desbloqueado)...")
    vehicle = db_manager.get_vehicle_by_imei(imei_test)
    if vehicle:
        vehicle_data = dict(vehicle)
        if '_id' in vehicle_data:
            del vehicle_data['_id']
        vehicle_data['bloqueado'] = False  # DESBLOQUEADO
        vehicle_data['comandobloqueo'] = None
        
        from models import Vehicle
        updated_vehicle = Vehicle(**vehicle_data)
        db_manager.upsert_vehicle(updated_vehicle)
        
        print(f"   ✅ Estado inicial: bloqueado = {vehicle_data['bloqueado']}")
    
    # 2. Configurar comando de bloqueio
    print("2. Configurando comando de BLOQUEIO...")
    handler.set_blocking_command(imei_test, True)
    
    vehicle = db_manager.get_vehicle_by_imei(imei_test)
    print(f"   ✅ Comando: comandobloqueo = {vehicle.get('comandobloqueo')}")
    print(f"   ✅ Status atual: bloqueado = {vehicle.get('bloqueado')}")
    
    return imei_test

def simular_bloqueio_completo(imei):
    """Simular ciclo completo de bloqueio"""
    print(f"\n=== SIMULANDO CICLO COMPLETO DE BLOQUEIO ===")
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 8000))
        print("✅ Conectado ao servidor TCP")
        
        # Enviar mensagem GPS
        mensagem_gps = f"+RESP:GTFRI,060228,{imei},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12348$"
        
        print("📡 Enviando mensagem GPS...")
        client_socket.send(mensagem_gps.encode('utf-8'))
        
        # Aguardar comando de bloqueio
        comando_recebido = None
        start_time = time.time()
        
        while time.time() - start_time < 5:
            try:
                client_socket.settimeout(1)
                data = client_socket.recv(1024)
                if data:
                    response = data.decode('utf-8')
                    print(f"📥 Resposta: {response}")
                    
                    if "AT+GTOUT" in response and ",1," in response:
                        comando_recebido = response
                        print("🔒 Comando de bloqueio recebido!")
                        
                        # Simular confirmação do dispositivo
                        confirmacao = f"+ACK:GTOUT,060228,{imei},,0000,20250727{time.strftime('%H%M%S')},11F0$"
                        print(f"📤 Enviando confirmação: {confirmacao}")
                        client_socket.send(confirmacao.encode('utf-8'))
                        break
                else:
                    break
            except socket.timeout:
                continue
        
        client_socket.close()
        return comando_recebido
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def verificar_mudanca_status(imei, comando_recebido):
    """Verificar se status mudou corretamente"""
    print(f"\n=== VERIFICANDO MUDANÇA DE STATUS ===")
    
    vehicle = db_manager.get_vehicle_by_imei(imei)
    if vehicle:
        print(f"📊 Status após comando:")
        print(f"   IMEI: {vehicle['IMEI']}")
        print(f"   Comando pendente: {vehicle.get('comandobloqueo', 'N/A')}")
        print(f"   Status bloqueado: {vehicle.get('bloqueado', 'N/A')}")
        print(f"   Última atualização: {vehicle.get('tsusermanu', 'N/A')}")
        
        # Verificar se status mudou corretamente
        if comando_recebido and vehicle.get('bloqueado') == True:
            print("✅ STATUS MUDOU CORRETAMENTE!")
            print("✅ Veículo agora está bloqueado")
            return True
        else:
            print("❌ STATUS NÃO MUDOU!")
            print("❌ Veículo deveria estar bloqueado mas não está")
            return False
    
    return False

def teste_comando_troca_ip():
    """Testar comando de troca de IP"""
    print(f"\n=== TESTE: COMANDO DE TROCA DE IP ===")
    
    imei_test = "865083030056741"
    handler = MessageHandler()
    
    # Configurar comando de troca de IP
    print("1. Configurando comando de troca de IP...")
    handler.set_ip_change_command(imei_test)
    
    vehicle = db_manager.get_vehicle_by_imei(imei_test)
    if vehicle:
        print(f"   ✅ Comando troca IP: {vehicle.get('comandotrocarip', 'N/A')}")
    
    # Simular conexão para verificar se comando é enviado
    print("2. Testando envio do comando...")
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 8000))
        
        # Enviar mensagem GPS
        mensagem_gps = f"+RESP:GTFRI,060228,{imei_test},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12348$"
        client_socket.send(mensagem_gps.encode('utf-8'))
        
        comando_ip_recebido = False
        start_time = time.time()
        
        while time.time() - start_time < 3:
            try:
                client_socket.settimeout(1)
                data = client_socket.recv(1024)
                if data:
                    response = data.decode('utf-8')
                    print(f"📥 Resposta: {response}")
                    
                    # Verificar se há comando de troca de IP
                    if "AT+GTIPSET" in response:  # Comando típico para troca de IP
                        comando_ip_recebido = True
                        print("🌐 Comando de troca de IP recebido!")
                        break
                else:
                    break
            except socket.timeout:
                continue
        
        client_socket.close()
        
        if comando_ip_recebido:
            print("✅ COMANDO DE TROCA DE IP FUNCIONANDO!")
        else:
            print("❌ COMANDO DE TROCA DE IP NÃO ENVIADO!")
            print("❌ Implementação pode estar incompleta")
        
        return comando_ip_recebido
        
    except Exception as e:
        print(f"❌ Erro testando troca de IP: {e}")
        return False

def main():
    """Executar todos os testes"""
    print("🧪 TESTE COMPLETO: STATUS E COMANDOS")
    print("="*50)
    
    # Teste 1: Status de bloqueio
    imei = teste_status_bloqueio()
    time.sleep(2)
    
    comando_recebido = simular_bloqueio_completo(imei)
    time.sleep(1)
    
    status_ok = verificar_mudanca_status(imei, comando_recebido)
    
    # Teste 2: Comando de troca de IP
    time.sleep(2)
    ip_ok = teste_comando_troca_ip()
    
    # Resultado final
    print("\n" + "="*50)
    print("📊 RESULTADO DOS TESTES:")
    print(f"   Status de bloqueio: {'✅ OK' if status_ok else '❌ FALHOU'}")
    print(f"   Comando troca IP: {'✅ OK' if ip_ok else '❌ FALHOU'}")
    
    if status_ok and ip_ok:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM - CORREÇÕES NECESSÁRIAS")
    print("="*50)
    
    return status_ok and ip_ok

if __name__ == "__main__":
    sucesso = main()
    exit(0 if sucesso else 1)