"""
__main__.py — entry point.

Run with:    python -m bot

Reads env vars (TELEGRAM_BOT_TOKEN, LLM_*) and starts the Telegram bot.
To run the orchestrator without the bot (e.g. for a smoke test or a
future web /council endpoint), use `python -m bot.core` instead.
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--core-smoke":
        # Run the orchestrator without the bot, for sanity checks.
        from bot.core import CouncilRequest, run_council
        from bot.llm import LLMClient
        from bot.personas import load_all_personas

        question = " ".join(sys.argv[2:]) or (
            "Should we drop the Smart City Thailand standards section "
            "from our knowledge folder to save embedding cost?"
        )
        print(f"[bot] core smoke test · question: {question}")
        llm = LLMClient()
        print(f"[bot] llm: {llm.describe()}")
        personas = load_all_personas()
        req = CouncilRequest(question=question)
        result = run_council(req, llm, personas=personas)
        from bot.verdict import render_markdown
        print()
        print(render_markdown(result)[:4000])
        return

    from bot.telegram import main as telegram_main
    telegram_main()


if __name__ == "__main__":
    main()
