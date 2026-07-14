from typing import Literal

from pydantic import Field

from app.schemas.responses import TriageResponse

# 기존 TriageResponse 은 실제 분석결과인 반면 이 TriageAPIResponse는 
# 그 결과에 run_id, mode, latency_ms 를 추가 한 것
# 즉 실행에 대한 메타 정보만을 별도의 파일로 생성하여 분리

# 기존 TriageResponse를 그대로 상속
class TriageAPIResponse(TriageResponse):
    run_id: str = Field(description="Unique ID for this triage run.")
    mode: Literal["simple_rag", "baseline", "agentic_llm"] = Field(
        description="Workflow mode used for this run."
    )
    latency_ms: int = Field(
        ge=0,
        description="End-to-end API latency in milliseconds.",
    )
