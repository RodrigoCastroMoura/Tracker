# Guia de Instalação - GPS Tracker Service no Linux

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Acesso ao servidor MongoDB

## 🚀 Passo a Passo de Instalação

### 1. Preparar o Ambiente

```bash
# Atualizar sistema (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip -y

# OU no CentOS/RHEL
sudo yum install python3 python3-pip -y
```

### 2. Copiar os Arquivos do Projeto

```bash
# Criar diretório do projeto
mkdir -p /opt/tracker
cd /opt/tracker

# Copiar todos os arquivos do projeto para /opt/tracker
# Estrutura esperada:
# /opt/tracker/
#   ├── gv50/
#   │   ├── __init__.py
#   │   ├── tcp_server.py
#   │   ├── message_handler.py
#   │   ├── database.py
#   │   ├── models.py
#   │   ├── protocol_parser.py
#   │   ├── config.py
#   │   ├── logger.py
#   │   └── datetime_converter.py
#   ├── start_service.py
#   ├── requirements.txt
#   └── .env
```

### 3. Instalar Dependências Python

```bash
cd /opt/tracker

# Instalar dependências
pip3 install -r requirements.txt

# OU instalar manualmente:
pip3 install mongoengine==0.29.1
pip3 install pymongo==4.13.2
pip3 install python-dotenv==1.0.0
pip3 install python-dateutil==2.9.0
```

### 4. Configurar Variáveis de Ambiente

Crie o arquivo `.env` na raiz do projeto:

```bash
nano /opt/tracker/.env
```

Adicione as seguintes variáveis:

```env
# Configurações do MongoDB
MONGODB_URI=mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/tracker
DATABASE_NAME=tracker

# Configurações do Servidor TCP
TCP_PORT=8000
MAX_CONNECTIONS=100

# Configurações de Log
LOG_LEVEL=ERROR
LOG_FILE=gv50_tracker.log

# Configurações de IP (opcional)
# PRIMARY_SERVER_IP=seu_ip_primario
# PRIMARY_SERVER_PORT=8000
# BACKUP_SERVER_IP=seu_ip_backup
# BACKUP_SERVER_PORT=8000
```

Salve com `Ctrl+O` e saia com `Ctrl+X`

### 5. Testar a Aplicação

```bash
cd /opt/tracker/gv50
python3 start_service.py
```

Se tudo estiver correto, você verá:
```
=== STARTING GV50 SERVICE ON PORT 8000 ===
============================================================
GV50 Tracker Service Starting
============================================================
✓ GV50 service started successfully
GV50 Tracker Service ready
✅ GV50 Service started successfully on port 8000
```

### 6. Configurar para Rodar em Background

#### Opção A: Usando systemd (Recomendado)

Crie o arquivo de serviço:

```bash
sudo nano /etc/systemd/system/gv50-tracker.service
```

Adicione o conteúdo:

```ini
[Unit]
Description=GV50 GPS Tracker Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tracker/gv50
ExecStart=/usr/bin/python3 /opt/tracker/gv50/start_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Ative e inicie o serviço:

```bash
# Recarregar configurações do systemd
sudo systemctl daemon-reload

# Ativar o serviço para iniciar no boot
sudo systemctl enable gv50-tracker

# Iniciar o serviço
sudo systemctl start gv50-tracker

# Verificar status
sudo systemctl status gv50-tracker

# Ver logs do serviço
sudo journalctl -u gv50-tracker -f
```

#### Opção B: Usando screen (Alternativa)

```bash
# Instalar screen
sudo apt install screen -y

# Criar sessão screen
screen -S gv50tracker

# Dentro do screen, executar:
cd /opt/tracker/gv50
python3 start_service.py

# Desanexar do screen: Ctrl+A, depois D
# Para voltar: screen -r gv50tracker
```

#### Opção C: Usando nohup (Simples)

```bash
cd /opt/tracker/gv50
nohup python3 start_service.py > /var/log/gv50_tracker.log 2>&1 &

# Ver PID do processo
ps aux | grep start_service

# Ver logs
tail -f /var/log/gv50_tracker.log
```

### 7. Comandos Úteis

```bash
# Parar o serviço (systemd)
sudo systemctl stop gv50-tracker

# Reiniciar o serviço (systemd)
sudo systemctl restart gv50-tracker

# Ver logs em tempo real (systemd)
sudo journalctl -u gv50-tracker -f

# Verificar se a porta está aberta
netstat -tuln | grep 8000
# OU
ss -tuln | grep 8000

# Testar conexão local
telnet localhost 8000
```

### 8. Firewall (Se necessário)

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 8000/tcp
sudo ufw reload

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

### 9. Monitoramento

```bash
# Ver processos Python em execução
ps aux | grep python

# Verificar uso de memória
top -p $(pgrep -f start_service)

# Verificar conexões TCP
netstat -an | grep 8000

# Ver últimos erros no log
tail -100 /opt/tracker/gv50/gv50_tracker.log | grep ERROR
```

### 10. Solução de Problemas

#### Erro: "No module named 'mongoengine'"
```bash
pip3 install mongoengine pymongo python-dotenv python-dateutil
```

#### Erro: "Permission denied" na porta 8000
```bash
# Usar porta acima de 1024 ou executar como root
sudo python3 start_service.py
```

#### Erro: "Cannot connect to MongoDB"
```bash
# Verificar variável MONGODB_URI no arquivo .env
# Testar conexão com MongoDB
```

#### Serviço não inicia
```bash
# Ver logs detalhados
sudo journalctl -u gv50-tracker -n 100 --no-pager
```

## 📝 Estrutura de Arquivos

```
/opt/tracker/
├── gv50/
│   ├── __init__.py
│   ├── tcp_server.py
│   ├── message_handler.py
│   ├── database.py
│   ├── models.py
│   ├── protocol_parser.py
│   ├── config.py
│   ├── logger.py
│   ├── datetime_converter.py
│   └── start_service.py
├── requirements.txt
├── .env
└── gv50_tracker.log
```

## ✅ Verificação Final

Após a instalação, verifique:

1. ✅ Serviço está rodando: `sudo systemctl status gv50-tracker`
2. ✅ Porta 8000 está aberta: `netstat -tuln | grep 8000`
3. ✅ Sem erros nos logs: `tail -f /var/log/gv50_tracker.log`
4. ✅ MongoDB conectado: Verificar logs iniciais

## 📞 Suporte

Para problemas ou dúvidas, verifique os logs em:
- `/var/log/gv50_tracker.log` (se usando nohup)
- `sudo journalctl -u gv50-tracker` (se usando systemd)
- `/opt/tracker/gv50/gv50_tracker.log` (log da aplicação)
