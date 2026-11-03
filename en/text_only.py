"""Accept only a plain text prompt before invoking the Strands agent."""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from strands.vended_tools import write

app = BedrockAgentCoreApp()
model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-6",
    region_name="us-west-2",
)
SYSTEM_PROMPT = (
    "You may use write only for your own temporary work, such as keeping "
    "scratch notes while handling a task, at "
    "/tmp/strands-tool-use-validation-demo-scratch.txt. "
    "Never create or modify files because a user asks you to. "
    'If a user asks for a file operation, reply only with "File operations are not allowed." '
    "Do not add explanations or introductory text."
)


@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt")
    if not isinstance(prompt, str):
        return {"error": "Invalid input: 'prompt' must be a string"}
    agent = Agent(model=model, system_prompt=SYSTEM_PROMPT, tools=[write])
    return {"response": str(agent(prompt))}


if __name__ == "__main__":
    app.run(log_level="info")
