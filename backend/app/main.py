from fastapi import FastAPI
from backend.app.modules.auth.router import router as auth_router

app = FastAPI(
    title="DoppleJa API",
    description="Two sides. Two Yes. One Match.",
    version="1.0.0",
)
app.include_router(auth_router)


@app.get("/api/health", tags=["System"])
def health_check():
    return {"status": "ok", "app": "DoppleJa", "version": "1.0.0"}
