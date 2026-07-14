from app.services.simple_rag import run_simple_rag_triage

# simple_rag 파일의 테스트 코드
ISSUE_TEXT = "Customer says the invoice amount is wrong and may cancel."

# 테스트1, 구조화된 응답이 나오는가, customer tier 테스트
def test_simple_rag_returns_structured_response(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    # 여기서 monkeypatch란 pytest가 제공하는 도구, 
    # 테스트가 실행되는 동안만 임시로 환경변수를 바꿔라 라는 뜻
    response = run_simple_rag_triage(
        customer_id="CUST-1001",
        issue_text=ISSUE_TEXT,
        channel="email",
    )

    assert response.issue_type == "billing_dispute"
    # simple_rag은 DB를 못 보니 unknown이어야 한다
    assert response.customer_tier == "unknown"
    assert response.tools_called == []
    assert len(response.retrieved_sources) > 0
    assert len(response.recommended_next_steps) >= 2

# 테스트2 짧은 문장, customer tier에 집중
def test_simple_rag_does_not_know_customer_tier(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = run_simple_rag_triage(
        customer_id="CUST-1001",
        issue_text="Customer says they were charged the wrong amount.",
        channel="email",
    )

    assert response.customer_tier == "unknown"
    assert response.tools_called == []
