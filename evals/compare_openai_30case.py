import json
from pathlib import Path
from typing import Any


RESULTS_DIR = Path("evals/results")

MOCK_SIMPLE_PATH = RESULTS_DIR / "simple_rag_results.json"
MOCK_AGENTIC_PATH = RESULTS_DIR / "agentic_llm_results.json"

OPENAI_SIMPLE_PATH = RESULTS_DIR / "simple_rag_openai_30case_results.json"
OPENAI_AGENTIC_PATH = RESULTS_DIR / "agentic_llm_openai_30case_results.json"

REPORT_PATH = RESULTS_DIR / "openai_30case_report.md"


SUMMARY_METRICS = [
    ("Schema validity", "schema_valid"),
    ("Issue type accuracy", "issue_type_correct"),
    ("Customer tier accuracy", "customer_tier_correct"),
    ("Urgency accuracy", "urgency_correct"),
    ("Escalation accuracy", "escalation_correct"),
    ("Retrieval hit rate", "retrieval_hit_rate"),
    ("Required tool call rate", "required_tool_call_rate"),
    ("Conditional branch accuracy", "conditional_branch_correct"),
    ("Tool dependency validity", "tool_dependency_valid"),
    ("Execution path contains rate", "execution_path_contains_rate"),
    ("Execution path excludes rate", "execution_path_excludes_rate"),
    ("Error rate", "error_rate"),
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing result file: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def format_number(value: float) -> str:
    return f"{value:.2f}"


def build_openai_summary_table(
    simple_summary: dict[str, Any],
    agentic_summary: dict[str, Any],
) -> str:
    lines = [
        "| Metric | simple_rag OpenAI | agentic_llm OpenAI |",
        "|---|---:|---:|",
    ]

    for label, key in SUMMARY_METRICS:
        lines.append(
            f"| {label} | {format_percent(simple_summary[key])} | "
            f"{format_percent(agentic_summary[key])} |"
        )

    lines.append(
        f"| Average latency ms | {simple_summary['average_latency_ms']:.0f} | "
        f"{agentic_summary['average_latency_ms']:.0f} |"
    )
    lines.append(
        f"| Average tool calls | {format_number(simple_summary['average_tool_call_count'])} | "
        f"{format_number(agentic_summary['average_tool_call_count'])} |"
    )
    lines.append(
        f"| Average execution path length | {format_number(simple_summary['average_execution_path_length'])} | "
        f"{format_number(agentic_summary['average_execution_path_length'])} |"
    )

    return "\n".join(lines)


def build_mock_vs_openai_table(
    mock_simple: dict[str, Any],
    mock_agentic: dict[str, Any],
    openai_simple: dict[str, Any],
    openai_agentic: dict[str, Any],
) -> str:
    rows = [
        ("simple_rag", mock_simple["summary"], openai_simple["summary"]),
        ("agentic_llm", mock_agentic["summary"], openai_agentic["summary"]),
    ]

    lines = [
        "| Mode | Provider | Issue type | Urgency | Escalation | Conditional branch | Avg latency ms | Error rate |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for mode, mock_summary, openai_summary in rows:
        lines.append(
            f"| {mode} | mock | "
            f"{format_percent(mock_summary['issue_type_correct'])} | "
            f"{format_percent(mock_summary['urgency_correct'])} | "
            f"{format_percent(mock_summary['escalation_correct'])} | "
            f"{format_percent(mock_summary['conditional_branch_correct'])} | "
            f"{mock_summary['average_latency_ms']:.0f} | "
            f"{format_percent(mock_summary['error_rate'])} |"
        )
        lines.append(
            f"| {mode} | openai | "
            f"{format_percent(openai_summary['issue_type_correct'])} | "
            f"{format_percent(openai_summary['urgency_correct'])} | "
            f"{format_percent(openai_summary['escalation_correct'])} | "
            f"{format_percent(openai_summary['conditional_branch_correct'])} | "
            f"{openai_summary['average_latency_ms']:.0f} | "
            f"{format_percent(openai_summary['error_rate'])} |"
        )

    return "\n".join(lines)


def build_case_latency_table(
    simple_results: list[dict[str, Any]],
    agentic_results: list[dict[str, Any]],
) -> str:
    simple_by_case = {
        result["case_id"]: result
        for result in simple_results
    }

    lines = [
        "| Case | simple_rag latency ms | agentic_llm latency ms | agentic escalation | agentic tool calls |",
        "|---|---:|---:|---:|---:|",
    ]

    for agentic_result in agentic_results:
        case_id = agentic_result["case_id"]
        simple_result = simple_by_case[case_id]
        output = agentic_result.get("output") or {}

        lines.append(
            f"| `{case_id}` | "
            f"{simple_result['latency_ms']} | "
            f"{agentic_result['latency_ms']} | "
            f"{output.get('escalation_required')} | "
            f"{len(agentic_result.get('tool_names', []))} |"
        )

    return "\n".join(lines)


def build_report(
    mock_simple: dict[str, Any],
    mock_agentic: dict[str, Any],
    openai_simple: dict[str, Any],
    openai_agentic: dict[str, Any],
) -> str:
    openai_summary_table = build_openai_summary_table(
        simple_summary=openai_simple["summary"],
        agentic_summary=openai_agentic["summary"],
    )

    mock_vs_openai_table = build_mock_vs_openai_table(
        mock_simple=mock_simple,
        mock_agentic=mock_agentic,
        openai_simple=openai_simple,
        openai_agentic=openai_agentic,
    )

    case_latency_table = build_case_latency_table(
        simple_results=openai_simple["results"],
        agentic_results=openai_agentic["results"],
    )

    return f"""# Week 7C OpenAI 30-Case Evaluation Report

## Goal

This evaluation reruns the same 30-case triage dataset using the real OpenAI API.

Week 7B used mock mode to evaluate deterministic workflow structure. Week 7C uses the same dataset with the OpenAI provider to evaluate real LLM behavior, structured output reliability, recommendation quality, fallback behavior, and real API latency.

## OpenAI 30-Case Summary

{openai_summary_table}

## Mock vs OpenAI Comparison

{mock_vs_openai_table}

## Case-Level OpenAI Latency

{case_latency_table}

## Interpretation

The Week 7C evaluation uses the same 30-case dataset as Week 7B. This keeps the comparison consistent and separates two questions:

1. Does the workflow structure behave correctly under deterministic mock conditions?
2. Does the same workflow remain reliable when real OpenAI calls are used?

The mock-mode evaluation remains the primary evidence for deterministic workflow structure. The OpenAI evaluation complements it by checking real LLM behavior, structured output reliability, and latency.
"""


def main() -> None:
    mock_simple = load_json(MOCK_SIMPLE_PATH)
    mock_agentic = load_json(MOCK_AGENTIC_PATH)
    openai_simple = load_json(OPENAI_SIMPLE_PATH)
    openai_agentic = load_json(OPENAI_AGENTIC_PATH)

    report = build_report(
        mock_simple=mock_simple,
        mock_agentic=mock_agentic,
        openai_simple=openai_simple,
        openai_agentic=openai_agentic,
    )

    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Saved OpenAI 30-case report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
