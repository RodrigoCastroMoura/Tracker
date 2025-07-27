#!/usr/bin/env python3
"""
Teste Real: Verificar se comandos são enviados ao dispositivo
"""

import os
import time
from datetime import datetime

# Force correct configuration
os.environ['SERVER_PORT'] = '8000'
os.environ['DATABASE_NAME'] = 'track'

from database import db_manager
from message_handler import MessageHandler

def testar_comando_bloqueio():
    """Testar se comando de bloqueio é realmente enviado"""
    print("=== TESTE REAL DE COMANDO DE BLOQUEIO ===")
    
    imei = "865083030056741"
    handler = MessageHandler()
    
    # 1. Definir comando de bloqueio
    print("1. Definindo comando de bloqueio...")
    handler.set_blocking_command(imei, True)
    
    # Verificar se comando foi salvo
    vehicle = db_manager.get_vehicle_by_imei(imei)
    if vehicle and vehicle.get('comandobloqueo') == True:
        print("✅ Comando SALVO no banco: comandobloqueo = True")
    else:
        print("❌ Comando NÃO foi salvo")
        return False
    
    # 2. Simular mensagem do dispositivo (isso deveria disparar o comando)
    print("\n2. Simulando mensagem do dispositivo...")
    mensagem_gps = f"+RESP:GTFRI,060228,{imei},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12348$"
    
    print(f"Enviando: {mensagem_gps[:60]}...")
    
    # Processar mensagem - AQUI deve enviar o comando
    resposta = handler.handle_incoming_message(mensagem_gps, "177.94.51.99")
    
    print(f"\n3. Resposta recebida:")
    if resposta:
        print(f"   {resposta}")
        
        # Verificar se é comando de bloqueio
        if "AT+GTRTO" in resposta and ",1," in resposta:
            print("✅ COMANDO DE BLOQUEIO ENVIADO CORRETAMENTE!")
            print("   Formato: AT+GTRTO=gv50,1,... (1 = bloquear)")
            return True
        elif "+ACK:" in resposta:
            print("❌ PROBLEMA: Apenas ACK foi enviado, comando não foi enviado")
            print("   O sistema deveria enviar comando AT ao invés de ACK")
            return False
        else:
            print(f"❌ RESPOSTA INESPERADA: {resposta}")
            return False
    else:
        print("❌ Nenhuma resposta - erro crítico")
        return False

def testar_comando_desbloqueio():
    """Testar comando de desbloqueio"""
    print("\n=== TESTE DE COMANDO DE DESBLOQUEIO ===")
    
    imei = "865083030056741"
    handler = MessageHandler()
    
    # Definir comando de desbloqueio
    print("1. Definindo comando de desbloqueio...")
    handler.set_blocking_command(imei, False)
    
    # Simular mensagem
    mensagem_gps = f"+RESP:GTFRI,060228,{imei},,0,0,1,1,4.3,92,70.0,-46.635000,-23.551000,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2100.0,12349$"
    
    resposta = handler.handle_incoming_message(mensagem_gps, "177.94.51.99")
    
    if resposta and "AT+GTRTO" in resposta and ",0," in resposta:
        print("✅ COMANDO DE DESBLOQUEIO ENVIADO!")
        print("   Formato: AT+GTRTO=gv50,0,... (0 = desbloquear)")
        return True
    else:
        print("❌ Comando de desbloqueio NÃO foi enviado")
        return False

def verificar_status_pos_comando():
    """Verificar se comando foi limpo após envio"""
    print("\n=== VERIFICANDO STATUS PÓS-COMANDO ===")
    
    imei = "865083030056741"
    vehicle = db_manager.get_vehicle_by_imei(imei)
    
    if vehicle:
        print(f"Estado atual do veículo:")
        print(f"   comandobloqueo: {vehicle.get('comandobloqueo')}")
        print(f"   bloqueado: {vehicle.get('bloqueado')}")
        print(f"   comandotrocarip: {vehicle.get('comandotrocarip')}")
        
        # IMPORTANTE: Comando deveria continuar True até dispositivo confirmar
        if vehicle.get('comandobloqueo') is not None:
            print("✅ Comando ainda está pendente (correto)")
            print("   Será limpo quando dispositivo confirmar com GTOUT")
        else:
            print("⚠️ Comando foi limpo imediatamente (pode estar incorreto)")
    
    return True

def main():
    """Executar testes de comando"""
    print("🧪 TESTE CRÍTICO: ENVIO DE COMANDOS PARA DISPOSITIVO")
    print("="*60)
    print("OBJETIVO: Verificar se comandos são REALMENTE enviados")
    print("="*60)
    
    # Testar bloqueio
    sucesso_block = testar_comando_bloqueio()
    time.sleep(2)
    
    # Testar desbloqueio
    sucesso_unblock = testar_comando_desbloqueio()
    time.sleep(2)
    
    # Verificar status
    verificar_status_pos_comando()
    
    # Resultado final
    print("\n" + "="*60)
    print("📊 RESULTADO FINAL")
    print("="*60)
    
    if sucesso_block and sucesso_unblock:
        print("🎉 SUCESSO TOTAL!")
        print("✅ Comandos de bloqueio/desbloqueio funcionando")
        print("✅ Sistema envia AT commands corretamente")
        print("✅ Problema original RESOLVIDO")
    else:
        print("❌ FALHA DETECTADA!")
        print(f"   Bloqueio: {'✅' if sucesso_block else '❌'}")
        print(f"   Desbloqueio: {'✅' if sucesso_unblock else '❌'}")
        print("   Verificar implementação")
    
    print("="*60)
    
    return sucesso_block and sucesso_unblock

if __name__ == "__main__":
    sucesso = main()
    exit(0 if sucesso else 1)