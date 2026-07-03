# OpsPilot: Agentic Operations Assistant

OpsPilot is a production-style agentic AI assistant for internal operations issue triage.

The system receives an operational issue, classifies the issue type, retrieves relevant internal policies, calls tools such as customer profile lookup and SLA checking, assesses urgency and escalation risk, and returns a structured next-step recommendation.

## Current Status

Week 0: Project setup and FastAPI health check.
Week 1: Domain design, issue type definitions, and Pydantic schemas.
Week 2: Business tool layer — customer profile lookup, SLA policy check, document search, and ticket draft generation.
Week 3: RAG retrieval layer — document chunking and TF-IDF based search.

## Tech Stack

- Python
- FastAPI
- Pydantic
- LangGraph
- RAG
- Docker
- pytest

## Planned Workflow

User issue input  
→ issue classification  
→ internal document retrieval  
→ customer profile lookup  
→ SLA policy check  
→ risk and escalation assessment  
→ structured recommendation  

## Local Development

```bash
uv run uvicorn app.main:app --reload

## Problem

Internal operations teams often receive messy customer or business issue reports through email, support tools, or chat messages.

These reports may include billing disputes, refund requests, service outages, account access problems, or cancellation risks. A human operator usually needs to read the message, identify the issue type, check customer information, review internal policies, decide urgency, and determine whether escalation is required.

OpsPilot is designed to support this workflow by turning an unstructured operations issue into a structured triage result.

## Initial Scope

The first version focuses on five issue types:

- billing_dispute
- technical_outage
- refund_request
- account_access
- cancellation_risk

The system will classify the issue, retrieve relevant internal policy documents, call business tools, assess urgency, and return a structured recommendation.

## Business Context

OpsPilot simulates a B2B SaaS company serving standard, premium, and enterprise customers.

Customer tier matters because premium and enterprise customers may have stricter SLA requirements and higher escalation priority.

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