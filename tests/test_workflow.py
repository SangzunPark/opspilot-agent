from app.graph.workflow import run_ops_workflow
from app.schemas.state import OpsAgentState
# 워크플로우 전체가 end-to-end로 동작하는 확인하는 테스트 7개의 노드와 흐름을 체크
# 첫 번째 테스트는 premium 고객 + billing + 취소위험 조합 테스트
def test_ops_workflow_handles_premium_billing_cancellation_risk() -> None:
    initial_state = OpsAgentState(
        request_id="test-run-001",
        customer_id="CUST-1001",
        issue_text="Premium customer says the invoice amount is wrong and may cancel.",
        channel="email",
    )

    response = run_ops_workflow(initial_state)

    assert response.issue_type == "billing_dispute"
    assert response.urgency == "high"
    assert response.customer_tier == "premium"
    assert response.escalation_required is True
    assert len(response.retrieved_sources) > 0
    assert len(response.tools_called) >= 3
    assert len(response.recommended_next_steps) > 0

# 두 번째 테스트는 enterprise 고객  + 서비스 장애
def test_ops_workflow_handles_enterprise_outage_as_critical() -> None:
    initial_state = OpsAgentState(
        request_id="test-run-002",
        customer_id="CUST-1003",
        issue_text="The service is unavailable for multiple users.",
        channel="support_ticket",
    )

    response = run_ops_workflow(initial_state)

    assert response.issue_type == "technical_outage"
    assert response.urgency == "critical"
    assert response.customer_tier == "enterprise"
    assert response.escalation_required is True
