from fastapi.testclient import TestClient

from app.main import app
# API 엔드포인트 자체가 제대로 동작하는지 확인하는 테스트
# TestClient를 통해 실제 서버를 띄우지 않고 메모리 안에서 HTTP 요청 테스트
client = TestClient(app)


def test_triage_endpoint_returns_structured_response() -> None:
    # HTTP 요청 보내기
    response = client.post(
        "/triage",
        json={
            "customer_id": "CUST-1001",
            "issue_text": "Premium customer says the invoice amount is wrong and may cancel.",
            "channel": "email",
        },
    )
    # HTTP 상태 확인, 200성공/ 400잘못된요청/ 422유효성검사실패/ 500서버내부오류
    assert response.status_code == 200
    # json 응답파싱, HTTP 응답의 body를 json으로 파싱해 딕셔너리로 변환
    data = response.json()
    # 검증
    assert data["issue_type"] == "billing_dispute"
    assert data["urgency"] == "high"
    assert data["customer_tier"] == "premium"
    assert data["escalation_required"] is True
    assert isinstance(data["retrieved_sources"], list)
    assert isinstance(data["tools_called"], list)
    assert isinstance(data["recommended_next_steps"], list)
