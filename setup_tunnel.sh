#!/bin/bash

# Cores para facilitar a leitura
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}   CONFIGURAÇÃO AUTOMÁTICA CLOUDFLARE     ${NC}"
echo -e "${BLUE}   (Debian/Ubuntu, Fedora, Arch/Manjaro)  ${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# 1. Verifica Arquitetura do Sistema
ARCH_RAW=$(uname -m)
case $ARCH_RAW in
    x86_64)
        ARCH_DEB="amd64"
        ARCH_RPM="x86_64"
        ARCH_BIN="amd64"
        ;;
    aarch64|arm64)
        ARCH_DEB="arm64"
        ARCH_RPM="aarch64"
        ARCH_BIN="arm64"
        ;;
    armv7l)
        ARCH_DEB="armhf"
        ARCH_RPM="armhfp"
        ARCH_BIN="arm"
        ;;
    *)
        echo -e "${RED}Arquitetura $ARCH_RAW não suportada automaticamente.${NC}"
        exit 1
        ;;
esac

# 2. Verifica a Distribuição (baseado no gerenciador de pacotes)
if command -v apt-get &> /dev/null; then
    # === DEBIAN / UBUNTU / MINT ===
    DISTRO="Debian/Ubuntu/Mint"
    PACKAGE_TYPE="deb"
    URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH_DEB}.deb"
    INSTALL_CMD="sudo dpkg -i cloudflared.deb"

elif command -v dnf &> /dev/null; then
    # === FEDORA / RHEL ===
    DISTRO="Fedora/RHEL"
    PACKAGE_TYPE="rpm"
    URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH_RPM}.rpm"
    INSTALL_CMD="sudo dnf install -y ./cloudflared.rpm"

elif command -v pacman &> /dev/null; then
    # === ARCH / MANJARO ===
    # Arch não usa .deb/.rpm nativamente. 
    # A maneira mais segura sem AUR helpers é baixar o binário direto.
    DISTRO="Arch Linux/Manjaro"
    PACKAGE_TYPE="binary"
    URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH_BIN}"
    # Não há comando de pacote, instalação é manual (mover binário)
else
    echo -e "${RED}Sistema operacional não identificado ou não suportado.${NC}"
    exit 1
fi

echo -e "Sistema detectado: ${GREEN}$DISTRO ($ARCH_RAW)${NC}"
echo -e "Baixando versão: ${GREEN}$URL${NC}..."

# 3. Download
if [ "$PACKAGE_TYPE" == "binary" ]; then
    wget -q $URL -O cloudflared
else
    wget -q $URL -O "cloudflared.$PACKAGE_TYPE"
fi

# 4. Instalação
echo "Instalando..."

if [ "$PACKAGE_TYPE" == "binary" ]; then
    # Instalação manual para Arch/Outros (Binário puro)
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/
    if ! command -v cloudflared &> /dev/null; then
        echo -e "${RED}Erro ao mover binário. Verifique seu PATH.${NC}"
        exit 1
    fi
else
    # Instalação via Gerenciador de Pacotes (Debian/Fedora)
    $INSTALL_CMD
    rm "cloudflared.$PACKAGE_TYPE"
fi

echo ""
echo -e "${GREEN}✅ Cloudflared instalado com sucesso!${NC}"
echo ""
echo "PRÓXIMOS PASSOS:"
echo "1. Acesse https://one.dash.cloudflare.com/"
echo "2. Vá em Access > Tunnels > Create a Tunnel."
echo "3. Copie o comando de instalação (sudo cloudflared service install ...)"
echo "4. Cole o comando no terminal."
echo ""
read -p "Pressione ENTER para sair..."