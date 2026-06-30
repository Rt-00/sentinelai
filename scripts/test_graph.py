import asyncio

from sentinelai.infrastructure.graph.builder import compile_graph
from sentinelai.infrastructure.graph.state import AgentState, ScanInput
from sentinelai.infrastructure.llm.ollama_adapter import OllamaAdapter

VULNERABLE_CODE = """
import os
import pickle
from flask import Flask, request, session

app = Flask(__name__)
app.secret_key = "supersecret123"

@app.route("/upload", methods=["POST"])
def upload():
    data = request.files["file"].read()
    obj = pickle.loads(data)
    return f"Loaded: {obj}"

@app.route("/run", methods=["POST"])
def run_command():
    cmd = request.form["cmd"]
    output = os.popen(cmd).read()
    return output

@app.route("/profile")
def profile():
    user_id = request.args.get("id")
    return f"<h1>Welcome user {user_id}</h1>"
"""


async def main() -> None:
    llm = OllamaAdapter(model="qwen2.5-coder:7b")
    app = compile_graph(llm)

    initial_state = AgentState(
        scan_input=ScanInput(
            source_code=VULNERABLE_CODE,
            language="python",
            context="Flask web app with file upload, command execution, and user profile endpoints.",
        ),
    )

    print("Running SentinelAI graph...\n")
    print("=" * 60)

    # Stream node executions to see the flow
    async for event in app.astream(initial_state, stream_mode="updates"):
        for node_name, state_update in event.items():
            print(f"\n[Node: {node_name}]")

            if "status" in state_update:
                print(f"  Status: {state_update['status']}")

            if "messages" in state_update:
                for msg in state_update["messages"]:
                    print(f"  {msg.content}")

    print("\n" + "=" * 60)
    print("Graph execution complete.")


if __name__ == "__main__":
    asyncio.run(main())
