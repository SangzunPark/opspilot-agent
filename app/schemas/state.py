from pydantic import BaseModel, Field

from app.schemas.domain import Channel, CustomerTier, IssueType, UrgencyLevel
from app.schemas.responses import RetrievedSource, ToolCallRecord

# 워크플로우 전체 7개의 노드가 공유하는 state 공책
class OpsAgentState(BaseModel):
    # 워크플로우가 시작될때 외부에서 들어오는 값들
    request_id: str
    customer_id: str | None = None
    issue_text: str
    channel: Channel = "email"
    # 기본값으로 시작해서 노드가 실행되면 업데이트
    issue_type: IssueType = "unknown"
    urgency: UrgencyLevel = "medium"
    customer_tier: CustomerTier = "unknown"

    # default_factory=list는 객체를 만들 때마다 list()를 새로 호출, 각자 다른 빈 리스트 생성
    # 클래스 내부에서 리스트를 공유하게 되어서 생기는 객체 끼리의 리스트 오류를 방지
    # factory는 값을 찍어내는 공장을 의미
    retrieved_sources: list[RetrievedSource] = Field(default_factory=list)
    tools_called: list[ToolCallRecord] = Field(default_factory=list)

    # 최종 결과 정보
    escalation_required: bool = False
    recommended_next_steps: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning_summary: str = ""

    ticket_title: str | None = None
    ticket_description: str | None = None
    assigned_team: str | None = None

    errors: list[str] = Field(default_factory=list)
