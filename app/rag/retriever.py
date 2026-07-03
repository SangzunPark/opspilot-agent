from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.rag.chunker import build_chunks_from_documents
from app.rag.document_loader import load_markdown_documents
from app.schemas.rag import DocumentChunk
from app.schemas.tool_outputs import DocumentSearchResult

# TF(Term Frequency) 이 문서에서 특정 단어가 얼마나 자주 나오나
# IDF(InverseDocumentFrequency) 이 단어가 전체 문서들 중에서 얼마나 희귀한가

class TfidfDocumentRetriever:
    # 변수 초기화, _build_index 호출 
    def __init__(self, docs_path: Path) -> None:
        self.docs_path = docs_path
        self.chunks: list[DocumentChunk] = []
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.chunk_matrix = None
        self._build_index()
    # 문서 읽기, 청킹, TF-IDF 행렬 생성
    def _build_index(self) -> None:
        documents = load_markdown_documents(self.docs_path)
        self.chunks = build_chunks_from_documents(documents)

        if not self.chunks:
            self.chunk_matrix = None
            return

        texts = [chunk.text for chunk in self.chunks]
        self.chunk_matrix = self.vectorizer.fit_transform(texts)
    # 검색어 벡터화, 유사도 계산, 결과 반환
    def search(self, query: str, top_k: int = 3) -> list[DocumentSearchResult]:
        if not query.strip() or not self.chunks or self.chunk_matrix is None:
            return []

        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.chunk_matrix).flatten()

        ranked_indices = similarities.argsort()[::-1]

        results: list[DocumentSearchResult] = []

        for index in ranked_indices[:top_k]:
            score = float(similarities[index])

            if score <= 0:
                continue

            chunk = self.chunks[index]
            results.append(
                DocumentSearchResult(
                    title=chunk.source_title,
                    snippet=chunk.text,
                    score=round(score, 4),
                )
            )

        return results
