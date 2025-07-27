#!/usr/bin/env python3
"""
Teste simples: Status de bloqueio e comando de troca de IP
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

def main():
    print("🧪 TESTE SIMPLES: STATUS E COMANDOS")
    print("="*50)
    
    imei_test = "865083030056741"
    handler = MessageHandler()
    
    # 1. Configurar comando de bloqueio
    print("1. Configurando comando de BLOQUEIO...")
    handler.set_blocking_command(imei_test, True)
    
    # 2. Configurar comando de troca de IP
    print("2. Configurando comando de TROCA DE IP...")
    handler.set_ip_change_command(imei_test)
    
    # 3. Verificar comandos pendentes
    vehicle = db_manager.get_vehicle_by_imei(imei_test)
    if vehicle:
        print(f"   Comando bloqueio: {vehicle.get('comandobloqueo', 'N/A')}")
        print(f"   Comando troca IP: {vehicle.get('comandotrocarip', 'N/A')}")
        print(f"   Status bloqueado: {vehicle.get('bloqueado', 'N/A')}")
    
    # 4. Simular conexão e comando
    print("3. Simulando conexão de dispositivo...")
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 8000))
        
        # Enviar mensagem GPS para ativar execução imediata
        mensagem_gps = f"+RESP:GTFRI,060228,{imei_test},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12348$"
        print(f"   Enviando: {mensagem_gps[:50]}...")
        client_socket.send(mensagem_gps.encode('utf-8'))
        
        # Aguardar resposta do servidor
        comandos_recebidos = []
        start_time = time.time()
        
        while time.time() - start_time < 3:
            try:
                client_socket.settimeout(0.5)
                data = client_socket.recv(1024)
                if data:
                    response = data.decode('utf-8')
                    print(f"   Recebido: {response}")
                    
                    if "AT+GTOUT" in response:
                        comandos_recebidos.append("BLOQUEIO")
                    if "AT+GTIPSET" in response:
                        comandos_recebidos.append("TROCA_IP")
                        
                    # Simular confirmação se for comando de bloqueio
                    if "AT+GTOUT" in response and ",1," in response:
                        confirmacao = f"+ACK:GTOUT,060228,{imei_test},,0000,{time.strftime('%Y%m%d%H%M%S')},11F0$"
                        print(f"   Enviando confirmação: {confirmacao}")
                        client_socket.send(confirmacao.encode('utf-8'))
                        time.sleep(0.5)  # Aguardar processamento
                else:
                    break
            except socket.timeout:
                continue
        
        client_socket.close()
        
        # 5. Verificar status final
        print("4. Verificando status após comandos...")
        time.sleep(1)  # Aguardar processamento
        vehicle = db_manager.get_vehicle_by_imei(imei_test)
        if vehicle:
            print(f"   Comando bloqueio: {vehicle.get('comandobloqueo', 'N/A')}")
            print(f"   Comando troca IP: {vehicle.get('comandotrocarip', 'N/A')}")
            print(f"   Status bloqueado: {vehicle.get('bloqueado', 'N/A')}")
            
            # Resultados
            print("\n📊 RESULTADOS:")
            bloqueio_ok = "BLOQUEIO" in comandos_recebidos
            ip_ok = "TROCA_IP" in comandos_recebidos
            status_ok = vehicle.get('bloqueado') == True and vehicle.get('comandobloqueo') is None
            
            print(f"   Comando bloqueio enviado: {'✅' if bloqueio_ok else '❌'}")
            print(f"   Comando troca IP enviado: {'✅' if ip_ok else '❌'}")
            print(f"   Status atualizado corretamente: {'✅' if status_ok else '❌'}")
            
            if bloqueio_ok and ip_ok and status_ok:
                print("\n🎉 TODOS OS TESTES PASSARAM!")
                return True
            else:
                print("\n❌ ALGUNS TESTES FALHARAM")
                return False
        else:
            print("❌ Veículo não encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    sucesso = main()
    print("="*50)