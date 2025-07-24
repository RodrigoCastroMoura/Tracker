#!/bin/bash

# Script de Monitoramento CentOS - Sistema GV50 Tracker
# Diretório base: /tracker/gv50tracker/gv50-tracker/
# Uso: bash monitor-centos.sh

SERVICE_NAME="gv50-tracker.service"
LOG_FILE="/var/log/gv50-monitor.log"
CHECK_INTERVAL=30  # segundos
MAX_RESTART_ATTEMPTS=3
RESTART_DELAY=5
BASE_DIR="/tracker/gv50tracker/gv50-tracker"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função de log
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] CentOS - ${message}" | tee -a "$LOG_FILE"
}

# Verificar se o serviço está rodando
check_service_status() {
    systemctl is-active --quiet "$SERVICE_NAME"
    return $?
}

# Verificar conectividade de rede na porta 5000 (usando ss para CentOS)
check_network_connectivity() {
    ss -tlnp | grep -q ":5000"
    return $?
}

# Verificar uso de recursos
check_resources() {
    local pid=$(systemctl show --property MainPID --value "$SERVICE_NAME")
    
    if [ "$pid" != "0" ] && [ -n "$pid" ]; then
        local cpu_usage=$(ps -p "$pid" -o %cpu --no-headers 2>/dev/null | tr -d ' ')
        local mem_usage=$(ps -p "$pid" -o %mem --no-headers 2>/dev/null | tr -d ' ')
        local rss_kb=$(ps -p "$pid" -o rss --no-headers 2>/dev/null | tr -d ' ')
        
        echo "CPU: ${cpu_usage}% | MEM: ${mem_usage}% | RSS: ${rss_kb}KB"
        
        # Alertar se uso de CPU > 80% ou Memória > 80%
        if [ -n "$cpu_usage" ] && (( $(echo "$cpu_usage > 80" | bc -l 2>/dev/null) )); then
            log_message "WARNING" "Alto uso de CPU: ${cpu_usage}%"
        fi
        
        if [ -n "$mem_usage" ] && (( $(echo "$mem_usage > 80" | bc -l 2>/dev/null) )); then
            log_message "WARNING" "Alto uso de memória: ${mem_usage}%"
        fi
    else
        echo "Processo não encontrado"
    fi
}

# Verificar logs de erro recentes
check_recent_errors() {
    local error_count=$(journalctl -u "$SERVICE_NAME" --since "5 minutes ago" -p err --no-pager -q | wc -l)
    
    if [ "$error_count" -gt 0 ]; then
        log_message "WARNING" "Encontrados $error_count erros nos últimos 5 minutos"
        return 1
    fi
    
    return 0
}

# Verificar firewall CentOS
check_firewall_status() {
    if systemctl is-active --quiet firewalld; then
        if firewall-cmd --list-ports | grep -q "5000/tcp"; then
            echo "Firewall: OK (porta 5000 liberada)"
            return 0
        else
            echo "Firewall: PROBLEMA (porta 5000 não liberada)"
            return 1
        fi
    else
        echo "Firewall: INATIVO"
        return 1
    fi
}

# Verificar SELinux
check_selinux_status() {
    if command -v getenforce >/dev/null 2>&1; then
        local selinux_status=$(getenforce)
        echo "SELinux: $selinux_status"
        
        if [ "$selinux_status" = "Enforcing" ]; then
            # Verificar se há negações relacionadas ao serviço
            local denials=$(ausearch -m avc -ts recent 2>/dev/null | grep -i gv50 | wc -l)
            if [ "$denials" -gt 0 ]; then
                echo "SELinux: $denials negações recentes encontradas"
                return 1
            fi
        fi
    else
        echo "SELinux: Não disponível"
    fi
    
    return 0
}

# Verificar espaço em disco
check_disk_space() {
    local disk_usage=$(df "$BASE_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    local disk_available=$(df -h "$BASE_DIR" | awk 'NR==2 {print $4}')
    
    echo "Disco: ${disk_usage}% usado (${disk_available} livre)"
    
    if [ "$disk_usage" -gt 90 ]; then
        log_message "WARNING" "Espaço em disco crítico: ${disk_usage}%"
        return 1
    elif [ "$disk_usage" -gt 80 ]; then
        log_message "WARNING" "Espaço em disco baixo: ${disk_usage}%"
        return 1
    fi
    
    return 0
}

# Verificar conectividade com MongoDB
check_mongodb_connectivity() {
    local python_exec="$BASE_DIR/venv/bin/python"
    
    if [ -f "$python_exec" ]; then
        local mongo_test=$("$python_exec" -c "
import sys
sys.path.append('$BASE_DIR/gv50')
try:
    from pymongo import MongoClient
    client = MongoClient('mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('OK')
except Exception as e:
    print('ERRO')
" 2>/dev/null)
        
        if [ "$mongo_test" = "OK" ]; then
            echo "MongoDB: OK"
            return 0
        else
            echo "MongoDB: ERRO"
            return 1
        fi
    else
        echo "MongoDB: Não testado (Python não encontrado)"
        return 1
    fi
}

# Verificar arquivos de log grandes
check_log_sizes() {
    local large_logs=$(find "$BASE_DIR/logs" -name "*.log" -size +100M 2>/dev/null)
    
    if [ -n "$large_logs" ]; then
        echo "Logs grandes encontrados:"
        echo "$large_logs" | while read log_file; do
            local size=$(du -h "$log_file" | cut -f1)
            echo "  $log_file ($size)"
        done
        return 1
    fi
    
    return 0
}

# Verificar conexões de rede ativas
check_network_connections() {
    local connections=$(ss -tn state established '( dport = :5000 or sport = :5000 )' | wc -l)
    local listening=$(ss -tln | grep ":5000" | wc -l)
    
    echo "Rede: $listening socket(s) em listen, $connections conexão(ões) ativa(s)"
    
    return 0
}

# Reiniciar serviço
restart_service() {
    local attempt=$1
    
    log_message "WARNING" "Tentativa $attempt de $MAX_RESTART_ATTEMPTS: Reiniciando serviço..."
    
    systemctl restart "$SERVICE_NAME"
    sleep "$RESTART_DELAY"
    
    if check_service_status; then
        log_message "INFO" "Serviço reiniciado com sucesso"
        return 0
    else
        log_message "ERROR" "Falha ao reiniciar serviço (tentativa $attempt)"
        return 1
    fi
}

# Verificação completa do sistema
perform_health_check() {
    local status="OK"
    local issues=()
    
    echo -e "${BLUE}=== Verificação de Saúde do Sistema GV50 - CentOS ===${NC}"
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Diretório base: $BASE_DIR"
    echo ""
    
    # Verificar status do serviço
    echo -n "Status do Serviço: "
    if check_service_status; then
        echo -e "${GREEN}ATIVO${NC}"
    else
        echo -e "${RED}INATIVO${NC}"
        status="CRITICAL"
        issues+=("Serviço não está rodando")
    fi
    
    # Verificar conectividade de rede
    echo -n "Porta 5000: "
    if check_network_connectivity; then
        echo -e "${GREEN}ABERTA${NC}"
    else
        echo -e "${RED}FECHADA${NC}"
        status="WARNING"
        issues+=("Porta 5000 não está aberta")
    fi
    
    # Verificar recursos
    echo -n "Recursos do Sistema: "
    local resources=$(check_resources)
    echo -e "${GREEN}$resources${NC}"
    
    # Verificar erros recentes
    echo -n "Erros Recentes: "
    if check_recent_errors; then
        echo -e "${GREEN}NENHUM${NC}"
    else
        echo -e "${YELLOW}ENCONTRADOS${NC}"
        status="WARNING"
        issues+=("Erros encontrados nos logs recentes")
    fi
    
    # Verificar espaço em disco
    echo -n "Espaço em Disco: "
    if check_disk_space; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}ATENÇÃO${NC}"
        status="WARNING"
        issues+=("Espaço em disco baixo")
    fi
    
    # Verificar firewall
    echo -n "Firewall: "
    if check_firewall_status; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}ATENÇÃO${NC}"
        issues+=("Problema no firewall")
    fi
    
    # Verificar SELinux
    echo -n "SELinux: "
    if check_selinux_status; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}ATENÇÃO${NC}"
        issues+=("Problema no SELinux")
    fi
    
    # Verificar MongoDB
    echo -n "MongoDB: "
    if check_mongodb_connectivity; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}ERRO${NC}"
        status="CRITICAL"
        issues+=("Problemas de conectividade com MongoDB")
    fi
    
    # Verificar logs grandes
    echo -n "Tamanho dos Logs: "
    if check_log_sizes; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}LOGS GRANDES${NC}"
        issues+=("Logs grandes detectados")
    fi
    
    # Verificar conexões de rede
    echo -n "Conexões de Rede: "
    check_network_connections
    echo -e "${GREEN}OK${NC}"
    
    # Resumo
    echo ""
    echo -n "Status Geral: "
    case "$status" in
        "OK")
            echo -e "${GREEN}SAUDÁVEL${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}ATENÇÃO${NC}"
            ;;
        "CRITICAL")
            echo -e "${RED}CRÍTICO${NC}"
            ;;
    esac
    
    # Listar problemas encontrados
    if [ ${#issues[@]} -gt 0 ]; then
        echo ""
        echo "Problemas encontrados:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
    fi
    
    echo ""
    
    return $status
}

# Modo daemon (monitoramento contínuo)
daemon_mode() {
    log_message "INFO" "Iniciando monitoramento CentOS em modo daemon (intervalo: ${CHECK_INTERVAL}s)"
    
    local restart_attempts=0
    
    while true; do
        if ! check_service_status; then
            log_message "ERROR" "Serviço não está rodando!"
            
            if [ $restart_attempts -lt $MAX_RESTART_ATTEMPTS ]; then
                restart_attempts=$((restart_attempts + 1))
                
                if restart_service $restart_attempts; then
                    restart_attempts=0  # Reset contador em caso de sucesso
                else
                    log_message "ERROR" "Falha na tentativa $restart_attempts de reinício"
                fi
            else
                log_message "CRITICAL" "Máximo de tentativas de reinício atingido ($MAX_RESTART_ATTEMPTS)"
                log_message "CRITICAL" "Intervenção manual necessária!"
                
                # Esperar mais tempo antes de tentar novamente
                sleep 300  # 5 minutos
                restart_attempts=0  # Reset para tentar novamente
            fi
        else
            # Serviço está rodando, verificar outros aspectos
            if ! check_network_connectivity; then
                log_message "WARNING" "Porta 5000 não está disponível"
            fi
            
            if ! check_firewall_status; then
                log_message "WARNING" "Problemas no firewall detectados"
            fi
            
            check_recent_errors
            restart_attempts=0  # Reset contador se tudo está OK
        fi
        
        sleep "$CHECK_INTERVAL"
    done
}

# Função de ajuda
show_help() {
    cat << EOF
Uso: $0 [OPÇÃO]

OPÇÕES:
  --daemon, -d    Executar em modo daemon (monitoramento contínuo)
  --status, -s    Verificar status atual do sistema
  --restart, -r   Reiniciar o serviço manualmente
  --logs, -l      Mostrar logs recentes
  --firewall      Verificar status do firewall
  --selinux       Verificar status do SELinux
  --help, -h      Mostrar esta ajuda

Exemplos:
  $0 --status     # Verificação única
  $0 --daemon     # Monitoramento contínuo
  $0 --restart    # Reiniciar serviço
  $0 --firewall   # Status do firewall

Específico para CentOS:
- Verifica firewalld e SELinux
- Usa ss em vez de netstat
- Monitora journalctl
- Verifica ausearch para SELinux

Logs do monitor: $LOG_FILE
Diretório base: $BASE_DIR
EOF
}

# Função principal
main() {
    # Verificar se está rodando como root
    if [ "$EUID" -ne 0 ]; then
        echo "Este script precisa ser executado como root (use sudo)"
        exit 1
    fi
    
    # Criar arquivo de log se não existir
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    
    # Verificar argumentos
    case "${1:-}" in
        "--daemon"|"-d")
            daemon_mode
            ;;
        "--status"|"-s")
            perform_health_check
            ;;
        "--restart"|"-r")
            log_message "INFO" "Reinício manual solicitado"
            restart_service 1
            ;;
        "--logs"|"-l")
            echo "Logs do serviço (últimas 50 linhas):"
            journalctl -u "$SERVICE_NAME" -n 50 --no-pager
            ;;
        "--firewall")
            echo "Status do firewall:"
            check_firewall_status
            echo ""
            echo "Regras ativas:"
            firewall-cmd --list-all
            ;;
        "--selinux")
            echo "Status do SELinux:"
            check_selinux_status
            echo ""
            if command -v ausearch >/dev/null 2>&1; then
                echo "Negações recentes (últimas 24h):"
                ausearch -m avc -ts yesterday 2>/dev/null | grep -i gv50 || echo "Nenhuma negação encontrada"
            fi
            ;;
        "--help"|"-h")
            show_help
            ;;
        *)
            perform_health_check
            echo ""
            echo "Para monitoramento contínuo: $0 --daemon"
            echo "Para ver todas as opções: $0 --help"
            ;;
    esac
}

# Executar função principal
main "$@"