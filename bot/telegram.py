"""
telegram.py — the Telegram adapter.

This is the channel. The orchestrator in `core.py` knows nothing about
Telegram; this file wraps `run_council()` in a Telegram bot that:

  - accepts `/council <question>` or a plain DM (treated as a question
    if no command is present)
  - sends a "thinking..." status message immediately, then edits it
    as the council progresses (Stage 1 → 2 → 3 → 4)
  - sends the verdict as one or more Telegram messages, each ≤ 4096
    chars (we use 3800 for safety)
  - on any error, sends a single short reply explaining what failed

The bot polls Telegram with `python-telegram-bot`. To run:

    TELEGRAM_BOT_TOKEN=... python -m bot

Configuration (env vars)
------------------------

  TELEGRAM_BOT_TOKEN      required
  TELEGRAM_ALLOWED_USERS  optional, comma-separated Telegram user IDs.
                          If set, the bot ignores messages from other
                          users. Leave unset to allow anyone (DMs only).

The bot only responds in DMs and group commands (`@botname /council`).
It does not auto-reply to every message in a group.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Iterable

from telegram import Message, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .core import CouncilRequest, run_council
from .llm import LLMClient
from .personas import load_all_personas
from .verdict import chunk_for_telegram, render_markdown


# ---------- logging ----------

log = logging.getLogger("bot.telegram")
logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=os.environ.get("LOG_LEVEL", "INFO"),
)


# ---------- access control ----------

def _parse_allowed_users() -> set[int]:
    raw = os.environ.get("TELEGRAM_ALLOWED_USERS", "").strip()
    if not raw:
        return set()  # empty = allow everyone
    return {int(x) for x in raw.split(",") if x.strip().isdigit()}


def _user_allowed(update: Update, allowed: set[int]) -> bool:
    if not allowed:
        return True
    user = update.effective_user
    return bool(user and user.id in allowed)


# ---------- handlers ----------

HELP_TEXT = (
    "*Council bot* — in-process multi-persona deliberation.\n\n"
    "Usage:\n"
    "  `/council <your question>` — convene the council on your question\n"
    "  `/panel` — show which personas are on the panel for this bot\n"
    "  `/help` — this message\n\n"
    "The council runs 5 stages (independent → cross-examine → final → "
    "synthesis) over a small panel of personas. Takes 1–5 minutes "
    "depending on the LLM. The verdict is returned as one or more "
    "Telegram messages, each ≤ 4096 chars.\n\n"
    "Send anything that doesn't start with `/` and I'll treat it as a "
    "council question."
)


async def _cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _user_allowed(update, context.bot_data.setdefault("allowed", _parse_allowed_users())):
        return
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN)


async def _cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = context.bot_data.setdefault("allowed", _parse_allowed_users())
    if not _user_allowed(update, allowed):
        return
    personas = context.bot_data["personas"]
    from .personas import select_panel
    panel = select_panel(personas, question="")  # default question → no rag-curator auto-add
    lines = ["*Default panel* (profile=execution-lean, triad=ship-now):", ""]
    for p in panel:
        lines.append(f"• `{p.name}` — *{p.figure}*")
    lines.append("")
    lines.append(
        "The `council-rag-curator` is auto-added when your question "
        "matches its keywords (retrieval, knowledge, rag, embedding, "
        "faithfulness)."
    )
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def _run_and_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    question: str,
) -> None:
    """The shared workhorse. Edits the status message as the council progresses."""
    chat = update.effective_chat
    status_msg = await chat.send_message(
        f"🔵 *Council convening…*\n\nQuestion: _{question}_",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Run the council in a worker thread (LLMClient is sync).
    llm: LLMClient = context.bot_data["llm"]
    personas = context.bot_data["personas"]
    req = CouncilRequest(question=question)

    async def edit_status(text: str) -> None:
        try:
            await status_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:  # noqa: BLE001
            # Telegram rate-limits edits; ignore.
            pass

    try:
        await context.bot.send_chat_action(chat.id, ChatAction.TYPING)

        # Run stages sequentially, edit the status message between stages.
        # We re-implement the orchestration as a thin wrapper so we can
        # emit progress events without forking core.py.
        from .core import (
            DEFAULT_PROFILE, DEFAULT_TRIAD,
            _stage01_prompt, _stage02_prompt, _stage03_prompt,
            _stage04_chairman_prompt, _anonymise_stage01,
            _stage_records_to_block, _extract_section,
            _run_parallel,
        )
        from .personas import select_panel
        import time

        await edit_status(
            f"🔵 *Council convening…*\n\n"
            f"Question: _{question}_\n\n"
            f"Stage 00: selecting panel…"
        )
        panel = select_panel(
            personas,
            profile=DEFAULT_PROFILE,
            triad=DEFAULT_TRIAD,
            include_rag_curator=True,
            question=question,
        )

        # --- Stage 01 ---
        await edit_status(
            f"🔵 *Council convening…*\n\n"
            f"Question: _{question}_\n\n"
            f"Stage 01/04: independent analysis ({len(panel)} personas)…"
        )
        stage01_user = _stage01_prompt(question, 280)
        started = time.monotonic()
        stage01_contents = await asyncio.to_thread(
            _run_parallel,
            panel,
            lambda p: llm.complete(system=p.system_prompt, user=stage01_user),
        )

        # --- Stage 02 ---
        await edit_status(
            f"🔵 *Council convening…*\n\n"
            f"Question: _{question}_\n\n"
            f"Stage 02/04: cross-examination…"
        )
        stage01_block, _ = _anonymise_stage01(list(zip(panel, stage01_contents)))
        stage02_user = _stage02_prompt(question, stage01_block, 220)
        stage02_contents = await asyncio.to_thread(
            _run_parallel,
            panel,
            lambda p: llm.complete(system=p.system_prompt, user=stage02_user),
        )

        # --- Stage 03 ---
        await edit_status(
            f"🔵 *Council convening…*\n\n"
            f"Question: _{question}_\n\n"
            f"Stage 03/04: final stance…"
        )
        stage02_block = _stage_records_to_block(
            [(p.figure, c) for p, c in zip(panel, stage02_contents)]
        )
        stage03_user = _stage03_prompt(question, stage02_block, 200)
        stage03_contents = await asyncio.to_thread(
            _run_parallel,
            panel,
            lambda p: llm.complete(system=p.system_prompt, user=stage03_user),
        )

        # --- Stage 04 ---
        await edit_status(
            f"🔵 *Council convening…*\n\n"
            f"Question: _{question}_\n\n"
            f"Stage 04/04: chairman synthesis…"
        )
        stage03_block = _stage_records_to_block(
            [(p.figure, c) for p, c in zip(panel, stage03_contents)]
        )
        chairman = panel[0]
        chairman_user = _stage04_chairman_prompt(
            question=question, panel=panel,
            stage01_block=stage01_block,
            stage02_block=stage02_block,
            stage03_block=stage03_block,
            word_limit=500,
        )
        chairman_system = (
            chairman.system_prompt
            + "\n\n---\n\nFor this round, you are additionally the CHAIRMAN. "
            "Synthesise; do not advocate."
        )
        synthesis = await asyncio.to_thread(
            llm.complete,
            chairman_system,
            chairman_user,
        )
        elapsed = time.monotonic() - started

        # Build the verdict markdown + disagreement list
        from .verdict import CouncilResult
        result = CouncilResult(
            question=question, panel=panel,
            provider_summary=llm.describe(),
            elapsed_seconds=elapsed,
            synthesis=synthesis.strip(),
        )
        for persona, content in zip(panel, stage01_contents):
            result.record(persona, "01", "Independent Analysis", content)
        for persona, content in zip(panel, stage02_contents):
            result.record(persona, "02", "Cross-Examination", content)
        for persona, content in zip(panel, stage03_contents):
            from .verdict import _evidence_and_confidence
            ev, conf = _evidence_and_confidence(content)
            result.record(persona, "03", "Final Stance", content,
                          evidence_label=ev, confidence=conf)
        for d_line in _collect_disagreements(panel, stage02_contents):
            result.disagreements.append(d_line)
        result.next_step = _extract_section(synthesis, "Concrete next step") or ""
        unresolved_block = _extract_section(synthesis, "Unresolved questions") or ""
        if unresolved_block:
            result.unresolved = [
                ln.lstrip("- ").strip()
                for ln in unresolved_block.splitlines()
                if ln.strip().startswith("-")
            ]

        verdict_md = render_markdown(result)
        chunks = chunk_for_telegram(verdict_md)

        # Replace the status message with the first chunk; send the rest as follow-ups.
        await status_msg.edit_text(
            chunks[0],
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        for extra in chunks[1:]:
            await chat.send_message(
                extra,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

        # Send a short follow-up hint
        n = len(panel)
        await chat.send_message(
            f"✅ Council done in {elapsed:.1f}s · {n} personas · "
            f"{len(chunks)} message(s)\n\n"
            f"Send another question or `/help`.",
            disable_web_page_preview=True,
        )

    except Exception as exc:  # noqa: BLE001
        log.exception("council run failed")
        await status_msg.edit_text(
            f"❌ Council failed: `{type(exc).__name__}`\n\n"
            f"```\n{str(exc)[:1500]}\n```",
            parse_mode=ParseMode.MARKDOWN,
        )


def _collect_disagreements(panel: list, stage02_contents: list[str]) -> list[str]:
    from .verdict import _extract_bullets
    out: list[str] = []
    for persona, content in zip(panel, stage02_contents):
        for line in _extract_bullets(content, "### Disagree:"):
            short = line.split(":", 1)[-1].strip()
            if short:
                out.append(f"{persona.figure}: {short}")
    return out


async def _cmd_council(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = context.bot_data.setdefault("allowed", _parse_allowed_users())
    if not _user_allowed(update, allowed):
        await update.message.reply_text("🚫 Not authorised.")
        return
    question = " ".join(context.args or []).strip()
    if not question:
        await update.message.reply_text(
            "Usage: `/council <your question>`\n\nExample:\n"
            "`/council Should we drop the Smart City standards section?`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    await _run_and_reply(update, context, question)


async def _on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Plain (non-command) messages: treat as a council question if DM."""
    allowed = context.bot_data.setdefault("allowed", _parse_allowed_users())
    if not _user_allowed(update, allowed):
        return
    msg = update.message
    if not msg or not msg.text:
        return
    # Only auto-trigger in DMs (chat.type == 'private'). In groups, the
    # user must explicitly @ the bot or use a command.
    if msg.chat.type != "private":
        return
    question = msg.text.strip()
    if question.startswith("/"):
        return
    if len(question) < 8:
        # Too short to be a real council question; skip.
        return
    await _run_and_reply(update, context, question)


# ---------- entry ----------

def build_application() -> "Application":
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not set. Add it to .env or export it."
        )
    personas = load_all_personas()
    llm = LLMClient()
    log.info("loaded %d personas; llm=%s", len(personas), llm.describe())

    app = ApplicationBuilder().token(token).build()
    app.bot_data["personas"] = personas
    app.bot_data["llm"] = llm
    app.bot_data["allowed"] = _parse_allowed_users()

    app.add_handler(CommandHandler("help", _cmd_help))
    app.add_handler(CommandHandler("start", _cmd_help))
    app.add_handler(CommandHandler("panel", _cmd_panel))
    app.add_handler(CommandHandler("council", _cmd_council))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_message))

    log.info("Telegram bot ready (token ends in …%s)", token[-6:])
    return app


def main() -> None:
    app = build_application()
    log.info("starting polling…")
    app.run_polling(allowed_updates=None)
