#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
open_grok_server.py — Servidor e bridge local OpenAI/Responses compatível com CORS PLENO.
Conecta-se a qualquer llama-server local ou remoto (em qualquer porta: 5173, 8080, 8081, 11434, etc.).

Totalmente soberano e funcional:
  - Zero telemetria e sem dependência de nuvem
  - CORS PLENO (*) para navegadores, extensões, WebUIs e agentes
  - Compatibilidade com a API Responses do Grok CLI (injeção de output_tokens_details)
  - Suporte a streaming SSE e requisições síncronas
  - Busca na Web integrada via DuckDuckGo
"""

from __future__ import annotations

import argparse
import gzip
import html
import http.client
import http.server
import json
import mimetypes
import os
import re
import signal
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

VERSION = "2.2.0-universal"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5174
USUAL_UPSTREAM_PORTS = (5173, 8080, 8081, 11434, 5000, 8000, 9090)

BASE_DIR = Path(__file__).resolve().parent
PID_FILE = BASE_DIR / "open_grok_server.pid"
LOG_FILE = BASE_DIR / "open_grok_server.log"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

def _find_webui_dir() -> Path | None:
    candidates = [
        Path.home() / "llama_server_VULLKAN_MIXED_HERMES" / "tools" / "ui" / "dist",
        Path.home() / "llama_server_VULLKAN_MIXED_HERMES" / "build" / "bin" / "public",
        Path.home() / "bkr_gguf" / "webui",
        BASE_DIR / "webui",
    ]
    for c in candidates:
        if (c / "index.html").is_file():
            return c.resolve()
    return None

WEBUI_DIR = _find_webui_dir()

DROP_KEYS = {
    "cache_prompt",
    "id_slot",
    "slot_id",
    "id_task",
    "samplers",
    "min_p",
    "typical_p",
    "tfs_z",
    "mirostat",
    "mirostat_tau",
    "mirostat_eta",
    "grammar",
    "json_schema",
    "penalty_last_n",
    "penalty_repeat",
    "penalty_freq",
    "penalty_present",
    "repeat_last_n",
    "repeat_penalty",
    "n_predict",
    "n_keep",
    "n_probs",
    "lora",
    "image_data",
    "t_max_predict_ms",
}

class ServerConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    upstream: str = ""
    daemon: bool = False

CFG = ServerConfig()

def _log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[OPEN_GROK {ts}] {msg}\n"
    sys.stderr.write(line)
    sys.stderr.flush()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass

def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0

def detect_upstream(preferred_url: str = "") -> str:
    """Detecta automaticamente onde o llama-server está rodando."""
    if preferred_url:
        return preferred_url.rstrip("/")

    env_url = (
        os.environ.get("LLAMA_URL")
        or os.environ.get("LLAMA_SERVER_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("GROK_MODELS_BASE_URL")
    )
    if env_url:
        clean = env_url.rstrip("/").removesuffix("/v1")
        if clean and not clean.endswith(f":{CFG.port}"):
            return clean

    # Escanear portas usuais
    for port in USUAL_UPSTREAM_PORTS:
        if port == CFG.port:
            continue
        test_url = f"http://127.0.0.1:{port}"
        try:
            req = urllib.request.Request(f"{test_url}/health", headers={"User-Agent": "open-grok"})
            with urllib.request.urlopen(req, timeout=0.4) as resp:
                if resp.status == 200:
                    _log(f"llama-server detectado automaticamente via /health em {test_url}")
                    return test_url
        except Exception:
            pass
        try:
            req = urllib.request.Request(f"{test_url}/v1/models", headers={"User-Agent": "open-grok"})
            with urllib.request.urlopen(req, timeout=0.4) as resp:
                if resp.status == 200:
                    _log(f"llama-server detectado automaticamente via /v1/models em {test_url}")
                    return test_url
        except Exception:
            pass

    return "http://127.0.0.1:5173"

def search_duckduckgo(query: str, max_results: int = 5) -> list[dict[str, str]]:
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            if resp.info().get("Content-Encoding") == "gzip" or data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            content = data.decode("utf-8", errors="ignore")
    except Exception as e:
        _log(f"Erro na busca DuckDuckGo: {e}")
        return []

    results = []
    blocks = re.findall(r'<div class="result results_links[^"]*">(.*?)</div>\s*</div>', content, re.DOTALL)
    for b in blocks[:max_results]:
        t_match = re.search(r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b, re.DOTALL)
        if not t_match:
            continue
        raw_url = t_match.group(1)
        if "uddg=" in raw_url:
            m = re.search(r"uddg=([^&]+)", raw_url)
            if m:
                raw_url = urllib.parse.unquote(m.group(1))
        title = html.unescape(re.sub(r"<[^>]+>", "", t_match.group(2))).strip()
        snip_match = re.search(r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>', b, re.DOTALL)
        snippet = ""
        if snip_match:
            snippet = html.unescape(re.sub(r"<[^>]+>", "", snip_match.group(1))).strip()
        results.append({"title": title, "url": raw_url, "snippet": snippet})
    return results

class OpenGrokHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = f"OpenGrokServer/{VERSION}"

    def log_message(self, fmt: str, *args: Any) -> None:
        _log(f"{self.address_string()} {fmt % args}")

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Expose-Headers", "*")
        self.send_header("Access-Control-Max-Age", "86400")

    def _send(self, code: int, body: bytes, ctype: str, extra: dict[str, str] | None = None) -> None:
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self._cors()
            if extra:
                for k, v in extra.items():
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def _send_json(self, code: int, obj: Any) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(code, raw, "application/json; charset=utf-8")

    def _drain_body(self) -> bytes:
        try:
            n = int(self.headers.get("Content-Length") or 0)
            return self.rfile.read(n) if n > 0 else b""
        except Exception:
            return b""

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path in ("/health", "/healthz"):
            self._handle_health()
            return
        if path == "/props":
            self._handle_proxy_get("/props")
            return
        if path == "/slots":
            self._handle_proxy_get("/slots")
            return
        if path in ("/v1/models", "/models"):
            self._handle_models()
            return
        if path.startswith("/v1/models/"):
            mid = path.split("/v1/models/", 1)[1]
            self._send_json(200, {
                "id": mid or "local-llama",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local",
            })
            return
        if path == "/cors-proxy":
            self._handle_cors_proxy()
            return
        if path == "/":
            self._handle_root()
            return

        if self._serve_static(path):
            return

        self._send_json(404, {"error": {"message": f"Endpoint GET não encontrado: {path}", "type": "not_found"}})

    def do_POST(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path in ("/v1/chat/completions", "/chat/completions"):
            self._handle_chat_completions()
            return
        if path in ("/v1/responses", "/responses"):
            self._handle_responses()
            return
        if path in ("/v1/completions", "/completion"):
            self._handle_completions()
            return
        if path in ("/v1/embeddings", "/embedding"):
            self._handle_embeddings()
            return
        if path == "/cors-proxy":
            self._handle_cors_proxy()
            return

        self._drain_body()
        self._send_json(404, {"error": {"message": f"Endpoint POST não encontrado: {path}", "type": "not_found"}})

    def _handle_root(self) -> None:
        if self._serve_static("index.html"):
            return
        self._handle_health()

    def _serve_static(self, rel_path: str) -> bool:
        if not WEBUI_DIR:
            return False
        rel = rel_path.lstrip("/")
        target = (WEBUI_DIR / rel).resolve() if rel else WEBUI_DIR / "index.html"
        if not target.is_relative_to(WEBUI_DIR) or not target.is_file():
            return False
        ctype, _ = mimetypes.guess_type(str(target))
        ctype = ctype or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        try:
            data = target.read_bytes()
            self._send(200, data, ctype)
            return True
        except Exception:
            return False

    def _handle_health(self) -> None:
        upstream_ok = False
        try:
            req = urllib.request.Request(f"{CFG.upstream}/health", headers={"User-Agent": "open-grok"})
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                upstream_ok = resp.status == 200
        except Exception:
            try:
                req = urllib.request.Request(f"{CFG.upstream}/v1/models", headers={"User-Agent": "open-grok"})
                with urllib.request.urlopen(req, timeout=0.8) as resp:
                    upstream_ok = resp.status == 200
            except Exception:
                upstream_ok = False

        self._send_json(200, {
            "status": "ok",
            "server": "open_grok_server",
            "version": VERSION,
            "upstream": CFG.upstream,
            "upstream_healthy": upstream_ok,
            "webui_available": bool(WEBUI_DIR),
        })

    def _handle_proxy_get(self, upstream_path: str) -> None:
        target_url = f"{CFG.upstream}{upstream_path}"
        try:
            req = urllib.request.Request(target_url, headers={"User-Agent": "open-grok"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = resp.read()
                self._send(resp.status, data, resp.getheader("Content-Type") or "application/json")
        except Exception as e:
            self._send_json(502, {"error": {"message": f"Erro de comunicação com upstream: {e}"}})

    def _handle_models(self) -> None:
        models_data = []
        target_url = f"{CFG.upstream}/v1/models"
        try:
            req = urllib.request.Request(target_url, headers={"User-Agent": "open-grok"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8", "replace"))
                if isinstance(data, dict):
                    models_data = data.get("data", [])
                elif isinstance(data, list):
                    models_data = data
        except Exception:
            pass

        # Garantir aliases essenciais para que nenhum pedido falhe
        existing_ids = {m.get("id") for m in models_data if isinstance(m, dict)}
        for alias in ("local-llama", "grok-build", "grok-2", "grok-4.5", "default", "llama-5173", "llama-8080"):
            if alias not in existing_ids:
                models_data.append({
                    "id": alias,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "local-llama-server",
                })

        self._send_json(200, {
            "object": "list",
            "data": models_data,
        })

    def _handle_chat_completions(self) -> None:
        raw_body = self._drain_body()
        if not raw_body:
            self._send_json(400, {"error": {"message": "Corpo da requisição vazio"}})
            return

        is_stream = False
        try:
            payload = json.loads(raw_body.decode("utf-8", "replace"))
            is_stream = bool(payload.get("stream", False))
            filtered = {k: v for k, v in payload.items() if k not in DROP_KEYS}
            raw_body = json.dumps(filtered, ensure_ascii=False).encode("utf-8")
        except Exception:
            pass

        u = urllib.parse.urlsplit(CFG.upstream)
        port = u.port or (443 if u.scheme == "https" else 80)
        conn_cls = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection

        try:
            conn = conn_cls(u.hostname or "127.0.0.1", port, timeout=600)
            headers = {
                "Content-Type": "application/json",
                "Content-Length": str(len(raw_body)),
                "User-Agent": f"OpenGrokServer/{VERSION}",
            }
            auth = self.headers.get("Authorization")
            if auth:
                headers["Authorization"] = auth

            target_path = (u.path.rstrip("/") + "/v1/chat/completions") or "/v1/chat/completions"
            conn.request("POST", target_path, body=raw_body, headers=headers)
            resp = conn.getresponse()

            if is_stream:
                self.send_response(resp.status)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self._cors()
                self.end_headers()

                while True:
                    chunk = resp.read(1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
                conn.close()
            else:
                body = resp.read()
                try:
                    data = json.loads(body.decode("utf-8", "replace"))
                    if isinstance(data, dict):
                        usage = data.get("usage")
                        if isinstance(usage, dict):
                            usage.setdefault("prompt_tokens_details", {"cached_tokens": 0})
                            usage.setdefault("completion_tokens_details", {"reasoning_tokens": 0})
                        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                except Exception:
                    pass
                self._send(resp.status, body, resp.getheader("Content-Type") or "application/json")
                conn.close()
        except Exception as e:
            self._send_json(502, {"error": {"message": f"Erro de comunicação com llama-server ({CFG.upstream}): {e}"}})

    def _handle_responses(self) -> None:
        raw_body = self._drain_body()
        if not raw_body:
            self._send_json(400, {"error": {"message": "Corpo da requisição vazio"}})
            return

        payload = {}
        try:
            payload = json.loads(raw_body.decode("utf-8", "replace"))
        except Exception:
            pass

        # 1. Tentar encaminhar diretamente ao llama-server /v1/responses
        u = urllib.parse.urlsplit(CFG.upstream)
        target_path = (u.path.rstrip("/") + "/v1/responses") or "/v1/responses"
        target_url = f"{CFG.upstream}/v1/responses"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"OpenGrokServer/{VERSION}",
        }
        auth = self.headers.get("Authorization")
        if auth:
            headers["Authorization"] = auth

        try:
            req = urllib.request.Request(target_url, data=raw_body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=300) as resp:
                resp_data = resp.read()
                try:
                    data = json.loads(resp_data.decode("utf-8", "replace"))
                    if isinstance(data, dict):
                        usage = data.get("usage")
                        if isinstance(usage, dict):
                            # INJEÇÃO CRÍTICA: Garante que o serde do Grok CLI nunca falhe por falta de campos
                            usage.setdefault("output_tokens_details", {"reasoning_tokens": 0})
                            usage.setdefault("input_tokens_details", {"cached_tokens": 0})
                        resp_data = json.dumps(data, ensure_ascii=False).encode("utf-8")
                except Exception:
                    pass
                self._send(resp.status, resp_data, "application/json; charset=utf-8")
                return
        except urllib.error.HTTPError as e:
            if e.code != 404:
                err_data = e.read()
                self._send(e.code, err_data, "application/json; charset=utf-8")
                return
            # Se for 404, cai no fallback universal abaixo
        except Exception as e:
            _log(f"Upstream /v1/responses falhou ou não implementado: {e}")

        # 2. Fallback Universal: Se o llama-server não implementa /v1/responses
        self._fallback_responses(payload, raw_body)

    def _fallback_responses(self, payload: dict, raw_body: bytes) -> None:
        model = payload.get("model", "local-llama")
        input_data = payload.get("input", "")
        
        # Verificar se é busca web direta solicitada
        query = ""
        if isinstance(input_data, str) and ("search" in input_data.lower() or "noticia" in input_data.lower()):
            query = input_data
        elif isinstance(input_data, list):
            for item in input_data:
                if isinstance(item, dict) and "search" in str(item).lower():
                    query = str(item.get("content", ""))
                    break

        web_results_text = ""
        if query:
            ddg_hits = search_duckduckgo(query, max_results=4)
            if ddg_hits:
                web_results_text = "\n\nResultados da Busca na Web em Tempo Real:\n"
                for h in ddg_hits:
                    web_results_text += f"- [{h['title']}]({h['url']}): {h['snippet']}\n"

        messages = []
        if isinstance(input_data, str):
            messages = [{"role": "user", "content": input_data + web_results_text}]
        elif isinstance(input_data, list):
            for item in input_data:
                if isinstance(item, dict):
                    role = item.get("role", "user")
                    content = item.get("content", "")
                    if isinstance(content, list):
                        text_parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("text")]
                        content = " ".join(text_parts) if text_parts else str(content)
                    messages.append({"role": role, "content": str(content)})
                elif isinstance(item, str):
                    messages.append({"role": "user", "content": item})
            if web_results_text and messages:
                messages[-1]["content"] += web_results_text

        if not messages:
            messages = [{"role": "user", "content": str(input_data) + web_results_text}]

        chat_payload = {
            "model": model,
            "messages": messages,
            "temperature": payload.get("temperature", 0.7),
            "top_p": payload.get("top_p", 0.95),
            "stream": False,
        }
        target_url = f"{CFG.upstream}/v1/chat/completions"
        try:
            req = urllib.request.Request(
                target_url,
                data=json.dumps(chat_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                chat_res = json.loads(resp.read().decode("utf-8", "replace"))
                msg = chat_res.get("choices", [{}])[0].get("message", {})
                text_content = msg.get("content", "")
                chat_usage = chat_res.get("usage", {})
                p_tokens = chat_usage.get("prompt_tokens", 0)
                c_tokens = chat_usage.get("completion_tokens", 0)
                t_tokens = chat_usage.get("total_tokens", p_tokens + c_tokens)

                resp_obj = {
                    "id": f"resp_{uuid.uuid4().hex}",
                    "object": "response",
                    "created_at": int(time.time()),
                    "model": model,
                    "status": "completed",
                    "output": [
                        {
                            "id": f"msg_{uuid.uuid4().hex}",
                            "type": "message",
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": text_content,
                                    "annotations": [],
                                    "logprobs": []
                                }
                            ]
                        }
                    ],
                    "usage": {
                        "input_tokens": p_tokens,
                        "input_tokens_details": {"cached_tokens": 0},
                        "output_tokens": c_tokens,
                        "output_tokens_details": {"reasoning_tokens": 0},
                        "total_tokens": t_tokens
                    }
                }
                self._send_json(200, resp_obj)
        except Exception as e:
            self._send_json(502, {"error": {"message": f"Erro fallback responses: {e}"}})

    def _handle_completions(self) -> None:
        raw_body = self._drain_body()
        target_url = f"{CFG.upstream}/v1/completions"
        try:
            req = urllib.request.Request(
                target_url,
                data=raw_body,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = resp.read()
                self._send(resp.status, body, resp.getheader("Content-Type") or "application/json")
        except Exception as e:
            self._send_json(502, {"error": {"message": f"Erro completions: {e}"}})

    def _handle_embeddings(self) -> None:
        raw_body = self._drain_body()
        target_url = f"{CFG.upstream}/v1/embeddings"
        try:
            req = urllib.request.Request(
                target_url,
                data=raw_body,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
                self._send(resp.status, body, resp.getheader("Content-Type") or "application/json")
        except Exception as e:
            self._send_json(502, {"error": {"message": f"Erro embeddings: {e}"}})

    def _handle_cors_proxy(self) -> None:
        query = urllib.parse.urlsplit(self.path).query
        target_url = urllib.parse.parse_qs(query).get("url", [None])[0]
        raw_body = self._drain_body()
        if not target_url:
            self._send_json(400, {"error": {"message": "Parâmetro url ausente no cors-proxy"}})
            return
        
        target_parsed = urllib.parse.urlsplit(target_url)
        if target_parsed.hostname not in ("127.0.0.1", "localhost", "0.0.0.0", "::1"):
            self._send_json(403, {"error": {"message": "CORS proxy restrito exclusivamente a hosts locais"}})
            return

        try:
            req = urllib.request.Request(
                target_url,
                data=raw_body if raw_body else None,
                headers={"Content-Type": self.headers.get("Content-Type") or "application/json"},
                method=self.command,
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                self._send(resp.status, data, resp.getheader("Content-Type") or "application/json")
        except Exception as e:
            self._send_json(502, {"error": {"message": f"Erro cors-proxy local: {e}"}})

def run_server():
    CFG.upstream = detect_upstream(CFG.upstream)
    _log(f"Iniciando OpenGrok Server em http://{CFG.host}:{CFG.port}")
    _log(f"Upstream llama-server configurado para: {CFG.upstream}")
    _log("CORS: Habilitado (*) | Modo: Universal Local/Rede")

    server = http.server.ThreadingHTTPServer((CFG.host, CFG.port), OpenGrokHandler)
    server.daemon_threads = True

    PID_FILE.write_text(str(os.getpid()))

    def handle_sig(sig, frame):
        _log("Encerrando servidor...")
        if PID_FILE.is_file():
            try:
                PID_FILE.unlink()
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    try:
        server.serve_forever()
    finally:
        if PID_FILE.is_file():
            try:
                PID_FILE.unlink()
            except Exception:
                pass

def stop_server():
    if not PID_FILE.is_file():
        print("Nenhum OpenGrok Server em execução encontrado.")
        return
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        print(f"Sinal de término enviado ao processo {pid}.")
        time.sleep(0.5)
        if PID_FILE.is_file():
            PID_FILE.unlink()
    except Exception as e:
        print(f"Erro ao parar o servidor: {e}")

def server_status():
    if not PID_FILE.is_file():
        print("OpenGrok Server: PARADO")
        return
    pid = int(PID_FILE.read_text().strip())
    try:
        os.kill(pid, 0)
        print(f"OpenGrok Server: EM EXECUÇÃO (PID: {pid})")
    except OSError:
        print("OpenGrok Server: PARADO (PID órfão limpo)")
        PID_FILE.unlink()

def main():
    parser = argparse.ArgumentParser(description="OpenGrok Local Server & Bridge com CORS PLENO")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Endereço de bind (padrão: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta de escuta (padrão: 5174)")
    parser.add_argument("--upstream", default="", help="URL do llama-server (ex: http://127.0.0.1:5173)")
    parser.add_argument("--daemon", action="store_true", help="Executar em segundo plano")
    parser.add_argument("--stop", action="store_true", help="Parar servidor em execução")
    parser.add_argument("--status", action="store_true", help="Verificar status do servidor")
    parser.add_argument("--restart", action="store_true", help="Reiniciar servidor")

    args = parser.parse_args()

    if args.stop:
        stop_server()
        return
    if args.status:
        server_status()
        return
    if args.restart:
        stop_server()
        time.sleep(1)

    CFG.host = args.host
    CFG.port = args.port
    CFG.upstream = args.upstream

    if args.daemon:
        import subprocess
        cmd = [sys.executable, str(Path(__file__).resolve()), "--host", CFG.host, "--port", str(CFG.port)]
        if CFG.upstream:
            cmd.extend(["--upstream", CFG.upstream])
        with open(LOG_FILE, "a") as log:
            proc = subprocess.Popen(cmd, stdout=log, stderr=log, start_new_session=True)
        print(f"OpenGrok Server iniciado em segundo plano (PID: {proc.pid}) em http://{CFG.host}:{CFG.port}")
        return

    run_server()

if __name__ == "__main__":
    main()
