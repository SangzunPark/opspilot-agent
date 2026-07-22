# OpsPilot: Agentic Operations Assistant

OpsPilot is a production-style agentic AI assistant for internal operations issue triage.

The system receives an operational issue, classifies the issue type, retrieves relevant internal policies, calls tools such as customer profile lookup and SLA checking, assesses urgency and escalation risk, and returns a structured next-step recommendation.

## Tech Stack

- Python
- FastAPI
- Pydantic
- LangGraph
- RAG
- Docker
- pytest

## Problem

Internal operations teams often receive messy customer or business issue reports through email, support tools, or chat messages.

These reports may include billing disputes, refund requests, service outages, account access problems, or cancellation risks. A human operator usually needs to read the message, identify the issue type, check customer information, review internal policies, decide urgency, and determine whether escalation is required.

OpsPilot is designed to support this workflow by turning an unstructured operations issue into a structured triage result.

## Why this is more than basic RAG

The main difference is not data access — any pipeline can add a database lookup. The difference is **execution structure**.

A standard RAG+LLM pipeline retrieves relevant context and generates a response. This works well for question answering, but it cannot naturally represent tool dependency chains, intermediate state, and conditional execution.

In this project, the agentic workflow uses customer-lookup results, SLA checks, and risk assessment to decide whether a ticket draft should be created. One step's output becomes part of the workflow state and controls later actions — for example, a ticket is created only when risk assessment marks the case as requiring escalation.

## Business Context

OpsPilot simulates a B2B SaaS company serving standard, premium, and enterprise customers.

Customer tier matters because premium and enterprise customers may have stricter SLA requirements and higher escalation priority.

## Initial Scope

The first version focuses on five issue types:

- billing_dispute
- technical_outage
- refund_request
- account_access
- cancellation_risk

The system will classify the issue, retrieve relevant internal policy documents, call business tools, assess urgency, and return a structured recommendation.

---

## System Architecture

```text
User request
  ↓
FastAPI  /triage?mode=...
  ↓
Workflow router
  ├── simple_rag
  │     └── retrieve_docs → generate_simple_rag_response
  │
  ├── baseline
  │     └── deterministic LangGraph workflow (all steps, unconditional)
  │
  └── agentic_llm
        └── classify_issue
            → retrieve_docs
            → get_customer_profile
            → check_sla
            → assess_risk
               ├── escalation_required = true
               │     → create_ticket → generate_llm_response
               └── escalation_required = false
                     → generate_llm_response
  ↓
Structured TriageResponse
  ↓
Run log  /  evaluation results
```

---


## Business Tools

OpsPilot includes four typed business tools that the agent can call during triage:

- `get_customer_profile` — looks up customer tier and account status from internal records
- `check_sla_policy` — returns response time and escalation guidance based on customer tier and issue type
- `search_internal_docs` — retrieves relevant internal policy documents for the issue
- `create_ticket_draft` — generates a structured ticket draft with assigned team and urgency level

All tool outputs are validated with Pydantic models to ensure predictable, typed results.

Business rules such as SLA response times and escalation conditions are implemented directly in code rather than delegated to the LLM. This makes the system more reliable and easier to test.

## Retrieval Design

OpsPilot includes a retrieval layer for searching internal operations policy documents.

In the current MVP, documents are loaded from `data/internal_docs`, split into text chunks, indexed with a TF-IDF retriever, and searched using cosine similarity.

The retrieval tool returns structured results with document title, relevant snippet, and relevance score.

This design keeps the retrieval interface simple while allowing the backend to be upgraded later to embedding-based search with Chroma, pgvector, or another vector database.

Current retrieval flow:

1. Load markdown policy documents
2. Split documents into chunks
3. Build a TF-IDF index
4. Search relevant chunks for an issue query
5. Return top-k document snippets to the agent workflow

## Workflow Modes

OpsPilot supports three workflow modes accessible via `POST /triage?mode=`.

### `simple_rag`

Retrieves relevant internal policy documents using TF-IDF search and passes
them to the LLM along with the issue text. The LLM handles the full triage
decision including issue classification, urgency assessment, and recommendation
generation.

This mode does **not** use customer profile tools or SLA policy tools.
As a result, `customer_tier` is always `unknown` and `tools_called` is always
empty. This means escalation decisions may be incorrect when customer tier
matters.

### `baseline`

The deterministic Week 4 workflow. Uses LangGraph, typed tools, RAG retrieval,
SLA rules, and rule-based recommendation generation. No LLM involved.
Customer tier and urgency are verified through actual tools.

### `agentic_llm`

The full agentic workflow. Keeps customer lookup, SLA checks, retrieval,
risk assessment, and ticket routing deterministic. Uses an LLM only for
structured recommendation generation.

The LLM receives verified customer tier, SLA results, retrieved policy
documents, and tool call summaries as context — then generates grounded
recommendations with specific next steps.

Key difference from `simple_rag`:

| | simple_rag | agentic_llm |
|---|---|---|
| customer_tier | always unknown | verified via lookup tool |
| urgency | LLM estimate | SLA rule applied |
| escalation | may be incorrect | deterministic rule |
| tools_called | [] | 4 tools |

The evaluation compares `simple_rag` vs `agentic_llm` on the same dataset
to measure the real-world impact of tool-augmented agentic design.

## Conditional Execution

The `agentic_llm` mode uses conditional routing after risk assessment. This is what distinguishes it from a linear pipeline: the execution path depends on intermediate results.

```text
assess_risk
├── escalation_required = true  → create_ticket → generate_llm_response
└── escalation_required = false → generate_llm_response
```

A premium customer with cancellation risk triggers ticket creation; a standard customer with a low-risk billing question skips it. The same issue type can take a different execution path depending on customer context and risk signals.

## Observability and Run Logging

OpsPilot records each triage execution as a JSONL run log, giving every request
an end-to-end trace that can be retrieved later for debugging and evaluation.

Each run captures:

- **run ID** — unique identifier for the execution
- **workflow mode** — `simple_rag`, `baseline`, or `agentic_llm`
- **input payload** — the original triage request
- **workflow steps** — the high-level stages that were executed
- **retrieved sources** — internal policy documents used as evidence
- **tool calls** — which tools ran, with inputs and output summaries
- **llm_used** — whether the mode invoked an LLM
- **fallback_used** — whether deterministic fallback was triggered
- **latency_ms** — end-to-end latency in milliseconds
- **final_response** — the full response returned to the user
- **errors** — any errors captured during the run

**Example response (`POST /triage`):**

```json
{
  "run_id": "d8691cac-cd28-4270-9cbf-20da5d270566",
  "mode": "agentic_llm",
  "latency_ms": 8,
  "issue_type": "billing_dispute",
  "customer_tier": "premium",
  "escalation_required": true
}
```

**Retrieve a run log:**

```
GET /runs/{run_id}
```

Logs are stored locally at:

```
logs/runs.jsonl
```

This logging layer is intentionally simple and file-based for the MVP.
It can later be replaced with PostgreSQL, OpenTelemetry, or LangSmith
without changing the workflow code.

## Evaluation

The project includes an evaluation harness that scores all three modes on the same dataset and compares them across accuracy **and** structural metrics (tool dependency chains, conditional branching, execution paths). The evaluation was built up in three stages.

### Preliminary Evaluation Results

I first ran a 10-case synthetic evaluation to validate the comparison framework.(Mock Mode)

The `simple_rag` mode achieved a 100% retrieval hit rate, showing that it could retrieve relevant policy documents. However, it had no tool calls, no valid tool dependency chain, and only 50% conditional branch accuracy.

The `agentic_llm` mode achieved 100% accuracy across customer tier, urgency, escalation decision, required tool calls, tool dependency validity, and conditional branch accuracy in this preliminary evaluation.

This supports the main design point: the difference is not simply data access or retrieval quality. The agentic workflow maintains intermediate state, passes tool outputs into later steps, and changes the execution path based on previous results.

Latency was measured in mock mode and does not represent real LLM API latency.

### Full Mock-Mode Evaluation

After validating the evaluation pipeline with the initial 10-case preliminary evaluation, I expanded the dataset to 30 synthetic operations triage cases. The expanded dataset covers billing disputes, technical outages, refund requests, account access issues, cancellation risk, and ambiguous requests across standard, premium, enterprise, and unknown customer contexts.

The evaluation was run in mock mode to make the comparison deterministic, reproducible, and focused on workflow structure rather than LLM text variability.

| Metric | simple_rag | baseline | agentic_llm |
|---|---:|---:|---:|
| Schema validity | 100.0% | 100.0% | 100.0% |
| Issue type accuracy | 96.7% | 96.7% | 96.7% |
| Customer tier accuracy | 3.3% | 100.0% | 100.0% |
| Urgency accuracy | 40.0% | 96.7% | 96.7% |
| Escalation accuracy | 56.7% | 100.0% | 100.0% |
| Retrieval hit rate | 98.3% | 98.3% | 98.3% |
| Required tool call rate | 0.0% | 100.0% | 100.0% |
| Conditional branch accuracy | 43.3% | 56.7% | 100.0% |
| Tool dependency validity | 0.0% | 100.0% | 100.0% |
| Execution path contains rate | 18.1% | 100.0% | 100.0% |
| Execution path excludes rate | 100.0% | 56.7% | 100.0% |
| Average tool calls | 0.00 | 4.00 | 3.57 |
| Average execution path length | 2.00 | 7.00 | 6.57 |
| Error rate | 0.0% | 0.0% | 0.0% |

The results show that `simple_rag` retrieved relevant policy documents in most cases, with a 98.3% retrieval hit rate. However, it had no tool calls, no valid tool dependency chain, and limited conditional branch accuracy.

The `baseline` workflow used the expected tools and achieved strong output accuracy, but it followed the full workflow path unconditionally. As a result, it could not reliably skip unnecessary actions such as ticket draft creation in low-risk cases.

The `agentic_llm` workflow achieved 100% customer tier accuracy, 100% escalation accuracy, 100% required tool call rate, 100% conditional branch accuracy, and 100% tool dependency validity in the 30-case mock-mode evaluation.

These results support the main design point of the project: the difference between standard RAG+LLM and an agentic workflow is not simply retrieval quality or data access. The agentic workflow maintains intermediate state, uses tool outputs in later decisions, and changes the execution path based on previous results.

Latency was measured in mock mode and does not represent real LLM API latency.

### Real OpenAI Evaluation on the Same 30-Case Dataset

After completing the 30-case mock-mode structural evaluation, I reran the same 30-case dataset using the real OpenAI API for `simple_rag` and `agentic_llm`.

The goal was to complement the deterministic mock-mode evaluation with real LLM behavior, including structured output reliability, recommendation quality, fallback behavior, and real API latency.

| Metric | simple_rag OpenAI | agentic_llm OpenAI |
|---|---:|---:|
| Schema validity | 100.0% | 100.0% |
| Issue type accuracy | 96.7% | 96.7% |
| Customer tier accuracy | 3.3% | 100.0% |
| Urgency accuracy | 76.7% | 96.7% |
| Escalation accuracy | 73.3% | 100.0% |
| Retrieval hit rate | 98.3% | 98.3% |
| Required tool call rate | 0.0% | 100.0% |
| Conditional branch accuracy | 43.3% | 100.0% |
| Tool dependency validity | 0.0% | 100.0% |
| Execution path contains rate | 18.1% | 100.0% |
| Execution path excludes rate | 100.0% | 100.0% |
| Average tool calls | 0.00 | 3.57 |
| Average execution path length | 2.00 | 6.57 |
| Average latency ms | 3930 | 3247 |
| Error rate | 0.0% | 0.0% |

**What the numbers show:**

- **Execution structure differs, not just data access.** `simple_rag` scores 0% on required tool calls and tool-dependency validity — it retrieves documents but represents no tool chain. `agentic_llm` scores 100% on both.

- **The agentic workflow is stable across providers.** Its structural metrics (customer tier, escalation, conditional branch) are identical under mock and real OpenAI. This is by design: the LLM only generates recommendation text, while tier, SLA, escalation, and routing are handled by deterministic code — so real LLM variability does not disturb the parts of the workflow that control execution.

- **`simple_rag`'s higher judgment scores are guesses, not capability.** Under OpenAI it improves on urgency and escalation because a real LLM infers plausibly from the issue text. But customer-tier accuracy stays at 3.3% because tier cannot be guessed from text — it requires a lookup `simple_rag` never performs. (The one tier "hit" is the case whose correct answer is `unknown`.)

- **Real API latency is the main practical cost.** Mock latency is negligible; real OpenAI latency runs to several seconds per case and varies with network conditions. Most of it comes from the OpenAI call rather than local workflow steps — the extra tool calls in `agentic_llm` did not add a latency penalty.

Overall: real LLM reasoning can improve a retrieve-and-generate baseline, but an agentic workflow is still needed when the task requires verified tool outputs, stateful decision-making, and conditional follow-up actions.

---

## How to Run

```bash
uv sync                                              # install dependencies
PYTHONPATH=. uv run pytest                           # run tests
PYTHONPATH=. uv run uvicorn app.main:app --reload    # start the API
curl http://localhost:8000/health                    # health check
```

---

## Example API Request

```bash
curl -X POST "http://localhost:8000/triage?mode=agentic_llm" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-1001",
    "issue_text": "Customer says the invoice amount is wrong and may cancel.",
    "channel": "email"
  }'
```

Example response fields:

```json
{
  "issue_type": "billing_dispute",
  "urgency": "high",
  "customer_tier": "premium",
  "escalation_required": true,
  "tools_called": [
    { "tool_name": "search_internal_docs" },
    { "tool_name": "get_customer_profile" },
    { "tool_name": "check_sla_policy" },
    { "tool_name": "create_ticket_draft" }
  ],
  "run_id": "…",
  "mode": "agentic_llm",
  "latency_ms": 8
}
```

---

## Docker

```bash
docker compose build
docker compose up
curl http://localhost:8000/health
```

The `.env` file is not baked into the image; it is injected at runtime via `env_file`, and run logs are persisted outside the container through a volume mount.

---

## Project Structure

```text
app/
  core/           configuration and settings
  graph/          LangGraph workflow definitions and nodes
  rag/            document loading, chunking, and TF-IDF retrieval
  schemas/        Pydantic request, response, state, and evaluation schemas
  services/       LLM service, simple RAG service, and run logging
  tools/          typed tools for customer, SLA, ticket, and retrieval actions
  main.py         FastAPI application entry point

data/
  internal_docs/       internal policy documents (markdown)
  mock_customers.json  mock customer database

evals/
  dataset.jsonl               30-case evaluation dataset
  dataset_10case_smoke.jsonl  10-case smoke dataset
  run_eval.py                 per-mode evaluation runner
  compare_results.py          mock-mode comparison report
  compare_openai_30case.py    mock vs OpenAI comparison report
  results/                    generated result files and reports

logs/
  runs.jsonl           run logs (gitignored)
```

---

## Limitations

- The evaluation dataset is synthetic and designed for portfolio demonstration.
- The customer database is a static mock JSON file.
- Retrieval uses TF-IDF for simplicity and reproducibility rather than embedding-based vector search.
- Real OpenAI latency varies with network conditions and model response behavior.
- The tool-dependency metric checks expected tool order but does not fully validate every intermediate tool input and output.

---

## Future Improvements

- Replace TF-IDF retrieval with embedding-based vector search.
- Store customer profiles, tickets, and run logs in a database such as PostgreSQL.
- Add authentication and role-based access control.
- Add OpenTelemetry or LangSmith tracing for deeper observability.
- Extend dependency validation to full tool input/output chains.
- Expand the evaluation dataset with more realistic historical support tickets.
- Add a lightweight frontend for reviewing triage results and traces.

---

## Current Status

- **Week 0** — Project setup: FastAPI structure, health check, pytest, repo config.
- **Week 1** — Domain schema design: typed request, response, issue category, urgency, tier, channel, and policy schemas.
- **Week 2** — Business tool layer: typed tools for customer lookup, SLA checks, document search, and ticket drafting.
- **Week 3** — RAG retrieval: document loading, chunking, and TF-IDF-based policy retrieval.
- **Week 4** — LangGraph workflow MVP: end-to-end deterministic triage workflow.
- **Week 5** — LLM integration: `simple_rag`, `baseline`, and `agentic_llm` modes through one endpoint.
- **Week 6** — Observability and deployment: run-level JSONL logging, `GET /runs/{run_id}`, latency tracking, Docker.
- **Week 6.5** — Conditional routing: ticket creation triggered only when `escalation_required=true`.
- **Week 7** — Evaluation framework: from a 10-case smoke test to a 30-case dataset, run in both mock mode and real OpenAI, confirming the agentic workflow preserves its structural advantages across providers.
- **Week 8** — Portfolio polish: README, project structure, evaluation summaries, limitations, and future improvements.