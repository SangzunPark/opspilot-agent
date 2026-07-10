# nodes.py가 각 node를 정의했다면 workflow.py는 각 노드를 연결
# stategraph는 상태 기반 워크플로우를 만드는 핵심 도구
from langgraph.graph import END, START, StateGraph

# nodes.py에서 만들어진 7개의 노드 함수 호출
from app.graph.nodes import (
    assess_risk_node,
    check_sla_node,
    classify_issue_node,
    create_ticket_node,
    generate_response_node,
    get_customer_profile_node,
    retrieve_docs_node,
)
# OpsAgentState(공책) 와 TriageResponse(최종보고서)를 호출
from app.schemas.responses import TriageResponse
from app.schemas.state import OpsAgentState

# 1단계 StateGraph 생성
def build_ops_workflow():
    workflow = StateGraph(OpsAgentState)

    # 2단계 노드 등록
    workflow.add_node("classify_issue", classify_issue_node)
    workflow.add_node("retrieve_docs", retrieve_docs_node)
    workflow.add_node("get_customer_profile", get_customer_profile_node)
    workflow.add_node("check_sla", check_sla_node)
    workflow.add_node("assess_risk", assess_risk_node)
    workflow.add_node("create_ticket", create_ticket_node)
    workflow.add_node("generate_response", generate_response_node)

    # 3단계 엣지 연결 
    workflow.add_edge(START, "classify_issue")
    workflow.add_edge("classify_issue", "retrieve_docs")
    workflow.add_edge("retrieve_docs", "get_customer_profile")
    workflow.add_edge("get_customer_profile", "check_sla")
    workflow.add_edge("check_sla", "assess_risk")
    workflow.add_edge("assess_risk", "create_ticket")
    workflow.add_edge("create_ticket", "generate_response")
    workflow.add_edge("generate_response", END)
    
    # 4단계 컴파일
    return workflow.compile()

# 모듈 레벨에서 실행(파일의 최상단 레벨)
ops_workflow = build_ops_workflow()

# 외부(API엔드포인트) 에서 호출하는 함수 초기 공책(initial_state)를 받아서
# 워크플로우를 실행하고 최종결과 TriageResponse를 반환
def run_ops_workflow(initial_state: OpsAgentState) -> TriageResponse:
    final_state = ops_workflow.invoke(initial_state)

    if not isinstance(final_state, OpsAgentState):
        final_state = OpsAgentState(**final_state)

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
