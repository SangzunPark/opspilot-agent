# pydantic의 BaseModel이 각 필드가 어떤 타입인지만 정의한것이라면 
# Field는 이 필드에 추가 정보나 규칙을 붙이는 도구
# description / default 기본값 / ge le 숫자범위 제한/ min_lengh 문자열길이 제한
from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    chunk_id: str = Field(description="Unique ID for the document chunk.")
    source_title: str = Field(description="Original document file name.")
    text: str = Field(description="Chunk text.")
    chunk_index: int = Field(description="Position of the chunk within the source document.")
