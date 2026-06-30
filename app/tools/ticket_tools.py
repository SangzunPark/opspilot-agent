from app.schemas.domain import IssueType, UrgencyLevel
from app.schemas.tool_outputs import TicketDraft


def create_ticket_draft(
    issue_type: IssueType,
    issue_summary: str,
    urgency: UrgencyLevel,
    escalation_required: bool,
) -> TicketDraft:
    assigned_team = _select_assigned_team(issue_type)

    title = f"[{urgency.upper()}] {issue_type.replace('_', ' ').title()}"

    description = (
        f"Issue summary: {issue_summary}\n\n"
        f"Detected issue type: {issue_type}\n"
        f"Urgency: {urgency}\n"
        f"Escalation required: {escalation_required}\n"
        f"Assigned team: {assigned_team}"
    )

    return TicketDraft(
        title=title,
        description=description,
        urgency=urgency,
        escalation_required=escalation_required,
        assigned_team=assigned_team,
    )


def _select_assigned_team(issue_type: IssueType) -> str:
    if issue_type == "billing_dispute":
        return "Billing Operations"

    if issue_type == "technical_outage":
        return "Engineering On-Call"

    if issue_type == "refund_request":
        return "Customer Support"

    if issue_type == "account_access":
        return "Identity and Access Support"

    if issue_type == "cancellation_risk":
        return "Customer Success"

    return "Operations Triage"
