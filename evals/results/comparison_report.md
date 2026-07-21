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
| Avg. tool calls | 0.00 | 4.00 | 3.57 |
| Avg. execution path length | 2.00 | 7.00 | 6.57 |
| Avg. latency ms | 0 | 2 | 2 |
| Error rate | 0.0% | 0.0% | 0.0% |

## Structural Interpretation

A standard RAG+LLM pipeline can retrieve relevant policy documents, but it does not naturally represent tool dependency chains or conditional execution paths.

The `agentic_llm` workflow maintains intermediate state and uses previous step outputs to control later steps. In this project, customer lookup, SLA checking, risk assessment, and ticket draft creation form a dependency chain.

The baseline workflow uses the same tools but runs them unconditionally, so it always executes every step regardless of the case. It cannot skip actions that a given case does not require. The agentic workflow differs precisely in its conditional routing: it changes the execution path based on intermediate results rather than always following the full sequence.

Ticket creation is conditionally triggered only when `escalation_required=true`.

## Notable Conditional Branch Cases

- `case_001_premium_billing_cancel`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_003_enterprise_outage`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_007_premium_billing_legal_risk`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_008_enterprise_billing_dispute`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_009_standard_cancellation_risk`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_012_premium_contract_billing_risk`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_013_enterprise_tax_invoice_issue`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_015_premium_unexpected_renewal_fee`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_016_enterprise_full_outage`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_019_enterprise_outage_multiple_users`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_021_premium_refund_contract_risk`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_022_enterprise_refund_legal_risk`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_026_premium_password_access`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_027_enterprise_access_locked`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_028_premium_cancel_subscription`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_029_enterprise_terminate_contract`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].
- `case_030_unknown_general_question`: `simple_rag` did not match the expected conditional branch, while `agentic_llm` did. simple_rag tools=[], agentic_llm tools=['search_internal_docs', 'get_customer_profile', 'check_sla_policy', 'create_ticket_draft'].

## Main Takeaway

The difference between simple RAG and the agentic workflow is not merely data access.

The stronger distinction is execution structure:

- `simple_rag` follows a retrieve-and-generate pattern.
- `agentic_llm` passes intermediate state across steps, calls tools in sequence, and changes the execution path based on previous results.

This makes the agentic workflow more suitable for business processes where decisions depend on customer context, SLA rules, risk assessment, and conditional follow-up actions.
