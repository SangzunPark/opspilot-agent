from app.tools.customer_tools import get_customer_profile
from app.tools.retrieval_tools import search_internal_docs
from app.tools.sla_tools import check_sla_policy
from app.tools.ticket_tools import create_ticket_draft


def test_get_customer_profile_returns_existing_customer() -> None:
    customer = get_customer_profile("CUST-1001")

    assert customer.customer_id == "CUST-1001"
    assert customer.name == "Acme GmbH"
    assert customer.tier == "premium"


def test_get_customer_profile_handles_unknown_customer() -> None:
    customer = get_customer_profile("UNKNOWN")

    assert customer.customer_id == "UNKNOWN"
    assert customer.name == "Unknown Customer"
    assert customer.tier == "unknown"


def test_check_sla_policy_for_enterprise_outage_is_critical() -> None:
    result = check_sla_policy(
        customer_tier="enterprise",
        issue_type="technical_outage",
    )

    assert result.default_urgency == "critical"
    assert "engineering" in result.escalation_guidance.lower()


def test_check_sla_policy_for_premium_billing_is_high() -> None:
    result = check_sla_policy(
        customer_tier="premium",
        issue_type="billing_dispute",
    )

    assert result.default_urgency == "high"
    assert "4 business hours" in result.response_time


def test_search_internal_docs_returns_billing_policy() -> None:
    results = search_internal_docs("billing invoice dispute", top_k=3)

    titles = [result.title for result in results]

    assert "billing_policy.md" in titles


def test_create_ticket_draft_assigns_billing_team() -> None:
    draft = create_ticket_draft(
        issue_type="billing_dispute",
        issue_summary="Customer says the invoice amount is incorrect.",
        urgency="high",
        escalation_required=True,
    )

    assert draft.urgency == "high"
    assert draft.escalation_required is True
    assert draft.assigned_team == "Billing Operations"
    assert "Billing Dispute" in draft.title
