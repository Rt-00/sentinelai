# SentinelAI

Multi-Agent Security Assistant powered by LangGraph + Ollama. A system of collaborative AI agents that analyzes source code for security vulnerabilities, maps known CVEs, and generates structured security reports — all running locally with full privacy.

## Architecture

```
                    ┌──────────────┐
                    │  Supervisor  │
                    │   (Router)   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Code    │ │  Vuln    │ │  Report  │
        │ Analyzer │ │ Scanner  │ │ Writer   │
        └──────────┘ └──────────┘ └──────────┘
```

**Phase 2 graph flow (linear):**
```
START → intake → analyze_code → synthesize → END
```

- **intake** — validates the scan input and routes to the appropriate agent
- **analyze_code** — runs the Code Analyzer chain and produces structured findings
- **synthesize** — formats findings into a human-readable security report
- **Supervisor** — conditional routing across multiple agents *(Phase 3)*
- **Vuln Scanner** — queries a CVE knowledge base using semantic search *(Phase 4)*

## Tech Stack

| Layer | Technology |
|---|---|
| LLM Provider | Ollama (local, qwen2.5-coder:7b) |
| LLM Framework | LangChain |
| Agent Orchestration | LangGraph |
| Vector Store | ChromaDB *(Phase 4)* |
| API | FastAPI *(Phase 5)* |
| Validation | Pydantic v2 |
| Architecture | Clean Architecture / Hexagonal (Ports & Adapters) |
| Package Manager | uv |

## Project Structure

```
sentinelai/
├── pyproject.toml
├── scripts/
│   ├── test_chain.py              # Manual test: code analyzer chain only
│   └── test_graph.py              # Manual test: full LangGraph execution
├── src/
│   └── sentinelai/
│       ├── domain/
│       │   ├── entities/
│       │   │   ├── finding.py          # Security finding entity
│       │   │   ├── scan_request.py     # Scan request value object
│       │   │   ├── report.py           # Report aggregate
│       │   │   └── severity.py         # Severity enum
│       │   └── ports/
│       │       └── llm_port.py         # LLM abstraction (interface)
│       ├── application/
│       │   └── services/
│       │       └── code_analyzer.py    # Code → findings chain
│       └── infrastructure/
│           ├── llm/
│           │   └── ollama_adapter.py   # LangChain ChatOllama adapter
│           └── graph/
│               ├── state.py            # AgentState + ScanInput (Pydantic)
│               ├── nodes.py            # GraphNodes: intake, analyze_code, synthesize
│               └── builder.py          # Graph builder + compile_graph()
└── tests/
```

The domain layer has **zero external dependencies** — no LangChain, no Pydantic in entities. The infrastructure layer implements domain ports, keeping the architecture invertible.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/)

## Getting Started

```bash
# Clone the repo
git clone https://github.com/Rt-00/sentinelai.git
cd sentinelai

# Install dependencies
uv sync

# Pull the LLM model
ollama pull qwen2.5-coder:7b

# Run the full graph
uv run python scripts/test_graph.py

# Or run the code analyzer chain only
uv run python scripts/test_chain.py
```

## Example Output

The test script runs a deliberately vulnerable Flask app (insecure deserialization, command injection, XSS, missing security configs, no logging) through the full graph:

```
Running SentinelAI graph...

============================================================

[Node: intake]
  Status: analyzing
  Scan intake complete. Routing to Code Analyzer.

[Node: analyze_code]
  Status: analyzed
  Analysis complete: found 5 issues (2) critical/high severity.

[Node: synthesize]
  Status: completed
  ## Security Scan Report

**Summary:** The provided Flask web app has several security vulnerabilities that could be exploited by attackers.

🔴 **[HIGH] Insecure deserialization**
   Location: /upload
   The `upload` function uses `pickle.loads()` to deserialize data received from the client.
   **Fix:** Avoid using `pickle` for deserializing untrusted data. Use JSON instead.

🔴 **[HIGH] Command injection**
   Location: /run
   The `run_command` function executes user-provided commands directly using `os.popen()`.
   **Fix:** Use `subprocess.run()` with proper argument handling and validation.

🟡 **[MEDIUM] Cross-site scripting (XSS)**
   Location: /profile
   User input is included in the HTML response without sanitization.
   **Fix:** Sanitize and escape user input before rendering.

🟡 **[MEDIUM] Security misconfigurations**
   Location: /
   No HTTPS or CORS headers configured.
   **Fix:** Implement HTTPS and configure CORS appropriately.

🟡 **[MEDIUM] Insufficient logging**
   Location: /
   No logging configured, making it hard to detect breaches.
   **Fix:** Configure logging to capture errors and access attempts.

============================================================
Graph execution complete.
```

*(actual output varies by model)*

## Design Decisions

- **Clean Architecture** — Domain entities are pure Python dataclasses with no framework dependencies. The `LLMPort` abstract class defines the contract; `OllamaAdapter` implements it via LangChain. Swapping to a different provider means writing a new adapter, nothing else changes.
- **LangGraph State** — `AgentState` is a Pydantic `BaseModel` with `Annotated` message list using `add_messages` reducer. Nodes return partial dicts that are merged into the state automatically.
- **Async Nodes** — All graph nodes are `async`, enabling concurrent execution in future phases.
- **Structured Output** — The analyzer uses `with_structured_output()` to get Pydantic-validated responses from the LLM, ensuring type-safe findings.
- **Immutable Entities** — All domain entities use `frozen=True` dataclasses for safety and predictability.
- **Ollama (Local)** — Full privacy. No data leaves your machine.

## Roadmap

- [x] **Phase 1** — LangChain + Ollama foundation, domain entities, first chain (Code Analyzer)
- [x] **Phase 2** — LangGraph basics: `AgentState`, `StateGraph`, Code Analyzer as a node
- [ ] **Phase 3** — Multi-agent orchestration with Supervisor routing + conditional edges
- [ ] **Phase 4** — RAG pipeline: CVE ingestion into ChromaDB, semantic retrieval, reranking
- [ ] **Phase 5** — FastAPI endpoints, SSE streaming, LangSmith tracing, tests

## License

MIT
