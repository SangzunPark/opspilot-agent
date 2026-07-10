# uuid(universally unique identifier)는 파이썬 내장 라이브러리로 
# 전 세계에서 겹치지 않는 고유한 ID를 랜덤으로 생성 
from uuid import uuid4

from fastapi import FastAPI

from app.graph.workflow import run_ops_workflow
from app.schemas.requests import IssueTriageRequest
from app.schemas.responses import TriageResponse
from app.schemas.state import OpsAgentState

app = FastAPI(
    title="OpsPilot Agent",
    description="Agentic AI assistant for operations issue triage",
    version="0.1.0",
)

# get은 데이터를 불러올때, post는 내보낼때 
@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

# 고객 문의를 서버로 보냄
@app.post("/triage", response_model=TriageResponse)
#FastAPI는 타입힌트를 인식, 그리고 json 형태의 파일을 request->IssueTriageRequest 객체로 변환
def triage_issue(request: IssueTriageRequest) -> TriageResponse:
    initial_state = OpsAgentState(
        request_id=str(uuid4()),
        customer_id=request.customer_id,
        issue_text=request.issue_text,
        channel=request.channel,
    )

    return run_ops_workflow(initial_state)
