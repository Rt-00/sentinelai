import asyncio

from sentinelai.infrastructure.graph import AgentState, ScanInput, compile_graph
from sentinelai.infrastructure.llm.ollama_adapter import OllamaAdapter

VULNERABLE_API = """
import jwt
import hashlib
from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient("mongodb://admin:admin123@localhost:27017")
db = client["myapp"]

SECRET_KEY = "my-secret-key-123"

@app.route("/api/users", methods=["GET"])
def get_users():
    username = request.args.get("username", "")
    users = db.users.find({"username": {"$regex": username}})
    return jsonify([u for u in users])

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    password_hash = hashlib.md5(data["password"].encode()).hexdigest()
    user = db.users.find_one({
        "username": data["username"],
        "password": password_hash,
    })
    if user:
        token = jwt.encode({"user_id": str(user["_id"]), "role": user["role"]},
                          SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/admin/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    db.users.delete_one({"_id": user_id})
    return jsonify({"deleted": True})

@app.route("/api/export", methods=["GET"])
def export_data():
    collection = request.args.get("collection", "users")
    data = list(db[collection].find())
    return jsonify(data)
"""


async def main() -> None:
    llm = OllamaAdapter(model="qwen2.5-coder:7b")
    app = compile_graph(llm)

    initial_state = AgentState(
        scan_input=ScanInput(
            source_code=VULNERABLE_API,
            language="python",
            context="Flask REST API with MongoDB, JWT auth, and data export functionality",
        ),
    )

    print("🛡️  SentinelAI Multi-Agent Security Scan")
    print("=" * 60)

    async for event in app.astream(initial_state, stream_mode="updates"):
        for node_name, state_update in event.items():
            status = state_update.get("status", "")
            agent = state_update.get("current_agent", "")

            if node_name == "supervisor":
                print(f"\n🧠 [Supervisor] → routing to: {agent}")
            elif node_name == "finalize":
                print(f"\n✅ [Finalize] Status: {status}")
            else:
                print(f"\n⚙️  [Node: {node_name}] Status: {status}")

            if "messages" in state_update:
                for msg in state_update["messages"]:
                    content = msg.content if hasattr(msg, "content") else str(msg)
                    # Print full report at the end, truncate intermediate messages
                    if node_name == "finalize":
                        print(f"\n{content}")
                    else:
                        preview = content[:200] + "..." if len(content) > 200 else content
                        print(f"  → {preview}")

    print("\n" + "=" * 60)
    print("🛡️  Scan complete.")


if __name__ == "__main__":
    asyncio.run(main())
