# Manual de Instalação - Sistema GV50 Tracker

## Requisitos do Sistema

### Sistema Operacional
- Ubuntu 20.04 LTS ou superior
- CentOS 7/8 ou RHEL 7/8
- Debian 10 ou superior

### Recursos Mínimos
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disco**: 20GB livres
- **Rede**: Conexão estável com internet

### Portas Necessárias
- **5000**: Porta TCP para receber conexões dos dispositivos GV50
- **Saída HTTPS (443)**: Para conexão com MongoDB Atlas

## Pré-requisitos

### 1. Atualizar o Sistema
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 2. Instalar Python 3.11
```bash
# Ubuntu/Debian
sudo apt install python3.11 python3.11-pip python3.11-venv -y

# CentOS/RHEL
sudo yum install python311 python311-pip -y
```

### 3. Instalar Git
```bash
# Ubuntu/Debian
sudo apt install git -y

# CentOS/RHEL
sudo yum install git -y
```

## Instalação do Sistema

### 1. Criar Usuário do Sistema
```bash
# Criar usuário dedicado
sudo useradd -m -s /bin/bash gv50tracker
sudo usermod -aG sudo gv50tracker

# Mudar para o usuário
sudo su - gv50tracker
```

### 2. Baixar o Código
```bash
# Criar diretório do projeto
mkdir -p /home/gv50tracker/gv50-tracker
cd /home/gv50tracker/gv50-tracker

# Copiar arquivos do sistema (substitua pelo seu método de transferência)
# Exemplo: scp, git clone, ou transferência manual
```

### 3. Estrutura de Diretórios
```
/home/gv50tracker/gv50-tracker/
├── gv50/                    # Serviço GV50
│   ├── main.py             # Executável principal
│   ├── .env                # Configurações
│   ├── config.py           # Gerenciamento de configuração
│   ├── database.py         # MongoDB
│   ├── logger.py           # Sistema de logs
│   ├── message_handler.py  # Processamento de mensagens
│   ├── models.py           # Modelos de dados
│   ├── protocol_parser.py  # Parser Queclink
│   └── tcp_server.py       # Servidor TCP
├── logs/                   # Logs do sistema
├── scripts/                # Scripts de instalação
└── systemd/                # Arquivos de serviço
```

### 4. Configurar Ambiente Python
```bash
cd /home/gv50tracker/gv50-tracker

# Criar ambiente virtual
python3.11 -m venv venv

# Ativar ambiente
source venv/bin/activate

# Instalar dependências
pip install pymongo python-dotenv
```

### 5. Configurar Variáveis de Ambiente
```bash
cd gv50/

# Editar arquivo .env
nano .env
```

**Conteúdo do arquivo .env:**
```env
# IP e Porta - configurações que podem ser alteradas
ALLOWED_IPS=0.0.0.0/0
SERVER_PORT=5000

# Logging Configuration - apenas ativar/desativar log
LOGGING_ENABLED=true

# Database Configuration
MONGODB_URI=mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/tracker
DATABASE_NAME=tracker
```

### 6. Criar Diretório de Logs
```bash
mkdir -p /home/gv50tracker/gv50-tracker/logs
chmod 755 /home/gv50tracker/gv50-tracker/logs
```

## Configuração do Firewall

### Ubuntu/Debian (UFW)
```bash
# Permitir porta 5000
sudo ufw allow 5000/tcp

# Permitir SSH (se necessário)
sudo ufw allow 22/tcp

# Ativar firewall
sudo ufw enable
```

### CentOS/RHEL (firewalld)
```bash
# Permitir porta 5000
sudo firewall-cmd --permanent --add-port=5000/tcp

# Recarregar configuração
sudo firewall-cmd --reload
```

## Configuração do Systemd

### 1. Criar Arquivo de Serviço
```bash
sudo nano /etc/systemd/system/gv50-tracker.service
```

**Conteúdo do arquivo:**
```ini
[Unit]
Description=GV50 GPS Tracker Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=gv50tracker
Group=gv50tracker
WorkingDirectory=/home/gv50tracker/gv50-tracker/gv50
Environment=PATH=/home/gv50tracker/gv50-tracker/venv/bin
ExecStart=/home/gv50tracker/gv50-tracker/venv/bin/python main.py
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
ReadWritePaths=/home/gv50tracker/gv50-tracker/logs

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

# Teste de conexão local
telnet localhost 5000
```

### 3. Teste com Dispositivo Simulado
```bash
cd /home/gv50tracker/gv50-tracker/gv50

# Ativar ambiente virtual
source ../venv/bin/activate

# Executar teste
python3 -c "
import socket
message = '+RESP:GTIGN,060228,TEST123456789,,0,0,1,1,4.3,92,70.0,121.354335,31.222073,20090214013254,0460,0000,18d8,6141,00,2000.0,12345$'
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 5000))
sock.send(message.encode('utf-8'))
response = sock.recv(1024)
print(f'Resposta: {response.decode()}')
sock.close()
"
```

## Comandos de Gestão

### Controle do Serviço
```bash
# Iniciar serviço
sudo systemctl start gv50-tracker.service

# Parar serviço
sudo systemctl stop gv50-tracker.service

# Reiniciar serviço
sudo systemctl restart gv50-tracker.service

# Recarregar configuração
sudo systemctl reload-or-restart gv50-tracker.service

# Ver status
sudo systemctl status gv50-tracker.service
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
```

## Backup e Manutenção

### Backup da Configuração
```bash
# Criar backup
sudo tar -czf /backup/gv50-tracker-$(date +%Y%m%d).tar.gz \
  /home/gv50tracker/gv50-tracker/gv50/.env \
  /etc/systemd/system/gv50-tracker.service

# Restaurar backup
sudo tar -xzf /backup/gv50-tracker-YYYYMMDD.tar.gz -C /
```

### Atualização do Sistema
```bash
# Parar serviço
sudo systemctl stop gv50-tracker.service

# Fazer backup da configuração
cp /home/gv50tracker/gv50-tracker/gv50/.env /tmp/gv50-env-backup

# Atualizar código (método depende da sua estratégia)
# Exemplo: git pull, scp, etc.

# Restaurar configuração se necessário
cp /tmp/gv50-env-backup /home/gv50tracker/gv50-tracker/gv50/.env

# Iniciar serviço
sudo systemctl start gv50-tracker.service

# Verificar se funcionou
sudo systemctl status gv50-tracker.service
```

## Solução de Problemas

### Serviço não inicia
```bash
# Verificar logs de erro
sudo journalctl -u gv50-tracker.service -p err

# Verificar permissões
ls -la /home/gv50tracker/gv50-tracker/gv50/

# Testar manualmente
sudo su - gv50tracker
cd /home/gv50tracker/gv50-tracker/gv50
source ../venv/bin/activate
python main.py
```

### Porta ocupada
```bash
# Verificar qual processo está usando a porta
sudo lsof -i :5000
sudo netstat -tlnp | grep :5000

# Matar processo se necessário
sudo kill -9 PID_DO_PROCESSO
```

### Problemas de conectividade
```bash
# Verificar firewall
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS

# Testar conectividade externa
telnet SEU_SERVIDOR_IP 5000
```

## Segurança

### Configurações Recomendadas
1. **Firewall**: Permitir apenas IPs necessários na porta 5000
2. **Usuário**: Executar sempre com usuário dedicado (não root)
3. **Logs**: Monitorar logs regularmente
4. **Backup**: Fazer backup regular das configurações
5. **Atualizações**: Manter sistema operacional atualizado

### Monitoramento
- Configure alertas para quando o serviço parar
- Monitore uso de CPU e memória
- Acompanhe logs de erro
- Verifique conectividade de rede regularmente

## Suporte

Para problemas técnicos:
1. Verifique os logs do sistema
2. Teste conectividade de rede
3. Confirme configurações do banco de dados
4. Verifique permissões de arquivos

O sistema está configurado para reiniciar automaticamente em caso de falha.