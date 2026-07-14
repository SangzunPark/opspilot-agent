from typing import Any, Literal

from pydantic import BaseModel, Field

# run log 즉 실행 일지 한 건의 양식을 정의하는 파일 

WorkflowMode = Literal["simple_rag", "baseline", "agentic_llm"]


class RunLog(BaseModel):
    # Field는 pydantic 이 제공하는 함수로, 세부 규칙과 설명을 붙이는 도구
    # description 이하의 내용은 나중에 API 문서에 자동으로 표시
    # default=None 이면 비어있는 상태로 시작
    # ge = 0 은 greater than or equal to 0 
    run_id: str = Field(description="Unique ID for this triage run.")
    # 실행이 끝난 시각
    timestamp_utc: str = Field(description="UTC timestamp when the run completed.")
    mode: WorkflowMode = Field(description="Workflow mode used for this run.")
    # input은 원래 들어온 요청
    input: dict[str, Any] = Field(description="Original triage request payload.")

    # 거친 단계들
    steps: list[str] = Field(
        default_factory=list,
        description="High-level workflow steps executed.",
    )
    # rag으로 찾은 문서들
    # str, Any 중 Any는 아무 타입이나 허용한다는 의미
    retrieved_sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Retrieved policy sources used during the run.",
    )
    # 호출한 툴들
    tools_called: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Tool calls recorded during the run.",
    )

    # llm 사용 여부
    llm_used: bool = Field(description="Whether this mode used an LLM.")
    # 대체 로직 사용 여부
    fallback_used: bool = Field(description="Whether deterministic fallback was used.")
    # 소요시간
    latency_ms: int = Field(ge=0, description="End-to-end latency in milliseconds.")
    
    #최종 응답 
    final_response: dict[str, Any] | None = Field(
        default=None,
        description="Final API response returned to the user.",
    )
    # 에러 리스트
    errors: list[str] = Field(
        default_factory=list,
        description="Errors captured during the run.",
    )
