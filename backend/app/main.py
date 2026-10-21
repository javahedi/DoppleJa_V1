from fastapi import FastAPI

app = FastAPI(
    title="DoppleJa API",
    description="Two sides. Two Yes. One Match.",
    version="1.0.0",
)


@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "app": "DoppleJa",
        "version": "1.0.0"
    }
