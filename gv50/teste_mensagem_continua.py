#!/usr/bin/env python3
"""
Teste: Comando executado a cada mensagem (dispositivo conectado permanentemente)
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
    print("🧪 TESTE: DISPOSITIVO CONECTADO PERMANENTEMENTE")
    print("="*60)
    
    imei_test = "865083030056741"
    handler = MessageHandler()
    
    try:
        # 1. Conectar ao servidor (simular conexão permanente)
        print("1. Conectando ao servidor (conexão permanente)...")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 8000))
        client_socket.settimeout(2)
        print("   ✅ Conectado permanentemente")
        
        # 2. Enviar primeira mensagem GPS (sem comando pendente)
        print("\n2. Enviando primeira mensagem GPS (sem comando)...")
        mensagem1 = f"+RESP:GTFRI,060228,{imei_test},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12348$"
        client_socket.send(mensagem1.encode('utf-8'))
        
        # Aguardar resposta
        try:
            response = client_socket.recv(1024).decode('utf-8')
            print(f"   Resposta: {response[:50]}...")
        except socket.timeout:
            print("   Sem comando (esperado)")
        
        # 3. Configurar comando de bloqueio
        print("\n3. Configurando comando de BLOQUEIO...")
        handler.set_blocking_command(imei_test, True)
        print("   ✅ Comando configurado no banco")
        
        # 4. Enviar segunda mensagem GPS (agora COM comando pendente)
        print("\n4. Enviando segunda mensagem GPS (com comando pendente)...")
        time.sleep(1)
        mensagem2 = f"+RESP:GTFRI,060228,{imei_test},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12349$"
        client_socket.send(mensagem2.encode('utf-8'))
        
        # Aguardar comando de bloqueio
        comando_recebido = False
        try:
            response = client_socket.recv(1024).decode('utf-8')
            print(f"   Resposta: {response}")
            if "AT+GTOUT" in response and ",1," in response:
                comando_recebido = True
                print("   🔒 COMANDO DE BLOQUEIO RECEBIDO!")
                
                # Enviar confirmação
                confirmacao = f"+ACK:GTOUT,060228,{imei_test},,0000,{time.strftime('%Y%m%d%H%M%S')},11F0$"
                client_socket.send(confirmacao.encode('utf-8'))
                print("   📤 Confirmação enviada")
        except socket.timeout:
            print("   ❌ Nenhum comando recebido")
        
        # 5. Configurar comando de troca de IP
        print("\n5. Configurando comando de TROCA DE IP...")
        handler.set_ip_change_command(imei_test)
        print("   ✅ Comando IP configurado")
        
        # 6. Enviar terceira mensagem GPS (comando de IP)
        print("\n6. Enviando terceira mensagem GPS (comando IP pendente)...")
        time.sleep(1)
        mensagem3 = f"+RESP:GTFRI,060228,{imei_test},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12350$"
        client_socket.send(mensagem3.encode('utf-8'))
        
        # Aguardar comando de IP
        comando_ip_recebido = False
        try:
            response = client_socket.recv(1024).decode('utf-8')
            print(f"   Resposta: {response}")
            if "AT+GTIPSET" in response:
                comando_ip_recebido = True
                print("   🌐 COMANDO DE TROCA DE IP RECEBIDO!")
        except socket.timeout:
            print("   ❌ Nenhum comando IP recebido")
        
        # 7. Enviar quarta mensagem (sem comandos pendentes)
        print("\n7. Enviando quarta mensagem GPS (sem comandos)...")
        time.sleep(1)
        mensagem4 = f"+RESP:GTFRI,060228,{imei_test},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12351$"
        client_socket.send(mensagem4.encode('utf-8'))
        
        try:
            response = client_socket.recv(1024).decode('utf-8')
            print(f"   Resposta: {response[:50]}...")
        except socket.timeout:
            print("   Sem comando (esperado)")
        
        client_socket.close()
        
        # 8. Verificar status final
        print("\n8. Verificando status final no banco...")
        time.sleep(1)
        vehicle = db_manager.get_vehicle_by_imei(imei_test)
        if vehicle:
            print(f"   Status bloqueado: {vehicle.get('bloqueado', 'N/A')}")
            print(f"   Comando bloqueio: {vehicle.get('comandobloqueo', 'N/A')}")
            print(f"   Comando troca IP: {vehicle.get('comandotrocarip', 'N/A')}")
        
        # 9. Resultados
        print("\n" + "="*60)
        print("📊 RESULTADOS DO TESTE:")
        print(f"   Comando bloqueio enviado: {'✅' if comando_recebido else '❌'}")
        print(f"   Comando troca IP enviado: {'✅' if comando_ip_recebido else '❌'}")
        
        status_ok = vehicle and vehicle.get('bloqueado') == True
        print(f"   Status atualizado: {'✅' if status_ok else '❌'}")
        
        if comando_recebido and comando_ip_recebido and status_ok:
            print("\n🎉 SUCESSO! COMANDOS EXECUTADOS A CADA MENSAGEM!")
            print("✅ Sistema funciona com dispositivo conectado permanentemente")
            return True
        else:
            print("\n❌ FALHA! Alguns comandos não foram executados")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    sucesso = main()
    print("="*60)