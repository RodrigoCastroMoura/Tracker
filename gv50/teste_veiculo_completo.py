#!/usr/bin/env python3
"""
Teste Completo: Criar Veículo e Testar Sistema + Comandos
"""

import os
import time
from datetime import datetime

# Force correct configuration
os.environ['SERVER_PORT'] = '8000'
os.environ['DATABASE_NAME'] = 'track'

from database import db_manager
from models import Vehicle, VehicleData
from message_handler import MessageHandler

def criar_veiculo_teste():
    """Criar veículo de teste na base"""
    print("=== CRIANDO VEÍCULO DE TESTE ===")
    
    # IMEI real do dispositivo mencionado
    imei_teste = "865083030056741"
    
    veiculo = Vehicle(
        IMEI=imei_teste,
        dsplaca="ABC-1234",
        dsmodelo="GV50 GPS Tracker",
        comandobloqueo=None,  # Sem comando pendente
        bloqueado=False,      # Desbloqueado
        comandotrocarip=None, # Sem comando de IP
        ignicao=False,        # Ignição desligada
        bateriavoltagem=12.6, # Bateria normal
        bateriabaixa=False,   # Bateria OK
        ultimoalertabateria=None,
        tsusermanu=datetime.utcnow()
    )
    
    # Salvar veículo
    sucesso = db_manager.upsert_vehicle(veiculo)
    
    if sucesso:
        print(f"✅ Veículo criado: IMEI {imei_teste}")
        print(f"   Placa: {veiculo.dsplaca}")
        print(f"   Modelo: {veiculo.dsmodelo}")
        print(f"   Status: Desbloqueado, Ignição OFF")
        print(f"   Bateria: {veiculo.bateriavoltagem}V")
    else:
        print("❌ Erro ao criar veículo")
        
    return imei_teste if sucesso else None

def simular_dados_gps(imei):
    """Simular recebimento de dados GPS"""
    print("\n=== SIMULANDO DADOS GPS ===")
    
    handler = MessageHandler()
    
    # Mensagens GPS simuladas (São Paulo - diferentes localizações)
    mensagens_gps = [
        f"+RESP:GTFRI,060228,{imei},,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,20250127084500,0724,0000,18d8,6141,00,2000.0,12348$",
        f"+RESP:GTIGN,060228,{imei},,0,0,1,1,4.3,92,70.0,-46.635000,-23.551000,20250127084600,0724,0000,18d8,6141,00,2100.0,12349$",
        f"+RESP:GTFRI,060228,{imei},,0,0,1,1,4.5,95,75.0,-46.637000,-23.552000,20250127084700,0724,0000,18d8,6141,00,2200.0,12350$"
    ]
    
    for i, mensagem in enumerate(mensagens_gps, 1):
        print(f"\n📡 Processando mensagem {i}:")
        print(f"   {mensagem[:60]}...")
        
        # Processar mensagem
        resposta = handler.handle_incoming_message(mensagem, "177.94.51.99")
        
        if resposta:
            print(f"✅ Mensagem processada, ACK enviado")
            print(f"   Resposta: {resposta}")
        else:
            print("❌ Erro ao processar mensagem")
        
        time.sleep(1)
    
    return True

def verificar_dados_salvos(imei):
    """Verificar se dados foram salvos corretamente"""
    print("\n=== VERIFICANDO DADOS SALVOS ===")
    
    # Verificar veículo
    veiculo = db_manager.get_vehicle_by_imei(imei)
    if veiculo:
        print(f"✅ Veículo encontrado:")
        print(f"   IMEI: {veiculo['IMEI']}")
        print(f"   Placa: {veiculo['dsplaca']}")
        print(f"   Ignição: {'Ligada' if veiculo['ignicao'] else 'Desligada'}")
        print(f"   Bloqueado: {'Sim' if veiculo['bloqueado'] else 'Não'}")
        print(f"   Última atualização: {veiculo['tsusermanu']}")
    else:
        print("❌ Veículo não encontrado")
        return False
    
    # Verificar dados GPS
    collection = db_manager.db['vehicle_data']
    dados_gps = list(collection.find({'imei': imei}).sort('timestamp', -1).limit(5))
    
    print(f"\n📍 Dados GPS encontrados: {len(dados_gps)} registros")
    for i, dado in enumerate(dados_gps, 1):
        print(f"   {i}. Lat: {dado['latitude']}, Lon: {dado['longitude']}")
        print(f"      Time: {dado['timestamp']}")
    
    return len(dados_gps) > 0

def testar_comandos(imei):
    """Testar sistema de comandos"""
    print("\n=== TESTANDO COMANDOS ===")
    
    handler = MessageHandler()
    
    # Teste 1: Comando de bloqueio
    print("\n🔒 Teste 1: Comando de Bloqueio")
    resultado_block = handler.set_blocking_command(imei, True)
    print(f"   Comando enviado: {resultado_block}")
    
    # Verificar se comando foi salvo
    veiculo = db_manager.get_vehicle_by_imei(imei)
    if veiculo and veiculo.get('comandobloqueo') == True:
        print("   ✅ Comando de bloqueio definido no veículo")
    else:
        print("   ❌ Comando de bloqueio NÃO foi definido")
    
    time.sleep(1)
    
    # Teste 2: Comando de desbloqueio
    print("\n🔓 Teste 2: Comando de Desbloqueio")
    resultado_unblock = handler.set_blocking_command(imei, False)
    print(f"   Comando enviado: {resultado_unblock}")
    
    # Verificar comando
    veiculo = db_manager.get_vehicle_by_imei(imei)
    if veiculo and veiculo.get('comandobloqueo') == False:
        print("   ✅ Comando de desbloqueio definido")
    else:
        print("   ❌ Comando de desbloqueio NÃO foi definido")
    
    time.sleep(1)
    
    # Teste 3: Comando de troca de IP
    print("\n🌐 Teste 3: Comando de Troca de IP")
    resultado_ip = handler.set_ip_change_command(imei)
    print(f"   Comando enviado: {resultado_ip}")
    
    # Verificar comando de IP
    veiculo = db_manager.get_vehicle_by_imei(imei)
    if veiculo and veiculo.get('comandotrocarip') is not None:
        print("   ✅ Comando de troca de IP definido")
        print(f"   Comando: {veiculo.get('comandotrocarip')}")
    else:
        print("   ❌ Comando de troca de IP NÃO foi definido")
    
    return True

def simular_execucao_comandos(imei):
    """Simular execução de comandos pelo dispositivo"""
    print("\n=== SIMULANDO EXECUÇÃO DE COMANDOS ===")
    
    handler = MessageHandler()
    
    # Simular resposta GTOUT (comando executado)
    mensagem_comando = f"+RESP:GTOUT,060228,{imei},,0,0,1,1,4.3,92,70.0,-46.639000,-23.553000,20250127085000,0724,0000,18d8,6141,00,2300.0,12351$"
    
    print("📤 Simulando execução de comando pelo dispositivo:")
    print(f"   {mensagem_comando[:60]}...")
    
    # Processar comando
    resposta = handler.handle_incoming_message(mensagem_comando, "177.94.51.99")
    
    if resposta:
        print("✅ Comando executado pelo dispositivo")
        print(f"   ACK enviado: {resposta}")
        
        # Verificar se status foi atualizado
        veiculo = db_manager.get_vehicle_by_imei(imei)
        if veiculo:
            print(f"   Status bloqueado: {veiculo.get('bloqueado', 'N/A')}")
            print(f"   Comando pendente: {veiculo.get('comandobloqueo', 'N/A')}")
    else:
        print("❌ Erro ao processar comando")
    
    return True

def relatorio_final(imei):
    """Gerar relatório final do teste"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO FINAL DO TESTE")
    print("="*60)
    
    # Status do veículo
    veiculo = db_manager.get_vehicle_by_imei(imei)
    if veiculo:
        print(f"🚗 Veículo: {veiculo['dsplaca']} (IMEI: {veiculo['IMEI']})")
        print(f"   Modelo: {veiculo['dsmodelo']}")
        print(f"   Ignição: {'🔥 Ligada' if veiculo['ignicao'] else '❄️ Desligada'}")
        print(f"   Status: {'🔒 Bloqueado' if veiculo['bloqueado'] else '🔓 Desbloqueado'}")
        print(f"   Bateria: {veiculo['bateriavoltagem']}V")
        print(f"   Última atualização: {veiculo['tsusermanu']}")
    
    # Contagem de dados
    collection = db_manager.db['vehicle_data']
    total_dados = collection.count_documents({'imei': imei})
    print(f"\n📍 Total de registros GPS: {total_dados}")
    
    # Último dado GPS
    ultimo_dado = collection.find_one({'imei': imei}, sort=[('timestamp', -1)])
    if ultimo_dado:
        print(f"   Última posição: {ultimo_dado['latitude']}, {ultimo_dado['longitude']}")
        print(f"   Última atualização: {ultimo_dado['timestamp']}")
    
    print("\n✅ TESTE COMPLETO FINALIZADO")
    print("="*60)

def main():
    """Executar teste completo"""
    print("🧪 TESTE COMPLETO: VEÍCULO + SISTEMA + COMANDOS")
    print("="*60)
    print(f"🕐 Iniciado em: {datetime.now()}")
    print("="*60)
    
    # 1. Criar veículo
    imei = criar_veiculo_teste()
    if not imei:
        print("❌ Falha ao criar veículo - teste abortado")
        return False
    
    # 2. Simular dados GPS
    if not simular_dados_gps(imei):
        print("❌ Falha ao simular dados GPS")
        return False
    
    # 3. Verificar dados salvos
    if not verificar_dados_salvos(imei):
        print("❌ Falha ao verificar dados salvos")
        return False
    
    # 4. Testar comandos
    if not testar_comandos(imei):
        print("❌ Falha ao testar comandos")
        return False
    
    # 5. Simular execução de comandos
    if not simular_execucao_comandos(imei):
        print("❌ Falha ao simular execução de comandos")
        return False
    
    # 6. Relatório final
    relatorio_final(imei)
    
    return True

if __name__ == "__main__":
    sucesso = main()
    exit(0 if sucesso else 1)