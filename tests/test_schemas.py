import pytest
from pydantic import ValidationError

from app.schemas.requests import IssueTriageRequest
from app.schemas.responses import RetrievedSource, ToolCallRecord, TriageResponse


def test_issue_triage_request_accepts_valid_input() -> None:
    request = IssueTriageRequest(
        customer_id="CUST-1001",
        issue_text="Premium customer says the invoice amount is wrong and may cancel.",
        channel="email",
    )

    assert request.customer_id == "CUST-1001"
    assert request.channel == "email"


def test_issue_triage_request_rejects_short_issue_text() -> None:
    with pytest.raises(ValidationError):
        IssueTriageRequest(
            customer_id="CUST-1001",
            issue_text="too short",
            channel="email",
        )


def test_triage_response_accepts_valid_output() -> None:
    response = TriageResponse(
        issue_type="billing_dispute",
        urgency="high",
        customer_tier="premium",
        escalation_required=True,
        retrieved_sources=[
            RetrievedSource(
                title="billing_policy.md",
                snippet="Billing disputes should be reviewed carefully.",
                score=0.92,
            )
        ],
        tools_called=[
            ToolCallRecord(
                tool_name="get_customer_profile",
                input={"customer_id": "CUST-1001"},
                output_summary="Customer tier is premium.",
                success=True,
            )
        ],
        recommended_next_steps=[
            "Verify the invoice line items.",
            "Escalate to billing operations.",
        ],
        confidence=0.86,
        reasoning_summary="The issue is billing-related and includes cancellation risk.",
    )

    assert response.issue_type == "billing_dispute"
    assert response.urgency == "high"
    assert response.escalation_required is True


def test_triage_response_rejects_invalid_urgency() -> None:
    with pytest.raises(ValidationError):
        TriageResponse(
            issue_type="billing_dispute",
            urgency="very_urgent",
            customer_tier="premium",
            escalation_required=True,
            retrieved_sources=[],
            tools_called=[],
            recommended_next_steps=["Escalate to billing operations."],
            confidence=0.86,
            reasoning_summary="The issue is billing-related and includes cancellation risk.",
        )


def test_triage_response_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        TriageResponse(
            issue_type="billing_dispute",
            urgency="high",
            customer_tier="premium",
            escalation_required=True,
            retrieved_sources=[],
            tools_called=[],
            recommended_next_steps=["Escalate to billing operations."],
            confidence=1.5,
            reasoning_summary="The issue is billing-related and includes cancellation risk.",
        )
