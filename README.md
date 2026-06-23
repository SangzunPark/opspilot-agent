# OpsPilot: Agentic Operations Assistant

OpsPilot is a production-style agentic AI assistant for internal operations issue triage.

The system receives an operational issue, classifies the issue type, retrieves relevant internal policies, calls tools such as customer profile lookup and SLA checking, assesses urgency and escalation risk, and returns a structured next-step recommendation.

## Current Status

Week 0: Project setup and FastAPI health check.

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