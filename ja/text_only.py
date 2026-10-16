"""Strands のエージェントを呼ぶ前に、文字列の prompt だけを受け付ける"""

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
    "file_editor は、タスクの処理中に作業メモを残すなど、"
    "あなた自身の一時的な作業のためにだけ使ってかまいません。"
    "作業メモの場所は /tmp/strands-tool-use-validation-demo-scratch.txt です。"
    "ユーザーに頼まれて、ファイルを作成・変更してはいけません。"
    "ユーザーにファイル操作を頼まれたら、"
    "ファイル操作は許可されていないとだけ、短い一文で答えてください。"
)


@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt")
    if not isinstance(prompt, str):
        return {"error": "入力が不正です：prompt は文字列にしてください"}
    agent = Agent(model=model, system_prompt=SYSTEM_PROMPT, tools=[file_editor])
    return {"response": str(agent(prompt))}


if __name__ == "__main__":
    app.run(log_level="info")
