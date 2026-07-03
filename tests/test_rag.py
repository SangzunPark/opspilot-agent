from pathlib import Path

from app.rag.chunker import build_chunks_from_documents, split_text_into_chunks
from app.rag.document_loader import load_markdown_documents
from app.rag.retriever import TfidfDocumentRetriever

# 청킹 작동 확인
def test_split_text_into_chunks_creates_chunks() -> None:
    text = "Billing disputes require invoice review. " * 50

    chunks = split_text_into_chunks(
        source_title="billing_policy.md",
        text=text,
        chunk_size=200,
        overlap=50,
    )

    assert len(chunks) > 1
    assert chunks[0].source_title == "billing_policy.md"
    assert chunks[0].chunk_id == "billing_policy.md::0"

# 복수의 문서 청킹 확인
def test_build_chunks_from_documents() -> None:
    documents = {
        "billing_policy.md": "Billing disputes require invoice review.",
        "refund_policy.md": "Refund requests require eligibility checks.",
    }

    chunks = build_chunks_from_documents(documents)

    assert len(chunks) == 2
    assert {chunk.source_title for chunk in chunks} == {
        "billing_policy.md",
        "refund_policy.md",
    }

# 실제 파일 리딩 확인
def test_load_markdown_documents_reads_internal_docs() -> None:
    documents = load_markdown_documents(Path("data/internal_docs"))

    assert "billing_policy.md" in documents
    assert "premium_customer_sla.md" in documents
    assert "Billing Policy" in documents["billing_policy.md"]

# Billing 관련 검색 확인 (문서 읽기 + 청킹 + TF-IDF 행렬 생성 / 검색)
def test_tfidf_retriever_returns_billing_policy_for_billing_query() -> None:
    retriever = TfidfDocumentRetriever(docs_path=Path("data/internal_docs"))

    results = retriever.search("invoice billing dispute", top_k=3)

    titles = [result.title for result in results]

    assert "billing_policy.md" in titles

# Outage 관련 검색 확인 (Billing 테스트와 같은 방식이나 outage에 대해 검색)
def test_tfidf_retriever_returns_outage_guide_for_outage_query() -> None:
    retriever = TfidfDocumentRetriever(docs_path=Path("data/internal_docs"))

    results = retriever.search("service unavailable outage engineering", top_k=3)

    titles = [result.title for result in results]

    assert "technical_outage_guide.md" in titles
