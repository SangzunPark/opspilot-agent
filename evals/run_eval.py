import argparse
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

# evaluation 흐름
# 1. 데이터셋 읽기(dataset.jsonl)
# 2. 각 케이스를 workflow로 실행
# 3. 결과를 정답과 비교해서 점수 측정
# 4. 전체 평균 계산
# 5. 결과를 JSON파일로 저장, 화면 출력

WorkflowMode = Literal["simple_rag", "baseline", "agentic_llm"]

DATASET_PATH = Path("evals/dataset.jsonl")
RESULTS_DIR = Path("evals/results")

# 데이터 읽기
def load_dataset(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                cases.append(json.loads(line))

    return cases

# 케이스 1 건 실행
def run_case(case: dict[str, Any], mode: WorkflowMode) -> dict[str, Any]:
    from app.graph.workflow import run_ops_workflow
    from app.schemas.state import OpsAgentState

    input_payload = case["input"]
    expected = case["expected"]

    initial_state = OpsAgentState(
        request_id=case["case_id"],
        customer_id=input_payload.get("customer_id"),
        issue_text=input_payload["issue_text"],
        channel=input_payload.get("channel", "email"),
    )

    start_time = perf_counter()

    try:
        response = run_ops_workflow(initial_state, mode=mode)
        latency_ms = int((perf_counter() - start_time) * 1000)

        output = response.model_dump(mode="json")
        # 결과에서 tool_names, source_titles 추출
        tool_names = [tool["tool_name"] for tool in output["tools_called"]]
        source_titles = [source["title"] for source in output["retrieved_sources"]]
        execution_path = build_execution_path(
            mode=mode,
            tool_names=tool_names,
        )
        # 점수 계산
        metrics = evaluate_output(
            output=output,
            expected=expected,
            source_titles=source_titles,
            tool_names=tool_names,
            execution_path=execution_path,
        )
        # 결과 담아서 반환
        return {
            "case_id": case["case_id"],
            "mode": mode,
            "input": input_payload,
            "expected": expected,
            "output": output,
            "source_titles": source_titles,
            "tool_names": tool_names,
            "execution_path": execution_path,
            "latency_ms": latency_ms,
            "error": None,
            "metrics": metrics,
        }
    # 에러난 케이스는 모든 지표를 0점으로 처리해서 진행
    except Exception as exc:
        latency_ms = int((perf_counter() - start_time) * 1000)

        return {
            "case_id": case["case_id"],
            "mode": mode,
            "input": input_payload,
            "expected": expected,
            "output": None,
            "source_titles": [],
            "tool_names": [],
            "execution_path": [],
            "latency_ms": latency_ms,
            "error": str(exc),
            "metrics": {
                "schema_valid": 0,
                "issue_type_correct": 0,
                "customer_tier_correct": 0,
                "urgency_correct": 0,
                "escalation_correct": 0,
                "retrieval_hit_rate": 0,
                "required_tool_call_rate": 0,
                "conditional_branch_correct": 0,
                "tool_dependency_valid": 0,
                "execution_path_contains_rate": 0,
                "execution_path_excludes_rate": 0,
            },
        }

# 실행 경로 구성
def build_execution_path(
    mode: WorkflowMode,
    tool_names: list[str],
) -> list[str]:
    if mode == "simple_rag":
        return [
            "retrieve_docs",
            "generate_simple_rag_response",
        ]
    # 7단계 고정
    if mode == "baseline":
        return [
            "classify_issue",
            "retrieve_docs",
            "get_customer_profile",
            "check_sla",
            "assess_risk",
            "create_ticket",
            "generate_response",
        ]
    # 5단계 고정
    path = [
        "classify_issue",
        "retrieve_docs",
        "get_customer_profile",
        "check_sla",
        "assess_risk",
    ]

    if "create_ticket_draft" in tool_names:
        path.append("create_ticket")

    path.append("generate_llm_response")

    return path


def evaluate_output(
    output: dict[str, Any],
    expected: dict[str, Any],
    source_titles: list[str],
    tool_names: list[str],
    execution_path: list[str],
) -> dict[str, float | int]:
    # 이 케이스는 티켓을 생성해야 했나를 기준으로 정답과 결과를 비교해서 스코어링
    # 정답은 jsonl 데이터셋에 미리 생성,머신러닝 라벨링
    expected_create_ticket = expected.get("create_ticket_called")
    actual_create_ticket = "create_ticket_draft" in tool_names

    # 패턴1 정답과 결과가 같은면 1점 틀리면 0점으로 점수 산정
    return {
        "schema_valid": 1,
        "issue_type_correct": int(output["issue_type"] == expected["issue_type"]),
        "customer_tier_correct": int(
            output["customer_tier"] == expected["customer_tier"]
        ),
        "urgency_correct": int(output["urgency"] == expected["urgency"]),
        "escalation_correct": int(
            output["escalation_required"] == expected["escalation_required"]
        ),
    # 패턴 2 비율, 기대한 문서 대비 실제 문서의 비율로 산정
        "retrieval_hit_rate": calculate_match_rate(
            expected_items=expected.get("required_sources", []),
            actual_items=source_titles,
        ),
        "required_tool_call_rate": calculate_match_rate(
            expected_items=expected.get("required_tools", []),
            actual_items=tool_names,
        ),
        # 조건부 분기 작동 부분
        "conditional_branch_correct": int(
            actual_create_ticket == expected_create_ticket
        ),
        "tool_dependency_valid": int(
            # 순서까지 확인
            is_subsequence(
                expected_sequence=expected.get("expected_tool_chain", []),
                actual_sequence=tool_names,
            )
        ),
        "execution_path_contains_rate": calculate_match_rate(
            expected_items=expected_path_contains(expected),
            actual_items=execution_path,
        ),
    # 패턴 3 없어야 할 것들이 실제로 없는 비율
        "execution_path_excludes_rate": calculate_exclusion_rate(
            excluded_items=expected_path_excludes(expected),
            actual_items=execution_path,
        ),
    }


def expected_path_contains(expected: dict[str, Any]) -> list[str]:
    base_path = [
        "classify_issue",
        "retrieve_docs",
        "get_customer_profile",
        "check_sla",
        "assess_risk",
    ]

    if expected.get("create_ticket_called") is True:
        return [*base_path, "create_ticket"]

    return base_path


def expected_path_excludes(expected: dict[str, Any]) -> list[str]:
    if expected.get("create_ticket_called") is False:
        return ["create_ticket"]

    return []


def calculate_match_rate(
    expected_items: list[str],
    actual_items: list[str],
) -> float:
    if not expected_items:
        return 1.0

    matched = sum(1 for item in expected_items if item in actual_items)
    return matched / len(expected_items)


def calculate_exclusion_rate(
    excluded_items: list[str],
    actual_items: list[str],
) -> float:
    if not excluded_items:
        return 1.0

    correctly_excluded = sum(1 for item in excluded_items if item not in actual_items)
    return correctly_excluded / len(excluded_items)


def is_subsequence(
    expected_sequence: list[str],
    actual_sequence: list[str],
) -> bool:
    if not expected_sequence:
        return True

    actual_iterator = iter(actual_sequence)
    return all(
        expected_item in actual_iterator
        for expected_item in expected_sequence
    )

# 전체 평균
def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    metric_names = [
        "schema_valid",
        "issue_type_correct",
        "customer_tier_correct",
        "urgency_correct",
        "escalation_correct",
        "retrieval_hit_rate",
        "required_tool_call_rate",
        "conditional_branch_correct",
        "tool_dependency_valid",
        "execution_path_contains_rate",
        "execution_path_excludes_rate",
    ]

    summary: dict[str, Any] = {
        "total_cases": len(results),
        "error_rate": average(
            [int(result["error"] is not None) for result in results]
        ),
        "average_latency_ms": average(
            [result["latency_ms"] for result in results]
        ),
        "average_tool_call_count": average(
            [len(result["tool_names"]) for result in results]
        ),
        "average_execution_path_length": average(
            [len(result["execution_path"]) for result in results]
        ),
    }

    for metric_name in metric_names:
        summary[metric_name] = average(
            [result["metrics"][metric_name] for result in results]
        )

    return summary


def average(values: list[float | int]) -> float:
    if not values:
        return 0.0

    return sum(values) / len(values)

# 모드별로 결과를 파일로 저장
def save_results(
    mode: WorkflowMode,
    results: list[dict[str, Any]],
    summary: dict[str, Any],
    output_suffix: str | None = None,
) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    suffix = f"_{output_suffix}" if output_suffix else ""
    output_path = RESULTS_DIR / f"{mode}{suffix}_results.json"

    payload = {
        "mode": mode,
        "summary": summary,
        "results": results,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["simple_rag", "baseline", "agentic_llm"],
        required=True,
    )
    parser.add_argument(
        "--llm-provider",
        choices=["mock", "openai"],
        default="mock",
    )
    parser.add_argument(
        "--dataset-path",
        default="evals/dataset.jsonl",
        help="Path to evaluation dataset in JSONL format.",
    )
    parser.add_argument(
        "--output-suffix",
        default=None,
        help="Optional suffix for the output filename.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    os.environ["LLM_PROVIDER"] = args.llm_provider

    dataset_path = Path(args.dataset_path)
    cases = load_dataset(dataset_path)

    results = [
        run_case(case=case, mode=args.mode)
        for case in cases
    ]
    summary = summarize_results(results)
    output_path = save_results(
        mode=args.mode,
        results=results,
        summary=summary,
        output_suffix=args.output_suffix,
    )

    print(f"Saved {args.mode} results to {output_path}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
