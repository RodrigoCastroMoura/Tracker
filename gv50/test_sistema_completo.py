#!/usr/bin/env python3
"""
Teste Completo do Sistema GV50
Testa todas as funcionalidades usando a database tracker
"""

import os
import sys
import time
import socket
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Force correct configuration
os.environ['SERVER_PORT'] = '8000'
os.environ['DATABASE_NAME'] = 'track'

# Import system components
from database import db_manager
from models import Vehicle, VehicleData
from message_handler import MessageHandler
from protocol_parser import QueclinkProtocolParser
from config import Config

class TesteSistemaCompleto:
    """Classe para testar todo o sistema GV50"""
    
    def __init__(self):
        self.handler = MessageHandler()
        self.parser = QueclinkProtocolParser()
        self.test_results = []
        self.test_imei = "865083030999999"  # IMEI de teste
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log dos resultados dos testes"""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.utcnow()
        })
        
    def test_1_database_connection(self):
        """Teste 1: Conexão com database"""
        try:
            # Testar conexão
            connected = db_manager.test_connection()
            
            # Verificar collections
            collections = db_manager.db.list_collection_names()
            has_vehicles = 'vehicles' in collections
            has_vehicle_data = 'vehicle_data' in collections
            
            success = connected and has_vehicles and has_vehicle_data
            details = f"Collections: {collections}, Connected: {connected}"
            
            self.log_test("Conexão Database", success, details)
            return success
            
        except Exception as e:
            self.log_test("Conexão Database", False, str(e))
            return False
    
    def test_2_vehicle_crud(self):
        """Teste 2: CRUD de veículos"""
        try:
            # Criar veículo de teste
            test_vehicle = Vehicle(
                IMEI=self.test_imei,
                dsplaca="TEST-001",
                dsmodelo="GV50 Test",
                comandobloqueo=None,
                bloqueado=False,
                comandotrocarip=None,
                ignicao=False,
                bateriavoltagem=12.5,
                bateriabaixa=False,
                ultimoalertabateria=None,
                tsusermanu=datetime.utcnow()
            )
            
            # CREATE - Inserir veículo
            created = db_manager.upsert_vehicle(test_vehicle)
            
            # READ - Buscar veículo
            found = db_manager.get_vehicle_by_imei(self.test_imei)
            
            # UPDATE - Atualizar veículo
            test_vehicle.ignicao = True
            test_vehicle.bateriavoltagem = 11.8
            updated = db_manager.upsert_vehicle(test_vehicle)
            
            # Verificar atualização
            updated_vehicle = db_manager.get_vehicle_by_imei(self.test_imei)
            
            success = (created and found and updated and 
                      updated_vehicle and updated_vehicle['ignicao'] == True)
            
            details = f"Created: {created}, Found: {found is not None}, Updated: {updated}"
            self.log_test("CRUD Veículos", success, details)
            return success
            
        except Exception as e:
            self.log_test("CRUD Veículos", False, str(e))
            return False
    
    def test_3_vehicle_data_storage(self):
        """Teste 3: Armazenamento de dados GPS"""
        try:
            # Criar dados de localização
            test_data = VehicleData(
                imei=self.test_imei,
                longitude="-46.633308",
                latitude="-23.550520",  # São Paulo
                altitude=760.0,
                timestamp=datetime.utcnow(),
                deviceTimestamp=datetime.utcnow(),
                systemDate=datetime.utcnow(),
                mensagem_raw="+RESP:GTFRI,060228,865083030999999,,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,20250724100000,0724,0000,18d8,6141,00,2000.0,12348$"
            )
            
            # Salvar dados
            saved = db_manager.insert_vehicle_data(test_data)
            
            # Verificar se foi salvo
            collection = db_manager.db['vehicle_data']
            found_data = collection.find_one({'imei': self.test_imei})
            
            success = saved and found_data is not None
            details = f"Saved: {saved}, Found: {found_data is not None}"
            
            self.log_test("Dados GPS", success, details)
            return success
            
        except Exception as e:
            self.log_test("Dados GPS", False, str(e))
            return False
    
    def test_4_protocol_parsing(self):
        """Teste 4: Parse de mensagens do protocolo"""
        try:
            # Mensagens de teste reais do protocolo GV50
            test_messages = [
                "+RESP:GTFRI,060228,865083030999999,,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,20250724100000,0724,0000,18d8,6141,00,2000.0,12348$",
                "+RESP:GTIGN,060228,865083030999999,,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,20250724100000,0724,0000,18d8,6141,00,2000.0,12348$",
                "+RESP:GTIGF,060228,865083030999999,,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,20250724100000,0724,0000,18d8,6141,00,2000.0,12348$"
            ]
            
            successful_parses = 0
            
            for msg in test_messages:
                try:
                    parsed = self.parser.parse_message(msg)
                    if parsed and 'imei' in parsed:
                        successful_parses += 1
                except Exception:
                    pass
            
            success = successful_parses == len(test_messages)
            details = f"Parsed {successful_parses}/{len(test_messages)} messages"
            
            self.log_test("Parse Protocolo", success, details)
            return success
            
        except Exception as e:
            self.log_test("Parse Protocolo", False, str(e))
            return False
    
    def test_5_message_processing(self):
        """Teste 5: Processamento completo de mensagens"""
        try:
            # Mensagem GTFRI (localização)
            location_msg = "+RESP:GTFRI,060228,865083030999999,,0,0,1,1,4.3,92,70.0,-46.633308,-23.550520,20250724100000,0724,0000,18d8,6141,00,2000.0,12348$"
            
            # Processar mensagem usando handle_incoming_message
            response = self.handler.handle_incoming_message(location_msg, "127.0.0.1")
            
            # Verificar se dados foram salvos
            vehicle = db_manager.get_vehicle_by_imei(self.test_imei)
            
            collection = db_manager.db['vehicle_data']
            data_count = collection.count_documents({'imei': self.test_imei})
            
            success = response is not None and vehicle is not None and data_count > 0
            details = f"Response: {response is not None}, Vehicle: {vehicle is not None}, Data records: {data_count}"
            
            self.log_test("Processamento Mensagens", success, details)
            return success
            
        except Exception as e:
            self.log_test("Processamento Mensagens", False, str(e))
            return False
    
    def test_6_command_system(self):
        """Teste 6: Sistema de comandos"""
        try:
            # Testar comando de bloqueio
            block_result = self.handler.set_blocking_command(self.test_imei, True)
            
            # Verificar se comando foi definido
            vehicle = db_manager.get_vehicle_by_imei(self.test_imei)
            has_block_command = vehicle and vehicle.get('comandobloqueo') == True
            
            # Testar comando de troca de IP
            ip_result = self.handler.set_ip_change_command(self.test_imei)
            
            # Verificar comando de IP
            vehicle_updated = db_manager.get_vehicle_by_imei(self.test_imei)
            has_ip_command = vehicle_updated and vehicle_updated.get('comandotrocarip') is not None
            
            success = has_block_command and has_ip_command  # Commands are set correctly
            details = f"Block command set: {has_block_command}, IP command set: {has_ip_command}"
            
            self.log_test("Sistema Comandos", success, details)
            return success
            
        except Exception as e:
            self.log_test("Sistema Comandos", False, str(e))
            return False
    
    def test_7_tcp_server_port(self):
        """Teste 7: Servidor TCP na porta correta"""
        try:
            # Verificar se porta 8000 está em uso (servidor rodando)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            
            # Tentar conectar na porta 8000
            result = sock.connect_ex(('127.0.0.1', 8000))
            sock.close()
            
            # Se result == 0, porta está em uso (servidor rodando)
            # Se result != 0, porta não está respondendo
            success = result == 0
            details = f"Port 8000 status: {'LISTENING' if success else 'NOT AVAILABLE'}"
            
            self.log_test("Servidor TCP Port 8000", success, details)
            return success
            
        except Exception as e:
            self.log_test("Servidor TCP Port 8000", False, str(e))
            return False
    
    def test_8_configuration(self):
        """Teste 8: Configuração do sistema"""
        try:
            # Verificar configurações críticas
            port_correct = Config.SERVER_PORT == 8000
            db_correct = Config.DATABASE_NAME == 'track'
            ip_correct = Config.SERVER_IP == '0.0.0.0'
            
            success = port_correct and db_correct and ip_correct
            details = f"Port: {Config.SERVER_PORT}, DB: {Config.DATABASE_NAME}, IP: {Config.SERVER_IP}"
            
            self.log_test("Configuração Sistema", success, details)
            return success
            
        except Exception as e:
            self.log_test("Configuração Sistema", False, str(e))
            return False
    
    def cleanup_test_data(self):
        """Limpar dados de teste"""
        try:
            # Remover veículo de teste
            db_manager.db['vehicles'].delete_many({'IMEI': self.test_imei})
            
            # Remover dados de teste
            db_manager.db['vehicle_data'].delete_many({'imei': self.test_imei})
            
            print(f"🧹 Dados de teste removidos (IMEI: {self.test_imei})")
        except Exception as e:
            print(f"⚠️ Erro ao limpar dados: {e}")
    
    def run_all_tests(self):
        """Executar todos os testes"""
        print("="*60)
        print("🧪 TESTE COMPLETO DO SISTEMA GV50")
        print("="*60)
        print(f"⏰ Iniciado em: {datetime.now()}")
        print(f"🎯 Database: {Config.DATABASE_NAME}")
        print(f"🔌 Porta: {Config.SERVER_PORT}")
        print(f"📱 IMEI de teste: {self.test_imei}")
        print("="*60)
        
        # Lista de testes
        tests = [
            self.test_1_database_connection,
            self.test_2_vehicle_crud,
            self.test_3_vehicle_data_storage,
            self.test_4_protocol_parsing,
            self.test_5_message_processing,
            self.test_6_command_system,
            self.test_7_tcp_server_port,
            self.test_8_configuration
        ]
        
        # Executar testes
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ ERRO - {test.__name__}: {e}")
                failed += 1
            
            time.sleep(0.5)  # Pausa entre testes
        
        # Relatório final
        print("="*60)
        print("📊 RELATÓRIO FINAL")
        print("="*60)
        print(f"✅ Testes passou: {passed}")
        print(f"❌ Testes falhou: {failed}")
        print(f"📈 Taxa de sucesso: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("🎉 TODOS OS TESTES PASSARAM - SISTEMA FUNCIONANDO PERFEITAMENTE!")
        else:
            print("⚠️ ALGUNS TESTES FALHARAM - VERIFICAR PROBLEMAS IDENTIFICADOS")
        
        print("="*60)
        
        # Limpar dados de teste
        self.cleanup_test_data()
        
        return failed == 0

def main():
    """Executar teste completo"""
    tester = TesteSistemaCompleto()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())