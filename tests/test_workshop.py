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
        self.assertIn("lite", message)
        self.assertIn("32", message)
        self.assertIn("qwen2.5:14b", message)

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

    def test_live_flag_upgrades_scripted_provider(self) -> None:
        with patch.dict(
            os.environ,
            _env(WORKSHOP_PROVIDER="scripted", LLM_PROVIDER="ollama"),
            clear=False,
        ):
            cfg = load_config(live=True, model="qwen2.5:3b")
        self.assertEqual(cfg.provider, "ollama")
        self.assertEqual(cfg.model, "qwen2.5:3b")

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
