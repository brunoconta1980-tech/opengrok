#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp_web.py — Servidor MCP Stdio nativo para Busca na Web, Leitura de Páginas e Download.
Funciona 100% com a biblioteca padrão do Python (sem necessidade de dependências externas).
Fornece ferramentas para navegação real e pesquisa na internet pelo Grok CLI e subagentes.
"""

from __future__ import annotations

import gzip
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

def strip_tags(html_text: str) -> str:
    cleaned = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<(br|p|div|h[1-6]|li|tr)[^>]*>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = html.unescape(cleaned)
    lines = [line.strip() for line in cleaned.splitlines()]
    return "\n".join(line for line in lines if line)

def search_duckduckgo(query: str, max_results: int = 6) -> str:
    """Busca no DuckDuckGo (HTML) e retorna títulos, URLs reais e snippets."""
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
            if resp.info().get("Content-Encoding") == "gzip" or data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            content = data.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"Erro ao acessar mecanismo de busca: {e}"

    results = []
    blocks = re.findall(r'<div class="result results_links[^"]*">(.*?)</div>\s*</div>', content, re.DOTALL)
    if not blocks:
        blocks = re.findall(r'<div class="links_main[^"]*">(.*?)</div>\s*</div>', content, re.DOTALL)

    for b in blocks[:max_results]:
        t_match = re.search(r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b, re.DOTALL)
        if not t_match:
            continue

        raw_url = t_match.group(1)
        if "uddg=" in raw_url:
            m = re.search(r"uddg=([^&]+)", raw_url)
            if m:
                raw_url = urllib.parse.unquote(m.group(1))

        raw_title = t_match.group(2)
        title = html.unescape(re.sub(r"<[^>]+>", "", raw_title)).strip()

        snip_match = re.search(r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>', b, re.DOTALL)
        snippet = ""
        if snip_match:
            snippet = html.unescape(re.sub(r"<[^>]+>", "", snip_match.group(1))).strip()

        results.append(f"• Título: {title}\n  URL: {raw_url}\n  Resumo: {snippet}\n")

    if not results:
        # Fallback genérico por regex de links
        for m in re.finditer(r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', content, re.DOTALL):
            raw_url = m.group(1)
            if "uddg=" in raw_url:
                u_m = re.search(r"uddg=([^&]+)", raw_url)
                if u_m:
                    raw_url = urllib.parse.unquote(u_m.group(1))
            title = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
            if title and not raw_url.startswith("/"):
                results.append(f"• Título: {title}\n  URL: {raw_url}\n")
            if len(results) >= max_results:
                break

    if not results:
        return f"Nenhum resultado retornado para a consulta: '{query}'."

    return "\n".join(results)

def fetch_web_page(url: str, max_chars: int = 25000) -> str:
    """Baixa o conteúdo de uma página web e retorna o texto formatado."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            if resp.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            content = raw.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"Erro ao acessar {url}: {e}"

    text = strip_tags(content)
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n[... Conteúdo truncado após {max_chars} caracteres ...]"
    return text if text else "(Página vazia ou sem texto legível retornado)"

def download_file(url: str, output_path: str) -> str:
    """Faz o download de um arquivo para o disco local."""
    out = os.path.expanduser(output_path)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp, open(out, "wb") as f:
            total = 0
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
        return f"Download concluído com sucesso: {out} ({total} bytes)."
    except Exception as e:
        return f"Erro no download de {url}: {e}"

TOOLS = [
    {
        "name": "web_search",
        "description": "Busca informações e notícias atualizadas na internet em tempo real via DuckDuckGo. Retorna títulos, URLs e resumos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Termos da busca na web."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Número máximo de resultados (padrão: 6).",
                    "default": 6
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_web_page",
        "description": "Lê e extrai o texto formatado de uma página da web ou documentação online.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "A URL completa da página a ser lida."
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Limite máximo de caracteres a retornar (padrão: 25000).",
                    "default": 25000
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "download_file",
        "description": "Faz download de um arquivo da internet diretamente para um caminho local.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL do arquivo a baixar."
                },
                "output_path": {
                    "type": "string",
                    "description": "Caminho de destino no sistema de arquivos local."
                }
            },
            "required": ["url", "output_path"]
        }
    }
]

def handle_rpc(msg: dict) -> dict | None:
    req_id = msg.get("id")
    method = msg.get("method")
    params = msg.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": False
                    }
                },
                "serverInfo": {
                    "name": "open-grok-web",
                    "version": "1.0.0"
                }
            }
        }

    if method == "notifications/initialized":
        return None

    if method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS
            }
        }

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})

        content = ""
        is_error = False

        if name == "web_search":
            query = args.get("query", "")
            limit = int(args.get("max_results", 6))
            content = search_duckduckgo(query, limit)
        elif name == "fetch_web_page":
            url = args.get("url", "")
            max_c = int(args.get("max_chars", 25000))
            content = fetch_web_page(url, max_c)
        elif name == "download_file":
            url = args.get("url", "")
            path = args.get("output_path", "")
            content = download_file(url, path)
        else:
            is_error = True
            content = f"Ferramenta desconhecida: {name}"

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": content
                    }
                ],
                "isError": is_error
            }
        }

    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Método não implementado: {method}"
            }
        }
    return None

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle_rpc(req)
            if res is not None:
                sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error ou falha interna: {e}"
                }
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
