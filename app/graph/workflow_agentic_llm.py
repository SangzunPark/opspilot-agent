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

# workflow 버전과 비교해 마지막에 generate_llm_response 부분만 추가 되었다
def build_agentic_llm_workflow():
    workflow = StateGraph(OpsAgentState)

    workflow.add_node("classify_issue", classify_issue_node)
    workflow.add_node("retrieve_docs", retrieve_docs_node)
    workflow.add_node("get_customer_profile", get_customer_profile_node)
    workflow.add_node("check_sla", check_sla_node)
    workflow.add_node("assess_risk", assess_risk_node)
    workflow.add_node("create_ticket", create_ticket_node)
    workflow.add_node("generate_llm_response", generate_llm_response_node)

    workflow.add_edge(START, "classify_issue")
    workflow.add_edge("classify_issue", "retrieve_docs")
    workflow.add_edge("retrieve_docs", "get_customer_profile")
    workflow.add_edge("get_customer_profile", "check_sla")
    workflow.add_edge("check_sla", "assess_risk")
    workflow.add_edge("assess_risk", "create_ticket")
    workflow.add_edge("create_ticket", "generate_llm_response")
    workflow.add_edge("generate_llm_response", END)

    return workflow.compile()


agentic_llm_workflow = build_agentic_llm_workflow()


def run_agentic_llm_workflow(initial_state: OpsAgentState) -> TriageResponse:
    final_state = agentic_llm_workflow.invoke(initial_state)

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
