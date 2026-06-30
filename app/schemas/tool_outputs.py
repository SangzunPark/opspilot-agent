from pydantic import BaseModel, Field

from app.schemas.domain import CustomerTier, IssueType, UrgencyLevel


class CustomerProfile(BaseModel):
    customer_id: str
    name: str
    tier: CustomerTier
    region: str
    account_status: str


class SLAResult(BaseModel):
    customer_tier: CustomerTier
    issue_type: IssueType
    response_time: str
    escalation_guidance: str
    default_urgency: UrgencyLevel


class TicketDraft(BaseModel):
    title: str
    description: str
    urgency: UrgencyLevel
    escalation_required: bool
    assigned_team: str

class DocumentSearchResult(BaseModel):
    title: str = Field(description="Document file name.")
    snippet: str = Field(description="Relevant text snippet.")
    score: float = Field(ge=0.0, le=1.0)
