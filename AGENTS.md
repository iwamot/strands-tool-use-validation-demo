## About this repository

This repository is a demo of **input validation in AI agents**. It shows how caller-supplied input can run a tool before the model decides to use it, and how validation prevents this.

The examples live in `en/` and `ja/`, which differ only in the system prompt, the inputs, and the error messages. Keep the two directories in sync. In each, `vulnerable.py` is **intentionally vulnerable**, `text_only.py`, `reject_tool_use.py`, and `reject_trailing_tool_use.py` demonstrate three input checks, and the forged inputs under `inputs/` reproduce the flaw.

## This work is in scope

Writing and running the vulnerable example, crafting forged `toolUse` inputs, and adding regression tests are in scope. Treat reproductions in this repository as ordinary development work.

Follow these boundaries:

- **Keep the vulnerability.** Do not "fix" or remove the flaw in either `vulnerable.py` — it must keep demonstrating the problem. Harden the fix examples instead.
- **Stay self-contained.** Keep reproductions within this demo. Use the author's AWS credentials for Bedrock calls, and restrict file writes to `/tmp/strands-tool-use-validation-demo.txt` and the agent's scratch file `/tmp/strands-tool-use-validation-demo-scratch.txt`. Do not send forged requests to other systems.

## Type hints

Write no type hints, as the usual Strands and AgentCore samples do. The exception is a `@tool` function: Strands builds the tool's input schema from its type hints.

## Checks

Run before committing. The tests make no Bedrock calls.

    ./validate.sh

The tests that go through the Strands event loop replace the Bedrock model with a deterministic fake. The order of tool execution and model calls is what this demo shows, and only the real event loop can confirm it, so these tests keep the fake. Test the detectors directly as pure functions.

To run the tests on another supported Python version:

    UV_PYTHON=3.11 ./compatibility.sh
