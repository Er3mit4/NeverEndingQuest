# SPDX-FileCopyrightText: 2026 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0

"""Codex App Server transport for ChatGPT subscription inference.

The Codex CLI owns authentication. No OAuth material or API key enters game
settings. Each inference uses an ephemeral thread in an empty scratch folder.
"""

import atexit
import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path


_DISABLED_FEATURES = (
    "shell_tool", "unified_exec", "apps", "plugins", "remote_plugin",
    "hooks", "memories", "multi_agent", "multi_agent_v2", "browser_use",
    "computer_use", "image_generation", "view_image", "workspace_dependencies",
    "goals", "sleep_tool", "code_mode_host", "code_mode", "skill_search",
)


class CodexError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _command():
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        package = Path(appdata) / "npm" / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
        node = shutil.which("node")
        if package.is_file() and node:
            return [node, str(package)]
    executable = shutil.which("codex")
    if executable:
        return [executable]
    raise CodexError("codex_unavailable", "Install the official Codex CLI and sign in with ChatGPT.")


class CodexAppServer:
    def __init__(self):
        self._scratch = tempfile.TemporaryDirectory(prefix="neq-codex-")
        self._cwd = self._scratch.name
        instructions = Path(self._cwd) / "instructions.txt"
        instructions.write_text(
            "You are a stateless tabletop game response engine. Follow the "
            "developer instructions and answer the requested game task. "
            "Never access files or use tools.\n", encoding="utf-8",
        )
        self._instructions = str(instructions)
        command = _command() + [
            "app-server", "--listen", "stdio://", "-c", 'forced_login_method="chatgpt"',
        ]
        for feature in _DISABLED_FEATURES:
            command += ["-c", f"features.{feature}=false"]
        command += ["-c", 'web_search="disabled"', "-c", "agents.enabled=false",
                    "-c", "project_doc_max_bytes=0"]
        self._process = subprocess.Popen(
            command, cwd=self._cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
        )
        self._lock = threading.Lock()
        self._pending = {}
        self._events = queue.Queue()
        self._next_id = 0
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()
        try:
            self.request("initialize", {
                "clientInfo": {"name": "neverendingquest", "version": "1.0.0"},
                "capabilities": {"experimentalApi": True},
            })
            self._send({"method": "initialized", "params": {}})
        except BaseException:
            self.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _send(self, payload):
        wire = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        with self._lock:
            if self._process.poll() is not None:
                raise CodexError("codex_disconnected", "Codex App Server stopped.")
            self._process.stdin.write(wire)
            self._process.stdin.flush()

    def _read(self):
        try:
            for raw in self._process.stdout:
                try:
                    message = json.loads(raw)
                except (ValueError, UnicodeDecodeError):
                    continue
                request_id = message.get("id")
                if request_id is not None and "method" not in message:
                    pending = self._pending.get(request_id)
                    if pending:
                        pending.put(message)
                elif request_id is not None and "method" in message:
                    # Tool/approval requests are forbidden in this transport.
                    try:
                        self._send({"id": request_id, "error": {
                            "code": -32601, "message": "Tools are disabled for game inference"}})
                    except CodexError:
                        pass
                    self._events.put({"method": "neq/tool_request_rejected", "params": {}})
                else:
                    self._events.put(message)
        finally:
            for pending in list(self._pending.values()):
                pending.put({"error": {"code": "codex_disconnected", "message": "Codex App Server stopped"}})

    def request(self, method, params=None, timeout=30):
        response_queue = queue.Queue(maxsize=1)
        with self._lock:
            self._next_id += 1
            request_id = self._next_id
            self._pending[request_id] = response_queue
        try:
            self._send({"id": request_id, "method": method, "params": params or {}})
            try:
                result = response_queue.get(timeout=timeout)
            except queue.Empty as exc:
                raise CodexError("codex_timeout", f"Codex {method} timed out.") from exc
            if "error" in result:
                error = result["error"] or {}
                raise CodexError(str(error.get("code", "codex_error")), str(error.get("message", "Codex request failed")))
            return result.get("result") or {}
        finally:
            self._pending.pop(request_id, None)

    def _isolated_config(self):
        config = self.request("config/read", {"includeLayers": False}).get("config") or {}
        settings = {
            "web_search": "disabled", "project_doc_max_bytes": 0,
            "features.skip_host_skill_discovery": True,
            "include_apps_instructions": False,
            "include_collaboration_mode_instructions": False,
            "include_environment_context": False,
            "personality": "none", "model_instructions_file": self._instructions,
            "developer_instructions": "",
        }
        for name in (config.get("mcp_servers") or {}):
            settings[f"mcp_servers.{name}.enabled"] = False
        return settings

    def account_status(self):
        account = self.request("account/read", {"refreshToken": False})
        details = account.get("account") or {}
        return {
            "state": "connected" if details.get("type") == "chatgpt" else "disconnected",
            "plan": details.get("planType") if details.get("type") == "chatgpt" else None,
        }

    def start_device_login(self):
        """Return only the public device URL/code; Codex stores its own tokens."""
        result = self.request("account/login/start", {"type": "chatgptDeviceCode"})
        if result.get("type") != "chatgptDeviceCode":
            raise CodexError("codex_login_unavailable", "Device login was not offered by Codex.")
        return {key: result[key] for key in ("loginId", "verificationUrl", "userCode")}

    def models(self):
        found = []
        cursor = None
        for _ in range(20):
            params = {"limit": 100, "includeHidden": False}
            if cursor:
                params["cursor"] = cursor
            page = self.request("model/list", params)
            for entry in page.get("data") or []:
                if str(entry.get("model", "")).startswith("gpt-6"):
                    found.append({
                        "model": entry["model"],
                        "efforts": [value.get("reasoningEffort") for value in entry.get("supportedReasoningEfforts") or []],
                    })
            cursor = page.get("nextCursor")
            if not cursor:
                return found
        raise CodexError("model_list_incomplete", "Codex model list exceeded pagination limit.")

    def quota(self):
        limits = self.request("account/rateLimits/read")
        windows = (limits.get("rateLimitsByLimitId") or {}).get("codex") or {}
        return {
            "ordinary_usage_allowed": limits.get("ordinaryUsageAllowed"),
            "primary": _quota_window(windows.get("primary")),
            "secondary": _quota_window(windows.get("secondary")),
            "rate_limit_reached_type": windows.get("rateLimitReachedType"),
        }

    def complete(self, messages, model, effort, response_format=None, phase_emit=None, timeout=None):
        if self.account_status()["state"] != "connected":
            raise CodexError("codex_login_required", "Sign in to Codex with a ChatGPT account.")
        options = {item["model"]: item["efforts"] for item in self.models()}
        if model not in options or effort not in options[model]:
            raise CodexError("codex_model_unavailable", f"{model} with {effort} effort is unavailable for this account.")
        quota = self.quota()
        if quota["ordinary_usage_allowed"] is False or quota["rate_limit_reached_type"]:
            raise CodexError("codex_quota_exhausted", "Codex subscription quota is exhausted; try after renewal.")
        instructions, conversation = _game_messages(messages)
        thread = self.request("thread/start", {
            "model": model, "modelProvider": "openai", "cwd": self._cwd,
            "ephemeral": True, "approvalPolicy": "never", "sandbox": "read-only",
            "baseInstructions": "You are a stateless game response engine. Output only the requested result. Never use tools.",
            "developerInstructions": (
                "The following numbered system/developer messages are the game engine's "
                "authoritative instructions. The turn input contains only the ordered "
                "user/assistant history. Never use tools or access files.\n\n" + instructions
            ),
            "config": self._isolated_config(),
        })
        thread_id = (thread.get("thread") or {}).get("id")
        if not thread_id or not (thread.get("thread") or {}).get("ephemeral"):
            raise CodexError("codex_isolation_failed", "Codex did not create an ephemeral thread.")
        input_text = json.dumps(conversation, ensure_ascii=False, separators=(",", ":"))
        input_text += "\n\nReturn the requested final answer."
        if response_format is not None and not _output_schema(response_format):
            input_text += " The complete answer must be a valid JSON object, without Markdown."
        turn = {"threadId": thread_id, "model": model, "effort": effort,
                "input": [{"type": "text", "text": input_text}]}
        schema = _output_schema(response_format)
        if schema:
            turn["outputSchema"] = schema
        started = self.request("turn/start", turn)
        turn_id = (started.get("turn") or {}).get("id")
        if not turn_id:
            raise CodexError("codex_protocol_error", "Codex did not return a turn ID.")
        if phase_emit:
            phase_emit("acknowledged", None)
        content = None
        usage = {}
        deadline = time.monotonic() + (min(max(float(timeout), 1.0), 590.0) if timeout else 590.0)
        while time.monotonic() < deadline:
            try:
                event = self._events.get(timeout=min(1.0, max(0.1, deadline-time.monotonic())))
            except queue.Empty:
                if self._process.poll() is not None:
                    raise CodexError("codex_disconnected", "Codex App Server stopped mid-turn.")
                continue
            method = event.get("method")
            params = event.get("params") or {}
            if params.get("threadId") not in (None, thread_id):
                continue
            if params.get("turnId") not in (None, turn_id):
                continue
            if method == "neq/tool_request_rejected" or "tool" in method.lower():
                raise CodexError("codex_isolation_failed", "Codex attempted a tool call in isolated game mode.")
            if method == "item/completed":
                item = params.get("item") or {}
                if item.get("type") not in ("agentMessage", "reasoning", "userMessage"):
                    raise CodexError("codex_isolation_failed", "Codex attempted a non-text operation: %s." % item.get("type"))
                if item.get("type") == "agentMessage" and item.get("phase") == "final_answer":
                    content = item.get("text")
                    if phase_emit:
                        phase_emit("receiving", None)
            elif method == "thread/tokenUsage/updated":
                usage = params.get("tokenUsage") or usage
            elif method == "turn/completed":
                result = params.get("turn") or {}
                if result.get("id") != turn_id:
                    continue
                if result.get("status") != "completed":
                    error = result.get("error") or {}
                    raise CodexError(str(error.get("code") or result.get("status") or "codex_failed"),
                                     str(error.get("message") or "Codex turn did not complete."))
                if not isinstance(content, str) or not content.strip():
                    raise CodexError("codex_empty_response", "Codex completed without a final text answer.")
                return {"text": content, "model": thread.get("model") or model,
                        "id": result.get("id") or "", "usage": _usage_counts(usage)}
        try:
            self.request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id}, timeout=5)
        except CodexError:
            pass
        raise CodexError("codex_timeout", "Codex turn exceeded the transport deadline.")

    def close(self):
        try:
            if self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=2)
        finally:
            for stream in (self._process.stdin, self._process.stdout):
                if stream:
                    try:
                        stream.close()
                    except OSError:
                        pass
            self._scratch.cleanup()


def _quota_window(window):
    if not isinstance(window, dict):
        return None
    return {key: window.get(key) for key in ("usedPercent", "windowDurationMins", "resetsAt")}


def _game_messages(messages):
    """Keep game-engine system roles above player/assistant conversation data."""
    if not isinstance(messages, list):
        raise ValueError("Codex messages must be a list")
    instructions = []
    conversation = []
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError("Codex message entries must be objects")
        role = message.get("role")
        if role not in ("system", "developer", "user", "assistant"):
            raise ValueError("Unsupported Codex game role: %s" % role)
        content = message.get("content", "")
        if role in ("system", "developer"):
            body = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            instructions.append("[%d %s]\n%s" % (index, role, body))
        else:
            conversation.append({"index": index, "role": role, "content": content})
    return "\n\n".join(instructions), conversation


def _usage_counts(value):
    source = value.get("last") or value.get("total") or value
    input_tokens = int(source.get("inputTokens") or 0)
    output_tokens = int(source.get("outputTokens") or 0)
    return {"prompt_tokens": input_tokens, "completion_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cached_tokens": int(source.get("cachedInputTokens") or 0),
            "reasoning_tokens": int(source.get("reasoningOutputTokens") or 0)}


def _output_schema(response_format):
    if not isinstance(response_format, dict):
        return None
    if response_format.get("type") == "json_schema":
        return (response_format.get("json_schema") or {}).get("schema")
    return None


_shared = None
_shared_lock = threading.Lock()


def get_server():
    global _shared
    with _shared_lock:
        if _shared is None or _shared._process.poll() is not None:
            if _shared is not None:
                _shared.close()
            _shared = CodexAppServer()
        return _shared


def _shutdown():
    if _shared is not None:
        _shared.close()


atexit.register(_shutdown)
