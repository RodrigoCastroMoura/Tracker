#!/usr/bin/env python3
"""
Teste Final: Verificar integração TCP + Comando
"""

import os
import time
from datetime import datetime

# Force correct configuration
os.environ['SERVER_PORT'] = '8000'
os.environ['DATABASE_NAME'] = 'track'

from database import db_manager
from message_handler import MessageHandler

def main():
    """Testar se comandos estão sendo executados corretamente"""
    print("🧪 TESTE FINAL: VERIFICAÇÃO DE COMANDO")
    print("="*50)
    
    # Setup
    imei_test = "865083030056741"
    handler = MessageHandler()
    
    # 1. Definir comando de bloqueio
    print("1. Definindo comando de bloqueio no banco...")
    handler.set_blocking_command(imei_test, True)
    
    # Alterar status para disparar comando
    print("2. Alterando status bloqueado para TRUE (para disparar comando)...")
    vehicle = db_manager.get_vehicle_by_imei(imei_test)
    if vehicle:
        vehicle_data = dict(vehicle)
        # Remover _id para evitar erro
        if '_id' in vehicle_data:
            del vehicle_data['_id']
        vehicle_data['bloqueado'] = True  # Forçar status de bloqueado
        vehicle_data['comandobloqueo'] = True  # Comando pendente
        
        from models import Vehicle
        updated_vehicle = Vehicle(**vehicle_data)
        db_manager.upsert_vehicle(updated_vehicle)
        print("✅ Status atualizado: bloqueado=True, comandobloqueo=True")
    
    # 3. Simular mensagem para disparar comando
    print("3. Simulando mensagem GPS para disparar comando...")
    mensagem_gps = f"+RESP:GTFRI,060228,{imei_test},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,{datetime.now().strftime('%Y%m%d%H%M%S')},0724,0000,18d8,6141,00,2000.0,12348$"
    
    response = handler.handle_incoming_message(mensagem_gps, "177.94.51.99")
    print(f"Resposta: {response}")
    
    # 4. Verificar se comando foi enfileirado
    print("4. Verificando comandos pendentes...")
    pending = handler.get_pending_command(imei_test)
    if pending:
        print(f"✅ COMANDO ENCONTRADO: {pending}")
        
        # Verificar formato do comando
        if "AT+GTOUT=gv50,1," in pending:
            print("✅ Formato correto: Comando de BLOQUEIO (bit=1)")
        elif "AT+GTOUT=gv50,0," in pending:
            print("✅ Formato correto: Comando de DESBLOQUEIO (bit=0)")
        else:
            print(f"❌ Formato incorreto: {pending}")
            
        return True
    else:
        print("❌ NENHUM COMANDO PENDENTE ENCONTRADO")
        return False

if __name__ == "__main__":
    sucesso = main()
    print("\n" + "="*50)
    if sucesso:
        print("🎉 TESTE APROVADO: Sistema de comandos funcionando!")
    else:
        print("❌ TESTE FALHOU: Comandos não estão sendo gerados")
    print("="*50)
    exit(0 if sucesso else 1)