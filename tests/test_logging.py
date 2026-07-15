from fastapi.testclient import TestClient

from app.main import app
from app.schemas.run_logs import RunLog
from app.services.run_logger import append_run_log, get_run_log

client = TestClient(app)

# 저장한 것을 다시 읽으면 값이 그대로 나오는가 여부 테스트
# 즉 append_run_log -> get_run_log 왕복 여부 테스트
def test_append_and_get_run_log(monkeypatch, tmp_path) -> None:
    # tmp_path는 pytest의 임시 폴더 생성 기능, 테스트후 소멸
    # monkeypatch는 테스트 중 특정 설정을 잠깐 변경, 테스트 후 복구
    log_path = tmp_path / "runs.jsonl"
    monkeypatch.setenv("RUN_LOG_PATH", str(log_path))

    run_log = RunLog(
        run_id="test-run-001",
        timestamp_utc="2026-01-01T00:00:00+00:00",
        mode="simple_rag",
        input={
            "customer_id": "CUST-1001",
            "issue_text": "Customer says invoice is wrong.",
            "channel": "email",
        },
        steps=["retrieve_docs", "generate_simple_rag_response"],
        retrieved_sources=[],
        tools_called=[],
        llm_used=True,
        fallback_used=False,
        latency_ms=123,
        final_response=None,
        errors=[],
    )

    append_run_log(run_log)

    loaded = get_run_log("test-run-001")

    assert loaded is not None
    assert loaded.run_id == "test-run-001"
    assert loaded.mode == "simple_rag"
    assert loaded.latency_ms == 123

# 실제 API 전체 흐름 테스트
def test_triage_creates_run_log(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "runs.jsonl"
    monkeypatch.setenv("RUN_LOG_PATH", str(log_path))
    # 비용절약의 이유로 mock으로 테스트
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = client.post(
        "/triage?mode=simple_rag",
        json={
            "customer_id": "CUST-1001",
            "issue_text": "Customer says the invoice amount is wrong and may cancel.",
            "channel": "email",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "run_id" in data
    assert data["mode"] == "simple_rag"
    # isinstance는 (a,b) a가 b가 맞는지 확인, 즉x가 정수타입이 맞는지 확인
    assert isinstance(data["latency_ms"], int)

    run_id = data["run_id"]

    log_response = client.get(f"/runs/{run_id}")

    assert log_response.status_code == 200

    log_data = log_response.json()

    assert log_data["run_id"] == run_id
    assert log_data["mode"] == "simple_rag"
    assert log_data["llm_used"] is True
    assert log_data["tools_called"] == []
    assert len(log_data["retrieved_sources"]) > 0

# 존재하지 않은 id로 조회해보고 404 에러 생성 확인
def test_get_missing_run_log_returns_404(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "runs.jsonl"
    monkeypatch.setenv("RUN_LOG_PATH", str(log_path))

    response = client.get("/runs/not-found")

    assert response.status_code == 404

# 저위험 케이스에서 티켓을 건너뛴 게 로그에도 제대로 남아 있는지 확인
# 중요 포인트는 로그에서 확인한다는 점
def test_agentic_llm_low_risk_run_log_skips_create_ticket(
    monkeypatch,
    tmp_path,
) -> None:
    log_path = tmp_path / "runs.jsonl"
    monkeypatch.setenv("RUN_LOG_PATH", str(log_path))
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    # 저위험 케이스 CUST1002를 agentic_llm에 전송
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
    run_id = data["run_id"]

    # 해당 run_id로 로그 조회
    log_response = client.get(f"/runs/{run_id}")

    assert log_response.status_code == 200

    log_data = log_response.json()
    tool_names = [
        tool["tool_name"]
        for tool in log_data["tools_called"]
    ]

    # 로그에 모드가 찍혔는지 / step 목록에 create_ticket이 없는지
    # 티켓 툴도 실제로 호출 안되었는지 / 로그에 저장된 최종응답에서 escalation이 False인지
    assert log_data["mode"] == "agentic_llm"
    assert "create_ticket" not in log_data["steps"]
    assert "create_ticket_draft" not in tool_names
    assert log_data["final_response"]["escalation_required"] is False
