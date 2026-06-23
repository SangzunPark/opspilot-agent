from fastapi import FastAPI

app = FastAPI(
    title="OpsPilot Agent",
    description="Agentic AI assistant for issue triage",
    version="0.1.0"
)


@app.get("/health")
def health_check() -> dict[str,str]:
    return {"status": "ok"}