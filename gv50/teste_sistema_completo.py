#!/usr/bin/env python3
"""
Teste Sistema Completo: Simular conexão TCP real com comandos
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

def criar_e_configurar_veiculo():
    """Criar veículo com comando de bloqueio pendente"""
    print("=== CONFIGURANDO VEÍCULO PARA TESTE ===")
    
    imei_test = "865083030056741"
    handler = MessageHandler()
    
    # Criar/atualizar veículo com comando pendente
    print("1. Configurando comando de bloqueio...")
    handler.set_blocking_command(imei_test, True)
    
    # Forçar status para disparar comando
    vehicle = db_manager.get_vehicle_by_imei(imei_test)
    if vehicle:
        vehicle_data = dict(vehicle)
        if '_id' in vehicle_data:
            del vehicle_data['_id']
        vehicle_data['bloqueado'] = True
        vehicle_data['comandobloqueo'] = True
        
        from models import Vehicle
        updated_vehicle = Vehicle(**vehicle_data)
        db_manager.upsert_vehicle(updated_vehicle)
        
        print(f"✅ Veículo configurado:")
        print(f"   IMEI: {imei_test}")
        print(f"   Comando bloqueio: {vehicle_data['comandobloqueo']}")
        print(f"   Status bloqueado: {vehicle_data['bloqueado']}")
        return imei_test
    
    return None

def simular_conexao_tcp(imei):
    """Simular conexão TCP real com o servidor"""
    print("\n=== SIMULANDO CONEXÃO TCP REAL ===")
    
    try:
        # Conectar ao servidor TCP
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 8000))
        print("✅ Conectado ao servidor TCP na porta 8000")
        
        # Enviar mensagem GPS GTFRI
        mensagem_gps = f"+RESP:GTFRI,060228,{imei},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12348$"
        
        print(f"📡 Enviando mensagem GPS:")
        print(f"   {mensagem_gps[:60]}...")
        
        client_socket.send(mensagem_gps.encode('utf-8'))
        
        # Aguardar resposta (ACK + possível comando)
        print("⏳ Aguardando resposta do servidor...")
        
        responses = []
        start_time = time.time()
        
        while time.time() - start_time < 5:  # Aguardar até 5 segundos
            try:
                client_socket.settimeout(1)
                data = client_socket.recv(1024)
                if data:
                    response = data.decode('utf-8')
                    responses.append(response)
                    print(f"📥 Resposta recebida: {response}")
                    
                    # Verificar se é comando de bloqueio
                    if "AT+GTOUT" in response:
                        print("🚨 COMANDO DE BLOQUEIO RECEBIDO!")
                        if ",1," in response:
                            print("   ✅ Comando correto: BLOQUEAR (bit=1)")
                        elif ",0," in response:
                            print("   ✅ Comando correto: DESBLOQUEAR (bit=0)")
                        
                        # Simular confirmação do dispositivo
                        confirmacao = f"+ACK:GTOUT,060228,{imei},,0000,20250727{time.strftime('%H%M%S')},11F0$"
                        print(f"📤 Enviando confirmação: {confirmacao}")
                        client_socket.send(confirmacao.encode('utf-8'))
                        
                else:
                    break
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Erro ao receber dados: {e}")
                break
        
        client_socket.close()
        print("🔌 Conexão TCP fechada")
        
        return responses
        
    except Exception as e:
        print(f"❌ Erro na conexão TCP: {e}")
        return []

def verificar_resultado(imei, responses):
    """Verificar se o comando foi processado corretamente"""
    print("\n=== VERIFICANDO RESULTADO ===")
    
    # Verificar respostas recebidas
    comando_enviado = False
    ack_recebido = False
    
    for response in responses:
        if "+ACK:" in response:
            ack_recebido = True
            print("✅ ACK recebido do servidor")
        if "AT+GTOUT" in response:
            comando_enviado = True
            print("✅ Comando AT enviado pelo servidor")
    
    # Verificar status no banco após processamento
    vehicle = db_manager.get_vehicle_by_imei(imei)
    if vehicle:
        print(f"\n📊 Status final do veículo:")
        print(f"   IMEI: {vehicle['IMEI']}")
        print(f"   Comando bloqueio: {vehicle.get('comandobloqueo', 'N/A')}")
        print(f"   Status bloqueado: {vehicle.get('bloqueado', 'N/A')}")
        print(f"   Última atualização: {vehicle.get('tsusermanu', 'N/A')}")
    
    # Resultado final
    if comando_enviado and ack_recebido:
        print("\n🎉 TESTE APROVADO!")
        print("✅ Servidor enviou comando AT corretamente")
        print("✅ Comunicação bidirecional funcionando")
        return True
    else:
        print("\n❌ TESTE FALHOU!")
        print(f"   Comando enviado: {'✅' if comando_enviado else '❌'}")
        print(f"   ACK recebido: {'✅' if ack_recebido else '❌'}")
        return False

def main():
    """Executar teste completo"""
    print("🧪 TESTE COMPLETO: SISTEMA DE COMANDOS TCP")
    print("="*60)
    print("OBJETIVO: Verificar se comandos são enviados via TCP")
    print("="*60)
    
    # 1. Configurar veículo
    imei = criar_e_configurar_veiculo()
    if not imei:
        print("❌ Falha ao configurar veículo")
        return False
    
    # Aguardar servidor estar pronto
    print("\n⏳ Aguardando servidor estar pronto...")
    time.sleep(2)
    
    # 2. Simular conexão TCP
    responses = simular_conexao_tcp(imei)
    
    # 3. Verificar resultado
    sucesso = verificar_resultado(imei, responses)
    
    print("\n" + "="*60)
    if sucesso:
        print("🎉 SISTEMA FUNCIONANDO CORRETAMENTE!")
        print("✅ Comandos de bloqueio operacionais")
        print("✅ Integração TCP completa")
    else:
        print("❌ SISTEMA COM PROBLEMAS!")
        print("❌ Comandos não estão sendo enviados corretamente")
    print("="*60)
    
    return sucesso

if __name__ == "__main__":
    sucesso = main()
    exit(0 if sucesso else 1)