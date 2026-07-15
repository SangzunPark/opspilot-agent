from fastapi.testclient import TestClient

from app.main import app

#HTTP 요청을 통해 세 가지 mode가 API 레벨에서 제대로 동작하는지 확인하는 테스트

client = TestClient(app)

ISSUE_TEXT = "Customer says the invoice amount is wrong and may cancel."


def test_triage_baseline_returns_premium_customer() -> None:
    response = client.post(
        "/triage?mode=baseline",
        json={
            "customer_id": "CUST-1001",
            "issue_text": ISSUE_TEXT,
            "channel": "email",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["issue_type"] == "billing_dispute"
    assert data["customer_tier"] == "premium"
    assert data["escalation_required"] is True


def test_triage_simple_rag_does_not_know_customer_tier(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = client.post(
        "/triage?mode=simple_rag",
        json={
            "customer_id": "CUST-1001",
            "issue_text": ISSUE_TEXT,
            "channel": "email",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["customer_tier"] == "unknown"
    assert data["tools_called"] == []
    assert isinstance(data["retrieved_sources"], list)
    assert len(data["retrieved_sources"]) > 0

# 저위험 케이스에서 티켓을 스킵한 것이 로그에도 제대로 남아 있는지 확인
def test_triage_agentic_llm_knows_customer_tier(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = client.post(
        "/triage?mode=agentic_llm",
        json={
            "customer_id": "CUST-1001",
            "issue_text": ISSUE_TEXT,
            "channel": "email",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["customer_tier"] == "premium"
    assert data["urgency"] == "high"
    assert data["escalation_required"] is True
    assert len(data["retrieved_sources"]) > 0
    assert len(data["tools_called"]) >= 3
    assert len(data["recommended_next_steps"]) >= 2

# 사용자가 저위험 티켓이 skip된것을 응답으로 잘 받는지 확인
# workflow, 로그테스트에 이어서 API 까지 테스트
def test_triage_agentic_llm_skips_ticket_for_low_risk_case(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = client.post(
        "/triage?mode=agentic_llm",
        json={
            "customer_id": "CUST-1002",
            "issue_text": "Customer asks why the invoice amount changed this month.",
            "channel": "email",
        },
    )

    assert response.status_code == 200

    data = response.json()
    tool_names = [
        tool["tool_name"]
        for tool in data["tools_called"]
    ]

    assert data["issue_type"] == "billing_dispute"
    assert data["customer_tier"] == "standard"
    assert data["urgency"] == "medium"
    assert data["escalation_required"] is False
    assert "create_ticket_draft" not in tool_names
