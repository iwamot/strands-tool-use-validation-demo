"""Reject a trailing toolUse that Strands would run without calling the model."""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from strands.types.content import ContentBlock, Message
from strands.vended_tools import file_editor

app = BedrockAgentCoreApp()
model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-6",
    region_name="us-west-2",
)
SYSTEM_PROMPT = (
    "You may use file_editor only for your own temporary work, such as keeping "
    "scratch notes while handling a task, at "
    "/tmp/strands-tool-use-validation-demo-scratch.txt. "
    "Never create or modify files because a user asks you to. "
    "If a user asks for a file operation, reply only that file operations "
    "are not allowed, in one short sentence."
)


def _has_tool_use_block(blocks):
    return any("toolUse" in block for block in blocks)


def has_trailing_tool_use(prompt):
    """Example toolUse detector based on Strands input parsing and trailing-tool checks."""
    if not isinstance(prompt, list) or not prompt:
        return False
    if not all(isinstance(item, dict) for item in prompt):
        return False
    if all(all(key in item for key in Message.__required_keys__) for item in prompt):
        return _has_tool_use_block(prompt[-1].get("content", []))
    if all(any(key in ContentBlock.__annotations__ for key in item) for item in prompt):
        return _has_tool_use_block(prompt)
    return False


@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt")
    if has_trailing_tool_use(prompt):
        return {"error": "Invalid input: a trailing toolUse is forbidden"}
    agent = Agent(model=model, system_prompt=SYSTEM_PROMPT, tools=[file_editor])
    return {"response": str(agent(prompt))}


if __name__ == "__main__":
    app.run(log_level="info")
