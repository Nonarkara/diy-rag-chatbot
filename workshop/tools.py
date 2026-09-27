"""Tools the agents actually call.

The model does not get the folder contents in the prompt and then
pretend it searched. ``search_knowledge``, ``read_knowledge_file``,
``read_artifact``, and ``write_artifact`` run here. ``fetch_url`` is
optional and refuses private hosts. There is no shell tool: an open
shell on the owner's laptop is not a safe default.
"""

from __future__ import annotations

import ipaddress
import json
import re
import socket
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from workshop.protocol import ProtocolError
from workshop.rag import format_passages, search


_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,80}$")
_TAG = re.compile(r"<[^>]+>")
_MAX_ARTIFACT = 80_000
_MAX_FETCH = 20_000


def tool_schemas() -> list[dict]:
    def fn(name: str, description: str, properties: dict, required: list[str]) -> dict:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    return [
        fn(
            "search_knowledge",
            "Search the local knowledge folder. Returns file paths and excerpts. Call this before you claim what the files say.",
            {"query": {"type": "string", "description": "What you need from the folder"}},
            ["query"],
        ),
        fn(
            "read_knowledge_file",
            "Read one file inside the knowledge folder. Path is relative, such as faq/example.md.",
            {"path": {"type": "string"}},
            ["path"],
        ),
        fn(
            "read_artifact",
            "Read a file this workshop already saved (notes, brief, review).",
            {"name": {"type": "string", "description": "File name only, no directories"}},
            ["name"],
        ),
        fn(
            "write_artifact",
            "Save your work product. Call this before you finish a research note or a brief.",
            {
                "name": {"type": "string"},
                "content": {"type": "string", "description": "The full markdown to save"},
            },
            ["name", "content"],
        ),
        fn(
            "fetch_url",
            "Fetch a public https page and return plain text. Local and private hosts are refused.",
            {"url": {"type": "string"}},
            ["url"],
        ),
    ]


@dataclass
class ToolBox:
    knowledge_dir: Path
    workspace: Path
    calls: list[str] = field(default_factory=list)
    last_write: str = ""

    def run(self, name: str, arguments: dict | str | None) -> str:
        args = _coerce_args(arguments)
        self.calls.append(name)
        try:
            if name == "search_knowledge":
                return self._search(str(args.get("query") or ""))
            if name == "read_knowledge_file":
                return self._read_knowledge(str(args.get("path") or ""))
            if name == "read_artifact":
                return self._read_artifact(str(args.get("name") or ""))
            if name == "write_artifact":
                return self._write_artifact(str(args.get("name") or ""), str(args.get("content") or ""))
            if name == "fetch_url":
                return self._fetch(str(args.get("url") or ""))
        except OSError as exc:
            return f"ERROR: {exc}"
        return f"ERROR: unknown tool {name}"

    def _search(self, query: str) -> str:
        if not query.strip():
            return "ERROR: query is empty"
        passages = search(self.knowledge_dir, query, k=4)
        return format_passages(passages)

    def _read_knowledge(self, relative: str) -> str:
        path = _inside(self.knowledge_dir, relative)
        if path is None or not path.is_file():
            return "ERROR: path must be a file inside the knowledge folder"
        return path.read_text(encoding="utf-8", errors="replace")[:_MAX_ARTIFACT]

    def _read_artifact(self, name: str) -> str:
        path = _artifact_path(self.workspace, name)
        if path is None or not path.is_file():
            return f"ERROR: no artifact named {name}"
        return path.read_text(encoding="utf-8", errors="replace")[:_MAX_ARTIFACT]

    def _write_artifact(self, name: str, content: str) -> str:
        path = _artifact_path(self.workspace, name)
        if path is None:
            return "ERROR: artifact name must be a single file name, not a path"
        if not content.strip():
            return "ERROR: content is empty"
        if len(content) > _MAX_ARTIFACT:
            return "ERROR: content is too large"
        self.workspace.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.last_write = content
        return f"wrote {name} ({len(content.split())} words)"

    def _fetch(self, url: str) -> str:
        blocked = _public_https(url)
        if blocked:
            return blocked
        import httpx

        try:
            with httpx.Client(timeout=10.0, follow_redirects=False) as client:
                response = client.get(url, headers={"User-Agent": "diy-rag-workshop/2"})
                response.raise_for_status()
        except Exception as exc:  # noqa: BLE001 — surface a tool error, do not crash the mission
            return f"ERROR: fetch failed: {exc}"
        text = _TAG.sub(" ", response.text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > _MAX_FETCH:
            text = text[:_MAX_FETCH] + "…"
        return text or "ERROR: page had no text"


def drive(llm, system: str, user: str, box: ToolBox, *, max_steps: int = 6) -> tuple[str, list[str]]:
    """Run one agent turn. Tool calls execute; the final message is the work object.

    ``max_steps`` stops a model that keeps calling tools and never finishes.
    """
    messages: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    used: list[str] = []
    schemas = tool_schemas()
    for _ in range(max_steps):
        result = llm.chat(messages, schemas)
        if result.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": result.content or "",
                    "tool_calls": [call.as_message() for call in result.tool_calls],
                }
            )
            for call in result.tool_calls:
                output = box.run(call.name, call.arguments)
                used.append(call.name)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.name,
                        "content": output,
                    }
                )
            continue
        return (result.content or ""), used
    raise ProtocolError(
        "tool loop hit its step cap without a final answer (idle tool chatter)"
    )


def _coerce_args(arguments: dict | str | None) -> dict:
    if arguments is None:
        return {}
    if isinstance(arguments, dict):
        return arguments
    text = arguments.strip() or "{}"
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _artifact_path(workspace: Path, name: str) -> Path | None:
    if not _NAME.match(name or ""):
        return None
    if "/" in name or "\\" in name or name.startswith("."):
        return None
    path = (workspace / name).resolve()
    root = workspace.resolve()
    if path.parent != root:
        return None
    return path


def _inside(root: Path, relative: str) -> Path | None:
    if not relative or relative.startswith(("/", "\\")):
        return None
    root_resolved = root.resolve()
    path = (root_resolved / relative).resolve()
    if root_resolved not in path.parents and path != root_resolved:
        return None
    return path


def _public_https(url: str) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        return "ERROR: only public https URLs are allowed"
    host = parsed.hostname or ""
    if not host or host in {"localhost"} or host.endswith(".local"):
        return "ERROR: local hosts are blocked"
    try:
        infos = socket.getaddrinfo(host, 443)
    except socket.gaierror as exc:
        return f"ERROR: could not resolve host: {exc}"
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            return "ERROR: private or local addresses are blocked"
    return None
