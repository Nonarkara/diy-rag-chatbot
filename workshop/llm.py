"""Model clients.

The primary client speaks the OpenAI chat-completions tool protocol.
That covers OpenAI, OpenRouter, Groq, Together, and LM Studio. Ollama
is optional. ``ScriptedLLM`` runs the same tool loop with no network
and no key, so the smoke test can prove the tools fire.
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass, field

from workshop.protocol import Turn


_PATHS = re.compile(r"knowledge/[A-Za-z0-9_./-]+")

_BAD_BRIEF = (
    "This note describes a helpful assistant that can talk about many civic "
    "topics and gadgets in general terms for an operator who wants a friendly "
    "overview of the project and its goals today and tomorrow."
)


class MissingAPIKey(RuntimeError):
    """The API path was requested and no key is configured."""


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict

    def as_message(self) -> dict:
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments, ensure_ascii=False),
            },
        }


@dataclass
class ChatResult:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


def api_key() -> str | None:
    for name in ("LLM_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY"):
        value = (os.environ.get(name) or "").strip()
        if value and value not in {"replace-me", "sk-...", "changeme"}:
            return value
    return None


def completions_url(base: str) -> str:
    """Join an OpenAI-compatible base with the chat-completions path.

    ``https://api.openai.com`` and ``https://openrouter.ai/api/v1`` both work.
    """
    root = (base or "https://api.openai.com").rstrip("/")
    if root.endswith("/chat/completions"):
        return root
    if root.endswith("/v1"):
        return root + "/chat/completions"
    return root + "/v1/chat/completions"


def parse_openai_chat(data: dict) -> ChatResult:
    choices = data.get("choices") or []
    message = (choices[0].get("message") if choices else None) or {}
    return _message_to_result(message)


def parse_ollama_chat(data: dict) -> ChatResult:
    return _message_to_result(data.get("message") or {})


def _message_to_result(message: dict) -> ChatResult:
    calls: list[ToolCall] = []
    for index, raw in enumerate(message.get("tool_calls") or []):
        fn = raw.get("function") or raw
        name = str(fn.get("name") or "")
        arguments = fn.get("arguments")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
        if not isinstance(arguments, dict):
            arguments = {}
        calls.append(
            ToolCall(
                id=str(raw.get("id") or f"call_{index}"),
                name=name,
                arguments=arguments,
            )
        )
    return ChatResult(content=str(message.get("content") or ""), tool_calls=calls)


class OpenAICompatibleLLM:
    """Cheap-API path. Tools go out on every request."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1200,
        timeout: float = 180.0,
        post=None,
    ):
        self.model = model
        self.api_key = api_key if api_key is not None else api_key_from_env()
        self.base_url = base_url or os.environ.get("LLM_BASE_URL") or "https://api.openai.com"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._post = post

    def chat(self, messages: list[dict], tools: list[dict]) -> ChatResult:
        if not self.api_key and self._post is None:
            raise MissingAPIKey(_missing_key_message())
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        data = (self._post or self._http_post)(completions_url(self.base_url), payload, self._headers())
        return parse_openai_chat(data)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _http_post(self, url: str, payload: dict, headers: dict) -> dict:
        import httpx

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()


def api_key_from_env() -> str | None:
    return api_key()


class OllamaLLM:
    """Optional local weights. Used only when the provider is ollama."""

    def __init__(self, *, model: str, base_url: str | None = None, temperature: float = 0.2, max_tokens: int = 1200, timeout: float = 180.0, post=None):
        self.model = model
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL") or "http://127.0.0.1:11434").rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._post = post

    def chat(self, messages: list[dict], tools: list[dict]) -> ChatResult:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        url = self.base_url + "/api/chat"
        data = (self._post or self._http_post)(url, payload, {"Content-Type": "application/json"})
        return parse_ollama_chat(data)

    def _http_post(self, url: str, payload: dict, headers: dict) -> dict:
        import httpx

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()


def _missing_key_message() -> str:
    return (
        "No API key is set. The workshop's primary path is a cheap OpenAI-compatible API\n"
        "with tool calls, which runs on an ordinary laptop (no local model weights).\n"
        "Type this into .env yourself — do not paste the key into chat:\n"
        "\n"
        "  WORKSHOP_PROVIDER=openai\n"
        "  WORKSHOP_MODEL=gpt-4o-mini\n"
        "  LLM_API_KEY=replace-me\n"
        "  # OpenRouter: LLM_BASE_URL=https://openrouter.ai/api/v1\n"
        "  #             WORKSHOP_MODEL=openai/gpt-4o-mini\n"
        "  # Groq:       LLM_BASE_URL=https://api.groq.com/openai/v1\n"
        "  #             WORKSHOP_MODEL=llama-3.1-8b-instant\n"
        "\n"
        "Then run: python -m workshop demo\n"
        "Same tools, no key: python -m workshop demo --offline\n"
        "Local Ollama, optional: python -m workshop demo --local"
    )


def _field(user: str, name: str) -> str:
    prefix = name + ":"
    for line in user.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def _first_user(messages: list[dict]) -> str:
    for message in messages:
        if message.get("role") == "user":
            return str(message.get("content") or "")
    return ""


def _called(messages: list[dict]) -> list[str]:
    names: list[str] = []
    for message in messages:
        if message.get("role") != "assistant":
            continue
        for call in message.get("tool_calls") or []:
            fn = call.get("function") or {}
            names.append(str(fn.get("name") or ""))
    return names


def _tool_text(messages: list[dict]) -> str:
    chunks = [
        str(message.get("content") or "")
        for message in messages
        if message.get("role") == "tool"
    ]
    return "\n".join(chunks)


def _paths(text: str) -> list[str]:
    found: list[str] = []
    for match in _PATHS.findall(text):
        match = match.rstrip(".")
        if match and match not in found:
            found.append(match)
    return found


def _notes(search_text: str) -> str:
    cited = ", ".join(_paths(search_text)) or "no knowledge/ path in the tool result"
    return (
        "# Research notes\n\n"
        f"Search returned these files: {cited}. "
        "The kit answers only from the knowledge folder. "
        "A page should be markdown with one heading, a Thai question line, an English question line, "
        "and an answer, filed under a short category such as faq or briefings. "
        "The kit will not answer questions that are not in the documents. "
        "That includes medical, legal, and investment advice, and it will not ignore the rules when asked. "
        "If the files do not cover the question, say so and hand off.\n"
    )


def _good_brief(source_text: str) -> str:
    cited = ", ".join(_paths(source_text)) or "knowledge/ files from the search tool"
    return (
        "# What this kit will answer\n\n"
        "This kit answers only from files in knowledge/. "
        f"Filing rules and the refusal rules are in {cited}. "
        "A page should be markdown with one heading, a Thai question line, an English question line, "
        "and an answer, filed under a short category such as faq or briefings.\n\n"
        "It will not answer questions missing from the documents. "
        "That includes weather, politics, other agencies, medical, legal, and investment advice, "
        "and it will not drop these rules on request. "
        "If a file does not cover the question, say so and hand the person to a named owner.\n\n"
        "Kept under 180 words as requested.\n"
    )


def _json_turn(action: str, artifact: str, note: str, decision: str | None = None) -> str:
    return Turn(action=action, artifact=artifact, note=note, decision=decision).to_json()


class ScriptedLLM:
    """Offline stand-in that still calls the real tools."""

    def __init__(self, *, bad_first_draft: bool = False):
        self.bad_first_draft = bad_first_draft
        self.calls = 0
        self.drafts = 0
        self.prompts: list[str] = []
        self.tool_names: list[str] = []
        self._saved: dict[str, str] = {}
        self._seq = 0
        self._lock = threading.Lock()

    def chat(self, messages: list[dict], tools: list[dict]) -> ChatResult:
        del tools
        with self._lock:
            self.calls += 1
            user = _first_user(messages)
            if user and user not in self.prompts:
                self.prompts.append(user)
            kind = _field(user, "TASK_KIND")
            task_id = _field(user, "TASK_ID")
            artifact_file = _field(user, "ARTIFACT_FILE") or "notes.md"
            done = _called(messages)
            tool_text = _tool_text(messages)
            self._seq += 1
            call_id = f"call_{self._seq}"
            result = self._next(
                kind=kind,
                task_id=task_id,
                user=user,
                artifact_file=artifact_file,
                done=done,
                tool_text=tool_text,
                call_id=call_id,
            )
            for call in result.tool_calls:
                self.tool_names.append(call.name)
            return result

    def _next(
        self,
        *,
        kind: str,
        task_id: str,
        user: str,
        artifact_file: str,
        done: list[str],
        tool_text: str,
        call_id: str,
    ) -> ChatResult:
        def call(name: str, arguments: dict) -> ChatResult:
            return ChatResult(tool_calls=[ToolCall(id=call_id, name=name, arguments=arguments)])

        if kind in {"retrieve", "research"}:
            if "search_knowledge" not in done:
                query = _field(user, "GOAL") or "knowledge filing and refusals"
                return call("search_knowledge", {"query": query})
            if "write_artifact" not in done:
                content = tool_text if kind == "retrieve" else _notes(tool_text)
                self._saved[task_id] = content
                return call("write_artifact", {"name": artifact_file, "content": content})
            return ChatResult(content=_json_turn("done", self._saved.get(task_id, tool_text), "saved from the search tool"))

        if kind == "draft":
            reads = done.count("read_artifact")
            needed = [part.strip() for part in _field(user, "READ_FILES").split(",") if part.strip()]
            if reads < max(1, len(needed)):
                name = needed[reads] if reads < len(needed) else "research.md"
                return call("read_artifact", {"name": name})
            if "write_artifact" not in done:
                self.drafts += 1
                revise = "REVISE:" in user
                if self.bad_first_draft and self.drafts == 1 and not revise:
                    content = _BAD_BRIEF
                else:
                    content = _good_brief(tool_text + "\n" + user)
                self._saved[task_id] = content
                return call("write_artifact", {"name": artifact_file or "brief.md", "content": content})
            return ChatResult(content=_json_turn("done", self._saved.get(task_id, ""), "brief saved"))

        if kind == "review":
            if "read_artifact" not in done:
                name = _field(user, "READ_FILES").split(",")[0].strip() or "brief.md"
                return call("read_artifact", {"name": name})
            return ChatResult(
                content=_json_turn(
                    "done",
                    "APPROVED. The brief cites knowledge/ paths and states what the kit will not answer.",
                    "read the brief file and checked it",
                    decision="approve",
                )
            )

        return ChatResult(content=_json_turn("yield", "", "no task kind matched"))
