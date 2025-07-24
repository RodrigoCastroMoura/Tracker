#!/bin/bash

# Script de Backup - Sistema GV50 Tracker
# Uso: bash backup.sh [--full|--config|--logs]

BACKUP_DIR="/home/gv50tracker/gv50-tracker/backup"
SERVICE_DIR="/home/gv50tracker/gv50-tracker"
CONFIG_FILE="$SERVICE_DIR/gv50/.env"
SYSTEMD_FILE="/etc/systemd/system/gv50-tracker.service"
DATE=$(date +%Y%m%d_%H%M%S)

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Criar diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

# Função de backup da configuração
backup_config() {
    echo -e "${BLUE}Fazendo backup da configuração...${NC}"
    
    local backup_file="$BACKUP_DIR/config_backup_$DATE.tar.gz"
    
    tar -czf "$backup_file" \
        -C / \
        "home/gv50tracker/gv50-tracker/gv50/.env" \
        "etc/systemd/system/gv50-tracker.service" \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Backup da configuração salvo: $backup_file${NC}"
        ls -lh "$backup_file"
    else
        echo "Erro ao criar backup da configuração"
        return 1
    fi
}

# Função de backup dos logs
backup_logs() {
    echo -e "${BLUE}Fazendo backup dos logs...${NC}"
    
    local backup_file="$BACKUP_DIR/logs_backup_$DATE.tar.gz"
    local logs_dir="$SERVICE_DIR/logs"
    
    if [ -d "$logs_dir" ] && [ "$(ls -A $logs_dir 2>/dev/null)" ]; then
        tar -czf "$backup_file" -C "$SERVICE_DIR" logs/
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Backup dos logs salvo: $backup_file${NC}"
            ls -lh "$backup_file"
        else
            echo "Erro ao criar backup dos logs"
            return 1
        fi
    else
        echo -e "${YELLOW}Nenhum log encontrado para backup${NC}"
    fi
}

# Função de backup completo
backup_full() {
    echo -e "${BLUE}Fazendo backup completo do sistema...${NC}"
    
    local backup_file="$BACKUP_DIR/full_backup_$DATE.tar.gz"
    
    tar -czf "$backup_file" \
        -C "/home/gv50tracker" \
        --exclude="gv50-tracker/venv" \
        --exclude="gv50-tracker/backup" \
        --exclude="gv50-tracker/gv50/__pycache__" \
        "gv50-tracker/" \
        2>/dev/null
    
    # Adicionar arquivo do systemd
    tar -rf "${backup_file%.gz}" \
        -C / \
        "etc/systemd/system/gv50-tracker.service" \
        2>/dev/null
    
    gzip "${backup_file%.gz}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Backup completo salvo: $backup_file${NC}"
        ls -lh "$backup_file"
    else
        echo "Erro ao criar backup completo"
        return 1
    fi
}

# Função para limpar backups antigos
cleanup_old_backups() {
    echo -e "${BLUE}Limpando backups antigos (>30 dias)...${NC}"
    
    local deleted_count=$(find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete -print | wc -l)
    
    if [ $deleted_count -gt 0 ]; then
        echo -e "${GREEN}✓ Removidos $deleted_count backups antigos${NC}"
    else
        echo "Nenhum backup antigo para remover"
    fi
}

# Função para listar backups
list_backups() {
    echo -e "${BLUE}Backups disponíveis:${NC}"
    echo ""
    
    if [ "$(ls -A $BACKUP_DIR/*.tar.gz 2>/dev/null)" ]; then
        ls -lht "$BACKUP_DIR"/*.tar.gz | while read line; do
            echo "  $line"
        done
    else
        echo "  Nenhum backup encontrado"
    fi
}

# Função para restaurar backup
restore_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        echo "Arquivo de backup não encontrado: $backup_file"
        return 1
    fi
    
    echo -e "${YELLOW}Atenção: Esta operação irá sobrescrever a configuração atual!${NC}"
    read -p "Continuar? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operação cancelada"
        return 1
    fi
    
    echo -e "${BLUE}Restaurando backup: $backup_file${NC}"
    
    # Parar serviço
    echo "Parando serviço..."
    systemctl stop gv50-tracker.service
    
    # Fazer backup da configuração atual antes de restaurar
    local current_backup="$BACKUP_DIR/pre_restore_backup_$DATE.tar.gz"
    backup_config
    mv "$BACKUP_DIR/config_backup_$DATE.tar.gz" "$current_backup"
    echo "Backup da configuração atual salvo em: $current_backup"
    
    # Restaurar
    tar -xzf "$backup_file" -C /
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Backup restaurado com sucesso${NC}"
        
        # Recarregar systemd e iniciar serviço
        systemctl daemon-reload
        systemctl start gv50-tracker.service
        
        echo "Verificando status do serviço..."
        sleep 3
        systemctl status gv50-tracker.service --no-pager
    else
        echo "Erro ao restaurar backup"
        return 1
    fi
}

# Função de ajuda
show_help() {
    cat << EOF
Uso: $0 [OPÇÃO]

OPÇÕES:
  --full, -f      Fazer backup completo do sistema
  --config, -c    Fazer backup apenas da configuração
  --logs, -l      Fazer backup apenas dos logs
  --list          Listar backups disponíveis
  --restore FILE  Restaurar backup específico
  --cleanup       Remover backups antigos (>30 dias)
  --help, -h      Mostrar esta ajuda

Exemplos:
  $0 --full                           # Backup completo
  $0 --config                         # Só configuração
  $0 --restore backup_20231201.tar.gz # Restaurar backup
  $0 --list                           # Listar backups
  $0 --cleanup                        # Limpar antigos

Diretório de backup: $BACKUP_DIR
EOF
}

# Função principal
main() {
    # Verificar se está rodando como root
    if [ "$EUID" -ne 0 ]; then
        echo "Este script precisa ser executado como root (use sudo)"
        exit 1
    fi
    
    case "${1:-}" in
        "--full"|"-f")
            backup_full
            cleanup_old_backups
            ;;
        "--config"|"-c")
            backup_config
            ;;
        "--logs"|"-l")
            backup_logs
            ;;
        "--list")
            list_backups
            ;;
        "--restore")
            if [ -z "$2" ]; then
                echo "Erro: Especifique o arquivo de backup"
                echo "Uso: $0 --restore <arquivo_backup>"
                exit 1
            fi
            restore_backup "$2"
            ;;
        "--cleanup")
            cleanup_old_backups
            ;;
        "--help"|"-h")
            show_help
            ;;
        *)
            echo "Fazendo backup padrão (configuração)..."
            backup_config
            echo ""
            echo "Para backup completo: $0 --full"
            echo "Para ver todas as opções: $0 --help"
            ;;
    esac
}

# Executar função principal
main "$@"