#!/bin/bash

# Script de Monitoramento - Sistema GV50 Tracker
# Uso: bash monitor.sh
# Para executar continuamente: bash monitor.sh --daemon

SERVICE_NAME="gv50-tracker.service"
LOG_FILE="/var/log/gv50-monitor.log"
CHECK_INTERVAL=30  # segundos
MAX_RESTART_ATTEMPTS=3
RESTART_DELAY=5

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
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Verificar se o serviço está rodando
check_service_status() {
    systemctl is-active --quiet "$SERVICE_NAME"
    return $?
}

# Verificar conectividade de rede na porta 5000
check_network_connectivity() {
    netstat -tlnp | grep -q ":5000"
    return $?
}

# Verificar uso de recursos
check_resources() {
    local pid=$(systemctl show --property MainPID --value "$SERVICE_NAME")
    
    if [ "$pid" != "0" ] && [ -n "$pid" ]; then
        local cpu_usage=$(ps -p "$pid" -o %cpu --no-headers 2>/dev/null | tr -d ' ')
        local mem_usage=$(ps -p "$pid" -o %mem --no-headers 2>/dev/null | tr -d ' ')
        
        echo "CPU: ${cpu_usage}% | MEM: ${mem_usage}%"
        
        # Alertar se uso de CPU > 80% ou Memória > 80%
        if (( $(echo "$cpu_usage > 80" | bc -l) 2>/dev/null )); then
            log_message "WARNING" "Alto uso de CPU: ${cpu_usage}%"
        fi
        
        if (( $(echo "$mem_usage > 80" | bc -l) 2>/dev/null )); then
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
    
    echo -e "${BLUE}=== Verificação de Saúde do Sistema GV50 ===${NC}"
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
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
    local disk_usage=$(df /home/gv50tracker/gv50-tracker | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 90 ]; then
        echo -e "${GREEN}${disk_usage}%${NC}"
    else
        echo -e "${RED}${disk_usage}%${NC}"
        status="WARNING"
        issues+=("Espaço em disco baixo: ${disk_usage}%")
    fi
    
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
    log_message "INFO" "Iniciando monitoramento em modo daemon (intervalo: ${CHECK_INTERVAL}s)"
    
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
            
            check_recent_errors
            restart_attempts=0  # Reset contador se tudo está OK
        fi
        
        sleep "$CHECK_INTERVAL"
    done
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
        "--help"|"-h")
            cat << EOF
Uso: $0 [OPÇÃO]

OPÇÕES:
  --daemon, -d    Executar em modo daemon (monitoramento contínuo)
  --status, -s    Verificar status atual do sistema
  --restart, -r   Reiniciar o serviço manualmente
  --logs, -l      Mostrar logs recentes
  --help, -h      Mostrar esta ajuda

Exemplos:
  $0 --status     # Verificação única
  $0 --daemon     # Monitoramento contínuo
  $0 --restart    # Reiniciar serviço

Logs do monitor: $LOG_FILE
EOF
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