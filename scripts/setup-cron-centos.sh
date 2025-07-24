#!/bin/bash

# Script para configurar Cron Jobs CentOS - Sistema GV50 Tracker
# Uso: sudo bash setup-cron-centos.sh

SCRIPT_DIR="/tracker/gv50tracker/gv50-tracker/scripts"
CRON_FILE="/etc/cron.d/gv50-tracker"

echo "=================================================="
echo "   Configuração Cron Jobs CentOS - Sistema GV50  "
echo "=================================================="

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    echo "Este script precisa ser executado como root (use sudo)"
    exit 1
fi

# Verificar se os scripts existem
if [ ! -f "$SCRIPT_DIR/auto-restart-centos.sh" ]; then
    echo "Erro: Script auto-restart-centos.sh não encontrado em $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/backup-centos.sh" ]; then
    echo "Erro: Script backup-centos.sh não encontrado em $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/monitor-centos.sh" ]; then
    echo "Erro: Script monitor-centos.sh não encontrado em $SCRIPT_DIR"
    exit 1
fi

# Tornar scripts executáveis
chmod +x "$SCRIPT_DIR/auto-restart-centos.sh"
chmod +x "$SCRIPT_DIR/backup-centos.sh"
chmod +x "$SCRIPT_DIR/monitor-centos.sh"

echo "Scripts tornados executáveis... ✓"

# Verificar e iniciar crond
if ! systemctl is-active --quiet crond; then
    echo "Iniciando serviço crond..."
    systemctl enable crond
    systemctl start crond
fi

# Criar arquivo de cron
cat > "$CRON_FILE" << 'EOF'
# Cron Jobs para Sistema GV50 Tracker - CentOS
# Gerado automaticamente - não editar manualmente
# Diretório base: /tracker/gv50tracker/gv50-tracker/

# Verificar e reiniciar serviço a cada 5 minutos
*/5 * * * * root /tracker/gv50tracker/gv50-tracker/scripts/auto-restart-centos.sh >/dev/null 2>&1

# Backup da configuração diariamente às 2:30
30 2 * * * root /tracker/gv50tracker/gv50-tracker/scripts/backup-centos.sh --config >/dev/null 2>&1

# Backup completo semanalmente (domingo às 3:00)
0 3 * * 0 root /tracker/gv50tracker/gv50-tracker/scripts/backup-centos.sh --full >/dev/null 2>&1

# Limpeza de backups antigos mensalmente (primeiro dia do mês às 4:00)
0 4 1 * * root /tracker/gv50tracker/gv50-tracker/scripts/backup-centos.sh --cleanup >/dev/null 2>&1

# Limpeza de logs antigos do sistema (semanalmente)
0 5 * * 1 root find /var/log -name "*gv50*" -mtime +30 -delete >/dev/null 2>&1

# Rotação manual de logs da aplicação (diariamente às 23:50)
50 23 * * * root find /tracker/gv50tracker/gv50-tracker/logs -name "*.log" -size +100M -exec gzip {} \; >/dev/null 2>&1

# Verificação de saúde do sistema diariamente às 6:00 (opcional - descomente se necessário)
# 0 6 * * * root /tracker/gv50tracker/gv50-tracker/scripts/monitor-centos.sh --status >> /var/log/gv50-health-check.log 2>&1

EOF

# Definir permissões corretas
chmod 644 "$CRON_FILE"

echo "Arquivo de cron criado em: $CRON_FILE ✓"

# Recarregar cron
systemctl restart crond

echo "Serviço crond reiniciado ✓"

# Verificar status do cron
if systemctl is-active --quiet crond; then
    echo "Serviço crond está ativo ✓"
else
    echo "Aviso: Serviço crond não está ativo"
fi

# Mostrar jobs configurados
echo ""
echo "=================================================="
echo "   Jobs Configurados - CentOS                     "
echo "=================================================="
echo ""
echo "1. Auto-restart do serviço: A cada 5 minutos"
echo "   - Verifica se o serviço está rodando"
echo "   - Reinicia automaticamente se necessário"
echo "   - Log: /var/log/gv50-auto-restart.log"
echo ""
echo "2. Backup da configuração: Diariamente às 2:30"
echo "   - Backup do arquivo .env e configuração systemd"
echo "   - Local: /tracker/gv50tracker/gv50-tracker/backup/"
echo ""
echo "3. Backup completo: Semanalmente (domingo às 3:00)"
echo "   - Backup de todo o sistema (exceto venv)"
echo "   - Local: /tracker/gv50tracker/gv50-tracker/backup/"
echo ""
echo "4. Limpeza de backups: Mensalmente (dia 1 às 4:00)"
echo "   - Remove backups com mais de 30 dias"
echo ""
echo "5. Limpeza de logs: Semanalmente (segunda às 5:00)"
echo "   - Remove logs do sistema com mais de 30 dias"
echo ""
echo "6. Rotação de logs da aplicação: Diariamente às 23:50"
echo "   - Compacta logs maiores que 100MB"
echo ""

# Verificar status atual
echo "=================================================="
echo "   Status Atual - CentOS                          "
echo "=================================================="
echo ""

# Verificar se o cron está rodando
if systemctl is-active --quiet crond; then
    echo "✓ Serviço crond está ativo"
else
    echo "✗ Serviço crond não está ativo"
fi

# Verificar se o serviço GV50 está rodando
if systemctl is-active --quiet gv50-tracker.service; then
    echo "✓ Serviço GV50 está ativo"
else
    echo "✗ Serviço GV50 não está ativo"
fi

# Verificar firewall
if systemctl is-active --quiet firewalld; then
    echo "✓ Firewalld está ativo"
    
    # Verificar se a porta 5000 está liberada
    if firewall-cmd --list-ports | grep -q "5000/tcp"; then
        echo "✓ Porta 5000 está liberada no firewall"
    else
        echo "⚠ Porta 5000 não está liberada no firewall"
        echo "  Execute: sudo firewall-cmd --permanent --add-port=5000/tcp && sudo firewall-cmd --reload"
    fi
else
    echo "⚠ Firewalld não está ativo"
fi

# Verificar SELinux
if command -v getenforce >/dev/null 2>&1; then
    SELINUX_STATUS=$(getenforce)
    echo "ℹ SELinux status: $SELINUX_STATUS"
fi

# Mostrar próximas execuções
echo ""
echo "Próximas verificações automáticas:"
echo "- Auto-restart: A cada 5 minutos"
echo "- Próximo backup de configuração: $(date -d 'tomorrow 2:30' '+%Y-%m-%d %H:%M')"

if [ $(date +%u) -le 6 ]; then
    next_sunday=$(date -d 'next sunday 3:00' '+%Y-%m-%d %H:%M')
else
    next_sunday=$(date -d 'sunday 3:00' '+%Y-%m-%d %H:%M')
fi
echo "- Próximo backup completo: $next_sunday"

echo ""
echo "=================================================="
echo "   Comandos Úteis - CentOS                        "
echo "=================================================="
echo ""
echo "Ver jobs ativos:"
echo "  crontab -l"
echo "  cat /etc/cron.d/gv50-tracker"
echo ""
echo "Ver logs do auto-restart:"
echo "  tail -f /var/log/gv50-auto-restart.log"
echo ""
echo "Executar verificação manual:"
echo "  sudo $SCRIPT_DIR/auto-restart-centos.sh"
echo ""
echo "Fazer backup manual:"
echo "  sudo $SCRIPT_DIR/backup-centos.sh --config"
echo ""
echo "Monitorar sistema:"
echo "  sudo $SCRIPT_DIR/monitor-centos.sh --status"
echo ""
echo "Ver logs do serviço:"
echo "  sudo journalctl -u gv50-tracker.service -f"
echo ""
echo "Verificar status do firewall:"
echo "  sudo firewall-cmd --list-all"
echo ""
echo "Testar conectividade:"
echo "  telnet localhost 5000"
echo ""
echo "Remover cron jobs (se necessário):"
echo "  sudo rm $CRON_FILE && sudo systemctl restart crond"
echo ""

echo "=================================================="
echo "   Configuração CentOS Concluída!                "
echo "=================================================="
echo ""
echo "O sistema agora irá:"
echo "• Verificar o serviço automaticamente a cada 5 minutos"
echo "• Reiniciar o serviço se ele parar de funcionar"
echo "• Fazer backup da configuração diariamente"
echo "• Fazer backup completo semanalmente"
echo "• Limpar arquivos antigos automaticamente"
echo "• Rotacionar logs grandes automaticamente"
echo ""
echo "Configurações específicas do CentOS:"
echo "• Diretório base: /tracker/gv50tracker/gv50-tracker/"
echo "• Serviço: gv50-tracker.service"
echo "• Firewall: firewalld configurado"
echo "• Logs: journalctl + logrotate"
echo ""
echo "Todos os scripts estão localizados em:"
echo "/tracker/gv50tracker/gv50-tracker/scripts/"
echo ""
echo "Logs do sistema em:"
echo "/var/log/gv50-*"