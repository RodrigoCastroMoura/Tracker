#!/bin/bash

# Script de Instalação Automática - Sistema GV50 Tracker
# Uso: sudo bash install.sh

set -e  # Parar em caso de erro

echo "=================================================="
echo "   Instalação Automática - Sistema GV50 Tracker  "
echo "=================================================="

# Verificar se está rodando como root
if [[ $EUID -eq 0 ]]; then
   echo "Este script deve ser executado como root (use sudo)"
fi

# Detectar distribuição Linux
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo "Erro: Não foi possível detectar a distribuição Linux"
    exit 1
fi

echo "Distribuição detectada: $OS $VER"

# Função para Ubuntu/Debian
install_ubuntu_debian() {
    echo "Instalando dependências para Ubuntu/Debian..."
    apt update
    apt install -y python3.11 python3.11-pip python3.11-venv git curl wget
    
    # Configurar firewall
    ufw allow 5000/tcp
    ufw --force enable
}

# Função para CentOS/RHEL
install_centos_rhel() {
    echo "Instalando dependências para CentOS/RHEL..."
    yum update -y
    yum install -y python311 python311-pip git curl wget
    
    # Configurar firewall
    firewall-cmd --permanent --add-port=5000/tcp
    firewall-cmd --reload
}

# Instalar dependências baseado na distribuição
case "$OS" in
    "Ubuntu"|"Debian"*)
        install_ubuntu_debian
        ;;
    "CentOS"*|"Red Hat"*)
        install_centos_rhel
        ;;
    *)
        echo "Distribuição não suportada: $OS"
        echo "Instale manualmente: python3.11, python3.11-pip, git"
        ;;
esac

# Criar usuário do sistema
echo "Criando usuário gv50tracker..."
if ! id "gv50tracker" &>/dev/null; then
    useradd -m -s /bin/bash gv50tracker
    echo "Usuário gv50tracker criado"
else
    echo "Usuário gv50tracker já existe"
fi

# Criar diretórios
echo "Criando estrutura de diretórios..."
mkdir -p /home/gv50tracker/gv50-tracker/logs
mkdir -p /home/gv50tracker/gv50-tracker/scripts
mkdir -p /home/gv50tracker/gv50-tracker/backup

# Definir permissões
chown -R gv50tracker:gv50tracker /home/gv50tracker/
chmod 755 /home/gv50tracker/gv50-tracker

# Criar ambiente virtual Python
echo "Configurando ambiente Python..."
su - gv50tracker -c "
cd /home/gv50tracker/gv50-tracker
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pymongo python-dotenv
"

# Criar arquivo de configuração systemd
echo "Criando serviço systemd..."
cat > /etc/systemd/system/gv50-tracker.service << 'EOF'
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
EOF

# Recarregar systemd
systemctl daemon-reload

echo "=================================================="
echo "   Instalação Concluída!                         "
echo "=================================================="
echo ""
echo "Próximos passos:"
echo "1. Copie os arquivos do sistema GV50 para:"
echo "   /home/gv50tracker/gv50-tracker/gv50/"
echo ""
echo "2. Configure o arquivo .env:"
echo "   nano /home/gv50tracker/gv50-tracker/gv50/.env"
echo ""
echo "3. Habilite e inicie o serviço:"
echo "   sudo systemctl enable gv50-tracker.service"
echo "   sudo systemctl start gv50-tracker.service"
echo ""
echo "4. Verifique o status:"
echo "   sudo systemctl status gv50-tracker.service"
echo ""
echo "Sistema instalado em: /home/gv50tracker/gv50-tracker/"
echo "Logs do sistema: sudo journalctl -u gv50-tracker.service -f"