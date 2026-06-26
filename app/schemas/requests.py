from pydantic import BaseModel, Field

from app.schemas.domain import Channel


class IssueTriageRequest(BaseModel):
    customer_id: str | None = Field(
        default=None,
        description="Internal customer ID if available.",
        examples=["CUST-1001"],
    )
    issue_text: str = Field(
        min_length=10,
        description="Unstructured issue description from email, chat, or ticket.",
        examples=[
            "Premium customer says the invoice amount is wrong and they may cancel."
        ],
    )
    channel: Channel = Field(
        default="email",
        description="Source channel of the issue.",
    )
