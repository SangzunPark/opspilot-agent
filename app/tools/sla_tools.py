from app.schemas.domain import CustomerTier, IssueType
from app.schemas.tool_outputs import SLAResult


def check_sla_policy(
    customer_tier: CustomerTier,
    issue_type: IssueType,
) -> SLAResult:
    if customer_tier == "enterprise" and issue_type == "technical_outage":
        return SLAResult(
            customer_tier=customer_tier,
            issue_type=issue_type,
            response_time="Immediate response required",
            escalation_guidance="Escalate to engineering on-call and customer success leadership.",
            default_urgency="critical",
        )

    if customer_tier in {"premium", "enterprise"} and issue_type in {
        "billing_dispute",
        "account_access",
        "cancellation_risk",
    }:
        return SLAResult(
            customer_tier=customer_tier,
            issue_type=issue_type,
            response_time="First response within 4 business hours",
            escalation_guidance="Escalate to a human manager if cancellation, legal, or contract risk is mentioned.",
            default_urgency="high",
        )

    if issue_type == "refund_request" and customer_tier in {"premium", "enterprise"}:
        return SLAResult(
            customer_tier=customer_tier,
            issue_type=issue_type,
            response_time="First response within 1 business day",
            escalation_guidance="Escalate if refund amount is high or contract terms are unclear.",
            default_urgency="medium",
        )

    if customer_tier == "unknown":
        return SLAResult(
            customer_tier=customer_tier,
            issue_type=issue_type,
            response_time="Response time unknown",
            escalation_guidance="Recommend human review because customer tier is unknown.",
            default_urgency="high",
        )

    return SLAResult(
        customer_tier=customer_tier,
        issue_type=issue_type,
        response_time="First response within 2 business days",
        escalation_guidance="Handle through standard support process unless risk signals are present.",
        default_urgency="medium",
    )
