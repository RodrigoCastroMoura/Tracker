#!/bin/bash

# Script de Instalação Automática CentOS - Sistema GV50 Tracker
# Uso: sudo bash install-centos.sh

set -e  # Parar em caso de erro

echo "=================================================="
echo "   Instalação CentOS - Sistema GV50 Tracker      "
echo "=================================================="

# Verificar se está rodando como root
if [[ $EUID -ne 0 ]]; then
   echo "Este script deve ser executado como root (use sudo)"
   exit 1
fi

# Detectar versão do CentOS
if [ -f /etc/centos-release ]; then
    CENTOS_VERSION=$(rpm -q --queryformat '%{VERSION}' centos-release 2>/dev/null || echo "unknown")
    echo "CentOS $CENTOS_VERSION detectado"
elif [ -f /etc/redhat-release ]; then
    echo "Sistema Red Hat compatível detectado"
    CENTOS_VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+' | head -1)
else
    echo "Erro: Sistema não é CentOS/RHEL compatível"
    exit 1
fi

echo "Versão detectada: $CENTOS_VERSION"

# Função para CentOS 7
install_centos7() {
    echo "Configurando CentOS 7..."
    
    # Atualizar sistema
    yum update -y
    
    # Instalar EPEL
    yum install epel-release -y
    
    # Instalar dependências básicas
    yum install git curl wget tar gzip net-tools -y
    
    # Instalar Python 3.11 (via Software Collections)
    yum install centos-release-scl -y
    yum install rh-python38 -y
    
    echo "CentOS 7 configurado. Nota: Use 'scl enable rh-python38 bash' para ativar Python"
}

# Função para CentOS 8/9
install_centos8_9() {
    echo "Configurando CentOS 8/9..."
    
    # Atualizar sistema
    dnf update -y
    
    # Instalar EPEL
    dnf install epel-release -y
    
    # Instalar dependências
    dnf install git curl wget tar gzip net-tools python3.11 python3.11-pip -y
}

# Instalar baseado na versão
if [[ "$CENTOS_VERSION" == "7" ]]; then
    install_centos7
else
    install_centos8_9
fi

# Configurar firewall
echo "Configurando firewall..."
systemctl enable firewalld
systemctl start firewalld

# Permitir porta 5000
firewall-cmd --permanent --add-port=5000/tcp
firewall-cmd --reload

echo "Firewall configurado (porta 5000 liberada)"

# Criar diretório principal /tracker
echo "Criando estrutura de diretórios..."
mkdir -p /tracker
chmod 755 /tracker

# Criar usuário do sistema
echo "Criando usuário gv50tracker..."
if ! id "gv50tracker" &>/dev/null; then
    useradd -m -d /tracker/gv50tracker -s /bin/bash gv50tracker
    echo "Usuário gv50tracker criado em /tracker/gv50tracker"
else
    echo "Usuário gv50tracker já existe"
fi

# Criar estrutura de diretórios
echo "Criando estrutura de diretórios..."
mkdir -p /tracker/gv50tracker/gv50-tracker/gv50
mkdir -p /tracker/gv50tracker/gv50-tracker/logs
mkdir -p /tracker/gv50tracker/gv50-tracker/scripts
mkdir -p /tracker/gv50tracker/gv50-tracker/backup

# Definir permissões
chown -R gv50tracker:gv50tracker /tracker/
chmod -R 755 /tracker/gv50tracker/

# Criar ambiente virtual Python
echo "Configurando ambiente Python..."

if [[ "$CENTOS_VERSION" == "7" ]]; then
    # Para CentOS 7, usar SCL
    su - gv50tracker -c "
    cd /tracker/gv50tracker/gv50-tracker
    scl enable rh-python38 'python3 -m venv venv'
    source venv/bin/activate
    pip install --upgrade pip
    pip install pymongo python-dotenv
    "
else
    # Para CentOS 8/9
    su - gv50tracker -c "
    cd /tracker/gv50tracker/gv50-tracker
    python3.11 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install pymongo python-dotenv
    "
fi

# Criar arquivo .env padrão
echo "Criando arquivo de configuração..."
cat > /tracker/gv50tracker/gv50-tracker/gv50/.env << 'EOF'
# IP e Porta - configurações que podem ser alteradas
ALLOWED_IPS=0.0.0.0/0
SERVER_PORT=5000

# Logging Configuration - apenas ativar/desativar log
LOGGING_ENABLED=true

# Database Configuration
MONGODB_URI=mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/tracker
DATABASE_NAME=tracker
EOF

# Definir propriedade do arquivo .env
chown gv50tracker:gv50tracker /tracker/gv50tracker/gv50-tracker/gv50/.env

# Criar arquivo de serviço systemd
echo "Criando serviço systemd..."
cat > /etc/systemd/system/gv50-tracker.service << 'EOF'
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
EOF

# Configurar logrotate
echo "Configurando logrotate..."
cat > /etc/logrotate.d/gv50-tracker << 'EOF'
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
EOF

# Configurar limites de sistema
echo "Configurando limites de sistema..."
cat >> /etc/security/limits.conf << 'EOF'

# Limites para usuário gv50tracker
gv50tracker soft nofile 65536
gv50tracker hard nofile 65536
EOF

# Recarregar systemd
systemctl daemon-reload

# Verificar SELinux
if command -v getenforce >/dev/null 2>&1; then
    SELINUX_STATUS=$(getenforce)
    echo "SELinux status: $SELINUX_STATUS"
    
    if [[ "$SELINUX_STATUS" == "Enforcing" ]]; then
        echo "Configurando SELinux para permitir conexões de rede..."
        setsebool -P httpd_can_network_connect 1 2>/dev/null || true
        
        # Adicionar contexto para a porta 5000 se necessário
        semanage port -a -t http_port_t -p tcp 5000 2>/dev/null || true
    fi
fi

echo "=================================================="
echo "   Instalação CentOS Concluída!                  "
echo "=================================================="
echo ""
echo "Estrutura criada em: /tracker/gv50tracker/gv50-tracker/"
echo ""
echo "Próximos passos:"
echo "1. Copie os arquivos do sistema GV50 para:"
echo "   /tracker/gv50tracker/gv50-tracker/gv50/"
echo ""
echo "2. Configure o arquivo .env se necessário:"
echo "   nano /tracker/gv50tracker/gv50-tracker/gv50/.env"
echo ""
echo "3. Habilite e inicie o serviço:"
echo "   sudo systemctl enable gv50-tracker.service"
echo "   sudo systemctl start gv50-tracker.service"
echo ""
echo "4. Verifique o status:"
echo "   sudo systemctl status gv50-tracker.service"
echo ""
echo "5. Configure monitoramento automático:"
echo "   sudo bash scripts/setup-cron-centos.sh"
echo ""
echo "Informações importantes:"
echo "• Firewall: Porta 5000 liberada"
echo "• Logrotate: Configurado para rotacionar logs"
echo "• Limites: Configurados para o usuário gv50tracker"
if [[ "$CENTOS_VERSION" == "7" ]]; then
echo "• Python: Use 'scl enable rh-python38 bash' quando necessário"
fi
echo ""
echo "Logs do sistema: sudo journalctl -u gv50-tracker.service -f"
echo "Diretório base: /tracker/gv50tracker/gv50-tracker/"