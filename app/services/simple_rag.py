from openai import OpenAI
# get_settings -> env 설정값 읽기
from app.core.config import get_settings
from app.schemas.responses import RetrievedSource, TriageResponse
# search_interanl_docs -> TF-IDF 함수 
from app.tools.retrieval_tools import search_internal_docs

# workflow 밖에서 실행되는 독립함수
def run_simple_rag_triage(
    customer_id: str | None,
    issue_text: str,
    channel: str,
) -> TriageResponse:
    settings = get_settings()

    results = search_internal_docs(query=issue_text, top_k=3)
    # mock 분기 셋업
    # mock 버전을 만드는 이유:
    # 1. 안정적인 테스트를 위해, LLM은 결과값이 불안정하다
    # 2. API 토큰 비용 절약, 모든 테스트에 API를 사용하면 낭비
    # 3. 코드 구조를 완성, 테스트하고 마지막에 LLM_PROVIDER를 openai로 변경해서 테스트 
    if settings.llm_provider == "mock":
        return _run_mock_simple_rag(
            customer_id=customer_id,
            issue_text=issue_text,
            channel=channel,
            results=results,
        )

    if settings.llm_provider != "openai":
        raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

    # 검색된 문서들을 텍스트로 합쳐서 LLM에게 "내부정책문서" 로 전달
    client = OpenAI(api_key=settings.openai_api_key)

    retrieved_context = "\n".join(
        f"[{result.title}]\n{result.snippet}" for result in results
    )

    completion = client.chat.completions.parse(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an operations triage assistant for a B2B SaaS company. "
                    "You must classify an incoming issue and return a structured triage result. "
                    "You have access to retrieved internal policy documents shown below, "
                    "but you do not have access to customer databases, SLA tools, "
                    "or ticket systems. Use only the information provided. "
                    "If a business fact cannot be known from the input and documents, "
                    "use unknown or lower confidence instead of inventing facts."
                ),
            },
            {
                "role": "user",
                "content": _build_simple_rag_prompt(
                    customer_id=customer_id,
                    issue_text=issue_text,
                    channel=channel,
                    retrieved_context=retrieved_context,
                ),
            },
        ],
        response_format=TriageResponse,
    )

    message = completion.choices[0].message

    if message.parsed is None:
        raise ValueError("Simple RAG response could not be parsed into TriageResponse")

    parsed = message.parsed

    # Enforce the definition of simple_rag:
    # it does not use customer DB tools or any business tools
    # DB가 필요한 부분들에 대한 강제보정
    parsed.customer_tier = "unknown"
    parsed.tools_called = []
    parsed.retrieved_sources = [
        RetrievedSource(
            title=result.title,
            snippet=result.snippet,
            score=result.score,
        )
        for result in results
    ]

    return parsed

# LLM 프롬프트 with 제약조건
def _build_simple_rag_prompt(
    customer_id: str | None,
    issue_text: str,
    channel: str,
    retrieved_context: str,
) -> str:
    return f"""
Customer ID:
{customer_id or "not provided"}

Channel:
{channel}

Issue text:
{issue_text}

Retrieved internal policy documents:
{retrieved_context or "No relevant documents found."}

Allowed issue_type values:
- billing_dispute
- technical_outage
- refund_request
- account_access
- cancellation_risk
- unknown

Allowed urgency values:
- low
- medium
- high
- critical

Allowed customer_tier values:
- standard
- premium
- enterprise
- unknown

Important constraints:
- You do not have access to the customer database.
- Set customer_tier to unknown unless the issue text explicitly states the tier.
- You do not have access to SLA tools or ticket systems.
- tools_called must be an empty list.
- Base your recommendation only on the retrieved documents above.
- recommended_next_steps must have at least 1 item.
- reasoning_summary must be at least 10 characters.
"""

# 분류하고 결과를 반환하는 흉내는 내는 mock 셋업
# 일부 값들은 중간 값이나 unknown으로 강제되기 때문에 evaluation에서 차이가 발생 할 수 밖에 없는 구조 
def _run_mock_simple_rag(
    customer_id: str | None,
    issue_text: str,
    channel: str,
    results,
) -> TriageResponse:
    text = issue_text.lower()
    # 
    if any(keyword in text for keyword in ["invoice", "billing", "charge", "charged"]):
        issue_type = "billing_dispute"
        urgency = "medium"
        confidence = 0.65
    elif any(
        keyword in text for keyword in ["outage", "unavailable", "down"]
    ):
        issue_type = "technical_outage"
        urgency = "high"
        confidence = 0.70
    elif "refund" in text:
        issue_type = "refund_request"
        urgency = "medium"
        confidence = 0.65
    elif any(keyword in text for keyword in ["login", "access", "password", "locked"]):
        issue_type = "account_access"
        urgency = "medium"
        confidence = 0.65
    elif any(keyword in text for keyword in ["cancel", "cancellation", "terminate"]):
        issue_type = "cancellation_risk"
        urgency = "high"
        confidence = 0.65
    else:
        issue_type = "unknown"
        urgency = "medium"
        confidence = 0.4

    escalation_required = urgency in {"high", "critical"} or any(
        keyword in text for keyword in ["cancel", "legal", "angry", "escalate"]
    )

    retrieved_sources = [
        RetrievedSource(
            title=result.title,
            snippet=result.snippet,
            score=result.score,
        )
        for result in results
    ]

    return TriageResponse(
        issue_type=issue_type,
        urgency=urgency,
        customer_tier="unknown",
        escalation_required=escalation_required,
        retrieved_sources=retrieved_sources,
        tools_called=[],
        recommended_next_steps=[
            f"Review the issue as {issue_type} based on retrieved policy documents.",
            "Confirm customer details before taking action.",
            "Escalate to a human owner if business impact is confirmed.",
        ],
        confidence=confidence,
        reasoning_summary=(
            "This result was produced by the simple RAG mode. "
            "Internal policy documents were retrieved and passed to the LLM. "
            "Customer profile tools and SLA tools were not used. "
            "Customer tier is unknown because the customer database was not accessed. "
            f"Channel: {channel}. Customer ID provided: {customer_id or 'none'}."
        ),
    )
