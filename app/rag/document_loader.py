# 추후 데이터 출처가 변경될 경우(AWS,DB..) 이 데이터 로더 부분만 변경하면 된다. 다수의 연관된 코드 수정을 방지
from pathlib import Path

def load_markdown_documents(docs_path: Path) -> dict[str, str]:
    documents: dict[str, str] = {}

    for path in sorted(docs_path.glob("*.md")):
        documents[path.name] = path.read_text(encoding="utf-8")

    return documents
