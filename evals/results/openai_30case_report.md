# Week 7C OpenAI 30-Case Evaluation Report

## Goal

This evaluation reruns the same 30-case triage dataset using the real OpenAI API.

Week 7B used mock mode to evaluate deterministic workflow structure. Week 7C uses the same dataset with the OpenAI provider to evaluate real LLM behavior, structured output reliability, recommendation quality, fallback behavior, and real API latency.

## OpenAI 30-Case Summary

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
| Error rate | 0.0% | 0.0% |
| Average latency ms | 3930 | 3247 |
| Average tool calls | 0.00 | 3.57 |
| Average execution path length | 2.00 | 6.57 |

## Mock vs OpenAI Comparison

| Mode | Provider | Issue type | Urgency | Escalation | Conditional branch | Avg latency ms | Error rate |
|---|---|---:|---:|---:|---:|---:|---:|
| simple_rag | mock | 96.7% | 40.0% | 56.7% | 43.3% | 0 | 0.0% |
| simple_rag | openai | 96.7% | 76.7% | 73.3% | 43.3% | 3930 | 0.0% |
| agentic_llm | mock | 96.7% | 96.7% | 100.0% | 100.0% | 2 | 0.0% |
| agentic_llm | openai | 96.7% | 96.7% | 100.0% | 100.0% | 3247 | 0.0% |

## Case-Level OpenAI Latency

| Case | simple_rag latency ms | agentic_llm latency ms | agentic escalation | agentic tool calls |
|---|---:|---:|---:|---:|
| `case_001_premium_billing_cancel` | 5025 | 3707 | True | 4 |
| `case_002_standard_billing_low_risk` | 2750 | 4900 | False | 3 |
| `case_003_enterprise_outage` | 4759 | 2611 | True | 4 |
| `case_004_premium_refund_low_risk` | 4633 | 2494 | False | 3 |
| `case_005_standard_refund_low_risk` | 3980 | 2752 | False | 3 |
| `case_006_standard_technical_low_risk` | 2914 | 2920 | False | 3 |
| `case_007_premium_billing_legal_risk` | 5451 | 3229 | True | 4 |
| `case_008_enterprise_billing_dispute` | 2968 | 3947 | True | 4 |
| `case_009_standard_cancellation_risk` | 2675 | 3293 | True | 4 |
| `case_010_premium_outage_low_risk` | 3975 | 3020 | False | 3 |
| `case_011_standard_duplicate_charge` | 3339 | 3787 | False | 3 |
| `case_012_premium_contract_billing_risk` | 3543 | 4938 | True | 4 |
| `case_013_enterprise_tax_invoice_issue` | 2776 | 3395 | True | 4 |
| `case_014_standard_missing_discount` | 5138 | 3083 | False | 3 |
| `case_015_premium_unexpected_renewal_fee` | 3223 | 2585 | True | 4 |
| `case_016_enterprise_full_outage` | 4161 | 2438 | True | 4 |
| `case_017_standard_dashboard_unavailable` | 3049 | 3448 | False | 3 |
| `case_018_premium_service_unavailable` | 3923 | 2212 | False | 3 |
| `case_019_enterprise_outage_multiple_users` | 4168 | 3175 | True | 4 |
| `case_020_standard_partial_outage` | 2963 | 5413 | False | 3 |
| `case_021_premium_refund_contract_risk` | 3808 | 3029 | True | 4 |
| `case_022_enterprise_refund_legal_risk` | 8323 | 3159 | True | 4 |
| `case_023_standard_refund_question` | 3346 | 3360 | False | 3 |
| `case_024_premium_refund_amount` | 3598 | 3650 | False | 3 |
| `case_025_standard_login_locked` | 3367 | 2899 | False | 3 |
| `case_026_premium_password_access` | 5805 | 3175 | True | 4 |
| `case_027_enterprise_access_locked` | 4243 | 3205 | True | 4 |
| `case_028_premium_cancel_subscription` | 3895 | 2458 | True | 4 |
| `case_029_enterprise_terminate_contract` | 3517 | 2695 | True | 4 |
| `case_030_unknown_general_question` | 2586 | 2436 | True | 4 |

## Interpretation

The Week 7C evaluation uses the same 30-case dataset as Week 7B, changing only the provider. This isolates the effect of real LLM behavior and separates two questions:

Does the workflow structure behave correctly under deterministic mock conditions?
Does the same workflow stay reliable when real OpenAI calls are used?
The agentic workflow is stable across providers

The agentic_llm structural metrics — customer tier, escalation, conditional branch, tool dependency — are identical under mock and OpenAI. Real LLM variability did not move them. This is by design: in this project the LLM only generates the recommendation text, while tier lookup, SLA rules, risk assessment, and routing are handled by deterministic code. The evaluation shows that swapping a mock LLM for a real one does not disturb the parts of the workflow that control execution. The case-level table reinforces this — every escalated case calls the ticket tool and every non-escalated case does not, with no exceptions across all 30 cases.

simple_rag improves on judgment metrics, but for the wrong reason

Under OpenAI, simple_rag scores higher on urgency and escalation than under mock. This is because a real LLM reads the issue text and guesses plausibly (e.g. inferring urgency from cancellation language), whereas the mock returns a fixed default. These gains are text-based guesses, not grounded decisions. Customer tier accuracy stays near zero because tier cannot be guessed from text — it requires a database lookup that simple_rag never performs. The improved numbers should therefore not be read as capability; they are confident guessing without access to the underlying data or rules.

Real API latency is the main practical cost

Mock latency is negligible; real OpenAI latency runs into several seconds per case and varies widely with network conditions. This cost is invisible in mock-mode evaluation and is the main trade-off to consider for production deployment.

Summary

The mock-mode evaluation remains the primary evidence for deterministic workflow structure. The OpenAI evaluation complements it by confirming that the same structure holds under real LLM behavior, exposing where a tool-less pipeline only appears to improve, and surfacing real API latency.
