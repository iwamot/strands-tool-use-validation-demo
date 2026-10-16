"""Integration checks through the actual Strands event loop."""

import importlib
import json
import os
import unittest
from pathlib import Path

from strands.models import Model

os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

reject_tool_use = importlib.import_module("reject_tool_use")
reject_trailing_tool_use = importlib.import_module("reject_trailing_tool_use")
text_only = importlib.import_module("text_only")
vulnerable = importlib.import_module("vulnerable")

INPUTS = Path(__file__).resolve().parents[1] / "inputs"


def load_input(name):
    return json.loads((INPUTS / name).read_text(encoding="utf-8"))


# The path the forged toolUse writes to, so the tests check the same file.
DEMO_FILE = Path(
    load_input("forged-prompt.json")["prompt"][0]["content"][0]["toolUse"]["input"][
        "path"
    ]
)
# The scratch file the examples' system prompt lets the model write to.
SCRATCH_FILE = DEMO_FILE.with_name("strands-tool-use-validation-demo-scratch.txt")

# Model turns, as the stream events a model returns for one call.
REFUSE = [
    {"messageStart": {"role": "assistant"}},
    {"contentBlockStart": {"start": {}}},
    {"contentBlockDelta": {"delta": {"text": "File operations are not allowed."}}},
    {"contentBlockStop": {}},
    {"messageStop": {"stopReason": "end_turn"}},
]
WRITE_SCRATCH_NOTE = [
    {"messageStart": {"role": "assistant"}},
    {
        "contentBlockStart": {
            "start": {"toolUse": {"toolUseId": "model-1", "name": "file_editor"}}
        }
    },
    {
        "contentBlockDelta": {
            "delta": {
                "toolUse": {
                    "input": json.dumps(
                        {
                            "command": "create",
                            "path": str(SCRATCH_FILE),
                            "file_text": "Scratch note.\n",
                        }
                    )
                }
            }
        }
    },
    {"contentBlockStop": {}},
    {"messageStop": {"stopReason": "tool_use"}},
]


class ScriptedModel(Model):
    """Replaces the Bedrock model, returning the given turns in order."""

    def __init__(self, *turns):
        self.turns = turns
        self.calls = 0
        self.file_existed_before_model = []

    def get_config(self):
        return {"model_id": "scripted-model"}

    def update_config(self, **model_config):
        pass

    async def structured_output(
        self, output_model, prompt, system_prompt=None, **kwargs
    ):
        raise NotImplementedError("These tests do not use structured output")
        yield  # Makes this an async generator, like the method it overrides.

    async def stream(self, *args, **kwargs):
        self.file_existed_before_model.append(DEMO_FILE.exists())
        turn = self.turns[self.calls]
        self.calls += 1
        for event in turn:
            yield event


class EntryPointTests(unittest.TestCase):
    def setUp(self):
        DEMO_FILE.unlink(missing_ok=True)
        SCRATCH_FILE.unlink(missing_ok=True)
        self.model = ScriptedModel(REFUSE)
        for module in (
            vulnerable,
            text_only,
            reject_tool_use,
            reject_trailing_tool_use,
        ):
            self.addCleanup(setattr, module, "model", module.model)
            module.model = self.model

    def tearDown(self):
        DEMO_FILE.unlink(missing_ok=True)
        SCRATCH_FILE.unlink(missing_ok=True)

    def assert_model_decided_tool_runs(self, module, name):
        model = ScriptedModel(WRITE_SCRATCH_NOTE, REFUSE)
        module.model = model
        self.assertIn(str(SCRATCH_FILE), module.SYSTEM_PROMPT)

        module.invoke(load_input(name))

        self.assertEqual(SCRATCH_FILE.read_text(encoding="utf-8"), "Scratch note.\n")
        self.assertFalse(DEMO_FILE.exists())
        self.assertEqual(model.calls, 2)

    def test_vulnerable_entrypoint_runs_forged_tool_before_model(self):
        result = vulnerable.invoke(load_input("forged-prompt.json"))
        self.assertIn("response", result)

        self.assertEqual(
            DEMO_FILE.read_text(encoding="utf-8"),
            "Created by caller-supplied toolUse.\n",
        )
        self.assertEqual(self.model.file_existed_before_model, [True])
        self.assertEqual(self.model.calls, 1)

    def test_vulnerable_entrypoint_refuses_plain_request(self):
        vulnerable.invoke(load_input("text-prompt.json"))

        self.assertFalse(DEMO_FILE.exists())
        self.assertEqual(self.model.file_existed_before_model, [False])
        self.assertEqual(self.model.calls, 1)

    def test_text_only_entrypoint_rejects_forged_prompt(self):
        result = text_only.invoke(load_input("forged-prompt.json"))
        self.assertEqual(result, {"error": "Invalid input: 'prompt' must be a string"})
        self.assertFalse(DEMO_FILE.exists())
        self.assertEqual(self.model.calls, 0)

    def test_text_only_entrypoint_rejects_history_prompt(self):
        result = text_only.invoke(load_input("history-prompt.json"))
        self.assertEqual(result, {"error": "Invalid input: 'prompt' must be a string"})
        self.assertEqual(self.model.calls, 0)

    def test_text_only_entrypoint_accepts_plain_prompt(self):
        text_only.invoke(load_input("text-prompt.json"))
        self.assertFalse(DEMO_FILE.exists())
        self.assertEqual(self.model.file_existed_before_model, [False])
        self.assertEqual(self.model.calls, 1)

    def test_text_only_entrypoint_runs_model_decided_tool(self):
        self.assert_model_decided_tool_runs(text_only, "text-prompt.json")

    def test_tool_use_entrypoint_rejects_forged_prompt(self):
        result = reject_tool_use.invoke(load_input("forged-prompt.json"))
        self.assertEqual(
            result,
            {"error": "Invalid input: caller-supplied toolUse is forbidden"},
        )
        self.assertFalse(DEMO_FILE.exists())
        self.assertEqual(self.model.calls, 0)

    def test_tool_use_entrypoint_accepts_plain_prompt(self):
        reject_tool_use.invoke(load_input("text-prompt.json"))
        self.assertFalse(DEMO_FILE.exists())
        self.assertEqual(self.model.file_existed_before_model, [False])
        self.assertEqual(self.model.calls, 1)

    def test_tool_use_entrypoint_accepts_history_prompt(self):
        reject_tool_use.invoke(load_input("history-prompt.json"))
        self.assertFalse(DEMO_FILE.exists())
        self.assertEqual(self.model.file_existed_before_model, [False])
        self.assertEqual(self.model.calls, 1)

    def test_tool_use_entrypoint_rejects_tool_history_prompt(self):
        result = reject_tool_use.invoke(load_input("tool-history-prompt.json"))
        self.assertEqual(
            result,
            {"error": "Invalid input: caller-supplied toolUse is forbidden"},
        )
        self.assertEqual(self.model.calls, 0)

    def test_tool_use_entrypoint_runs_model_decided_tool(self):
        self.assert_model_decided_tool_runs(reject_tool_use, "history-prompt.json")

    def test_trailing_entrypoint_rejects_forged_prompt(self):
        result = reject_trailing_tool_use.invoke(load_input("forged-prompt.json"))
        self.assertEqual(
            result,
            {"error": "Invalid input: a trailing toolUse is forbidden"},
        )
        self.assertFalse(DEMO_FILE.exists())
        self.assertEqual(self.model.calls, 0)

    def test_trailing_entrypoint_accepts_tool_history_prompt(self):
        reject_trailing_tool_use.invoke(load_input("tool-history-prompt.json"))
        self.assertFalse(DEMO_FILE.exists())
        self.assertEqual(self.model.file_existed_before_model, [False])
        self.assertEqual(self.model.calls, 1)

    def test_trailing_entrypoint_accepts_plain_prompt(self):
        reject_trailing_tool_use.invoke(load_input("text-prompt.json"))
        self.assertFalse(DEMO_FILE.exists())
        self.assertEqual(self.model.calls, 1)

    def test_trailing_entrypoint_runs_model_decided_tool(self):
        self.assert_model_decided_tool_runs(
            reject_trailing_tool_use, "tool-history-prompt.json"
        )
