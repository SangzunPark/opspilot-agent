# LLM이 반환할 출력을 정의한 스키마
# simple_rag 에서는 TriageResponse 전체를 LLM을 생성하지만 
# agentic_llm 에서는 LLM이 추천 부분만 생성 이후 workflow 부분과 결합
from pydantic import BaseModel, Field
 

class LLMRecommendation(BaseModel):
    recommended_next_steps: list[str] = Field(
        min_length=2,
        max_length=6,
        description="Actionable next steps for the operations team.",
    )
    reasoning_summary: str = Field(
        min_length=20,
        description="Brief explanation grounded in retrieved sources and tool results.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the recommendation.",
    )

