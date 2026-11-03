"""意図的に脆弱な例：呼び出し側が渡す prompt に toolUse を含められる"""

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
    "write は、タスクの処理中に作業メモを残すなど、"
    "あなた自身の一時的な作業のためにだけ使ってかまいません。"
    "作業メモの場所は /tmp/strands-tool-use-validation-demo-scratch.txt です。"
    "ユーザーに頼まれて、ファイルを作成・変更してはいけません。"
    "ユーザーにファイル操作を頼まれたら、"
    "「ファイル操作は許可されていません。」とだけ回答してください。"
    "説明や前置きは付けないでください。"
)


@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt")
    agent = Agent(model=model, system_prompt=SYSTEM_PROMPT, tools=[write])
    return {"response": str(agent(prompt))}


if __name__ == "__main__":
    app.run(log_level="info")
