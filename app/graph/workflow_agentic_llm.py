from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    assess_risk_node,
    check_sla_node,
    classify_issue_node,
    create_ticket_node,
    get_customer_profile_node,
    retrieve_docs_node,
)
from app.graph.nodes_llm import generate_llm_response_node
from app.schemas.responses import TriageResponse
from app.schemas.state import OpsAgentState


NextStepAfterRisk = Literal["create_ticket", "generate_llm_response"]

# 그래프 그리기, state 를 기반으로 한 빈 그래프를 작성
def build_agentic_llm_workflow():
    workflow = StateGraph(OpsAgentState)
    # 노드 등록
    workflow.add_node("classify_issue", classify_issue_node)
    workflow.add_node("retrieve_docs", retrieve_docs_node)
    workflow.add_node("get_customer_profile", get_customer_profile_node)
    workflow.add_node("check_sla", check_sla_node)
    workflow.add_node("assess_risk", assess_risk_node)
    workflow.add_node("create_ticket", create_ticket_node)
    workflow.add_node("generate_llm_response", generate_llm_response_node)
    # 엣지 연결
    workflow.add_edge(START, "classify_issue")
    workflow.add_edge("classify_issue", "retrieve_docs")
    workflow.add_edge("retrieve_docs", "get_customer_profile")
    workflow.add_edge("get_customer_profile", "check_sla")
    workflow.add_edge("check_sla", "assess_risk")
    # 조건부 연결, 갈림길 만들기 assess_risk 노드가 끝나면 route_After_risk_Assessment 호출
    # 함수의 반환 값(create_ticket or generate..)을 따라 해당 노드로 이동
    # 왼쪽이 함수의 출력 값, 오른쪽이 노드, 아래 코드는 이 둘이 동일 한 경우
    # 기존 LangChain 과 차별화되는 LangGraph의 특징  
    workflow.add_conditional_edges(
        "assess_risk",
        route_after_risk_assessment,
        {
            "create_ticket": "create_ticket",
            "generate_llm_response": "generate_llm_response",
        },
    )

    workflow.add_edge("create_ticket", "generate_llm_response")
    workflow.add_edge("generate_llm_response", END)

    return workflow.compile()

# 갈림길 판단 함수
# 실제로 방향을 결정하는 부분
def route_after_risk_assessment(state: OpsAgentState) -> NextStepAfterRisk:
    if state.escalation_required:
        return "create_ticket"

    return "generate_llm_response"


agentic_llm_workflow = build_agentic_llm_workflow()

# invoke를 통해 실제로 그래프를 실행
def run_agentic_llm_workflow(initial_state: OpsAgentState) -> TriageResponse:
    final_state = agentic_llm_workflow.invoke(initial_state)

    if not isinstance(final_state, OpsAgentState):
        final_state = OpsAgentState(**final_state)
    # TriageResponse 최종 조립
    return TriageResponse(
        issue_type=final_state.issue_type,
        urgency=final_state.urgency,
        customer_tier=final_state.customer_tier,
        escalation_required=final_state.escalation_required,
        retrieved_sources=final_state.retrieved_sources,
        tools_called=final_state.tools_called,
        recommended_next_steps=final_state.recommended_next_steps,
        confidence=final_state.confidence,
        reasoning_summary=final_state.reasoning_summary,
    )
