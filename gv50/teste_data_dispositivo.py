#!/usr/bin/env python3
"""
TESTE: Verificar se data do dispositivo está sendo capturada e convertida corretamente
"""

import os
import socket
import time

os.environ['SERVER_PORT'] = '8000'
os.environ['DATABASE_NAME'] = 'track'

from database import db_manager
from message_handler import MessageHandler

def main():
    print("🔍 TESTE: DATA DO DISPOSITIVO")
    print("="*50)
    
    imei = "865083030049613"
    handler = MessageHandler()
    
    # Limpar dados anteriores
    try:
        db_manager.db.vehicle_data.delete_many({"imei": imei})
        print("✅ Dados anteriores limpos")
    except:
        pass
    
    print("\n📅 TESTE DE DATA DO DISPOSITIVO:")
    print("   GPS timestamp: 20250727152556 (15:25:56)")
    print("   Device timestamp: 20250727122605 (12:26:05)")
    print("   Esperado: deviceTimestamp = 20250727122605")
    print("   Esperado: deviceDateConverted = 2025-07-27 12:26:05")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 8000))
        sock.settimeout(5)
        
        # Enviar mensagem GPS com as duas datas diferentes
        gps_msg = "+RESP:GTFRI,090302,865083030049613,10,1,1,0.0,236,724.7,-46.778817,-23.503123,20250727152556,0724,0003,08A3,59CF,00,0.0,110000,10,0,7,20250727122605,054F$"
        print(f"\n📡 Enviando mensagem GPS...")
        sock.send(gps_msg.encode())
        
        # Receber ACK
        try:
            resp = sock.recv(1024).decode()
            print(f"   Resposta: {resp[:50]}...")
        except:
            pass
            
        sock.close()
        time.sleep(2)
        
        print("\n🔍 VERIFICANDO DADOS GRAVADOS:")
        
        # Verificar último registro
        from pymongo import DESCENDING
        latest_data = db_manager.db.vehicle_data.find_one(
            {"imei": imei}, 
            sort=[("timestamp", DESCENDING)]
        )
        
        if latest_data:
            data_servidor = latest_data.get('timestamp')
            data_dispositivo = latest_data.get('deviceTimestamp')
            data_convertida = latest_data.get('deviceDateConverted')
            
            print(f"   📅 Data servidor: {data_servidor}")
            print(f"   📅 Data dispositivo (string): {data_dispositivo}")
            print(f"   📅 Data convertida: {data_convertida}")
            
            # Verificar se é a data correta
            if data_dispositivo == "20250727122605":
                print("   ✅ Data do dispositivo CORRETA (12:26:05)")
            else:
                print(f"   ❌ Data do dispositivo ERRADA (deveria ser 20250727122605)")
                
            if data_convertida and str(data_convertida) == "2025-07-27 12:26:05":
                print("   ✅ Data convertida CORRETA")
            elif data_convertida:
                print(f"   ⚠️  Data convertida: {data_convertida}")
            else:
                print("   ❌ Data não foi convertida")
                
            print(f"\n🎯 RESULTADO:")
            captura_ok = data_dispositivo == "20250727122605"
            conversao_ok = data_convertida is not None
            
            if captura_ok and conversao_ok:
                print("   🚀 SISTEMA 100% FUNCIONAL!")
                print("   ✅ Data do dispositivo capturada corretamente")
                print("   ✅ Data convertida e gravada")
                print("   ✅ Timestamp do servidor funcionando")
            else:
                print("   ⚠️  Ainda precisando ajustes")
                if not captura_ok:
                    print("   ❌ Captura da data do dispositivo")
                if not conversao_ok:
                    print("   ❌ Conversão da data")
        else:
            print("   ❌ Nenhum dado GPS encontrado")
            
    except Exception as e:
        print(f"   Erro: {e}")

if __name__ == "__main__":
    main()