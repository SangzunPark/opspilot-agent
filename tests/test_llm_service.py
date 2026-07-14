from app.schemas.state import OpsAgentState
from app.services.llm import generate_llm_recommendation

# generate_llm_recommendation은 workflow 안의 마지막 노드에서 호출되는 함수
# 즉 함수만 따로 테스트
# LLM 추천 품질을 확인 즉 LLM이 state 정보를 제대로 활용하는 지 검증
def test_generate_llm_recommendation_mock_mode(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    state = OpsAgentState(
        request_id="test-llm-001",
        customer_id="CUST-1001",
        issue_text="Customer says the invoice amount is wrong and may cancel.",
        channel="email",
        issue_type="billing_dispute",
        urgency="high",
        customer_tier="premium",
        escalation_required=True,
        assigned_team="Billing Operations",
        confidence=0.8,
    )

    result = generate_llm_recommendation(state)

    # 검증파트
    assert len(result.recommended_next_steps) >= 2
    assert result.confidence >= 0.75
    assert "billing_dispute" in result.reasoning_summary
    assert "premium" in result.reasoning_summary
