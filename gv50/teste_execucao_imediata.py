#!/usr/bin/env python3
"""
Teste: EXECUÇÃO IMEDIATA de comandos quando dispositivo conecta
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

def configurar_comando_antes_conexao():
    """Configurar comando ANTES do dispositivo conectar"""
    print("=== CONFIGURANDO COMANDO ANTES DA CONEXÃO ===")
    
    imei_test = "865083030056741"
    handler = MessageHandler()
    
    # Configurar comando de bloqueio ANTES da conexão
    print("1. Configurando comando de BLOQUEIO antes da conexão...")
    handler.set_blocking_command(imei_test, True)  # TRUE = BLOQUEAR
    
    # Verificar configuração
    vehicle = db_manager.get_vehicle_by_imei(imei_test)
    if vehicle:
        print(f"   ✅ Comando configurado: comandobloqueo = {vehicle.get('comandobloqueo')}")
        print(f"   ✅ Status atual: bloqueado = {vehicle.get('bloqueado', False)}")
        return imei_test
    
    return None

def simular_primeira_conexao(imei):
    """Simular primeira conexão do dispositivo - deve executar comando imediatamente"""
    print(f"\n=== SIMULANDO PRIMEIRA CONEXÃO DO DISPOSITIVO {imei} ===")
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 8000))
        print("✅ Dispositivo conectado ao servidor TCP")
        
        # Enviar PRIMEIRA mensagem GPS (deve disparar execução imediata)
        mensagem_gps = f"+RESP:GTFRI,060228,{imei},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12348$"
        
        print("📡 Enviando primeira mensagem GPS...")
        print("⚡ EXPECTATIVA: Comando deve ser executado IMEDIATAMENTE")
        
        client_socket.send(mensagem_gps.encode('utf-8'))
        
        # Aguardar resposta imediata
        print("⏳ Aguardando execução imediata do comando...")
        
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
                    
                    # Verificar execução imediata
                    if "AT+GTOUT" in response:
                        if ",1," in response:
                            print("⚡ EXECUÇÃO IMEDIATA DETECTADA!")
                            print("   ✅ Comando de bloqueio enviado imediatamente na conexão")
                            
                            # Simular confirmação
                            confirmacao = f"+ACK:GTOUT,060228,{imei},,0000,20250727{time.strftime('%H%M%S')},11F0$"
                            print(f"📤 Enviando confirmação: {confirmacao}")
                            client_socket.send(confirmacao.encode('utf-8'))
                        elif ",0," in response:
                            print("⚡ EXECUÇÃO IMEDIATA DETECTADA!")
                            print("   ✅ Comando de desbloqueio enviado imediatamente na conexão")
                            
                            # Simular confirmação
                            confirmacao = f"+ACK:GTOUT,060228,{imei},,0000,20250727{time.strftime('%H%M%S')},11F0$"
                            print(f"📤 Enviando confirmação: {confirmacao}")
                            client_socket.send(confirmacao.encode('utf-8'))
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

def verificar_execucao_imediata(imei, responses):
    """Verificar se comando foi executado imediatamente"""
    print("\n=== VERIFICANDO EXECUÇÃO IMEDIATA ===")
    
    execucao_imediata = False
    tipo_comando = None
    
    for response in responses:
        if "AT+GTOUT" in response:
            execucao_imediata = True
            if ",1," in response:
                tipo_comando = "BLOQUEIO"
            elif ",0," in response:
                tipo_comando = "DESBLOQUEIO"
            break
    
    # Verificar status no banco
    vehicle = db_manager.get_vehicle_by_imei(imei)
    if vehicle:
        print(f"\n📊 Status após execução imediata:")
        print(f"   IMEI: {vehicle['IMEI']}")
        print(f"   Comando pendente: {vehicle.get('comandobloqueo', 'N/A')}")
        print(f"   Status bloqueado: {vehicle.get('bloqueado', 'N/A')}")
        print(f"   Última atualização: {vehicle.get('tsusermanu', 'N/A')}")
    
    if execucao_imediata:
        print(f"\n🎉 EXECUÇÃO IMEDIATA FUNCIONANDO!")
        print(f"✅ Comando de {tipo_comando} executado na conexão")
        print("✅ Não precisa aguardar protocolos específicos")
        return True
    else:
        print("\n❌ EXECUÇÃO IMEDIATA FALHOU!")
        print("❌ Comando não foi enviado na primeira conexão")
        return False

def main():
    """Teste completo de execução imediata"""
    print("⚡ TESTE: EXECUÇÃO IMEDIATA DE COMANDOS")
    print("="*60)
    print("OBJETIVO: Comandos executados assim que dispositivo conecta")
    print("VANTAGEM: Não precisa aguardar mensagens específicas")
    print("="*60)
    
    # 1. Configurar comando antes da conexão
    imei = configurar_comando_antes_conexao()
    if not imei:
        print("❌ Falha na configuração")
        return False
    
    time.sleep(2)  # Aguardar servidor estar pronto
    
    # 2. Simular primeira conexão
    responses = simular_primeira_conexao(imei)
    
    # 3. Verificar execução imediata
    sucesso = verificar_execucao_imediata(imei, responses)
    
    print("\n" + "="*60)
    if sucesso:
        print("🎉 EXECUÇÃO IMEDIATA IMPLEMENTADA COM SUCESSO!")
        print("✅ Comandos executados imediatamente na conexão")
        print("✅ Sistema mais eficiente e responsivo")
        print("✅ Dispositivos recebem comandos instantaneamente")
    else:
        print("❌ EXECUÇÃO IMEDIATA PRECISA DE AJUSTES!")
        print("❌ Comandos ainda aguardam protocolos específicos")
    print("="*60)
    
    return sucesso

if __name__ == "__main__":
    sucesso = main()
    exit(0 if sucesso else 1)