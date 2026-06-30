from pathlib import Path

from app.schemas.tool_outputs import DocumentSearchResult

INTERNAL_DOCS_PATH = Path("data/internal_docs")


def search_internal_docs(query: str, top_k: int = 3) -> list[DocumentSearchResult]:
    query_terms = {
        term.lower()
        for term in query.replace("_", " ").split()
        if len(term.strip()) >= 3
    }

    results: list[DocumentSearchResult] = []

    for path in INTERNAL_DOCS_PATH.glob("*.md"):
        content = path.read_text(encoding="utf-8")
        normalized_content = content.lower()

        matched_terms = [
            term for term in query_terms if term in normalized_content
        ]

        if not matched_terms:
            continue

        score = min(1.0, len(matched_terms) / max(len(query_terms), 1))

        snippet = _make_snippet(content, matched_terms[0])

        results.append(
            DocumentSearchResult(
                title=path.name,
                snippet=snippet,
                score=score,
            )
        )

    results.sort(key=lambda item: item.score, reverse=True)

    return results[:top_k]


def _make_snippet(content: str, matched_term: str, window: int = 180) -> str:
    lower_content = content.lower()
    index = lower_content.find(matched_term)

    if index == -1:
        return content[:window].replace("\n", " ").strip()

    start = max(index - window // 2, 0)
    end = min(index + window // 2, len(content))

    return content[start:end].replace("\n", " ").strip()
