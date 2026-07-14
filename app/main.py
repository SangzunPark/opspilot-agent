from datetime import UTC, datetime
from time import perf_counter
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
# Query 추가로 import
# FastAPI에서 함수 인자를 받는 방법은 두 가지인데, JSON body로 받기
# 그리고 Query parameter로 받기 방법이 있다.
# 쿼리 파라미터란 웹 주소에서 ? 뒷 부분을 의미하며 해당 요청에 추가 정보를 전달 하는 기능
# 결국 JSON body, 쿼리 파라미터 모두 서버에 정보를 전달하는 방법
# http://localhost:8000/triage?mode=simple_rag
# 위의 예는, triage 기능을 쓰고 모드는 simple_reg을 쓰라는 뜻
from app.graph.workflow import run_ops_workflow
from app.schemas.api import TriageAPIResponse
from app.schemas.requests import IssueTriageRequest
from app.schemas.run_logs import RunLog
from app.schemas.state import OpsAgentState
from app.services.run_logger import append_run_log, get_run_log

app = FastAPI(
    title="OpsPilot Agent",
    description="Agentic AI assistant for operations issue triage",
    version="0.1.0",
)


WorkflowMode = Literal["simple_rag", "baseline", "agentic_llm"]

# 서버 체크
@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

# 메인파트, 분석 및 로그 생성
@app.post("/triage", response_model=TriageAPIResponse)
def triage_issue(
    request: IssueTriageRequest,
    mode: WorkflowMode = Query(default="agentic_llm"),
) -> TriageAPIResponse:
    # run_id 발급, time count
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
        # 최종 응답 조합
        api_response = TriageAPIResponse(
            # model_dump는 pydantic 특별 객체를 평범한 파이썬 dict로 변환
            # 이유는 TriageResponse는 객체를 갖고 있고 RunLog는 다소 느슨한 dict 형태를 요구하기 때문
            # RunLog는 기록,저장,조회 가 목적이라 일부러 느슨한 dict 타입으로 설계
            **triage_response.model_dump(),
            run_id=run_id,
            mode=mode,
            latency_ms=latency_ms,
        )
        # RunLog 객체 생성
        run_log = RunLog(
            run_id=run_id,
            timestamp_utc=datetime.now(UTC).isoformat(),
            mode=mode,
            # 사용자 input을 dict 로 변환
            input=request.model_dump(mode="json"),
            steps=_build_step_summary(mode),
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
    # 에러 처리    
    except Exception as exc:
        latency_ms = int((perf_counter() - start_time) * 1000)

        run_log = RunLog(
            run_id=run_id,
            timestamp_utc=datetime.now(UTC).isoformat(),
            mode=mode,
            input=request.model_dump(mode="json"),
            # 어떤 단계들을 거쳤는지 확인 후 목록 반환
            steps=_build_step_summary(mode),
            retrieved_sources=[],
            tools_called=[],
            llm_used=mode in {"simple_rag", "agentic_llm"},
            # reasoning_summary에 fallback이라는 단어 있으면 True
            fallback_used=False,
            latency_ms=latency_ms,
            final_response=None,
            errors=[str(exc)],
        )
        append_run_log(run_log)

        raise HTTPException(status_code=500, detail=str(exc)) from exc

# 저장된 로그 조회
@app.get("/runs/{run_id}", response_model=RunLog)
def read_run_log(run_id: str) -> RunLog:
    run_log = get_run_log(run_id)

    if run_log is None:
        raise HTTPException(status_code=404, detail="Run log not found")

    return run_log

# mode 별 단계 목록 만드는 helper
def _build_step_summary(mode: WorkflowMode) -> list[str]:
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

    return [
        "classify_issue",
        "retrieve_docs",
        "get_customer_profile",
        "check_sla",
        "assess_risk",
        "create_ticket",
        "generate_llm_response",
    ]

# fallback 사용했는 판단하는 함수
def _detect_fallback_used(reasoning_summary: str) -> bool:
    return "fallback" in reasoning_summary.lower()
