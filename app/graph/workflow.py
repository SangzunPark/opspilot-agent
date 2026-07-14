from typing import Literal
# 기존 workflow 구조에서 router 기능을 추가
# mode를 확인하고 어느 구현으로 보낼지 결정
from app.graph.workflow_agentic_llm import run_agentic_llm_workflow
from app.graph.workflow_baseline import run_baseline_workflow
from app.schemas.responses import TriageResponse
from app.schemas.state import OpsAgentState
from app.services.simple_rag import run_simple_rag_triage

# Literal은 리스트안 문자열 중 하나만 허용한다는 타입 제한
WorkflowMode = Literal["simple_rag", "baseline", "agentic_llm"]


def run_ops_workflow(
    initial_state: OpsAgentState,
    mode: WorkflowMode = "agentic_llm",
) -> TriageResponse:
# simple rag 만 세 가지 값만 사용(실험을 위한 제약)
    if mode == "simple_rag":
        return run_simple_rag_triage(
            customer_id=initial_state.customer_id,
            issue_text=initial_state.issue_text,
            channel=initial_state.channel,
        )

    if mode == "baseline":
        return run_baseline_workflow(initial_state)

    if mode == "agentic_llm":
        return run_agentic_llm_workflow(initial_state)

    raise ValueError(f"Unsupported workflow mode: {mode}")
