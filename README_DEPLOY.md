# Guia Rápido de Deploy - Sistema GV50 Tracker

## 📦 Pacote Completo de Instalação

Este sistema inclui tudo que você precisa para instalar e manter o serviço GV50 funcionando automaticamente em um servidor Linux.

## 🚀 Instalação Rápida (3 Passos)

### 1. Execute a Instalação Automática
```bash
# Baixar e executar script de instalação
sudo bash scripts/install.sh
```

### 2. Copie os Arquivos do Sistema
```bash
# Copie todos os arquivos da pasta gv50/ para:
sudo cp -r gv50/ /home/gv50tracker/gv50-tracker/
sudo chown -R gv50tracker:gv50tracker /home/gv50tracker/gv50-tracker/
```

### 3. Configure e Inicie o Serviço
```bash
# Edite as configurações se necessário
sudo nano /home/gv50tracker/gv50-tracker/gv50/.env

# Habilite e inicie o serviço
sudo systemctl enable gv50-tracker.service
sudo systemctl start gv50-tracker.service

# Verifique se está funcionando
sudo systemctl status gv50-tracker.service
```

## ⚡ Configuração de Monitoramento Automático

### Configure o Cron para Reinício Automático
```bash
# Configurar verificações automáticas
sudo bash scripts/setup-cron.sh
```

**Isso configura automaticamente:**
- ✅ Verificação a cada 5 minutos se o serviço está rodando
- ✅ Reinício automático se o serviço parar
- ✅ Backup da configuração diariamente
- ✅ Backup completo semanalmente
- ✅ Limpeza de arquivos antigos

## 📁 Estrutura de Arquivos

```
gv50-tracker/
├── MANUAL_INSTALACAO.md      # Manual completo e detalhado
├── README_DEPLOY.md           # Este guia rápido
├── gv50/                      # Código do serviço GV50
├── scripts/                   # Scripts de manutenção
│   ├── install.sh            # Instalação automática
│   ├── monitor.sh            # Monitoramento manual
│   ├── auto-restart.sh       # Reinício automático
│   ├── backup.sh             # Sistema de backup
│   └── setup-cron.sh         # Configurar cron jobs
├── systemd/                   # Arquivos de serviço
│   └── gv50-tracker.service  # Configuração systemd
└── logs/                      # Logs do sistema
```

## 🔧 Comandos Essenciais

### Controle do Serviço
```bash
# Ver status
sudo systemctl status gv50-tracker.service

# Iniciar/Parar/Reiniciar
sudo systemctl start gv50-tracker.service
sudo systemctl stop gv50-tracker.service
sudo systemctl restart gv50-tracker.service

# Ver logs em tempo real
sudo journalctl -u gv50-tracker.service -f
```

### Scripts de Manutenção
```bash
# Verificar saúde do sistema
sudo scripts/monitor.sh --status

# Fazer backup manual
sudo scripts/backup.sh --config

# Testar conexão
telnet SERVIDOR_IP 5000
```

## 🛡️ Características do Sistema

### Auto-Recuperação
- **Verificação a cada 5 minutos**: Se o serviço parar, é reiniciado automaticamente
- **Máximo 3 tentativas**: Evita loops infinitos de reinício
- **Logs detalhados**: Registro completo de todas as operações

### Backup Automático
- **Configuração diária**: Backup do .env e configurações systemd
- **Sistema completo semanal**: Backup de todo o código e configurações
- **Limpeza automática**: Remove backups com mais de 30 dias

### Segurança
- **Usuário dedicado**: Serviço roda com usuário `gv50tracker` (não root)
- **Permissões restritas**: Acesso limitado apenas ao necessário
- **Firewall configurado**: Apenas porta 5000 liberada

## 📊 Monitoramento

### Logs Importantes
```bash
# Logs do serviço GV50
sudo journalctl -u gv50-tracker.service

# Logs do sistema de auto-restart
sudo tail -f /var/log/gv50-auto-restart.log

# Logs de monitoramento
sudo tail -f /var/log/gv50-monitor.log
```

### Verificações de Saúde
- Status do serviço
- Conectividade na porta 5000
- Uso de CPU e memória
- Taxa de erros nos logs
- Espaço em disco

## 🚨 Solução de Problemas

### Serviço não inicia
```bash
# Ver erros específicos
sudo journalctl -u gv50-tracker.service -p err

# Testar manualmente
sudo su - gv50tracker
cd /home/gv50tracker/gv50-tracker/gv50
source ../venv/bin/activate
python main.py
```

### Porta ocupada
```bash
# Ver qual processo está usando a porta
sudo lsof -i :5000
sudo netstat -tlnp | grep :5000
```

### Problemas de conectividade
```bash
# Testar firewall
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS

# Testar conexão local
telnet localhost 5000
```

## 📞 Suporte

### Para problemas:
1. **Verifique os logs** primeiro
2. **Execute verificação de saúde**: `sudo scripts/monitor.sh --status`
3. **Teste conectividade**: `telnet SERVIDOR_IP 5000`
4. **Consulte o manual completo**: `MANUAL_INSTALACAO.md`

### Configurações importantes no .env:
```env
ALLOWED_IPS=0.0.0.0/0                    # IPs permitidos
SERVER_PORT=5000                         # Porta do serviço
LOGGING_ENABLED=true                     # Ativar logs
DATABASE_NAME=tracker                    # Nome do banco
```

## ✅ Sistema Pronto!

Após a instalação, seu sistema GV50 estará:
- 🏃‍♂️ **Rodando automaticamente** na inicialização do servidor
- 🔄 **Se reiniciando sozinho** se parar de funcionar
- 💾 **Fazendo backup** das configurações automaticamente
- 📊 **Monitorando** sua própria saúde
- 🗂️ **Limpando** arquivos antigos automaticamente

**O sistema está configurado para funcionar sozinho sem intervenção manual!**