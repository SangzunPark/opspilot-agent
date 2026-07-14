from app.schemas.responses import RetrievedSource, ToolCallRecord
from app.schemas.state import OpsAgentState
from app.tools.customer_tools import get_customer_profile
from app.tools.retrieval_tools import search_internal_docs
from app.tools.sla_tools import check_sla_policy
from app.tools.ticket_tools import create_ticket_draft

# week 1~3에서 만든 모든 모듈을 임포트
# 워크플로우의 7개 단계 노드를 구현
# 공책(state)를 받아서 자기 역할을 수행하고 업데이트 된 공책을 돌려주는 패턴

# 노드 1 이슈 분류
def classify_issue_node(state: OpsAgentState) -> OpsAgentState:
    text = state.issue_text.lower()

    # any는 하나라도 True면 참을 반환하는 함수
    if any(keyword in text for keyword in ["invoice", "billing", "charge", "charged"]):
        state.issue_type = "billing_dispute"
        state.confidence = 0.8
    elif any(keyword in text for keyword in ["outage", "unavailable", "down", "service is not working"]):
        state.issue_type = "technical_outage"
        state.confidence = 0.8
    elif "refund" in text:
        state.issue_type = "refund_request"
        state.confidence = 0.8
    elif any(keyword in text for keyword in ["login", "access", "password", "locked"]):
        state.issue_type = "account_access"
        state.confidence = 0.75
    elif any(keyword in text for keyword in ["cancel", "cancellation", "terminate contract"]):
        state.issue_type = "cancellation_risk"
        state.confidence = 0.75
    else:
        state.issue_type = "unknown"
        state.confidence = 0.4

    return state

# 노드 2 issue_type과 issue_text를 합쳐서 더 정확한 검색어 생성
def retrieve_docs_node(state: OpsAgentState) -> OpsAgentState:
    # 앞 노드에서 채워진 issue_type과 issue_text를 합쳐서 더 정확한 검색어 생성
    query = f"{state.issue_type} {state.issue_text}"
    results = search_internal_docs(query=query, top_k=3)

    state.retrieved_sources = [
        RetrievedSource(
            title=result.title,
            snippet=result.snippet,
            score=result.score,
        )
        for result in results
        # results 는 search_internal_docs 에서 list[DocumentSearchResult]을 생성
        # 필드 이름은 같지만 다른 클래스인 DocumentSearchResult 와 RetrievedSource에 대한
        # pydantic 에러를 방지하기 위해 for 문을 써서 results 안의 값을 추출
        # 같은 필드를 갖고 있지만 DocumentSearchResult는 내부용, Retrievedource는 외부용
    ]

    state.tools_called.append(
        ToolCallRecord(
            tool_name="search_internal_docs",
            input=str({"query": query, "top_k": 3}),
            output_summary=f"Retrieved {len(results)} internal document snippets.",
            success=True,
        )
    )

    return state

# 노드 3 고객 정보 조회
def get_customer_profile_node(state: OpsAgentState) -> OpsAgentState:
    # 고객 정보 조회 실패시
    if not state.customer_id:
        state.customer_tier = "unknown"
        state.tools_called.append(
            ToolCallRecord(
                tool_name="get_customer_profile",
                input=str({"customer_id": None}),
                output_summary="No customer ID provided.",
                success=False,
            )
        )
        return state
    # 조회 성공시
    customer = get_customer_profile(state.customer_id)
    state.customer_tier = customer.tier

    state.tools_called.append(
        ToolCallRecord(
            tool_name="get_customer_profile",
            input=str({"customer_id": state.customer_id}),
            output_summary=f"Customer tier is {customer.tier}.",
            success=True,
        )
    )

    return state

# 노드 4 SLA 정책 확인 (urgency 확인)
def check_sla_node(state: OpsAgentState) -> OpsAgentState:
    result = check_sla_policy(
        customer_tier=state.customer_tier,
        issue_type=state.issue_type,
    )

    state.urgency = result.default_urgency

    state.tools_called.append(
        ToolCallRecord(
            tool_name="check_sla_policy",
            input=str({
                "customer_tier": state.customer_tier,
                "issue_type": state.issue_type,
            }),
            output_summary=(
                f"{result.response_time}. {result.escalation_guidance}"
            ),
            success=True,
        )
    )

    return state

# 노드 5 위험도 평가
def assess_risk_node(state: OpsAgentState) -> OpsAgentState:
    text = state.issue_text.lower()

    risk_keywords = [
        "cancel",
        "cancellation",
        "legal",
        "contract",
        "angry",
        "unhappy",
        "escalate",
    ]

    has_risk_keyword = any(keyword in text for keyword in risk_keywords)

    high_value_customer = state.customer_tier in {"premium", "enterprise"}
    high_urgency = state.urgency in {"high", "critical"}
    no_sources = len(state.retrieved_sources) == 0
    low_confidence = state.confidence < 0.6

    state.escalation_required = (
        (high_value_customer and high_urgency)
        or has_risk_keyword
        or no_sources
        or low_confidence
    )

    return state

# 노드 6 티켓 생성
def create_ticket_node(state: OpsAgentState) -> OpsAgentState:
    draft = create_ticket_draft(
        issue_type=state.issue_type,
        issue_summary=state.issue_text,
        urgency=state.urgency,
        escalation_required=state.escalation_required,
    )

    state.ticket_title = draft.title
    state.ticket_description = draft.description
    state.assigned_team = draft.assigned_team

    state.tools_called.append(
        ToolCallRecord(
            tool_name="create_ticket_draft",
            input=str({
                "issue_type": state.issue_type,
                "urgency": state.urgency,
                "escalation_required": state.escalation_required,
            }),
            output_summary=f"Created ticket draft for {draft.assigned_team}.",
            success=True,
        )
    )

    return state

# 노드 7 최종 응답 생성
def generate_response_node(state: OpsAgentState) -> OpsAgentState:
    next_steps = [
        f"Review the issue as {state.issue_type}.",
        f"Route the case to {state.assigned_team or 'Operations Triage'}.",
    ]

    if state.retrieved_sources:
        next_steps.append(
            f"Use guidance from {state.retrieved_sources[0].title}."
        )

    if state.escalation_required:
        next_steps.append("Escalate to a human owner before sending a final response.")
    else:
        next_steps.append("Handle through the standard support process.")

    if state.ticket_title:
        next_steps.append(f"Create or update ticket: {state.ticket_title}.")

    state.recommended_next_steps = next_steps

    state.reasoning_summary = (
        f"The issue was classified as {state.issue_type}. "
        f"The customer tier is {state.customer_tier}. "
        f"The SLA-based urgency is {state.urgency}. "
        f"Escalation required: {state.escalation_required}."
    )

    return state
