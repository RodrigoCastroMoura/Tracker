# Manual de Instalação CentOS - Sistema GV50 Tracker

## Requisitos do Sistema

### Sistema Operacional
- **CentOS 7/8/9** ou RHEL 7/8/9
- **Rocky Linux 8/9** ou AlmaLinux 8/9

### Recursos Mínimos
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disco**: 20GB livres
- **Rede**: Conexão estável com internet

### Portas Necessárias
- **5000**: Porta TCP para receber conexões dos dispositivos GV50
- **Saída HTTPS (443)**: Para conexão com MongoDB Atlas

## Pré-requisitos

### 1. Atualizar o Sistema CentOS
```bash
# CentOS 7
sudo yum update -y

# CentOS 8/9, Rocky Linux, AlmaLinux
sudo dnf update -y
```

### 2. Instalar EPEL Repository
```bash
# CentOS 7
sudo yum install epel-release -y

# CentOS 8/9
sudo dnf install epel-release -y
```

### 3. Instalar Python 3.11
```bash
# CentOS 7 (usando Software Collections)
sudo yum install centos-release-scl -y
sudo yum install rh-python38 -y
scl enable rh-python38 bash

# CentOS 8/9
sudo dnf install python3.11 python3.11-pip -y

# Verificar instalação
python3.11 --version
```

### 4. Instalar Dependências
```bash
# CentOS 7
sudo yum install git curl wget tar gzip -y

# CentOS 8/9
sudo dnf install git curl wget tar gzip -y
```

## Instalação do Sistema

### 1. Criar Diretório Principal
```bash
# Criar diretório /tracker
sudo mkdir -p /tracker
sudo chmod 755 /tracker
```

### 2. Criar Usuário do Sistema
```bash
# Criar usuário dedicado
sudo useradd -m -d /tracker/gv50tracker -s /bin/bash gv50tracker

# Definir propriedade do diretório
sudo chown -R gv50tracker:gv50tracker /tracker/
```

### 3. Estrutura de Diretórios
```
/tracker/
├── gv50tracker/                # Home do usuário
│   └── gv50-tracker/           # Aplicação principal
│       ├── gv50/               # Serviço GV50
│       │   ├── main.py         # Executável principal
│       │   ├── .env            # Configurações
│       │   ├── config.py       # Gerenciamento de configuração
│       │   ├── database.py     # MongoDB
│       │   ├── logger.py       # Sistema de logs
│       │   ├── message_handler.py  # Processamento
│       │   ├── models.py       # Modelos de dados
│       │   ├── protocol_parser.py  # Parser Queclink
│       │   └── tcp_server.py   # Servidor TCP
│       ├── logs/               # Logs do sistema
│       ├── scripts/            # Scripts de manutenção
│       ├── backup/             # Backups automáticos
│       └── venv/               # Ambiente virtual Python
```

### 4. Configurar Ambiente Python
```bash
# Mudar para usuário gv50tracker
sudo su - gv50tracker

# Criar diretório da aplicação
mkdir -p /tracker/gv50tracker/gv50-tracker
cd /tracker/gv50tracker/gv50-tracker

# Criar ambiente virtual
python3.11 -m venv venv

# Ativar ambiente
source venv/bin/activate

# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install pymongo python-dotenv
```

### 5. Configurar Variáveis de Ambiente
```bash
# Criar arquivo .env na pasta gv50/
mkdir -p /tracker/gv50tracker/gv50-tracker/gv50
cd /tracker/gv50tracker/gv50-tracker/gv50

# Criar arquivo .env
cat > .env << 'EOF'
# IP e Porta - configurações que podem ser alteradas
ALLOWED_IPS=0.0.0.0/0
SERVER_PORT=5000

# Logging Configuration - apenas ativar/desativar log
LOGGING_ENABLED=true

# Database Configuration
MONGODB_URI=mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/tracker
DATABASE_NAME=tracker
EOF
```

### 6. Criar Diretórios de Logs e Backup
```bash
mkdir -p /tracker/gv50tracker/gv50-tracker/logs
mkdir -p /tracker/gv50tracker/gv50-tracker/backup
mkdir -p /tracker/gv50tracker/gv50-tracker/scripts

# Definir permissões
chmod 755 /tracker/gv50tracker/gv50-tracker/logs
chmod 755 /tracker/gv50tracker/gv50-tracker/backup
```

## Configuração do Firewall CentOS

### Firewalld (CentOS 7/8/9)
```bash
# Verificar se firewalld está ativo
sudo systemctl status firewalld

# Permitir porta 5000
sudo firewall-cmd --permanent --add-port=5000/tcp

# Permitir SSH (se necessário)
sudo firewall-cmd --permanent --add-service=ssh

# Recarregar configuração
sudo firewall-cmd --reload

# Verificar regras
sudo firewall-cmd --list-all
```

### SELinux (se habilitado)
```bash
# Verificar status do SELinux
sestatus

# Se necessário, permitir conexões na porta 5000
sudo setsebool -P httpd_can_network_connect 1

# Ou adicionar contexto específico
sudo semanage port -a -t http_port_t -p tcp 5000
```

## Configuração do Systemd

### 1. Criar Arquivo de Serviço
```bash
sudo nano /etc/systemd/system/gv50-tracker.service
```

**Conteúdo do arquivo:**
```ini
[Unit]
Description=GV50 GPS Tracker Service - CentOS
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=gv50tracker
Group=gv50tracker
WorkingDirectory=/tracker/gv50tracker/gv50-tracker/gv50
Environment=PATH=/tracker/gv50tracker/gv50-tracker/venv/bin
ExecStart=/tracker/gv50tracker/gv50-tracker/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=gv50-tracker

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/tracker/gv50tracker/gv50-tracker/logs
ReadWritePaths=/tracker/gv50tracker/gv50-tracker/backup

[Install]
WantedBy=multi-user.target
```

### 2. Habilitar e Iniciar Serviço
```bash
# Recarregar configuração do systemd
sudo systemctl daemon-reload

# Habilitar serviço para iniciar automaticamente
sudo systemctl enable gv50-tracker.service

# Iniciar serviço
sudo systemctl start gv50-tracker.service

# Verificar status
sudo systemctl status gv50-tracker.service
```

## Teste da Instalação

### 1. Verificar Status do Serviço
```bash
# Status do serviço
sudo systemctl status gv50-tracker.service

# Logs em tempo real
sudo journalctl -u gv50-tracker.service -f

# Logs completos
sudo journalctl -u gv50-tracker.service --no-pager
```

### 2. Teste de Conectividade
```bash
# Verificar se a porta está aberta
sudo netstat -tlnp | grep :5000
# ou
sudo ss -tlnp | grep :5000

# Teste de conexão local
telnet localhost 5000
```

### 3. Verificar Firewall
```bash
# Verificar se a porta está liberada
sudo firewall-cmd --list-ports

# Testar de outro servidor
telnet IP_DO_SERVIDOR 5000
```

## Comandos de Gestão CentOS

### Controle do Serviço
```bash
# Iniciar serviço
sudo systemctl start gv50-tracker.service

# Parar serviço
sudo systemctl stop gv50-tracker.service

# Reiniciar serviço
sudo systemctl restart gv50-tracker.service

# Status detalhado
sudo systemctl status gv50-tracker.service -l

# Habilitar/desabilitar inicialização automática
sudo systemctl enable gv50-tracker.service
sudo systemctl disable gv50-tracker.service
```

### Monitoramento de Logs
```bash
# Logs em tempo real
sudo journalctl -u gv50-tracker.service -f

# Logs das últimas 100 linhas
sudo journalctl -u gv50-tracker.service -n 100

# Logs de hoje
sudo journalctl -u gv50-tracker.service --since today

# Logs com filtro de erro
sudo journalctl -u gv50-tracker.service -p err

# Logs em formato JSON
sudo journalctl -u gv50-tracker.service -o json
```

### Monitoramento de Sistema
```bash
# Verificar processos
ps aux | grep python
ps aux | grep gv50

# Verificar uso de rede
sudo netstat -tlnp | grep :5000
sudo ss -tlnp | grep :5000

# Verificar uso de recursos
top -p $(pgrep -f gv50-tracker)
htop -p $(pgrep -f gv50-tracker)
```

## Configurações Específicas CentOS

### 1. Configurar Logrotate
```bash
sudo nano /etc/logrotate.d/gv50-tracker
```

```ini
/tracker/gv50tracker/gv50-tracker/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 gv50tracker gv50tracker
    postrotate
        systemctl reload gv50-tracker.service > /dev/null 2>&1 || true
    endscript
}
```

### 2. Configurar Limites de Sistema
```bash
# Aumentar limites de arquivos abertos para o usuário
sudo nano /etc/security/limits.conf
```

Adicionar:
```
gv50tracker soft nofile 65536
gv50tracker hard nofile 65536
```

### 3. Configurar Timezone
```bash
# Verificar timezone
timedatectl

# Configurar timezone (se necessário)
sudo timedatectl set-timezone America/Sao_Paulo
```

## Backup e Manutenção

### Backup Manual
```bash
# Criar backup da configuração
sudo tar -czf /backup/gv50-tracker-config-$(date +%Y%m%d).tar.gz \
  /tracker/gv50tracker/gv50-tracker/gv50/.env \
  /etc/systemd/system/gv50-tracker.service

# Backup completo
sudo tar -czf /backup/gv50-tracker-full-$(date +%Y%m%d).tar.gz \
  --exclude="/tracker/gv50tracker/gv50-tracker/venv" \
  --exclude="/tracker/gv50tracker/gv50-tracker/backup" \
  /tracker/gv50tracker/gv50-tracker/
```

### Atualização do Sistema
```bash
# 1. Parar serviço
sudo systemctl stop gv50-tracker.service

# 2. Backup da configuração atual
sudo cp /tracker/gv50tracker/gv50-tracker/gv50/.env /tmp/

# 3. Atualizar código (conforme seu método)
# Exemplo: scp, rsync, git pull, etc.

# 4. Restaurar configuração
sudo cp /tmp/.env /tracker/gv50tracker/gv50-tracker/gv50/

# 5. Recarregar e iniciar
sudo systemctl daemon-reload
sudo systemctl start gv50-tracker.service

# 6. Verificar
sudo systemctl status gv50-tracker.service
```

## Solução de Problemas CentOS

### Problemas Comuns

#### 1. Python não encontrado
```bash
# Verificar versão do Python
python3.11 --version

# Se não encontrado, instalar
sudo dnf install python3.11 python3.11-pip -y
```

#### 2. Módulo pymongo não encontrado
```bash
# Entrar no ambiente virtual
sudo su - gv50tracker
cd /tracker/gv50tracker/gv50-tracker
source venv/bin/activate
pip install pymongo python-dotenv
```

#### 3. Permissões negadas
```bash
# Verificar propriedade dos arquivos
ls -la /tracker/gv50tracker/

# Corrigir permissões se necessário
sudo chown -R gv50tracker:gv50tracker /tracker/gv50tracker/
sudo chmod -R 755 /tracker/gv50tracker/gv50-tracker/
```

#### 4. Firewall bloqueando
```bash
# Verificar se a porta está liberada
sudo firewall-cmd --list-ports

# Liberar porta se necessário
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

#### 5. SELinux bloqueando
```bash
# Verificar logs do SELinux
sudo ausearch -m avc -ts recent

# Desabilitar temporariamente (para teste)
sudo setenforce 0

# Para desabilitar permanentemente
sudo nano /etc/selinux/config
# Alterar: SELINUX=disabled
```

## Segurança CentOS

### Configurações Recomendadas
1. **Firewall**: Configurar firewalld adequadamente
2. **SELinux**: Manter habilitado com regras corretas
3. **Usuário**: Sempre usar usuário dedicado
4. **Permissões**: Mínimas necessárias
5. **Logs**: Monitoramento ativo
6. **Atualizações**: Sistema sempre atualizado

### Monitoramento
```bash
# Verificar conexões ativas
sudo ss -tulpn | grep :5000

# Verificar logs de segurança
sudo journalctl -f _TRANSPORT=audit

# Verificar tentativas de conexão
sudo tail -f /var/log/secure
```

## Estrutura Final

Após a instalação, a estrutura será:
```
/tracker/
└── gv50tracker/
    └── gv50-tracker/
        ├── gv50/           # Código do serviço
        ├── venv/           # Ambiente Python
        ├── logs/           # Logs da aplicação
        ├── backup/         # Backups automáticos
        └── scripts/        # Scripts de manutenção
```

**Sistema configurado e pronto para funcionar no CentOS com diretório /tracker!**