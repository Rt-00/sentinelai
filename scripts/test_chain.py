import asyncio

from sentinelai.application.services.code_analyzer import CodeAnalyzer
from sentinelai.infrastructure.llm.ollama_adapter import OllamaAdapter

VULNERABLE_CODE = """
import sqlite3
from flask import Flask, request

app = Flask(__name__)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)

    user = cursor.fetchone()
    if user:
        return f"Welcome {username}!"
    return "Invalid credentials", 401
"""


async def main() -> None:
    llm = OllamaAdapter(model="qwen2.5-coder:7b")
    analyzer = CodeAnalyzer(llm=llm)

    print("Analyzing code for vulnerabilities...\n")
    result = await analyzer.analyze(
        source_code=VULNERABLE_CODE,
        language="python",
        context="Flask web application authentication endpoint",
    )

    print(f"Summary: {result.summary}\n")
    print(f"Found {len(result.findings)} findings:\n")

    findings = CodeAnalyzer.to_domain_findings(result)
    for finding in findings:
        icon = "🔴" if finding.is_critical() else "🟡"
        print(f"{icon} [{finding.severity.value.upper()}] {finding.title}")
        print(f"   Location: {finding.location}")
        print(f"   {finding.description}")
        print(f"   Fix: {finding.recommendation}\n")


if __name__ == "__main__":
    asyncio.run(main())
