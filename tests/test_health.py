from fastapi.testclient import TestClient
# TestClient 는 fastapi가 제공하는 클라이언트를 모방한 시뮬레이션 도구
from app.main import app

client = TestClient(app)
# TestClient 에 연결한 후 .get / .post 등을 사용할 수 있다. 
# 서버를 따로 켜지 않아도 uvicorn을 통해 테스트 가능 
def test_health_check_return_ok() -> None:
    # pytest 를 염두해 이름이 test_로 시작, 함수 반환이 없으므로 None
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    # assert는 파이썬 키워드로 조건이 Ture면 다음 줄로 진행. False면 에러발생
