#!/usr/bin/env python3
"""
Script para monitorar dispositivos conectados ao servidor GV50
Mostra quantos dispositivos estão atualmente conectados
"""

import asyncio
import sys
import os
from datetime import datetime

# Adicionar pasta ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tcp_server import tcp_server
from database import db_manager


async def show_connected_devices():
    """Mostra dispositivos conectados"""
    print("=" * 70)
    print("📊 MONITORAMENTO DE DISPOSITIVOS GV50")
    print("=" * 70)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Conexões ativas no servidor
    connection_count = tcp_server.get_connection_count()
    print(f"🔌 Conexões TCP Ativas: {connection_count}")
    
    if connection_count > 0:
        print("\n📱 Dispositivos Conectados:")
        print("-" * 70)
        print(f"{'IMEI':<20} {'IP':<20} {'Última Atividade':<25}")
        print("-" * 70)
        
        for imei, connection in tcp_server.connections.items():
            last_activity = connection.last_activity.strftime('%Y-%m-%d %H:%M:%S')
            print(f"{imei:<20} {connection.client_ip:<20} {last_activity:<25}")
    
    print()
    
    # Estatísticas do banco de dados
    try:
        # Contar total de veículos cadastrados
        from models import Vehicle
        total_vehicles = Vehicle.objects.count()
        active_vehicles = Vehicle.objects(status='active').count()
        
        print(f"📊 ESTATÍSTICAS DO BANCO DE DADOS")
        print("-" * 70)
        print(f"Total de veículos cadastrados: {total_vehicles}")
        print(f"Veículos ativos: {active_vehicles}")
        
        # Mostrar últimos 10 veículos que reportaram
        print(f"\n📍 Últimos 10 Veículos que Reportaram:")
        print("-" * 70)
        print(f"{'IMEI':<20} {'Placa':<10} {'Última Atualização':<25}")
        print("-" * 70)
        
        recent = Vehicle.objects(tsusermanu__exists=True).order_by('-tsusermanu').limit(10)
        
        for vehicle in recent:
            imei = vehicle.IMEI or "N/A"
            placa = vehicle.dsplaca or "N/A"
            last_update = vehicle.tsusermanu.strftime('%Y-%m-%d %H:%M:%S') if vehicle.tsusermanu else "N/A"
            print(f"{imei:<20} {placa:<10} {last_update:<25}")
        
    except Exception as e:
        print(f"⚠️  Erro ao consultar banco: {e}")
    
    print()
    print("=" * 70)


async def monitor_loop():
    """Loop de monitoramento contínuo"""
    try:
        while True:
            # Limpar tela (funciona no Windows e Linux)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            await show_connected_devices()
            
            print("\n⏸️  Atualizando a cada 10 segundos... (Ctrl+C para sair)")
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoramento encerrado")


def show_once():
    """Mostra status uma única vez"""
    asyncio.run(show_connected_devices())


def monitor_continuous():
    """Monitor contínuo"""
    asyncio.run(monitor_loop())


def main():
    """Função principal"""
    print("\n📊 Monitor de Dispositivos GV50")
    print("\n1. Ver status agora")
    print("2. Monitor contínuo (atualiza a cada 10s)")
    print("0. Sair")
    
    choice = input("\nEscolha uma opção: ")
    
    if choice == '1':
        show_once()
    elif choice == '2':
        monitor_continuous()
    else:
        print("Saindo...")


if __name__ == "__main__":
    # Se chamado com argumento --continuous ou -c, inicia modo contínuo direto
    if len(sys.argv) > 1 and sys.argv[1] in ['--continuous', '-c']:
        monitor_continuous()
    else:
        main()