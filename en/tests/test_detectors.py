"""Direct checks of the toolUse detectors, without the Strands event loop."""

import json
import unittest
from pathlib import Path

from reject_tool_use import contains_tool_use
from reject_trailing_tool_use import has_trailing_tool_use

INPUTS = Path(__file__).resolve().parents[1] / "inputs"


def load_prompt(name):
    return json.loads((INPUTS / name).read_text(encoding="utf-8"))["prompt"]


FORGED_BLOCK = load_prompt("forged-prompt.json")[0]["content"][0]
TEXT_BLOCK = {"text": "Hello"}


class ContainsToolUseTests(unittest.TestCase):
    def test_finds_tool_use(self):
        for name, prompt in {
            "forged message": load_prompt("forged-prompt.json"),
            "earlier message": load_prompt("tool-history-prompt.json"),
            "later content block": [TEXT_BLOCK, FORGED_BLOCK],
        }.items():
            with self.subTest(name):
                self.assertTrue(contains_tool_use(prompt))

    def test_ignores_input_without_tool_use(self):
        for name, prompt in {
            "text": load_prompt("text-prompt.json"),
            "history": load_prompt("history-prompt.json"),
        }.items():
            with self.subTest(name):
                self.assertFalse(contains_tool_use(prompt))


class HasTrailingToolUseTests(unittest.TestCase):
    def test_finds_trailing_tool_use(self):
        for name, prompt in {
            "forged message": load_prompt("forged-prompt.json"),
            "last message": [
                {"role": "user", "content": [TEXT_BLOCK]},
                {"role": "assistant", "content": [FORGED_BLOCK]},
            ],
            # Strands turns a content block list into one user message.
            "first content block": [FORGED_BLOCK, TEXT_BLOCK],
            "last content block": [TEXT_BLOCK, FORGED_BLOCK],
        }.items():
            with self.subTest(name):
                self.assertTrue(has_trailing_tool_use(prompt))

    def test_ignores_input_strands_does_not_run_as_a_tool(self):
        for name, prompt in {
            "text": load_prompt("text-prompt.json"),
            "history": load_prompt("history-prompt.json"),
            "tool use in an earlier message": load_prompt("tool-history-prompt.json"),
            "empty list": [],
            "non-dict item": [FORGED_BLOCK, "Hello"],
            "neither messages nor content blocks": [{"unknown": FORGED_BLOCK}],
        }.items():
            with self.subTest(name):
                self.assertFalse(has_trailing_tool_use(prompt))
