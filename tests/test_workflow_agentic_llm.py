from app.graph.workflow import run_ops_workflow
from app.schemas.state import OpsAgentState

# 전체 워크플로우 테스트 + 비교 테스트
# 세가지 mode가 각자 의도한 대로 동작하는지, 그리고 서로 어떻게 다른지 확인 하는 통합 테스트 
# 테스트 1: agentic_llm workflow 동작 확인
# 테스트 2: baseline workflow 여전히 동작하는지 확인
# 테스트 3: simple_rag가 customer_tier를 모르는지 확인
# 테스트 4: simple_rag vs agentic_llm 직접 비교

ISSUE_TEXT = "Customer says the invoice amount is wrong and may cancel."

# 4개의 테스트에서 같은 초기 state을 사용해야 하기 때문에 함수로 별도 지정
def _make_billing_state(request_id: str) -> OpsAgentState:
    return OpsAgentState(
        request_id=request_id,
        customer_id="CUST-1001",
        issue_text=ISSUE_TEXT,
        channel="email",
    )


def test_agentic_llm_workflow_runs_with_mock_provider(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = run_ops_workflow(
        _make_billing_state("test-agentic-001"),
        mode="agentic_llm",
    )

    assert response.issue_type == "billing_dispute"
    assert response.urgency == "high"
    assert response.customer_tier == "premium"
    assert response.escalation_required is True
    assert len(response.retrieved_sources) > 0
    assert len(response.tools_called) >= 3
    assert len(response.recommended_next_steps) >= 2
    assert response.confidence >= 0.75


def test_baseline_workflow_still_runs() -> None:
    response = run_ops_workflow(
        _make_billing_state("test-baseline-001"),
        mode="baseline",
    )

    assert response.issue_type == "billing_dispute"
    assert response.urgency == "high"
    assert response.customer_tier == "premium"
    assert response.escalation_required is True


def test_simple_rag_does_not_know_customer_tier(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = run_ops_workflow(
        _make_billing_state("test-simple-rag-001"),
        mode="simple_rag",
    )

    assert response.customer_tier == "unknown"
    assert response.tools_called == []
    assert len(response.retrieved_sources) > 0

# 이 파일에서 가장 핵심이 되는 테스트
def test_agentic_vs_simple_rag_customer_tier_difference(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    simple_rag_response = run_ops_workflow(
        _make_billing_state("test-compare-simple-rag"),
        mode="simple_rag",
    )
    agentic_response = run_ops_workflow(
        _make_billing_state("test-compare-agentic"),
        mode="agentic_llm",
    )

    assert simple_rag_response.customer_tier == "unknown"
    assert agentic_response.customer_tier == "premium"
