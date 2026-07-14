from app.schemas.state import OpsAgentState
from app.services.llm import generate_llm_recommendation
# nodes_llm.py는 LLM을 호출하는 부분과, 실패시 에러 기록후 workflow 방식으로 전환 및 결과 반환
# 을 목적으로 설계한 reliability를 고려한 구조 

# state를 받아서 채우고 반환한다는 구조는 동일하지만 다른 점은 문자열을 LLM을 이용한다는 점
def generate_llm_response_node(state: OpsAgentState) -> OpsAgentState:
    try:
        recommendation = generate_llm_recommendation(state)

        state.recommended_next_steps = recommendation.recommended_next_steps
        state.reasoning_summary = recommendation.reasoning_summary
        state.confidence = recommendation.confidence

        return state
    # 에러 발생시 state.error에 기록, _generate_deterministic_fallback 실행
    # 그리고 rule_based 로 대신 채워서 반환
    except Exception as exc:
        state.errors.append(f"LLM recommendation failed: {exc}")
        return _generate_deterministic_fallback(state)

# Fallback 함수(LLM 실패시), workflow 방식과 동일, _는 내무 전용 함수, 
def _generate_deterministic_fallback(state: OpsAgentState) -> OpsAgentState:
    next_steps = [
        f"Review the issue as {state.issue_type}.",
        f"Route the case to {state.assigned_team or 'Operations Triage'}.",
    ]

    if state.retrieved_sources:
        next_steps.append(
            f"Use guidance from {state.retrieved_sources[0].title}."
        )

    if state.escalation_required:
        next_steps.append(
            "Escalate to a human owner before sending a final response."
        )
    else:
        next_steps.append("Handle through the standard support process.")

    if state.ticket_title:
        next_steps.append(f"Create or update ticket: {state.ticket_title}.")

    state.recommended_next_steps = next_steps
    state.reasoning_summary = (
        "Fallback response used due to LLM failure. "
        f"The issue was classified as {state.issue_type}. "
        f"Customer tier: {state.customer_tier}. "
        f"Urgency: {state.urgency}. "
        f"Escalation required: {state.escalation_required}."
    )
    state.confidence = min(state.confidence, 0.7)

    return state
