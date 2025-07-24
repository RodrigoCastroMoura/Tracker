#!/bin/bash

# Script de Auto-Restart Simplificado - Sistema GV50 Tracker
# Estrutura: /tracker/
# Uso: bash auto-restart-simple.sh

SERVICE_NAME="gv50-tracker.service"
LOG_FILE="/var/log/gv50-auto-restart.log"
LOCK_FILE="/var/run/gv50-auto-restart.lock"
MAX_RESTART_ATTEMPTS=3
RESTART_DELAY=10
BASE_DIR="/tracker"

# Função de log com timestamp
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${timestamp} [${level}] ${message}" >> "$LOG_FILE"
}

# Verificar se outro script já está rodando
check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local lock_pid=$(cat "$LOCK_FILE" 2>/dev/null)
        
        if [ -n "$lock_pid" ] && kill -0 "$lock_pid" 2>/dev/null; then
            log_message "INFO" "Script já está rodando (PID: $lock_pid)"
            exit 0
        else
            rm -f "$LOCK_FILE"
        fi
    fi
    
    echo $$ > "$LOCK_FILE"
}

# Remover arquivo de lock ao sair
cleanup() {
    rm -f "$LOCK_FILE"
}

trap cleanup EXIT

# Verificar se o serviço está ativo
check_service() {
    systemctl is-active --quiet "$SERVICE_NAME"
    return $?
}

# Verificar se a porta está respondendo
check_port_connectivity() {
    ss -tlnp | grep -q ":5000"
    return $?
}

# Tentar conexão real na porta
test_connection() {
    timeout 5 bash -c "</dev/tcp/localhost/5000" 2>/dev/null
    return $?
}

# Verificar se há muitos erros nos logs recentes
check_error_rate() {
    local error_count=$(journalctl -u "$SERVICE_NAME" --since "1 hour ago" -p err --no-pager -q | wc -l)
    
    if [ "$error_count" -gt 10 ]; then
        log_message "WARNING" "Muitos erros detectados na última hora ($error_count erros)"
        return 1
    fi
    
    return 0
}

# Verificar uso de memória do processo
check_memory_usage() {
    local pid=$(systemctl show --property MainPID --value "$SERVICE_NAME")
    
    if [ "$pid" != "0" ] && [ -n "$pid" ]; then
        local mem_usage=$(ps -p "$pid" -o %mem --no-headers 2>/dev/null | tr -d ' ')
        
        if [ -n "$mem_usage" ] && (( $(echo "$mem_usage > 80.0" | bc -l 2>/dev/null) )); then
            log_message "WARNING" "Alto uso de memória: ${mem_usage}%"
            return 1
        fi
    fi
    
    return 0
}

# Verificar espaço em disco
check_disk_space() {
    local disk_usage=$(df "$BASE_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -gt 90 ]; then
        log_message "WARNING" "Espaço em disco baixo: ${disk_usage}%"
        return 1
    fi
    
    return 0
}

# Verificar ambiente Python
check_python_environment() {
    local python_exec="$BASE_DIR/venv/bin/python"
    
    if [ ! -f "$python_exec" ]; then
        log_message "ERROR" "Python não encontrado em $python_exec"
        return 1
    fi
    
    if ! "$python_exec" -c "import pymongo, dotenv" 2>/dev/null; then
        log_message "ERROR" "Dependências Python não encontradas"
        return 1
    fi
    
    return 0
}

# Reiniciar o serviço
restart_service() {
    local reason=$1
    local attempt=${2:-1}
    
    log_message "WARNING" "Reiniciando serviço (Motivo: $reason, Tentativa: $attempt)"
    
    # Parar o serviço
    systemctl stop "$SERVICE_NAME"
    sleep 3
    
    # Verificar se realmente parou
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_message "WARNING" "Forçando parada do serviço..."
        systemctl kill "$SERVICE_NAME"
        sleep 5
    fi
    
    # Matar processos órfãos
    local orphan_pids=$(pgrep -f "gv50.*main.py" 2>/dev/null)
    if [ -n "$orphan_pids" ]; then
        log_message "WARNING" "Matando processos órfãos: $orphan_pids"
        echo "$orphan_pids" | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    # Iniciar o serviço
    systemctl start "$SERVICE_NAME"
    sleep "$RESTART_DELAY"
    
    # Verificar se iniciou corretamente
    if check_service; then
        log_message "INFO" "Serviço reiniciado com sucesso"
        
        # Verificar conectividade
        sleep 5
        if check_port_connectivity && test_connection; then
            log_message "INFO" "Serviço funcionando corretamente"
            return 0
        else
            log_message "ERROR" "Serviço não está respondendo"
            return 1
        fi
    else
        log_message "ERROR" "Falha ao reiniciar serviço (tentativa $attempt)"
        return 1
    fi
}

# Função principal
main() {
    # Verificar se está rodando como root
    if [ "$EUID" -ne 0 ]; then
        echo "Este script precisa ser executado como root"
        exit 1
    fi
    
    check_lock
    
    # Criar arquivo de log se não existir
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    
    log_message "INFO" "Iniciando verificação do serviço GV50"
    
    local restart_needed=false
    local restart_reason=""
    
    # Verificações em ordem de prioridade
    if ! check_python_environment; then
        restart_needed=true
        restart_reason="Ambiente Python com problemas"
    elif ! check_service; then
        restart_needed=true
        restart_reason="Serviço não está ativo"
    elif ! check_port_connectivity; then
        restart_needed=true
        restart_reason="Porta 5000 não disponível"
    elif ! test_connection; then
        restart_needed=true
        restart_reason="Não é possível conectar na porta 5000"
    elif ! check_error_rate; then
        restart_needed=true
        restart_reason="Taxa alta de erros"
    elif ! check_memory_usage; then
        restart_needed=true
        restart_reason="Alto uso de memória"
    fi
    
    # Verificações não críticas (apenas logs)
    check_disk_space
    
    if [ "$restart_needed" = true ]; then
        local attempt=1
        
        while [ $attempt -le $MAX_RESTART_ATTEMPTS ]; do
            if restart_service "$restart_reason" $attempt; then
                break
            fi
            
            attempt=$((attempt + 1))
            
            if [ $attempt -le $MAX_RESTART_ATTEMPTS ]; then
                log_message "WARNING" "Aguardando antes da próxima tentativa..."
                sleep $((RESTART_DELAY * attempt))
            fi
        done
        
        if [ $attempt -gt $MAX_RESTART_ATTEMPTS ]; then
            log_message "CRITICAL" "Falha em todas as $MAX_RESTART_ATTEMPTS tentativas"
            log_message "CRITICAL" "Intervenção manual necessária!"
        fi
    else
        log_message "INFO" "Serviço funcionando normalmente"
    fi
    
    log_message "INFO" "Verificação concluída"
}

# Executar função principal
main "$@"