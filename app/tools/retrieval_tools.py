from functools import lru_cache
from pathlib import Path

from app.rag.retriever import TfidfDocumentRetriever
from app.schemas.tool_outputs import DocumentSearchResult

# 키워드 매칭 즉 단어 존재 여부만 확인한 week2의 retrieval_tools와는 다르게
# 이 retrival_tools는 TF_IDF+cosine similarity 방식으로 작동
#  retriever.py 파일을 검색엔진으로 사용
INTERNAL_DOCS_PATH = Path("data/internal_docs")

# @는 데코레이터로 함수에 추가 기능을 붙이는 파이썬 기능
# lru_cache는 캐싱기능을 활성화 하는 기능
# 즉 아래 코드는 캐싱코드 활성화를 함수에 붙이는 역할
# maxsize는 결과 저장 설정
# TfidfDocumentRetriever 객체를 만들때 즉 TF-IDF 행렬을 만들때 캐싱을 활용 불필요하고 비용이 드는 반복을 피함 
@lru_cache(maxsize=1)  
def get_retriever() -> TfidfDocumentRetriever:
    return TfidfDocumentRetriever(docs_path=INTERNAL_DOCS_PATH)


def search_internal_docs(query: str, top_k: int = 3) -> list[DocumentSearchResult]:
    retriever = get_retriever()
    return retriever.search(query=query, top_k=top_k)
