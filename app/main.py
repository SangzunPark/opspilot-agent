from typing import Literal
from uuid import uuid4
# Query 추가로 import
# FastAPI에서 함수 인자를 받는 방법은 두 가지인데, JSON body로 받기
# 그리고 Query parameter로 받기 방법이 있다.
# 쿼리 파라미터란 웹 주소에서 ? 뒷 부분을 의미하며 해당 요청에 추가 정보를 전달 하는 기능
# 결국 JSON body, 쿼리 파라미터 모두 서버에 정보를 전달하는 방법
# http://localhost:8000/triage?mode=simple_rag
# 위의 예는, triage 기능을 쓰고 모드는 simple_reg을 쓰라는 뜻
from fastapi import FastAPI, Query

from app.graph.workflow import run_ops_workflow
from app.schemas.requests import IssueTriageRequest
from app.schemas.responses import TriageResponse
from app.schemas.state import OpsAgentState

# 기존 app/main 파일에 비해 mode 인자가 추가됨

app = FastAPI(
    title="OpsPilot Agent",
    description="Agentic AI assistant for operations issue triage",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageResponse)
def triage_issue(
    request: IssueTriageRequest,
    mode: Literal["simple_rag", "baseline", "agentic_llm"] = Query(
        default="agentic_llm"
    ),
) -> TriageResponse:
    initial_state = OpsAgentState(
        request_id=str(uuid4()),
        customer_id=request.customer_id,
        issue_text=request.issue_text,
        channel=request.channel,
    )

    return run_ops_workflow(initial_state, mode=mode)
