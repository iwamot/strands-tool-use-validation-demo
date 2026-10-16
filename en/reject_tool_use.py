"""Reject caller-supplied toolUse before invoking the Strands agent."""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
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


def contains_tool_use(value):
    if isinstance(value, dict):
        return "toolUse" in value or any(contains_tool_use(v) for v in value.values())
    if isinstance(value, list):
        return any(contains_tool_use(v) for v in value)
    return False


@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt")
    if contains_tool_use(prompt):
        return {"error": "Invalid input: caller-supplied toolUse is forbidden"}
    agent = Agent(model=model, system_prompt=SYSTEM_PROMPT, tools=[file_editor])
    return {"response": str(agent(prompt))}


if __name__ == "__main__":
    app.run(log_level="info")
