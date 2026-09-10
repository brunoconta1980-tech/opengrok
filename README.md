# OpenGrok

> **OpenGrok — An original OpenAI project**  
> Interface soberana, autêntica e 100% local do Grok CLI, com autonomia agêntica plena, acesso web nativo e conexão universal a qualquer `llama-server` ou Ollama com suporte a CORS PLENO (`*`).

---

## 🎯 Destaques do Projeto

- **Interface Original Autêntica com Identidade Própria:** Executa o binário nativo oficial do Grok Build 1.0.24 em Rust com a interface TUI completa (Ratatui/Crossterm), caixa de prompt interativa, suporte a raciocínio (`reasoning_content`), execução de comandos, edição de arquivos e subagentes. A tela inicial exibe no rodapé o nome e a frase com a mesma estilização visual original:
  ```text
  Logged in with API key  │   OpenGrok - An original OpenAI project   1.0.24
  ```
  O layout completo, a navegação e o logo em braille original permanecem 100% preservados e funcionais.
- **100% Auto-Contido e Portátil:** Todas as dependências (binário estático, ripgrep nativo, 24 skills, agentes, personas, papéis e workflows) residem dentro da pasta `open_grok_cli`.
- **Acesso Web e Ferramentas Agênticas (MCP Embutido):** Servidor MCP nativo em Python padrão ([`bin/mcp_web.py`](file:///home/userk21/open_grok_cli/bin/mcp_web.py)) integrado ao motor da CLI, fornecendo busca web real (DuckDuckGo), download de páginas com descompressão gzip e salvamento de arquivos sem dependências externas.
- **Arquitetura Agêntica & Subagentes Ativos:** Suporte habilitado para até 4 subagentes paralelos em fila com profundidade 3, cobrindo papéis especializados (`explore`, `plan`, `researcher`, `reviewer`, `implementer`, `test-writer`, `security-auditor`, `design-doc-writer`, `design-doc-reviewer`).
- **Bridge Universal Local com CORS PLENO (`open_grok_server.py`):** Proxy HTTP/SSE embutido com cabeçalhos `Access-Control-Allow-Origin: *` irrestritos, tradução em tempo real de streaming de pensamento e compatibilidade universal com qualquer `llama-server` e interfaces web.
- **Zero Chamadas Externas:** Bloqueio completo de telemetria (Mixpanel e OTLP), auto-update checks, downloads de marketplace no GitHub e pings na nuvem da xAI.
- **Auto-Detecção de Portas e Modelos:** O comando `opengrok` detecta automaticamente servidores locais rodando nas portas `5173`, `8080`, `8081`, `11434`, `5000`, `8000` ou `9090`.
- **Instalador Oficial Integrado:** Script `install.sh` que disponibiliza o comando global `opengrok` (e `open-grok`) no terminal do usuário.

---

## 📦 Estrutura e Componentes Auto-Contidos

Todos os componentes necessários estão devidamente organizados na estrutura do projeto:

| Componente | Localização | Função |
| :--- | :--- | :--- |
| **Motor da CLI** | [`downloads/grok-1.0.24-linux-x86_64`](file:///home/userk21/open_grok_cli/downloads/grok-1.0.24-linux-x86_64) | Binário oficial do Grok em Rust, estaticamente linkado, com patch cirúrgico de tela inicial. |
| **Backup de Fábrica** | [`downloads/grok-1.0.24-linux-x86_64.orig`](file:///home/userk21/open_grok_cli/downloads/grok-1.0.24-linux-x86_64.orig) | Cópia de segurança intocada do binário de fábrica original. |
| **Launcher Canônico** | [`bin/opengrok`](file:///home/userk21/open_grok_cli/bin/opengrok) | Launcher universal com auto-resolução de symlinks, descoberta de portas e injeção de ambiente. |
| **Servidor MCP Web** | [`bin/mcp_web.py`](file:///home/userk21/open_grok_cli/bin/mcp_web.py) | Ferramentas MCP de busca web, web fetch e download de arquivos integradas à CLI. |
| **Buscador Nativo** | [`vendor/rg-15.0.0-override`](file:///home/userk21/open_grok_cli/vendor/rg-15.0.0-override) | Executável estático do `ripgrep` (`rg`) exportado no `PATH` interno para buscas ultrarrápidas. |
| **Skills do Pacote** | [`bundled/skills/`](file:///home/userk21/open_grok_cli/bundled/skills/) & [`skills/`](file:///home/userk21/open_grok_cli/skills/) | 24 skills prontas para manipulação de código, documentos, auditoria e planejamento. |
| **Agentes e Papéis** | [`bundled/agents/`](file:///home/userk21/open_grok_cli/bundled/agents/) & [`bundled/roles/`](file:///home/userk21/open_grok_cli/bundled/roles/) | Definições completas de agentes e subagentes com roteamento de modelo. |
| **Personas e Fluxos**| [`bundled/personas/`](file:///home/userk21/open_grok_cli/bundled/personas/) & [`bundled/workflows/`](file:///home/userk21/open_grok_cli/bundled/workflows/) | Perfis de comportamento e fluxos orquestrados. |
| **Configuração Central**| [`config.toml`](file:///home/userk21/open_grok_cli/config.toml) | Configuração local desacoplada com rotas de modelos, subagentes e MCP ativos. |
| **Credenciais Locais**| [`auth.json`](file:///home/userk21/open_grok_cli/auth.json) | Autenticação estática offline pronta que dispensa login na nuvem. |
| **Servidor Bridge** | [`open_grok_server.py`](file:///home/userk21/open_grok_cli/open_grok_server.py) | Bridge HTTP/SSE em Python padrão (sem pip) com suporte irrestrito a CORS (`*`). |
| **Instalador** | [`install.sh`](file:///home/userk21/open_grok_cli/install.sh) | Script de instalação e desinstalação no sistema (`~/.local/bin`). |

---

## ⚡ Instalação do Comando `opengrok`

Para registrar o comando `opengrok` no seu console global:

```bash
cd /home/userk21/open_grok_cli
./install.sh
```

O instalador:
1. Cria o link simbólico executável `opengrok` (e o alias `open-grok`) em `~/.local/bin/`.
2. Garante a inclusão do caminho no `PATH` do `~/.bashrc` e `~/.zshrc`.
3. Instala o script de autocompletar do Bash.
4. Valida a execução em tempo real.

> **Para desinstalar futuramente:**
> ```bash
> /home/userk21/open_grok_cli/install.sh --uninstall
> ```

---

## 🛠️ Como Iniciar Qualquer `llama-server`

O OpenGrok conecta-se a qualquer binário do `llama-server` (Vulkan, CUDA, ROCm ou CPU pura).

### 1. Parâmetros Essenciais Recomendados
Para habilitar todas as funções de agente, raciocínio, ferramentas de arquivo, streaming e CORS:

- `--port <PORTA>`: Porta HTTP (ex.: `5173` ou `8080`).
- `--host 127.0.0.1`: Endereço local de escuta.
- `--cors-origins "*"`: Permite requisições cross-origin para WebUIs e ferramentas.
- `--agent`: Ativa o modo de agente no llama-server.
- `--tools all`: Ativa suporte completo a Function Calling / Tool Calling nativo.
- `--reasoning auto`: Ativa o processamento de raciocínio (emite `reasoning_content`).
- `--kv-unified` e `-fa on`: Unifica o cache KV e ativa Flash Attention para economia de VRAM.
- `-c <N>`: Tamanho de contexto (ex.: `8192`, `32768`, `131072`).
- `-ngl 99`: Descarrega as camadas para a GPU.

### 2. Exemplos Prontos:

#### Exemplo Vulkan (GPU Integrada / AMD / Intel):
```bash
/caminho/para/llama-server \
  -m "/caminho/para/seu-modelo.gguf" \
  -ngl 99 \
  -c 32768 \
  -t 4 -tb 4 \
  -fa on \
  --agent \
  --tools all \
  --reasoning auto \
  --cors-origins "*" \
  --port 5173 \
  --host 127.0.0.1
```

#### Exemplo CUDA (NVIDIA) ou CPU:
```bash
llama-server \
  -m "/caminho/para/seu-modelo.gguf" \
  -ngl 99 \
  -c 16384 \
  -t $(nproc) \
  --agent \
  --tools all \
  --reasoning auto \
  --cors-origins "*" \
  --port 8080 \
  --host 127.0.0.1
```

#### Exemplo Ollama:
```bash
ollama serve
# O opengrok detectará automaticamente a porta 11434
```

---

## 🚀 Como Usar o OpenGrok

Com o seu `llama-server` ativo:

### 1. Iniciar a Interface TUI Interativa
Basta digitar no terminal de qualquer pasta:
```bash
opengrok
```
A interface completa da TUI é iniciada imediatamente, exibindo o status de conexão local e a caixa de entrada de comandos.

### 2. Executar em Modo Headless (Linha de Comando Direta)
```bash
opengrok -p "Analise as funções deste arquivo e liste melhorias de performance"
```

### 3. Conectar a uma Porta ou URL Específica
```bash
# Porta arbitrária:
opengrok --llama-port 9090

# Host ou URL remota/Docker:
opengrok --llama-url http://192.168.1.100:8080
```

### 4. Troca Dinâmica de Modelos na TUI
- Pressione `Ctrl + M` durante a sessão para abrir o seletor modal de modelos.
- Ou utilize o comando de barra:
  ```text
  /model llama-8080
  ```

---

## ⌨️ Atalhos Principais da Interface

| Atalho | Ação |
| :--- | :--- |
| `Ctrl + W` | Iniciar uma nova Git Worktree isolada |
| `Ctrl + R` | Retomar sessão anterior do histórico |
| `Ctrl + M` | Abrir o menu seletor de modelos |
| `Ctrl + Q` | Sair da CLI |
| `/help` | Exibir comandos e ferramentas disponíveis |
| `/plan` | Alternar para o modo de planejamento antes da execução |
| `/compact` | Compactar o histórico da conversa para liberar contexto |
| `/clear` | Limpar a tela da conversa atual |

---

## 🌐 Servidor Bridge Universal Local (`open_grok_server.py`)

O launcher gerencia automaticamente o bridge local na porta `5174` para garantir CORS total e compatibilidade de chamadas. Se desejar gerenciá-lo manualmente:

```bash
# Iniciar em segundo plano apontando para porta 5173
python3 /home/userk21/open_grok_cli/open_grok_server.py --port 5174 --upstream http://127.0.0.1:5173 --daemon

# Checar status e saúde do bridge
python3 /home/userk21/open_grok_cli/open_grok_server.py --status

# Encerrar o processo
python3 /home/userk21/open_grok_cli/open_grok_server.py --stop
```

---

## 🔒 Segurança e Privacidade

- **Totalmente Offline / Local:** Nenhuma requisição ou telemetria sai da sua máquina (`127.0.0.1`).
- **Sem Telemetria ou Rastreamento:** Telemetria Mixpanel, OTLP e upload de logs para a nuvem desativados por padrão.
- **Execução Real:** Sem mocks, sem placeholders e sem dependência de serviços externos.
