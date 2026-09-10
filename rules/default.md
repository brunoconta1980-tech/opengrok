# Diretrizes Operacionais do OpenGrok CLI (Local Soberano)

## Ambiente e Conexão Universal
- Conectado diretamente ao llama-server local ou remoto através do bridge universal com CORS PLENO na porta 5174.
- Compatível com qualquer llama-server em qualquer porta (5173, 8080, 8081, 11434, etc.) em qualquer máquina da rede.
- Zero dependência de nuvem, cotas proprietárias ou telemetria.

## Capacidades Agênticas
- O sistema de subagentes está 100% ativo (`spawn_subagent`).
- Tipos de agentes disponíveis:
  * `general-purpose`: Execução geral de ponta a ponta com leitura, edição e comandos.
  * `explore`: Investigação profunda de código e leitura de arquitetura.
  * `plan`: Formulação de planos de implementação estruturados sem modificar arquivos.
  * Personas ativas: `researcher`, `reviewer`, `implementer`, `test-writer`, `security-auditor`, `design-doc-writer`, `design-doc-reviewer`.

## Acesso à Web e Conectividade
- Ferramenta `web_search`: Efetua buscas na internet em tempo real via DuckDuckGo com extração de títulos, URLs e resumos.
- Ferramenta `fetch_web_page`: Baixa e extrai conteúdo limpo de documentações e páginas online.
- Ferramenta `download_file`: Download direto de arquivos da web.

## Habilidades (Skills) e Fluxos de Trabalho
- 24 skills integradas disponíveis e indexadas pelo pacote original.
- Workflows disponíveis para pesquisa aprofundada (`deep-research.rhai`).

## Padrão de Execução
- NUNCA utilizar placeholders (ex.: `// TODO`, `...`, `pass`, dados parciais).
- Todas as soluções e modificações de código devem ser entregues 100% implementadas, íntegras e funcionais.
