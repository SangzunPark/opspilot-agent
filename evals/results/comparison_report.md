# Evaluation Report

## Evaluation Goal

This evaluation compares a standard RAG+LLM approach against deterministic and agentic workflow designs.

The main comparison is between:

- `simple_rag`: retrieves policy context and generates a structured response.
- `agentic_llm`: uses LangGraph, typed tools, workflow state, conditional routing, and LLM-based recommendation generation.

The key question is not simply whether the system can access more data. The key question is whether the system can represent multi-step dependent execution, where one step's output controls later actions.

## Summary Metrics

| Metric | simple_rag | baseline | agentic_llm |
|---|---:|---:|---:|
| Schema validity | 100.0% | 100.0% | 100.0% |
| Issue type accuracy | 90.0% | 100.0% | 100.0% |
| Customer tier accuracy | 0.0% | 100.0% | 100.0% |
| Urgency accuracy | 40.0% | 100.0% | 100.0% |
| Escalation accuracy | 80.0% | 100.0% | 100.0% |
| Retrieval hit rate | 100.0% | 100.0% | 100.0% |
| Required tool call rate | 0.0% | 100.0% | 100.0% |
| Conditional branch accuracy | 50.0% | 50.0% | 100.0% |
| Tool dependency validity | 0.0% | 100.0% | 100.0% |
| Execution path contains rate | 18.3% | 100.0% | 100.0% |
| Execution path excludes rate | 100.0% | 50.0% | 100.0% |
| Avg. tool calls | 0.00 | 4.00 | 3.50 |
| Avg. execution path length | 2.00 | 7.00 | 6.50 |
| Avg. latency ms | 1 | 4 | 2 |
| Error rate | 0.0% | 0.0% | 0.0% |

## Structural Interpretation

A standard RAG+LLM pipeline can retrieve relevant policy documents, but it does not naturally represent tool dependency chains or conditional execution paths.

The `agentic_llm` workflow maintains intermediate state and uses previous step outputs to control later steps. In this project, customer lookup, SLA checking, risk assessment, and ticket draft creation form a dependency chain.

Ticket creation is conditionally triggered only when `escalation_required=true`.

## Notable Conditional Branch Cases

- `case_001_premium_billing_cancel`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_003_enterprise_outage`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_007_premium_billing_legal_risk`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_008_enterprise_billing_dispute`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_009_standard_cancellation_risk`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].

## Main Takeaway

The difference between simple RAG and the agentic workflow is not merely data access.

The stronger distinction is execution structure:

- `simple_rag` follows a retrieve-and-generate pattern.
- `agentic_llm` passes intermediate state across steps, calls tools in sequence, and changes the execution path based on previous results.

This makes the agentic workflow more suitable for business processes where decisions depend on customer context, SLA rules, risk assessment, and conditional follow-up actions.
