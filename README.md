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

**Phase 3 graph flow (Supervisor routing):**
```
START → intake → supervisor ←──────────────────┐
                    │                           │
                    ├── analyze_code ───────────┤
                    ├── scan_vulns  ────────────┤
                    ├── write_report ───────────┘
                    └── FINISH → finalize → END
```

- **intake** — validates the scan input and routes to the Supervisor
- **supervisor** — decides which agent to call next based on current state (uses `with_structured_output`)
- **analyze_code** — runs the Code Analyzer chain and produces structured findings
- **scan_vulns** — maps findings to known CVEs and vulnerability patterns
- **write_report** — generates the final professional security assessment report
- **finalize** — assembles the completed report and exits the graph

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
│   ├── test_graph.py              # Manual test: Phase 2 linear graph
│   └── test_multi_agent.py        # Manual test: full multi-agent graph
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
│       │       ├── code_analyzer.py    # Code → findings chain
│       │       ├── vuln_scanner.py     # Findings → CVE matches chain
│       │       └── report_writer.py    # Findings + CVEs → report chain
│       └── infrastructure/
│           ├── llm/
│           │   └── ollama_adapter.py   # LangChain ChatOllama adapter
│           └── graph/
│               ├── state.py            # AgentState, ScanInput, SupervisorDecision
│               ├── nodes.py            # GraphNodes: all agent nodes + Supervisor
│               └── builder.py          # Graph builder + conditional edges
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

# Run the full multi-agent scan
uv run python scripts/test_multi_agent.py

# Or run the Phase 2 linear graph
uv run python scripts/test_graph.py

# Or run the code analyzer chain only
uv run python scripts/test_chain.py
```

## Example Output

The multi-agent script scans a deliberately vulnerable Flask REST API (MongoDB NoSQL injection, MD5 password hashing, hardcoded credentials, missing JWT expiry, collection enumeration, XSS):

```
🛡️  SentinelAI Multi-Agent Security Scan
============================================================

⚙️  [Node: intake] Status: routing
  → Scan intake complete. Language: python. Routing to Supervisor.

🧠 [Supervisor] → routing to: code_analyzer
  → Supervisor decision: route to code_analyzer. Reason: The code_analyzer must run first.

⚙️  [Node: analyze_code] Status: routing
  → Code analysis complete: 8 findings (3 critical/high).

🧠 [Supervisor] → routing to: vuln_scanner
  → Supervisor decision: route to vuln_scanner. Reason: code_analyzer is done; vuln_scanner needs its findings.

⚙️  [Node: scan_vulns] Status: routing
  → Vulnerability scan complete: 9 CVE matches. Multiple high-risk vulnerabilities found...

🧠 [Supervisor] → routing to: report_writer
  → Supervisor decision: route to report_writer. Reason: Both analyzers are done; report can now be generated.

⚙️  [Node: write_report] Status: routing
  → Security report generated successfully.

🧠 [Supervisor] → routing to: FINISH
  → Supervisor decision: FINISH. All agents have completed their tasks.

✅ [Finalize] Status: completed

# Security Assessment Report

## Executive Summary
...

## Critical Findings
1. SQL Injection — High Severity
2. Weak Hashing Algorithm (MD5) — High Severity
3. Sensitive Data Exposure — High Severity

## Detailed Findings
...

## Vulnerability Mapping
- SQL Injection (CVE-2016-1013): High Severity
- Weak Hashing Algorithm (CVE-2022-41935): High Severity
...

## Overall Risk Rating: High

============================================================
🛡️  Scan complete.
```

*(actual output varies by model)*

## Design Decisions

- **Clean Architecture** — Domain entities are pure Python dataclasses with no framework dependencies. The `LLMPort` abstract class defines the contract; `OllamaAdapter` implements it via LangChain. Swapping to a different provider means writing a new adapter, nothing else changes.
- **Supervisor pattern** — The Supervisor node uses `invoke_structured` with a `SupervisorDecision` schema to decide the next agent. It enforces ordering rules via prompt (code_analyzer → vuln_scanner → report_writer) without hardcoding edges.
- **Cyclic graph** — All worker nodes loop back to the Supervisor, which either routes to the next agent or returns `FINISH`. This makes adding new agents trivial: register a node and add a routing case.
- **LangGraph State** — `AgentState` is a Pydantic `BaseModel` with `Annotated` message list using `add_messages` reducer. Nodes return partial dicts that are merged into the state automatically.
- **Async Nodes** — All graph nodes are `async`, enabling concurrent execution in future phases.
- **Structured Output** — Every LLM call uses `with_structured_output()` for type-safe, Pydantic-validated responses. The `OllamaAdapter` caps generation at `num_predict=2048` tokens to prevent runaway inference on small models.
- **Immutable Entities** — All domain entities use `frozen=True` dataclasses for safety and predictability.
- **Ollama (Local)** — Full privacy. No data leaves your machine.

## Roadmap

- [x] **Phase 1** — LangChain + Ollama foundation, domain entities, first chain (Code Analyzer)
- [x] **Phase 2** — LangGraph basics: `AgentState`, `StateGraph`, Code Analyzer as a node
- [x] **Phase 3** — Multi-agent orchestration with Supervisor routing + conditional edges
- [ ] **Phase 4** — RAG pipeline: CVE ingestion into ChromaDB, semantic retrieval, reranking
- [ ] **Phase 5** — FastAPI endpoints, SSE streaming, LangSmith tracing, tests

## License

MIT
