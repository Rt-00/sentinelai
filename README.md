```markdown
# SentinelAI 🛡️

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

- **Supervisor** — routes input to the appropriate agent via conditional edges *(planned)*
- **Code Analyzer** — analyzes source code for security vulnerabilities and code smells
- **Vuln Scanner** — queries a CVE knowledge base using semantic search *(planned)*
- **Report Writer** — consolidates findings into a structured security report *(planned)*

## Tech Stack

| Layer | Technology |
|---|---|
| LLM Provider | Ollama (local, qwen2.5-coder:7b) |
| LLM Framework | LangChain |
| Agent Orchestration | LangGraph *(Phase 2)* |
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
│   └── test_chain.py              # Manual test script
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
│       │       └── code_analyzer.py    # First chain: code → findings
│       └── infrastructure/
│           └── llm/
│               └── ollama_adapter.py   # LangChain ChatOllama adapter
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
git clone https://github.com/rt-00/sentinelai.git
cd sentinelai

# Install dependencies
uv sync

# Pull the LLM model
ollama pull qwen2.5-coder:7b

# Run the code analyzer
uv run python scripts/test_chain.py
```

## Example Output

The test script analyzes a deliberately vulnerable Flask login endpoint (SQL injection, plaintext passwords, no rate limiting) and returns structured findings:

```
Analyzing code for vulnerabilities...

Summary: Multiple critical security issues found in authentication endpoint.

Found 3 findings:

🔴 [CRITICAL] SQL Injection in Login Query
   Location: login() — line 12
   User input is directly interpolated into SQL query string.
   Fix: Use parameterized queries with cursor.execute("SELECT ... WHERE username = ?", (username,))

🔴 [HIGH] Plaintext Password Storage
   Location: login() — password comparison
   Passwords are stored and compared in plaintext without hashing.
   Fix: Use bcrypt or argon2 for password hashing.

🟡 [MEDIUM] No Rate Limiting on Auth Endpoint
   Location: /login route
   No protection against brute-force attacks.
   Fix: Implement rate limiting with flask-limiter.
```

*(actual output varies by model)*

## Design Decisions

- **Clean Architecture** — Domain entities are pure Python dataclasses with no framework dependencies. The `LLMPort` abstract class defines the contract; `OllamaAdapter` implements it via LangChain. Swapping to a different provider means writing a new adapter, nothing else changes.
- **Structured Output** — The analyzer uses `with_structured_output()` to get Pydantic-validated responses from the LLM, ensuring type-safe findings.
- **Immutable Entities** — All domain entities use `frozen=True` dataclasses for safety and predictability.
- **Ollama (Local)** — Full privacy. No data leaves your machine.

## Roadmap

- [x] **Phase 1** — LangChain + Ollama foundation, domain entities, first chain (Code Analyzer)
- [ ] **Phase 2** — LangGraph basics: `AgentState`, `StateGraph`, Code Analyzer as a node
- [ ] **Phase 3** — Multi-agent orchestration with Supervisor routing + conditional edges
- [ ] **Phase 4** — RAG pipeline: CVE ingestion into ChromaDB, semantic retrieval, reranking
- [ ] **Phase 5** — FastAPI endpoints, SSE streaming, LangSmith tracing, tests

## License

MIT
```