# langchain 의 RecursiveCharacterTextSplitter와 는 달리 Langgraph를 위해 직접 구현한 청킹 방식으로,
# langchain에 비해 좀 더 세밀한 조정이 가능, 특히 메타데이터를 직접 관리한다.
from app.schemas.rag import DocumentChunk


def split_text_into_chunks(
    source_title: str,
    text: str,
    chunk_size: int = 600,
    overlap: int = 100,
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0:
        raise ValueError("overlap must be non-negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    cleaned_text = " ".join(text.split())

    if not cleaned_text:
        return []

    chunks: list[DocumentChunk] = []
    start = 0
    chunk_index = 0

    while start < len(cleaned_text):
        end = min(start + chunk_size, len(cleaned_text))
        chunk_text = cleaned_text[start:end]

        chunks.append(
            DocumentChunk(
                chunk_id=f"{source_title}::{chunk_index}",
                source_title=source_title,
                text=chunk_text,
                chunk_index=chunk_index,
            )
        )

        if end == len(cleaned_text):
            break

        start = end - overlap
        chunk_index += 1

    return chunks


def build_chunks_from_documents(
    documents: dict[str, str],
    chunk_size: int = 600,
    overlap: int = 100,
) -> list[DocumentChunk]:
    all_chunks: list[DocumentChunk] = []

    for source_title, text in documents.items():
        all_chunks.extend(
            split_text_into_chunks(
                source_title=source_title,
                text=text,
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )

    return all_chunks
