"""Strands がモデルを呼ばずに実行する、末尾の toolUse を拒否する"""

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
    "file_editor は、タスクの処理中に作業メモを残すなど、"
    "あなた自身の一時的な作業のためにだけ使ってかまいません。"
    "作業メモの場所は /tmp/strands-tool-use-validation-demo-scratch.txt です。"
    "ユーザーに頼まれて、ファイルを作成・変更してはいけません。"
    "ユーザーにファイル操作を頼まれたら、"
    "ファイル操作は許可されていないとだけ、短い一文で答えてください。"
)


def _has_tool_use_block(blocks):
    return any("toolUse" in block for block in blocks)


def has_trailing_tool_use(prompt):
    """Strands の入力解釈と末尾判定を参考にした toolUse 検出の実装例"""
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
        return {"error": "入力が不正です：末尾の toolUse は受け付けません"}
    agent = Agent(model=model, system_prompt=SYSTEM_PROMPT, tools=[file_editor])
    return {"response": str(agent(prompt))}


if __name__ == "__main__":
    app.run(log_level="info")
