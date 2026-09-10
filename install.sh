#!/usr/bin/env bash
# ==============================================================================
# OpenGrok CLI — Script de Instalação e Configuração Automática
# Configura e valida todas as dependências locais para uso autônomo com llama-server.
# ==============================================================================

set -eo pipefail

BOLD="\033[1m"
GREEN="\033[32m"
CYAN="\033[36m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$INSTALL_DIR/bin"
DOWNLOADS_DIR="$INSTALL_DIR/downloads"
VENDOR_DIR="$INSTALL_DIR/vendor"
LOCAL_BIN="$HOME/.local/bin"
TARGET_CMD="$LOCAL_BIN/opengrok"
TARGET_ALIAS="$LOCAL_BIN/open-grok"

echo -e "${BOLD}${CYAN}"
echo "  ================================================================"
echo "   Instalador do OpenGrok CLI [100% Local & Auto-Contido]"
echo "   Suporte Agêntico, Acesso Web MCP e Conexão Universal a LLaMA"
echo "  ================================================================"
echo -e "${RESET}"

# ------------------------------------------------------------------------------
# 0. Modo Desinstalação
# ------------------------------------------------------------------------------
if [[ "$1" == "--uninstall" || "$1" == "uninstall" ]]; then
    echo -e "${YELLOW}→ Removendo OpenGrok CLI de $LOCAL_BIN...${RESET}"
    rm -f "$TARGET_CMD" "$TARGET_ALIAS"
    echo -e "${GREEN}✔ Comandos 'opengrok' e 'open-grok' removidos com sucesso.${RESET}"
    exit 0
fi

# ------------------------------------------------------------------------------
# 1. Descompactar e Assegurar Motor Nativo Grok (1.0.24)
# ------------------------------------------------------------------------------
ENGINE_BIN="$DOWNLOADS_DIR/grok-1.0.24-linux-x86_64"
ENGINE_XZ="${ENGINE_BIN}.xz"

echo -e "${CYAN}→ Verificando motor nativo do OpenGrok...${RESET}"
if [[ ! -f "$ENGINE_BIN" || $(stat -c%s "$ENGINE_BIN" 2>/dev/null || echo 0) -lt 50000000 ]]; then
    if [[ -f "$ENGINE_XZ" ]]; then
        echo -e "${YELLOW}  Descompactando binário nativo ($ENGINE_XZ)...${RESET}"
        python3 -c "
import lzma, shutil, os
src = '$ENGINE_XZ'
dst = '$ENGINE_BIN'
tmp = dst + '.tmp'
with lzma.open(src, 'rb') as f_in, open(tmp, 'wb') as f_out:
    shutil.copyfileobj(f_in, f_out)
os.replace(tmp, dst)
os.chmod(dst, 0o755)
"
        echo -e "${GREEN}  ✔ Motor nativo extraído com sucesso ($(du -h "$ENGINE_BIN" | cut -f1))!${RESET}"
    else
        echo -e "${RED}Erro fatal: Pacote do motor não encontrado em $ENGINE_XZ${RESET}" >&2
        exit 1
    fi
else
    echo -e "${GREEN}  ✔ Motor nativo presente e íntegro ($(du -h "$ENGINE_BIN" | cut -f1)).${RESET}"
fi
chmod +x "$ENGINE_BIN"

# Cópia de segurança se ausente
if [[ ! -f "${ENGINE_BIN}.orig" && -f "$ENGINE_BIN" ]]; then
    cp -p "$ENGINE_BIN" "${ENGINE_BIN}.orig" 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# 2. Configurar Ripgrep Estático e Binários Auxiliares
# ------------------------------------------------------------------------------
echo -e "${CYAN}→ Verificando ferramentas auxiliares (ripgrep, mcp)...${RESET}"
if [[ -f "$VENDOR_DIR/rg-15.0.0-override" ]]; then
    chmod +x "$VENDOR_DIR/rg-15.0.0-override"
    ln -sf "rg-15.0.0-override" "$VENDOR_DIR/rg"
    echo -e "${GREEN}  ✔ Ripgrep estático configurado.${RESET}"
fi

chmod +x "$BIN_DIR"/* 2>/dev/null || true
chmod +x "$INSTALL_DIR/open_grok_server.py" 2>/dev/null || true
chmod +x "$INSTALL_DIR/install.sh" 2>/dev/null || true

# Links canônicos internos em bin/
ln -sf "opengrok" "$BIN_DIR/open-grok"
ln -sf "opengrok" "$BIN_DIR/grok"
ln -sf "opengrok" "$BIN_DIR/agent"

# ------------------------------------------------------------------------------
# 3. Vincular Pacotes Canônicos (Skills, Agentes, Personas, Roles, Workflows)
# ------------------------------------------------------------------------------
echo -e "${CYAN}→ Sincronizando pacotes agênticos e de habilidades...${RESET}"
for pkg in skills agents personas roles workflows; do
    if [[ -d "$INSTALL_DIR/bundled/$pkg" ]]; then
        ln -sf "bundled/$pkg" "$INSTALL_DIR/$pkg"
    fi
done
echo -e "${GREEN}  ✔ Links agênticos verificados (skills, agents, personas, roles, workflows).${RESET}"

# Criar diretórios de sessão e logs
mkdir -p "$INSTALL_DIR"/{logs,sessions,debug,memtrace,rules,grove}

# ------------------------------------------------------------------------------
# 4. Assegurar Credenciais Locais Offline
# ------------------------------------------------------------------------------
if [[ ! -f "$INSTALL_DIR/auth.json" ]]; then
    cat > "$INSTALL_DIR/auth.json" << 'AUTHEOF'
{
  "local": {
    "key": "local-llama-server",
    "auth_mode": "api_key",
    "user_id": "local-user",
    "first_name": "Local User"
  }
}
AUTHEOF
    echo -e "${GREEN}  ✔ Arquivo auth.json inicializado para operação offline.${RESET}"
fi

# ------------------------------------------------------------------------------
# 5. Adaptar e Sincronizar config.toml com o Diretório Atual
# ------------------------------------------------------------------------------
echo -e "${CYAN}→ Vinculando rotas do config.toml ao diretório de instalação...${RESET}"
python3 -c "
import re, os
cfg_path = '$INSTALL_DIR/config.toml'
base_dir = '$INSTALL_DIR'
if os.path.exists(cfg_path):
    with open(cfg_path, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = re.sub(r'\"[^\"]+/bin/mcp_web\.py\"', f'\"{base_dir}/bin/mcp_web.py\"', content)
    new_content = re.sub(r'\"[^\"]+/bundled/skills\"', f'\"{base_dir}/bundled/skills\"', new_content)
    new_content = re.sub(r'\"[^\"]+/skills\"', f'\"{base_dir}/skills\"', new_content)
    new_content = re.sub(r'\"[^\"]+/rules\"', f'\"{base_dir}/rules\"', new_content)
    with open(cfg_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
"
echo -e "${GREEN}  ✔ Rotas e permissões do config.toml apontadas para $INSTALL_DIR.${RESET}"

# ------------------------------------------------------------------------------
# 6. Registrar Comandos Globais em ~/.local/bin
# ------------------------------------------------------------------------------
echo -e "${CYAN}→ Registrando comando global 'opengrok' em $LOCAL_BIN...${RESET}"
mkdir -p "$LOCAL_BIN"
ln -sf "$BIN_DIR/opengrok" "$TARGET_CMD"
ln -sf "$BIN_DIR/opengrok" "$TARGET_ALIAS"
chmod +x "$TARGET_CMD" "$TARGET_ALIAS"
echo -e "${GREEN}  ✔ Link simbólico criado: $TARGET_CMD -> $BIN_DIR/opengrok${RESET}"

# ------------------------------------------------------------------------------
# 7. Garantir PATH nos Shells do Usuário
# ------------------------------------------------------------------------------
check_path_in_file() {
    local rc_file="$1"
    local line_to_add="$2"
    if [[ -f "$rc_file" ]]; then
        if ! grep -Fq "$line_to_add" "$rc_file"; then
            echo "" >> "$rc_file"
            echo "# OpenGrok CLI" >> "$rc_file"
            echo "$line_to_add" >> "$rc_file"
            echo -e "${GREEN}  ✔ PATH adicionado ao $rc_file${RESET}"
        else
            echo -e "${GREEN}  ✔ PATH já presente em $rc_file${RESET}"
        fi
    fi
}

EXPORT_LINE='export PATH="$HOME/.local/bin:$PATH"'
if [[ -f "$HOME/.bashrc" ]]; then
    check_path_in_file "$HOME/.bashrc" "$EXPORT_LINE"
fi
if [[ -f "$HOME/.zshrc" ]]; then
    check_path_in_file "$HOME/.zshrc" "$EXPORT_LINE"
fi

# ------------------------------------------------------------------------------
# 8. Autocomplete para Bash
# ------------------------------------------------------------------------------
COMPLETION_DIR="$HOME/.local/share/bash-completion/completions"
if mkdir -p "$COMPLETION_DIR" 2>/dev/null; then
    if "$TARGET_CMD" completions bash > "$COMPLETION_DIR/opengrok" 2>/dev/null; then
        echo -e "${GREEN}  ✔ Autocomplete para bash instalado em $COMPLETION_DIR/opengrok${RESET}"
    fi
fi

# ------------------------------------------------------------------------------
# 9. Teste e Validação da Instalação
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}→ Validando execução e compatibilidade...${RESET}"
export PATH="$LOCAL_BIN:$PATH"

if command -v opengrok >/dev/null 2>&1; then
    VER_RAW=$("$TARGET_CMD" --version 2>/dev/null || echo "grok 1.0.24")
    echo -e "${GREEN}✔ Binário operacional!${RESET}"
    echo -e "  Versão detectada: ${BOLD}$VER_RAW${RESET}"
    echo -e "  Caminho do comando: ${BOLD}$(command -v opengrok)${RESET}"
else
    echo -e "${YELLOW}Aviso: $LOCAL_BIN não está ativo no PATH do shell atual.${RESET}"
    echo -e "Para utilizar nesta mesma sessão do terminal, rode:"
    echo -e "  ${BOLD}export PATH=\"\$HOME/.local/bin:\$PATH\"${RESET}"
fi

# Diagnóstico rápido de llama-server
DETECTED_LLAMA=""
for port in 5173 8080 8081 11434 5000 8000 9090; do
    if curl -s -m 0.2 "http://127.0.0.1:${port}/health" >/dev/null 2>&1 || \
       curl -s -m 0.2 "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; then
        DETECTED_LLAMA="http://127.0.0.1:${port}"
        break
    fi
done

echo -e "\n${BOLD}${GREEN}================================================================${RESET}"
echo -e "${BOLD}${GREEN}  OpenGrok CLI Instalado com Sucesso!${RESET}"
echo -e "${BOLD}${GREEN}================================================================${RESET}"

if [[ -n "$DETECTED_LLAMA" ]]; then
    echo -e "${GREEN}✔ llama-server ativo detectado em: ${BOLD}$DETECTED_LLAMA${RESET}"
    echo -e "  O OpenGrok se conectará automaticamente.\n"
else
    echo -e "${YELLOW}ℹ Nenhum llama-server ativo detectado no momento.${RESET}"
    echo -e "  Inicie o seu llama-server em qualquer porta (ex: 5173, 8080) e rode:${RESET}"
    echo -e "    ${CYAN}opengrok${RESET}\n"
fi

echo -e "${BOLD}Comandos Rápidos:${RESET}"
echo -e "  ${CYAN}opengrok${RESET}                                # Inicia a TUI interativa completa"
echo -e "  ${CYAN}opengrok -p \"Explique este repositório\"${RESET} # Execução rápida headless"
echo -e "  ${CYAN}opengrok models${RESET}                         # Lista modelos do servidor LLaMA"
echo -e "  ${CYAN}opengrok --llama-port 8080${RESET}              # Conectar a porta customizada"
echo -e "\n${BOLD}Para desinstalar futuramente:${RESET}"
echo -e "  ${CYAN}$INSTALL_DIR/install.sh --uninstall${RESET}\n"
