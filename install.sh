#!/bin/bash

# Script de Instalação Automática - GV50 GPS Tracker Service
# Para Linux (Ubuntu/Debian/CentOS)

set -e

echo "=========================================="
echo "  GV50 GPS Tracker - Instalação Linux"
echo "=========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir mensagens
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    print_warning "Este script precisa ser executado como root (sudo)"
    exit 1
fi

# 1. Detectar sistema operacional
print_info "Detectando sistema operacional..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    print_info "Sistema detectado: $OS"
else
    print_error "Não foi possível detectar o sistema operacional"
    exit 1
fi

# 2. Instalar Python e pip
print_info "Instalando Python 3 e pip..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt update
    apt install -y python3 python3-pip
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
    yum install -y python3 python3-pip
else
    print_warning "Sistema não reconhecido, tentando instalação genérica..."
    apt install -y python3 python3-pip || yum install -y python3 python3-pip
fi

# 3. Criar diretório do projeto
INSTALL_DIR="/opt/tracker"
print_info "Criando diretório de instalação: $INSTALL_DIR"
mkdir -p $INSTALL_DIR

# 4. Copiar arquivos (assumindo que está executando do diretório do projeto)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
print_info "Copiando arquivos do projeto..."
cp -r "$SCRIPT_DIR"/* $INSTALL_DIR/
cd $INSTALL_DIR

# 5. Instalar dependências Python
print_info "Instalando dependências Python..."
pip3 install -r requirements.txt

# 6. Configurar arquivo .env se não existir
if [ ! -f "$INSTALL_DIR/.env" ]; then
    print_info "Criando arquivo .env..."
    cat > $INSTALL_DIR/.env << 'EOF'
# Configurações do MongoDB
MONGODB_URI=mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/tracker
DATABASE_NAME=tracker

# Configurações do Servidor TCP
TCP_PORT=8000
MAX_CONNECTIONS=100

# Configurações de Log
LOG_LEVEL=ERROR
LOG_FILE=gv50_tracker.log
EOF
    print_info "Arquivo .env criado. Configure as variáveis conforme necessário."
else
    print_info "Arquivo .env já existe, mantendo configurações atuais."
fi

# 7. Criar serviço systemd
print_info "Criando serviço systemd..."
cat > /etc/systemd/system/gv50-tracker.service << EOF
[Unit]
Description=GV50 GPS Tracker Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/gv50
ExecStart=/usr/bin/python3 $INSTALL_DIR/gv50/start_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 8. Recarregar systemd e habilitar serviço
print_info "Configurando serviço systemd..."
systemctl daemon-reload
systemctl enable gv50-tracker

# 9. Configurar firewall (se UFW estiver instalado)
if command -v ufw &> /dev/null; then
    print_info "Configurando firewall UFW..."
    ufw allow 8000/tcp
    ufw reload 2>/dev/null || true
fi

# 10. Configurar firewall (se firewalld estiver instalado)
if command -v firewall-cmd &> /dev/null; then
    print_info "Configurando firewall firewalld..."
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --reload 2>/dev/null || true
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  Instalação Concluída com Sucesso!${NC}"
echo "=========================================="
echo ""
print_info "Comandos úteis:"
echo "  Iniciar serviço:    sudo systemctl start gv50-tracker"
echo "  Parar serviço:      sudo systemctl stop gv50-tracker"
echo "  Status do serviço:  sudo systemctl status gv50-tracker"
echo "  Ver logs:           sudo journalctl -u gv50-tracker -f"
echo ""
print_info "Deseja iniciar o serviço agora? (s/n)"
read -r response
if [[ "$response" =~ ^([sS][iI][mM]|[sS])$ ]]; then
    print_info "Iniciando serviço GV50 Tracker..."
    systemctl start gv50-tracker
    sleep 2
    systemctl status gv50-tracker
    echo ""
    print_info "Serviço iniciado! Verifique os logs para confirmar."
else
    print_info "Para iniciar o serviço manualmente, execute:"
    echo "  sudo systemctl start gv50-tracker"
fi

echo ""
print_info "Instalação finalizada!"
