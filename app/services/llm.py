from openai import OpenAI

from app.core.config import get_settings
from app.schemas.llm_outputs import LLMRecommendation
from app.schemas.state import OpsAgentState
# LLM은 추천생성만 담당, 앞단계는 workflow에서 생성된 state를 받아서 진행

def generate_llm_recommendation(state: OpsAgentState) -> LLMRecommendation:
    settings = get_settings()

    if settings.llm_provider == "mock":
        return _generate_mock_recommendation(state)

    if settings.llm_provider != "openai":
        raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

    client = OpenAI(api_key=settings.openai_api_key)

    completion = client.chat.completions.parse(
        model=settings.openai_model,
        # 마지막줄에 "do no invent policy details..." 부분을 통해 환각 방지
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an operations triage assistant for a B2B SaaS company. "
                    "You generate concise, actionable next steps for internal operations teams. "
                    "Your recommendations must be grounded in the provided issue, "
                    "retrieved policy sources, customer tier, SLA result, "
                    "escalation decision, and ticket draft. "
                    "Do not invent policy details that are not provided."
                ),
            },
            {
                "role": "user",
                "content": _build_recommendation_prompt(state),
            },
        ],
        response_format=LLMRecommendation,
    )

    message = completion.choices[0].message

    if message.parsed is None:
        raise ValueError("LLM response could not be parsed into LLMRecommendation")

    return message.parsed


def _build_recommendation_prompt(state: OpsAgentState) -> str:
    retrieved_sources = "\n".join(
        f"- {source.title}: {source.snippet}"
        for source in state.retrieved_sources
    )

    tool_calls = "\n".join(
        f"- {tool.tool_name}: {tool.output_summary}"
        for tool in state.tools_called
    )

    return f"""
Issue text:
{state.issue_text}

Classified issue type:
{state.issue_type}

Customer tier:
{state.customer_tier}

Urgency:
{state.urgency}

Escalation required:
{state.escalation_required}

Assigned team:
{state.assigned_team}

Ticket title:
{state.ticket_title}

Retrieved policy sources:
{retrieved_sources or "No retrieved sources."}

Tool call summaries:
{tool_calls or "No tool calls recorded."}

Generate 2 to 6 practical next steps for the operations team.
The steps should be specific, business-relevant, and safe.
If escalation is required, include that clearly.
"""


def _generate_mock_recommendation(state: OpsAgentState) -> LLMRecommendation:
    next_steps = [
        f"Review the case as a {state.issue_type} issue.",
        f"Route the ticket to {state.assigned_team or 'Operations Triage'}.",
    ]

    if state.retrieved_sources:
        next_steps.append(
            f"Use the guidance from {state.retrieved_sources[0].title} before responding."
        )

    if state.escalation_required:
        next_steps.append(
            "Escalate to a human owner before sending a final customer response."
        )
    else:
        next_steps.append("Handle through the standard support process.")

    return LLMRecommendation(
        recommended_next_steps=next_steps,
        reasoning_summary=(
            f"The issue was classified as {state.issue_type}. "
            f"Customer tier is {state.customer_tier} "
            "(verified via customer profile tool). "
            f"SLA-based urgency is {state.urgency}. "
            f"Escalation required: {state.escalation_required}. "
            "Recommendation is grounded in retrieved policy documents and tool outputs."
        ),
        confidence=max(state.confidence, 0.75),
    )
