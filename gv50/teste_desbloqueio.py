#!/usr/bin/env python3
"""
Teste específico: Comando de DESBLOQUEIO
"""

import os
import socket
import time
import threading
from datetime import datetime

# Force correct configuration
os.environ['SERVER_PORT'] = '8000'
os.environ['DATABASE_NAME'] = 'track'

from database import db_manager
from message_handler import MessageHandler

def configurar_desbloqueio():
    """Configurar veículo para desbloqueio"""
    print("=== CONFIGURANDO COMANDO DE DESBLOQUEIO ===")
    
    imei_test = "865083030056741"
    handler = MessageHandler()
    
    # 1. Primeiro garantir que está bloqueado
    print("1. Definindo status como bloqueado...")
    vehicle = db_manager.get_vehicle_by_imei(imei_test)
    if vehicle:
        vehicle_data = dict(vehicle)
        if '_id' in vehicle_data:
            del vehicle_data['_id']
        
        # Forçar status bloqueado primeiro
        vehicle_data['bloqueado'] = True
        vehicle_data['comandobloqueo'] = None  # Limpar comando anterior
        
        from models import Vehicle
        updated_vehicle = Vehicle(**vehicle_data)
        db_manager.upsert_vehicle(updated_vehicle)
        print(f"   ✅ Veículo está bloqueado: {vehicle_data['bloqueado']}")
    
    # 2. Agora configurar comando de desbloqueio
    print("2. Configurando comando de DESBLOQUEIO...")
    handler.set_blocking_command(imei_test, False)  # FALSE = DESBLOQUEAR
    
    # 3. Verificar configuração
    vehicle = db_manager.get_vehicle_by_imei(imei_test)
    if vehicle:
        print(f"   ✅ Comando desbloqueio: {vehicle.get('comandobloqueo')}")
        print(f"   ✅ Status atual: bloqueado={vehicle.get('bloqueado')}")
        return imei_test
    
    return None

def simular_conexao_desbloqueio(imei):
    """Simular conexão TCP para testar desbloqueio"""
    print("\n=== TESTANDO COMANDO DE DESBLOQUEIO ===")
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 8000))
        print("✅ Conectado ao servidor TCP")
        
        # Enviar mensagem GPS para disparar comando
        mensagem_gps = f"+RESP:GTFRI,060228,{imei},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12348$"
        
        print(f"📡 Enviando mensagem GPS...")
        client_socket.send(mensagem_gps.encode('utf-8'))
        
        # Aguardar respostas
        print("⏳ Aguardando comando de desbloqueio...")
        
        responses = []
        start_time = time.time()
        
        while time.time() - start_time < 5:
            try:
                client_socket.settimeout(1)
                data = client_socket.recv(1024)
                if data:
                    response = data.decode('utf-8')
                    responses.append(response)
                    print(f"📥 Resposta: {response}")
                    
                    # Verificar comando de desbloqueio
                    if "AT+GTOUT" in response:
                        if ",0," in response:
                            print("🔓 COMANDO DE DESBLOQUEIO DETECTADO!")
                            print("   ✅ Comando correto: DESBLOQUEAR (bit=0)")
                            
                            # Simular confirmação
                            confirmacao = f"+ACK:GTOUT,060228,{imei},,0000,20250727{time.strftime('%H%M%S')},11F0$"
                            print(f"📤 Enviando confirmação: {confirmacao}")
                            client_socket.send(confirmacao.encode('utf-8'))
                        elif ",1," in response:
                            print("⚠️  ERRO: Comando de bloqueio quando deveria desbloquear!")
                else:
                    break
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Erro: {e}")
                break
        
        client_socket.close()
        return responses
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return []

def verificar_resultado_desbloqueio(imei, responses):
    """Verificar se desbloqueio funcionou"""
    print("\n=== VERIFICANDO RESULTADO DESBLOQUEIO ===")
    
    comando_desbloqueio = False
    for response in responses:
        if "AT+GTOUT" in response and ",0," in response:
            comando_desbloqueio = True
            print("✅ Comando de desbloqueio enviado corretamente")
            break
    
    # Verificar status final
    vehicle = db_manager.get_vehicle_by_imei(imei)
    if vehicle:
        print(f"\n📊 Status final:")
        print(f"   IMEI: {vehicle['IMEI']}")
        print(f"   Comando: {vehicle.get('comandobloqueo', 'N/A')}")
        print(f"   Bloqueado: {vehicle.get('bloqueado', 'N/A')}")
        print(f"   Atualização: {vehicle.get('tsusermanu', 'N/A')}")
    
    if comando_desbloqueio:
        print("\n🎉 DESBLOQUEIO FUNCIONANDO!")
        return True
    else:
        print("\n❌ DESBLOQUEIO FALHOU!")
        return False

def main():
    """Teste completo de desbloqueio"""
    print("🔓 TESTE: COMANDO DE DESBLOQUEIO")
    print("="*50)
    
    # 1. Configurar desbloqueio
    imei = configurar_desbloqueio()
    if not imei:
        print("❌ Falha na configuração")
        return False
    
    time.sleep(2)  # Aguardar servidor
    
    # 2. Testar desbloqueio
    responses = simular_conexao_desbloqueio(imei)
    
    # 3. Verificar resultado
    sucesso = verificar_resultado_desbloqueio(imei, responses)
    
    print("\n" + "="*50)
    if sucesso:
        print("🎉 DESBLOQUEIO OPERACIONAL!")
    else:
        print("❌ PROBLEMA NO DESBLOQUEIO!")
    print("="*50)
    
    return sucesso

if __name__ == "__main__":
    sucesso = main()
    exit(0 if sucesso else 1)