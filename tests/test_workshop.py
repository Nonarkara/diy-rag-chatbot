"""Smoke tests: the workshop finishes a job, and chatter dies quickly."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from workshop.config import (
    InsufficientResources,
    WorkshopConfigError,
    assert_resources,
    load_config,
)
from workshop.demo import run_demo, run_room_message
from workshop.llm import ScriptedLLM
from workshop.protocol import parse_turn


ROOT = Path(__file__).resolve().parents[1]


def _env(**extra: str) -> dict[str, str]:
    base = {
        "WORKSHOP_I_ACCEPT_RISK": "",
        "WORKSHOP_MODEL_GB": "",
        "WORKSHOP_RAM_GB": "",
        "WORKSHOP_RAM_TOTAL_GB": "",
        "WORKSHOP_MODE": "",
        "WORKSHOP_PROVIDER": "",
    }
    base.update(extra)
    return base


class DemoTests(unittest.TestCase):
    def test_lite_demo_finishes_with_a_brief(self) -> None:
        llm = ScriptedLLM()
        cfg = load_config(mode="lite", provider="scripted", knowledge_dir=ROOT / "knowledge")
        report = run_demo(cfg, llm)
        self.assertEqual(report.status, "done")
        self.assertIn("knowledge/GUARDRAILS.md", report.brief)
        self.assertIn("knowledge/HOW-WE-FILE.md", report.brief)
        self.assertIn("180", report.brief)
        self.assertLessEqual(len(report.brief.split()), 220)
        self.assertGreaterEqual(len(report.brief.split()), 40)
        self.assertLessEqual(report.llm_turns, 8)
        self.assertIn("search_knowledge", report.tool_calls)
        self.assertIn("write_artifact", report.tool_calls)
        self.assertIn("read_artifact", report.tool_calls)
        self.assertTrue(all(len(wave) == 1 for wave in report.waves))
        self.assertEqual(
            [wave[0] for wave in report.waves],
            ["retrieve", "research", "draft", "review"],
        )
        visible = report.room.render()
        self.assertNotIn("what do you think", visible.lower())
        writer_prompts = [p for p in llm.prompts if "TASK_KIND: draft" in p]
        research_prompts = [p for p in llm.prompts if "TASK_KIND: research" in p]
        self.assertEqual(len(writer_prompts), 1)
        self.assertIn("@writer", writer_prompts[0])
        self.assertIn("180", writer_prompts[0])
        self.assertTrue(research_prompts)
        self.assertNotIn("@writer", research_prompts[0])

    def test_full_mode_runs_both_research_tasks_in_one_wave(self) -> None:
        cfg = load_config(mode="full", provider="scripted", knowledge_dir=ROOT / "knowledge")
        report = run_demo(cfg, ScriptedLLM())
        self.assertEqual(report.status, "done")
        self.assertTrue(
            any(
                "research_facts" in wave and "research_limits" in wave
                for wave in report.waves
            )
        )
        owners = {task.owner for task in report.tasks}
        self.assertIn("scout", owners)
        self.assertIn("reviewer", owners)

    def test_weak_draft_gets_one_revision_then_stops(self) -> None:
        llm = ScriptedLLM(bad_first_draft=True)
        cfg = load_config(mode="lite", provider="scripted", knowledge_dir=ROOT / "knowledge")
        report = run_demo(cfg, llm)
        self.assertEqual(report.status, "done")
        self.assertEqual(llm.drafts, 2)
        ids = [task.id for task in report.tasks]
        self.assertIn("draft_r1", ids)
        self.assertIn("review_r1", ids)
        self.assertNotIn("draft_r2", ids)
        self.assertIn("knowledge/", report.brief)
        self.assertLessEqual(report.llm_turns, 8)

    def test_chatty_model_fails_closed(self) -> None:
        class Chatty:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, system: str, user: str) -> str:
                del system, user
                self.calls += 1
                return "Hey team, what do you all think? Let's chat."

        llm = Chatty()
        cfg = load_config(mode="lite", provider="scripted", knowledge_dir=ROOT / "knowledge")
        report = run_demo(cfg, llm)
        self.assertEqual(report.status, "failed")
        self.assertIn("idle", report.reason.lower())
        self.assertLessEqual(llm.calls, 2)
        self.assertNotIn("Hey team", report.room.render())

    def test_yield_does_not_become_a_conversation(self) -> None:
        class Yields:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, system: str, user: str) -> str:
                del system, user
                self.calls += 1
                return (
                    '{"action":"yield","note":"nothing to add","artifact":"",'
                    '"question":null,"handoff_to":null,"decision":null}'
                )

        llm = Yields()
        cfg = load_config(mode="lite", provider="scripted", knowledge_dir=ROOT / "knowledge")
        report = run_demo(cfg, llm)
        self.assertEqual(report.status, "failed")
        self.assertIn("yielded", report.reason)
        self.assertEqual(llm.calls, 2)
        speakers = {message.speaker for message in report.room.visible()}
        self.assertNotIn("researcher", speakers)

    def test_one_question_blocks_instead_of_looping(self) -> None:
        class Asks:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, system: str, user: str) -> str:
                del system, user
                self.calls += 1
                return (
                    '{"action":"ask","note":"need a scope","artifact":"",'
                    '"question":"Which city should the brief cover?",'
                    '"handoff_to":null,"decision":null}'
                )

        llm = Asks()
        cfg = load_config(mode="lite", provider="scripted", knowledge_dir=ROOT / "knowledge")
        report = run_demo(cfg, llm)
        self.assertEqual(report.status, "blocked")
        self.assertEqual(llm.calls, 1)
        self.assertIn("Which city should the brief cover?", report.room.render())

    def test_greeting_keeps_agents_silent(self) -> None:
        cfg = load_config(mode="lite", provider="scripted", knowledge_dir=ROOT / "knowledge")
        report = run_room_message(cfg, ScriptedLLM(), "hi")
        self.assertEqual(report.status, "yielded")
        self.assertEqual(report.llm_turns, 0)
        self.assertEqual(report.tasks, [])


class ResourceTests(unittest.TestCase):
    def test_full_mode_refuses_a_small_machine(self) -> None:
        with patch.dict(
            os.environ,
            _env(
                WORKSHOP_RAM_GB="8",
                WORKSHOP_RAM_TOTAL_GB="8",
                WORKSHOP_MODE="full",
            ),
            clear=False,
        ):
            cfg = load_config(mode="full", provider="ollama", model="qwen2.5:14b")
            with self.assertRaises(InsufficientResources) as caught:
                assert_resources(cfg)
        message = str(caught.exception)
        self.assertIn("ollama", message.lower())
        self.assertIn("qwen2.5:14b", message)
        self.assertIn("LLM_API_KEY", message)
        self.assertNotIn("32 GB", message)

    def test_unknown_local_model_fails_loudly(self) -> None:
        with patch.dict(os.environ, _env(), clear=False):
            with self.assertRaises(WorkshopConfigError) as caught:
                load_config(mode="lite", provider="ollama", model="mystery-70b")
        self.assertIn("WORKSHOP_MODEL_GB", str(caught.exception))

    def test_accept_risk_skips_the_refusal(self) -> None:
        with patch.dict(
            os.environ,
            _env(
                WORKSHOP_RAM_GB="8",
                WORKSHOP_RAM_TOTAL_GB="8",
                WORKSHOP_I_ACCEPT_RISK="1",
            ),
            clear=False,
        ):
            cfg = load_config(mode="full", provider="ollama", model="qwen2.5:14b")
            plan = assert_resources(cfg)
        self.assertIn("WORKSHOP_I_ACCEPT_RISK", plan.summary)

    def test_live_flag_upgrades_scripted_provider_to_api(self) -> None:
        with patch.dict(
            os.environ,
            _env(WORKSHOP_PROVIDER="scripted", LLM_PROVIDER="ollama"),
            clear=False,
        ):
            cfg = load_config(live=True, model="gpt-4o-mini")
        self.assertEqual(cfg.provider, "openai")
        self.assertEqual(cfg.model, "gpt-4o-mini")

    def test_remote_provider_has_no_weight_floor(self) -> None:
        with patch.dict(
            os.environ,
            _env(WORKSHOP_RAM_GB="2", WORKSHOP_RAM_TOTAL_GB="2"),
            clear=False,
        ):
            cfg = load_config(mode="full", provider="openai", model="gpt-4o-mini")
            plan = assert_resources(cfg)
        self.assertEqual(plan.required_gb, 0.0)
        self.assertEqual(plan.model_gb, 0.0)


class ToolTests(unittest.TestCase):
    def test_openai_tool_roundtrip_searches_and_saves(self) -> None:
        import tempfile

        from workshop.llm import OpenAICompatibleLLM, completions_url
        from workshop.tools import ToolBox, drive

        self.assertEqual(
            completions_url("https://openrouter.ai/api/v1"),
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertEqual(
            completions_url("https://api.openai.com"),
            "https://api.openai.com/v1/chat/completions",
        )
        payloads: list[dict] = []

        def post(url: str, payload: dict, headers: dict) -> dict:
            del url, headers
            payloads.append(payload)
            if len(payloads) == 1:
                return {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "call_search",
                                        "type": "function",
                                        "function": {
                                            "name": "search_knowledge",
                                            "arguments": '{"query": "how a page should be filed and what the kit refuses"}',
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"action":"done","note":"saved","artifact":"'
                                + "Notes cite knowledge/GUARDRAILS.md and knowledge/HOW-WE-FILE.md. "
                                + "The kit will not invent an answer when the file is silent. "
                                + 'This note is long enough to count as the work product.",'
                                + '"question":null,"handoff_to":null,"decision":null}'
                            )
                        }
                    }
                ]
            }

        llm = OpenAICompatibleLLM(model="gpt-4o-mini", api_key="test-key", post=post)
        box = ToolBox(ROOT / "knowledge", Path(tempfile.mkdtemp()))
        raw, used = drive(
            llm,
            "You search then stop.",
            "Find the filing rules.",
            box,
        )
        self.assertEqual(used, ["search_knowledge"])
        self.assertIn("tools", payloads[0])
        self.assertEqual(payloads[0]["tools"][0]["function"]["name"], "search_knowledge")
        followup = payloads[1]["messages"]
        self.assertTrue(any(message.get("role") == "tool" for message in followup))
        tool_body = next(message["content"] for message in followup if message.get("role") == "tool")
        self.assertIn("knowledge/", tool_body)
        self.assertIn("done", raw)

    def test_file_tools_stay_inside_the_workspace(self) -> None:
        from workshop.tools import ToolBox

        workspace = ROOT / "workshop-runs-sandbox"
        workspace.mkdir(exist_ok=True)
        box = ToolBox(ROOT / "knowledge", workspace)
        try:
            saved = box.run("write_artifact", {"name": "notes.md", "content": "hello from the tool"})
            self.assertIn("wrote notes.md", saved)
            self.assertIn("hello", box.run("read_artifact", {"name": "notes.md"}))
            self.assertIn("ERROR", box.run("write_artifact", {"name": "../escape.md", "content": "nope"}))
            self.assertIn("ERROR", box.run("read_knowledge_file", {"path": "../.env"}))
            self.assertIn("https", box.run("fetch_url", {"url": "http://example.com"}).lower())
            self.assertIn("blocked", box.run("fetch_url", {"url": "https://127.0.0.1/secret"}).lower())
        finally:
            import shutil

            shutil.rmtree(workspace, ignore_errors=True)

    def test_ollama_tool_payload_parses(self) -> None:
        from workshop.llm import parse_ollama_chat

        result = parse_ollama_chat(
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {"function": {"name": "write_artifact", "arguments": {"name": "brief.md", "content": "hi"}}}
                    ],
                }
            }
        )
        self.assertEqual(result.tool_calls[0].name, "write_artifact")
        self.assertEqual(result.tool_calls[0].arguments["name"], "brief.md")


class ProtocolTests(unittest.TestCase):
    def test_fenced_json_parses(self) -> None:
        raw = """```json
        {"action":"done","note":"filed","artifact":"A real artifact with enough words to count as work product for the task.","question":null,"handoff_to":null}
        ```"""
        turn = parse_turn(raw)
        self.assertEqual(turn.action, "done")

    def test_chatter_inside_json_is_rejected(self) -> None:
        from workshop.protocol import ProtocolError

        raw = (
            '{"action":"advance","note":"hey team what do you think",'
            '"artifact":"This artifact is long enough to pass the word floor easily today.",'
            '"question":null}'
        )
        with self.assertRaises(ProtocolError):
            parse_turn(raw)


if __name__ == "__main__":
    unittest.main()
