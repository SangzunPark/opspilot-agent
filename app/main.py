from datetime import UTC, datetime
from time import perf_counter
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query

from app.graph.workflow import run_ops_workflow
from app.schemas.api import TriageAPIResponse
from app.schemas.requests import IssueTriageRequest
from app.schemas.responses import TriageResponse
from app.schemas.run_logs import RunLog
from app.schemas.state import OpsAgentState
from app.services.run_logger import append_run_log, get_run_log

app = FastAPI(
    title="OpsPilot Agent",
    description="Agentic AI assistant for operations issue triage",
    version="0.1.0",
)


WorkflowMode = Literal["simple_rag", "baseline", "agentic_llm"]


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageAPIResponse)
def triage_issue(
    request: IssueTriageRequest,
    mode: WorkflowMode = Query(default="agentic_llm"),
) -> TriageAPIResponse:
    run_id = str(uuid4())
    start_time = perf_counter()

    try:
        initial_state = OpsAgentState(
            request_id=run_id,
            customer_id=request.customer_id,
            issue_text=request.issue_text,
            channel=request.channel,
        )

        triage_response = run_ops_workflow(initial_state, mode=mode)

        latency_ms = int((perf_counter() - start_time) * 1000)

        api_response = TriageAPIResponse(
            **triage_response.model_dump(),
            run_id=run_id,
            mode=mode,
            latency_ms=latency_ms,
        )

        run_log = RunLog(
            run_id=run_id,
            timestamp_utc=datetime.now(UTC).isoformat(),
            mode=mode,
            input=request.model_dump(mode="json"),
            steps=_build_step_summary(
                mode=mode,
                triage_response=triage_response,
            ),
            retrieved_sources=[
                source.model_dump(mode="json")
                for source in triage_response.retrieved_sources
            ],
            tools_called=[
                tool.model_dump(mode="json")
                for tool in triage_response.tools_called
            ],
            llm_used=mode in {"simple_rag", "agentic_llm"},
            fallback_used=_detect_fallback_used(
                triage_response.reasoning_summary
            ),
            latency_ms=latency_ms,
            final_response=api_response.model_dump(mode="json"),
            errors=[],
        )
        append_run_log(run_log)

        return api_response

    except Exception as exc:
        latency_ms = int((perf_counter() - start_time) * 1000)

        run_log = RunLog(
            run_id=run_id,
            timestamp_utc=datetime.now(UTC).isoformat(),
            mode=mode,
            input=request.model_dump(mode="json"),
            steps=_build_step_summary(mode=mode),
            retrieved_sources=[],
            tools_called=[],
            llm_used=mode in {"simple_rag", "agentic_llm"},
            fallback_used=False,
            latency_ms=latency_ms,
            final_response=None,
            errors=[str(exc)],
        )
        append_run_log(run_log)

        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/runs/{run_id}", response_model=RunLog)
def read_run_log(run_id: str) -> RunLog:
    run_log = get_run_log(run_id)

    if run_log is None:
        raise HTTPException(status_code=404, detail="Run log not found")

    return run_log

# routing으로 인한 변경 부분 
# WorkflowMode = Literal["simple_rag", "baseline", "agentic_llm"]
# _build_Step_summary 함수는 입력 값을 2개 받는다 mode, triage_response
def _build_step_summary(
    mode: WorkflowMode,
    # 입력값mode 와 타입 WorkflowMode
    triage_response: TriageResponse | None = None,
    # 입력값 triage_response /입력타입 TriageResponse | None /기본값 None
    # 여기서 | 표시는 or 를 의미
) -> list[str]:
  # 반환값을 list[str] 로 정의  
    if mode == "simple_rag":
        return [
            "retrieve_docs",
            "generate_simple_rag_response",
        ]

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

    steps = [
        "classify_issue",
        "retrieve_docs",
        "get_customer_profile",
        "check_sla",
        "assess_risk",
    ]
    # _tool_was_called 함수에 tool_name이 "create_ticket_draft" 일 경우 steps에 create_ticket 경로 추가
    if triage_response is None or _tool_was_called(
        triage_response=triage_response,
        tool_name="create_ticket_draft",
    ):
        steps.append("create_ticket")

    steps.append("generate_llm_response")

    return steps


def _tool_was_called(
    triage_response: TriageResponse,
    tool_name: str,
) -> bool:
    return any(
        tool.tool_name == tool_name
        for tool in triage_response.tools_called
    )


def _detect_fallback_used(reasoning_summary: str) -> bool:
    return "fallback" in reasoning_summary.lower()
