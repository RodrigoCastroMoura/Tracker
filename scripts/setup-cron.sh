#!/bin/bash

# Script para configurar Cron Jobs - Sistema GV50 Tracker
# Uso: sudo bash setup-cron.sh

SCRIPT_DIR="/home/gv50tracker/gv50-tracker/scripts"
CRON_FILE="/etc/cron.d/gv50-tracker"

echo "=================================================="
echo "   Configuração de Cron Jobs - Sistema GV50      "
echo "=================================================="

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    echo "Este script precisa ser executado como root (use sudo)"
    exit 1
fi

# Verificar se os scripts existem
if [ ! -f "$SCRIPT_DIR/auto-restart.sh" ]; then
    echo "Erro: Script auto-restart.sh não encontrado em $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/backup.sh" ]; then
    echo "Erro: Script backup.sh não encontrado em $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/monitor.sh" ]; then
    echo "Erro: Script monitor.sh não encontrado em $SCRIPT_DIR"
    exit 1
fi

# Tornar scripts executáveis
chmod +x "$SCRIPT_DIR/auto-restart.sh"
chmod +x "$SCRIPT_DIR/backup.sh"
chmod +x "$SCRIPT_DIR/monitor.sh"

echo "Tornando scripts executáveis... ✓"

# Criar arquivo de cron
cat > "$CRON_FILE" << 'EOF'
# Cron Jobs para Sistema GV50 Tracker
# Gerado automaticamente - não editar manualmente

# Verificar e reiniciar serviço a cada 5 minutos
*/5 * * * * root /home/gv50tracker/gv50-tracker/scripts/auto-restart.sh >/dev/null 2>&1

# Backup da configuração diariamente às 2:30
30 2 * * * root /home/gv50tracker/gv50-tracker/scripts/backup.sh --config >/dev/null 2>&1

# Backup completo semanalmente (domingo às 3:00)
0 3 * * 0 root /home/gv50tracker/gv50-tracker/scripts/backup.sh --full >/dev/null 2>&1

# Limpeza de backups antigos mensalmente (primeiro dia do mês às 4:00)
0 4 1 * * root /home/gv50tracker/gv50-tracker/scripts/backup.sh --cleanup >/dev/null 2>&1

# Limpeza de logs antigos do sistema (semanalmente)
0 5 * * 1 root find /var/log -name "*gv50*" -mtime +30 -delete >/dev/null 2>&1

# Verificação de saúde do sistema diariamente às 6:00 (opcional - descomente se necessário)
# 0 6 * * * root /home/gv50tracker/gv50-tracker/scripts/monitor.sh --status >> /var/log/gv50-health-check.log 2>&1

EOF

# Definir permissões corretas
chmod 644 "$CRON_FILE"

echo "Arquivo de cron criado em: $CRON_FILE ✓"

# Recarregar cron
systemctl restart cron 2>/dev/null || systemctl restart crond 2>/dev/null

echo "Serviço cron reiniciado ✓"

# Mostrar jobs configurados
echo ""
echo "=================================================="
echo "   Jobs Configurados                              "
echo "=================================================="
echo ""
echo "1. Auto-restart do serviço: A cada 5 minutos"
echo "   - Verifica se o serviço está rodando"
echo "   - Reinicia automaticamente se necessário"
echo "   - Log: /var/log/gv50-auto-restart.log"
echo ""
echo "2. Backup da configuração: Diariamente às 2:30"
echo "   - Backup do arquivo .env e configuração systemd"
echo "   - Local: /home/gv50tracker/gv50-tracker/backup/"
echo ""
echo "3. Backup completo: Semanalmente (domingo às 3:00)"
echo "   - Backup de todo o sistema (exceto venv)"
echo "   - Local: /home/gv50tracker/gv50-tracker/backup/"
echo ""
echo "4. Limpeza de backups: Mensalmente (dia 1 às 4:00)"
echo "   - Remove backups com mais de 30 dias"
echo ""
echo "5. Limpeza de logs: Semanalmente (segunda às 5:00)"
echo "   - Remove logs do sistema com mais de 30 dias"
echo ""

# Verificar status atual
echo "=================================================="
echo "   Status Atual                                   "
echo "=================================================="
echo ""

# Verificar se o cron está rodando
if systemctl is-active --quiet cron 2>/dev/null || systemctl is-active --quiet crond 2>/dev/null; then
    echo "✓ Serviço cron está ativo"
else
    echo "✗ Serviço cron não está ativo"
fi

# Verificar se o serviço GV50 está rodando
if systemctl is-active --quiet gv50-tracker.service; then
    echo "✓ Serviço GV50 está ativo"
else
    echo "✗ Serviço GV50 não está ativo"
fi

# Mostrar próximas execuções (se disponível)
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
echo "   Comandos Úteis                                 "
echo "=================================================="
echo ""
echo "Ver jobs ativos:"
echo "  crontab -l"
echo ""
echo "Ver logs do auto-restart:"
echo "  tail -f /var/log/gv50-auto-restart.log"
echo ""
echo "Executar verificação manual:"
echo "  sudo $SCRIPT_DIR/auto-restart.sh"
echo ""
echo "Fazer backup manual:"
echo "  sudo $SCRIPT_DIR/backup.sh --config"
echo ""
echo "Monitorar sistema:"
echo "  sudo $SCRIPT_DIR/monitor.sh --status"
echo ""
echo "Remover cron jobs (se necessário):"
echo "  sudo rm $CRON_FILE && sudo systemctl restart cron"
echo ""

echo "=================================================="
echo "   Configuração Concluída!                       "
echo "=================================================="
echo ""
echo "O sistema agora irá:"
echo "• Verificar o serviço automaticamente a cada 5 minutos"
echo "• Reiniciar o serviço se ele parar de funcionar"
echo "• Fazer backup da configuração diariamente"
echo "• Fazer backup completo semanalmente"
echo "• Limpar arquivos antigos automaticamente"
echo ""
echo "Todos os scripts e logs estão localizados em:"
echo "/home/gv50tracker/gv50-tracker/scripts/"
echo "/var/log/gv50-*"