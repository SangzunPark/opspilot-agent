from pydantic import BaseModel, Field

from app.schemas.domain import CustomerTier, IssueType, UrgencyLevel


class RetrievedSource(BaseModel):
    title: str = Field(description="Name of the retrieved internal document.")
    snippet: str = Field(description="Short relevant excerpt from the document.")
    score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional retrieval relevance score.",
    )


class ToolCallRecord(BaseModel):
    tool_name: str = Field(description="Name of the tool that was called.")
    input: dict = Field(default_factory=dict, description="Tool input arguments.")
    output_summary: str = Field(description="Short summary of the tool output.")
    success: bool = Field(description="Whether the tool call succeeded.")


class TriageResponse(BaseModel):
    issue_type: IssueType = Field(description="Predicted issue category.")
    urgency: UrgencyLevel = Field(description="Predicted urgency level.")
    customer_tier: CustomerTier = Field(description="Customer tier used for triage.")
    escalation_required: bool = Field(
        description="Whether a human should review or handle the case."
    )
    retrieved_sources: list[RetrievedSource] = Field(
        default_factory=list,
        description="Internal documents used as evidence.",
    )
    tools_called: list[ToolCallRecord] = Field(
        default_factory=list,
        description="Tools called during the triage workflow.",
    )
    recommended_next_steps: list[str] = Field(
        min_length=1,
        description="Actionable next steps for the operations team.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the triage result.",
    )
    reasoning_summary: str = Field(
        min_length=10,
        description="Short explanation of why the recommendation was made.",
    )
