# env 를 config에서 관리하는 것은 llm과, simple_rag 모두에서 env를 사용하며,
# 이때 llm_provider를 중앙에서 관리하기 위함
# 이 프로젝트 자체만 보면 오버스펙이나,production 스타일을 재현하기 위해 이 구조 사용

import os
# 파이썬 내장 라이브러리, os.getenv()를 쓰기 위해
from dataclasses import dataclass
# @dataclass 데코레이터를 쓰기 위해
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
# @dataclass는 클래스를 데이터 저장 용도로 지정-> 자동으로 init 생성
# frozen은 한 번 만들어진 값을 immutable로 고정
# BaseModel 과의 차이는 복잡한 검증 없이 단순히 값을 담기만 하면 되는 상황에서 사용
class Settings:
    app_env: str
    log_level: str
    llm_provider: str
    openai_api_key: str | None
    openai_model: str

# 환경변수 읽는 함수
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )
