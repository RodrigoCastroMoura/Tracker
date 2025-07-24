#!/bin/bash

# Script de Auto-Restart CentOS - Sistema GV50 Tracker
# Este script verifica se o serviço está rodando e o reinicia automaticamente
# Diretório base: /tracker/gv50tracker/gv50-tracker/

SERVICE_NAME="gv50-tracker.service"
LOG_FILE="/var/log/gv50-auto-restart.log"
LOCK_FILE="/var/run/gv50-auto-restart.lock"
MAX_RESTART_ATTEMPTS=3
RESTART_DELAY=10
BASE_DIR="/tracker/gv50tracker/gv50-tracker"

# Função de log com timestamp
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${timestamp} [${level}] CentOS - ${message}" >> "$LOG_FILE"
}

# Verificar se outro script já está rodando
check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local lock_pid=$(cat "$LOCK_FILE" 2>/dev/null)
        
        # Verificar se o processo ainda existe
        if [ -n "$lock_pid" ] && kill -0 "$lock_pid" 2>/dev/null; then
            log_message "INFO" "Script já está rodando (PID: $lock_pid)"
            exit 0
        else
            # Arquivo de lock órfão, remover
            rm -f "$LOCK_FILE"
        fi
    fi
    
    # Criar arquivo de lock
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

# Verificar se o serviço está rodando há muito tempo sem reiniciar
check_service_uptime() {
    local uptime_seconds=$(systemctl show --property=ActiveEnterTimestamp --value "$SERVICE_NAME")
    
    if [ -n "$uptime_seconds" ]; then
        local current_time=$(date +%s)
        local service_start_time=$(date -d "$uptime_seconds" +%s 2>/dev/null || echo 0)
        local uptime=$((current_time - service_start_time))
        
        # Se o serviço está rodando há mais de 7 dias, considerar reiniciar
        if [ $uptime -gt 604800 ]; then  # 7 dias em segundos
            log_message "INFO" "Serviço rodando há mais de 7 dias (${uptime}s). Considerando reinicialização preventiva."
            return 1
        fi
    fi
    
    return 0
}

# Verificar se há muitos erros nos logs recentes
check_error_rate() {
    local error_count=$(journalctl -u "$SERVICE_NAME" --since "1 hour ago" -p err --no-pager -q | wc -l)
    
    # Se há mais de 10 erros na última hora, algo pode estar errado
    if [ "$error_count" -gt 10 ]; then
        log_message "WARNING" "Muitos erros detectados na última hora ($error_count erros)"
        return 1
    fi
    
    return 0
}

# Verificar se a porta está respondendo (usando ss para CentOS)
check_port_connectivity() {
    local port_check=$(ss -tlnp | grep ":5000" | grep LISTEN)
    
    if [ -z "$port_check" ]; then
        log_message "ERROR" "Porta 5000 não está em LISTEN"
        return 1
    fi
    
    return 0
}

# Tentar conexão real na porta
test_connection() {
    local test_result=$(timeout 5 bash -c "</dev/tcp/localhost/5000" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        return 0
    else
        log_message "ERROR" "Não foi possível conectar na porta 5000"
        return 1
    fi
}

# Verificar uso de memória do processo
check_memory_usage() {
    local pid=$(systemctl show --property MainPID --value "$SERVICE_NAME")
    
    if [ "$pid" != "0" ] && [ -n "$pid" ]; then
        local mem_usage=$(ps -p "$pid" -o %mem --no-headers 2>/dev/null | tr -d ' ')
        
        # Se uso de memória > 80%, pode haver vazamento
        if [ -n "$mem_usage" ] && (( $(echo "$mem_usage > 80.0" | bc -l) 2>/dev/null )); then
            log_message "WARNING" "Alto uso de memória detectado: ${mem_usage}%"
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

# Verificar firewall CentOS
check_firewall() {
    if systemctl is-active --quiet firewalld; then
        if ! firewall-cmd --list-ports | grep -q "5000/tcp"; then
            log_message "ERROR" "Porta 5000 não está liberada no firewall"
            return 1
        fi
    else
        log_message "WARNING" "Firewalld não está ativo"
    fi
    
    return 0
}

# Reiniciar o serviço
restart_service() {
    local reason=$1
    local attempt=${2:-1}
    
    log_message "WARNING" "Reiniciando serviço (Motivo: $reason, Tentativa: $attempt)"
    
    # Parar o serviço primeiro
    systemctl stop "$SERVICE_NAME"
    sleep 3
    
    # Verificar se realmente parou
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_message "WARNING" "Serviço não parou, forçando..."
        systemctl kill "$SERVICE_NAME"
        sleep 5
    fi
    
    # Verificar se há processos Python órfãos
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
        
        # Aguardar um pouco e verificar conectividade
        sleep 5
        if check_port_connectivity && test_connection; then
            log_message "INFO" "Serviço funcionando corretamente após reinício"
            return 0
        else
            log_message "ERROR" "Serviço iniciou mas não está respondendo corretamente"
            return 1
        fi
    else
        log_message "ERROR" "Falha ao reiniciar serviço (tentativa $attempt)"
        return 1
    fi
}

# Verificar ambiente Python
check_python_environment() {
    local venv_path="$BASE_DIR/venv"
    local python_exec="$venv_path/bin/python"
    
    if [ ! -f "$python_exec" ]; then
        log_message "ERROR" "Ambiente virtual Python não encontrado em $venv_path"
        return 1
    fi
    
    # Verificar se as dependências estão instaladas
    if ! "$python_exec" -c "import pymongo, dotenv" 2>/dev/null; then
        log_message "ERROR" "Dependências Python não encontradas"
        return 1
    fi
    
    return 0
}

# Função principal de verificação
main() {
    # Verificar se está rodando como root
    if [ "$EUID" -ne 0 ]; then
        echo "Este script precisa ser executado como root"
        exit 1
    fi
    
    # Verificar lock
    check_lock
    
    # Criar arquivo de log se não existir
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    
    log_message "INFO" "Iniciando verificação do serviço GV50 (CentOS)"
    
    local restart_needed=false
    local restart_reason=""
    
    # Verificar ambiente Python primeiro
    if ! check_python_environment; then
        restart_needed=true
        restart_reason="Ambiente Python com problemas"
    
    # Verificar se o serviço está ativo
    elif ! check_service; then
        restart_needed=true
        restart_reason="Serviço não está ativo"
    
    # Verificar conectividade de porta
    elif ! check_port_connectivity; then
        restart_needed=true
        restart_reason="Porta 5000 não está disponível"
    
    # Testar conexão real
    elif ! test_connection; then
        restart_needed=true
        restart_reason="Não é possível conectar na porta 5000"
    
    # Verificar taxa de erros
    elif ! check_error_rate; then
        restart_needed=true
        restart_reason="Taxa alta de erros detectada"
    
    # Verificar uso de memória
    elif ! check_memory_usage; then
        restart_needed=true
        restart_reason="Alto uso de memória detectado"
    fi
    
    # Verificações não críticas (apenas alertas)
    check_disk_space
    check_firewall
    
    if [ "$restart_needed" = true ]; then
        local attempt=1
        local max_attempts=$MAX_RESTART_ATTEMPTS
        
        while [ $attempt -le $max_attempts ]; do
            if restart_service "$restart_reason" $attempt; then
                break
            fi
            
            attempt=$((attempt + 1))
            
            if [ $attempt -le $max_attempts ]; then
                log_message "WARNING" "Aguardando antes da próxima tentativa..."
                sleep $((RESTART_DELAY * attempt))
            fi
        done
        
        if [ $attempt -gt $max_attempts ]; then
            log_message "CRITICAL" "Falha em todas as $max_attempts tentativas de reinício"
            log_message "CRITICAL" "Intervenção manual necessária!"
            
            # Opcional: enviar notificação específica para CentOS
            # logger -t "gv50-tracker" "CRITICAL: GV50 Tracker falhou após $max_attempts tentativas"
        fi
    else
        log_message "INFO" "Serviço funcionando normalmente"
    fi
    
    log_message "INFO" "Verificação concluída (CentOS)"
}

# Executar função principal
main "$@"