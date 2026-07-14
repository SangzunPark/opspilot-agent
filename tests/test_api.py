from fastapi.testclient import TestClient

from app.main import app

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
