import json
import os
from pathlib import Path

from app.schemas.run_logs import RunLog

# schemas/Runlogs 파일이 기록양식이었다면 이 파일은 실제로 파일에 쓰고 다시 찾아 읽는 기능 

# 로그 파일 위치 확인 .env에 RUN_LOG_PATH가 있으면 그 값을 사용하고 아니라면
# "logs/runs.ksonl" 을 사용
def get_run_log_path() -> Path:
    return Path(os.getenv("RUN_LOG_PATH", "logs/runs.jsonl"))

# 새 기록 파일에 추가
def append_run_log(run_log: RunLog) -> None:
    log_path = get_run_log_path()
    # 폴더가 없으면 생성
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # "a" append 모드, 기존 내용 보존 및 신규 내용 추가
    with log_path.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(
                run_log.model_dump(mode="json"),
                ensure_ascii=False,
            )
            + "\n"
        )

# run_id 로 기록을 찾아 읽기
def get_run_log(run_id: str) -> RunLog | None:
    log_path = get_run_log_path()

    if not log_path.exists():
        return None

    with log_path.open("r", encoding="utf-8") as file:
        # 한줄 씩 읽기 loop
        for line in file:
            # 빈 줄 건너뛰기
            if not line.strip():
                continue
            # JSON 문자열을 다시 파이썬 dict로 되돌림
            data = json.loads(line)
            # 이 줄의 run_id가 내가 찾는 id와 같다면 dict를 다시 Runlog 양식으로 변환
            # RunLog(**data) 의 **는 dict를 풀어서 각 칸에 넣어라 라는 의미
            # 예 : {"run_id": "abc-1", "mode": "..."} → RunLog(run_id="abc-1", mode="...", ...) 
            if data.get("run_id") == run_id:
                return RunLog(**data)

    return None
