"""
bot — in-process 0xNyk council + Telegram adapter.

The repo ships two council engines: `council/` (skill, host-CLI) and
`karpathy-council/` (3-stage multi-model). Both are great for the repo
owner to make decisions about the project. This package is different:
it runs the council *inside a Python process* so an end user — anyone
who messages the Telegram bot — gets the same multi-perspective
deliberation without needing a host CLI, a tmux session, or a
subagent-capable client.

Why this package exists: a previous attempt to build an "AI council"
on Telegram used multiple bots, one per persona. That fails because
Telegram bots cannot initiate messages to other bots — they are
user-like accounts that can only respond to messages users send to
them. The "council" became N parallel siloed answers, not a
deliberation. The right architecture is one bot, one process, the
council happening internally as LLM calls. This package is that
architecture.

Layout
------

  bot/
    __main__.py     entry point — `python -m bot` reads env vars and starts
    core.py         the 5-stage protocol (orchestrator)
    personas.py     loads 19 personas from council/agents/council-*.md
    llm.py          multi-provider LLM client (Ollama default)
    verdict.py      verdict assembly + Telegram-safe chunking
    telegram.py     the python-telegram-bot adapter
    README.md       setup, env vars, deployment notes

The core (`core.py`) is channel-agnostic. To add Discord, Slack, or
a web `/council` endpoint, copy `telegram.py`, replace the channel
calls with the new platform's calls, and keep `core.py` untouched.
"""

__version__ = "0.1.0"
