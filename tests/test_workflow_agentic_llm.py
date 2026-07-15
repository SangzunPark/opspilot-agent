from app.graph.workflow import run_ops_workflow
from app.schemas.state import OpsAgentState

# 저위험일 경우 티켓발급이 실제로 스킵되는지 확인해보는 코드
HIGH_RISK_ISSUE_TEXT = (
    "Customer says the invoice amount is wrong and may cancel."
)

LOW_RISK_ISSUE_TEXT = (
    "Customer asks why the invoice amount changed this month."
)

# 고위험 상태 만들기
def _make_high_risk_billing_state(request_id: str) -> OpsAgentState:
    return OpsAgentState(
        request_id=request_id,
        customer_id="CUST-1001",
        issue_text=HIGH_RISK_ISSUE_TEXT,
        channel="email",
    )

# 저위험 상태 만들기
def _make_low_risk_billing_state(request_id: str) -> OpsAgentState:
    return OpsAgentState(
        request_id=request_id,
        customer_id="CUST-1002",
        issue_text=LOW_RISK_ISSUE_TEXT,
        channel="email",
    )

# 툴 이름만 뽑아서 리스트로 저장
def _tool_names(response) -> list[str]:
    return [tool.tool_name for tool in response.tools_called]


def test_agentic_llm_creates_ticket_for_high_risk_case(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = run_ops_workflow(
        _make_high_risk_billing_state("test-agentic-high-risk"),
        mode="agentic_llm",
    )

    tool_names = _tool_names(response)

    assert response.issue_type == "billing_dispute"
    assert response.urgency == "high"
    assert response.customer_tier == "premium"
    assert response.escalation_required is True
    assert "create_ticket_draft" in tool_names
    assert len(response.recommended_next_steps) >= 2


def test_agentic_llm_skips_ticket_for_low_risk_case(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = run_ops_workflow(
        _make_low_risk_billing_state("test-agentic-low-risk"),
        mode="agentic_llm",
    )

    tool_names = _tool_names(response)

    assert response.issue_type == "billing_dispute"
    assert response.urgency == "medium"
    assert response.customer_tier == "standard"
    assert response.escalation_required is False
    assert "create_ticket_draft" not in tool_names
    assert len(response.recommended_next_steps) >= 2

# 회귀테스트, 새 라우팅 기능과 기존 기능의 충돌 여부 확인, 실무의 기본
def test_baseline_workflow_still_runs() -> None:
    response = run_ops_workflow(
        _make_high_risk_billing_state("test-baseline-001"),
        mode="baseline",
    )

    assert response.issue_type == "billing_dispute"
    assert response.urgency == "high"
    assert response.customer_tier == "premium"
    assert response.escalation_required is True


def test_simple_rag_does_not_know_customer_tier(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = run_ops_workflow(
        _make_high_risk_billing_state("test-simple-rag-001"),
        mode="simple_rag",
    )

    assert response.customer_tier == "unknown"
    assert response.tools_called == []
    assert len(response.retrieved_sources) > 0


def test_agentic_vs_simple_rag_customer_tier_difference(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    simple_rag_response = run_ops_workflow(
        _make_high_risk_billing_state("test-compare-simple-rag"),
        mode="simple_rag",
    )
    agentic_response = run_ops_workflow(
        _make_high_risk_billing_state("test-compare-agentic"),
        mode="agentic_llm",
    )

    assert simple_rag_response.customer_tier == "unknown"
    assert agentic_response.customer_tier == "premium"
