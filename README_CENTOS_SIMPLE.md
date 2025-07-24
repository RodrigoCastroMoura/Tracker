# Guia de Instalação CentOS - Sistema GV50 Tracker (Estrutura Simplificada)

## 🎯 **ESTRUTURA SIMPLIFICADA - APENAS `/tracker/`**

```
/tracker/
├── gv50/           # Código do serviço GV50
├── venv/           # Ambiente virtual Python
├── logs/           # Logs da aplicação
├── backup/         # Backups automáticos
└── scripts/        # Scripts de manutenção
```

## 🚀 **INSTALAÇÃO RÁPIDA (3 PASSOS)**

### 1. Execute o Script de Instalação Automática
```bash
# Baixar e executar script de instalação CentOS simplificado
sudo bash scripts/install-centos-simple.sh
```

### 2. Copie os Arquivos do Sistema
```bash
# Copie todos os arquivos da pasta gv50/ para:
sudo cp -r gv50/* /tracker/gv50/
sudo chown -R gv50tracker:gv50tracker /tracker/
```

### 3. Configure e Inicie o Serviço
```bash
# Edite as configurações se necessário
sudo nano /tracker/gv50/.env

# Habilite e inicie o serviço
sudo systemctl enable gv50-tracker.service
sudo systemctl start gv50-tracker.service

# Verifique se está funcionando
sudo systemctl status gv50-tracker.service
```

## ⚡ **CONFIGURAÇÃO DE MONITORAMENTO AUTOMÁTICO**

### Configure o Cron para Monitoramento
```bash
# Copie os scripts primeiro
sudo cp scripts/auto-restart-simple.sh /tracker/scripts/
sudo cp scripts/backup-simple.sh /tracker/scripts/
sudo cp scripts/setup-cron-simple.sh /tracker/scripts/

# Configure monitoramento automático
sudo bash /tracker/scripts/setup-cron-simple.sh
```

## 🖥️ **ESPECÍFICO PARA CENTOS**

### Requisitos do Sistema
- **CentOS 7/8/9** ou **Rocky Linux** ou **AlmaLinux**
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disco**: 20GB livres

### Dependências Automaticamente Instaladas
```bash
# CentOS 7
yum install epel-release centos-release-scl rh-python38

# CentOS 8/9
dnf install epel-release python3.11 python3.11-pip
```

### Firewall Configurado Automaticamente
```bash
# Porta 5000 liberada automaticamente
firewall-cmd --permanent --add-port=5000/tcp
firewall-cmd --reload
```

### SELinux Configurado Automaticamente
```bash
# Permissões de rede configuradas
setsebool -P httpd_can_network_connect 1
semanage port -a -t http_port_t -p tcp 5000
```

## 🔧 **COMANDOS ESSENCIAIS CENTOS**

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

### Scripts de Manutenção Simplificados
```bash
# Verificar se está funcionando
sudo /tracker/scripts/auto-restart-simple.sh

# Fazer backup manual
sudo /tracker/scripts/backup-simple.sh --config

# Backup completo
sudo /tracker/scripts/backup-simple.sh --full

# Listar backups
sudo /tracker/scripts/backup-simple.sh --list
```

### Verificações do Sistema CentOS
```bash
# Verificar firewall
sudo firewall-cmd --list-all

# Verificar SELinux
sestatus

# Verificar porta aberta
sudo ss -tlnp | grep :5000

# Testar conectividade
telnet localhost 5000
```

## 🛡️ **CARACTERÍSTICAS DO SISTEMA SIMPLIFICADO**

### Auto-Recuperação
- ✅ **Verificação a cada 5 minutos** se o serviço está funcionando
- ✅ **Reinício automático** se parar de funcionar (máximo 3 tentativas)
- ✅ **Logs detalhados** de todas as verificações
- ✅ **Verificação de conectividade** na porta 5000

### Backup Automático
- ✅ **Backup diário** da configuração (.env, systemd) às 2:30
- ✅ **Backup semanal completo** (domingo às 3:00)
- ✅ **Limpeza automática** de backups antigos (>30 dias)
- ✅ **Compressão de logs** grandes automaticamente

### Segurança CentOS
- ✅ **Usuário dedicado** `gv50tracker` (não root)
- ✅ **Firewalld configurado** automaticamente
- ✅ **SELinux compatível** com regras específicas
- ✅ **Permissões restritas** apenas ao necessário

## 📊 **MONITORAMENTO ESPECÍFICO CENTOS**

### Logs Importantes
```bash
# Logs do serviço GV50
sudo journalctl -u gv50-tracker.service

# Logs do auto-restart
sudo tail -f /var/log/gv50-auto-restart.log

# Logs do firewall
sudo journalctl -u firewalld

# Logs do SELinux (se problemas)
sudo ausearch -m avc -ts recent
```

### Verificações de Saúde
- ✅ Status do serviço systemd
- ✅ Conectividade na porta 5000
- ✅ Firewalld e regras de porta
- ✅ SELinux e permissões
- ✅ Uso de CPU e memória
- ✅ Espaço em disco
- ✅ Conectividade com MongoDB

## 🚨 **SOLUÇÃO DE PROBLEMAS CENTOS**

### Serviço não inicia
```bash
# Ver erros específicos
sudo journalctl -u gv50-tracker.service -p err

# Testar Python manualmente
sudo su - gv50tracker
cd /tracker/gv50
source ../venv/bin/activate
python main.py
```

### Firewall bloqueando
```bash
# Verificar se porta está liberada
sudo firewall-cmd --list-ports

# Liberar porta se necessário
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### SELinux bloqueando
```bash
# Verificar negações
sudo ausearch -m avc -ts recent

# Configurar permissões de rede
sudo setsebool -P httpd_can_network_connect 1

# Desabilitar temporariamente (apenas para teste)
sudo setenforce 0
```

### Python não encontrado (CentOS 7)
```bash
# Ativar Software Collections
scl enable rh-python38 bash

# Recriar ambiente virtual
cd /tracker
scl enable rh-python38 'python3 -m venv venv'
```

## 📁 **ARQUIVO DE CONFIGURAÇÃO**

### `/tracker/gv50/.env`
```env
# IP e Porta
ALLOWED_IPS=0.0.0.0/0
SERVER_PORT=5000

# Logging
LOGGING_ENABLED=true

# Database (MongoDB Atlas)
MONGODB_URI=mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/tracker
DATABASE_NAME=tracker
```

## ✅ **SISTEMA PRONTO CENTOS!**

Após a instalação com estrutura simplificada, seu sistema GV50 estará:

- 🏃‍♂️ **Rodando automaticamente** na inicialização do CentOS
- 🔄 **Se reiniciando sozinho** se parar de funcionar
- 💾 **Fazendo backup automático** das configurações
- 🛡️ **Firewall configurado** com porta 5000 liberada
- 🔒 **SELinux compatível** com permissões corretas
- 📊 **Monitorando** sua própria saúde
- 🗂️ **Limpando** arquivos antigos automaticamente

**Estrutura simples `/tracker/` - fácil de gerenciar e manter!**