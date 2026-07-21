import json
from pathlib import Path
from typing import Any
# 세 모드의 채점결과를 읽어서 비교표와 해설이 담긴 마크다운 리포트를 자동 생성

RESULTS_DIR = Path("evals/results")
REPORT_PATH = RESULTS_DIR / "comparison_report.md"

MODES = [
    "simple_rag",
    "baseline",
    "agentic_llm",
]
# 각 항목은 코드용키(실제키/사람이 읽는 키(라벨))
METRICS = [
    ("schema_valid", "Schema validity"),
    ("issue_type_correct", "Issue type accuracy"),
    ("customer_tier_correct", "Customer tier accuracy"),
    ("urgency_correct", "Urgency accuracy"),
    ("escalation_correct", "Escalation accuracy"),
    ("retrieval_hit_rate", "Retrieval hit rate"),
    ("required_tool_call_rate", "Required tool call rate"),
    ("conditional_branch_correct", "Conditional branch accuracy"),
    ("tool_dependency_valid", "Tool dependency validity"),
    ("execution_path_contains_rate", "Execution path contains rate"),
    ("execution_path_excludes_rate", "Execution path excludes rate"),
    ("average_tool_call_count", "Avg. tool calls"),
    ("average_execution_path_length", "Avg. execution path length"),
    ("average_latency_ms", "Avg. latency ms"),
    ("error_rate", "Error rate"),
]

# 결과 파일 읽기
def load_result(mode: str) -> dict[str, Any]:
    path = RESULTS_DIR / f"{mode}_results.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Missing result file: {path}. Run eval for {mode} first."
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)

# 숫자 전처리
def format_value(metric_key: str, value: float) -> str:
    if metric_key in {
        "average_tool_call_count",
        "average_execution_path_length",
    }:
        return f"{value:.2f}"

    if metric_key == "average_latency_ms":
        return f"{value:.0f}"

    return f"{value * 100:.1f}%"

# 비교표 만들기(마크다운)
def build_metric_table(results_by_mode: dict[str, dict[str, Any]]) -> str:
    lines = [
        "| Metric | simple_rag | baseline | agentic_llm |",
        "|---|---:|---:|---:|",
    ]

    for metric_key, metric_label in METRICS:
        values = []
        for mode in MODES:
            value = results_by_mode[mode]["summary"][metric_key]
            values.append(format_value(metric_key, value))

        lines.append(
            f"| {metric_label} | {values[0]} | {values[1]} | {values[2]} |"
        )

    return "\n".join(lines)

# 눈에 띄는 케이스 찾기, 어떤 케이스에서 agentic이 simple_rag을 앞섰나 확인
def find_notable_cases(
    simple_rag_results: list[dict[str, Any]],
    agentic_results: list[dict[str, Any]],
) -> list[str]:
    simple_by_case = {
        result["case_id"]: result
        for result in simple_rag_results
    }
    agentic_by_case = {
        result["case_id"]: result
        for result in agentic_results
    }

    notable_cases: list[str] = []

    for case_id, simple_result in simple_by_case.items():
        agentic_result = agentic_by_case[case_id]

        simple_branch = simple_result["metrics"]["conditional_branch_correct"]
        agentic_branch = agentic_result["metrics"]["conditional_branch_correct"]

        simple_tools = simple_result["tool_names"]
        agentic_tools = agentic_result["tool_names"]

        if simple_branch < agentic_branch:
            notable_cases.append(
                f"- `{case_id}`: `simple_rag` did not match the expected "
                f"conditional branch, while `agentic_llm` did. "
                f"simple_rag tools={simple_tools}, agentic_llm tools={agentic_tools}."
            )

    return notable_cases

# 리포트 전체 조립
def build_report(results_by_mode: dict[str, dict[str, Any]]) -> str:
    metric_table = build_metric_table(results_by_mode)

    notable_cases = find_notable_cases(
        simple_rag_results=results_by_mode["simple_rag"]["results"],
        agentic_results=results_by_mode["agentic_llm"]["results"],
    )

    notable_section = "\n".join(notable_cases) if notable_cases else (
        "- No notable branch differences found."
    )

    return f"""# Evaluation Report

## Evaluation Goal

This evaluation compares a standard RAG+LLM approach against deterministic and agentic workflow designs.

The main comparison is between:

- `simple_rag`: retrieves policy context and generates a structured response.
- `agentic_llm`: uses LangGraph, typed tools, workflow state, conditional routing, and LLM-based recommendation generation.

The key question is not simply whether the system can access more data. The key question is whether the system can represent multi-step dependent execution, where one step's output controls later actions.

## Summary Metrics

{metric_table}

## Structural Interpretation

A standard RAG+LLM pipeline can retrieve relevant policy documents, but it does not naturally represent tool dependency chains or conditional execution paths.

The `agentic_llm` workflow maintains intermediate state and uses previous step outputs to control later steps. In this project, customer lookup, SLA checking, risk assessment, and ticket draft creation form a dependency chain.

The baseline workflow uses the same tools but runs them unconditionally, so it always executes every step regardless of the case. It cannot skip actions that a given case does not require. The agentic workflow differs precisely in its conditional routing: it changes the execution path based on intermediate results rather than always following the full sequence.

Ticket creation is conditionally triggered only when `escalation_required=true`.

## Notable Conditional Branch Cases

{notable_section}

## Main Takeaway

The difference between simple RAG and the agentic workflow is not merely data access.

The stronger distinction is execution structure:

- `simple_rag` follows a retrieve-and-generate pattern.
- `agentic_llm` passes intermediate state across steps, calls tools in sequence, and changes the execution path based on previous results.

This makes the agentic workflow more suitable for business processes where decisions depend on customer context, SLA rules, risk assessment, and conditional follow-up actions.
"""

# 실행 함수
def main() -> None:
    results_by_mode = {
        mode: load_result(mode)
        for mode in MODES
    }

    report = build_report(results_by_mode)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"Saved comparison report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
