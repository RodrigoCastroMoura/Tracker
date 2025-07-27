#!/usr/bin/env python3
"""
Teste direto: Comandos a cada mensagem
"""

import os
import socket
import time

os.environ['SERVER_PORT'] = '8000'
os.environ['DATABASE_NAME'] = 'track'

from message_handler import MessageHandler

def main():
    print("🧪 TESTE DIRETO: COMANDOS A CADA MENSAGEM")
    
    imei = "865083030056741"
    handler = MessageHandler()
    
    # 1. Configurar comando
    print("1. Configurando comando de bloqueio...")
    handler.set_blocking_command(imei, True)
    
    # 2. Simular conexão e envio de mensagens
    print("2. Testando conexão permanente...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 8000))
        sock.settimeout(3)
        
        # Primeira mensagem
        msg1 = f"+RESP:GTFRI,060228,{imei},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,20250727120000,0724,0000,18d8,6141,00,2000.0,12348$"
        print("   Enviando mensagem 1...")
        sock.send(msg1.encode())
        
        # Verificar resposta
        try:
            resp = sock.recv(1024).decode()
            print(f"   Resposta: {resp[:60]}...")
            if "AT+GTOUT" in resp:
                print("   ✅ COMANDO ENVIADO!")
                return True
        except:
            pass
        
        # Segunda mensagem (caso não tenha funcionado na primeira)
        time.sleep(1)
        msg2 = f"+RESP:GTFRI,060228,{imei},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,20250727120100,0724,0000,18d8,6141,00,2000.0,12349$"
        print("   Enviando mensagem 2...")
        sock.send(msg2.encode())
        
        try:
            resp = sock.recv(1024).decode()
            print(f"   Resposta: {resp[:60]}...")
            if "AT+GTOUT" in resp:
                print("   ✅ COMANDO ENVIADO!")
                return True
        except:
            pass
            
        sock.close()
        
    except Exception as e:
        print(f"   Erro: {e}")
    
    print("   ❌ Comando não foi enviado")
    return False

if __name__ == "__main__":
    main()