from typing import Literal

IssueType = Literal[
    "billing_dispute",
    "technical_outage",
    "refund_request",
    "account_access",
    "cancellation_risk",
    "unknown",
]

UrgencyLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

CustomerTier = Literal[
    "standard",
    "premium",
    "enterprise",
    "unknown",
]

Channel = Literal[
    "email",
    "chat",
    "support_ticket",
    "phone_note",
    "unknown",
]
