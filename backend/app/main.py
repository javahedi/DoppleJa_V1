from fastapi import FastAPI
from backend.app.modules.auth.router import router as auth_router
from backend.app.modules.workers.router import router as workers_router
from backend.app.modules.employers.router import router as employers_router
from backend.app.modules.jobs.router import router as jobs_router

from backend.app.modules.swipes.router import router as swipes_router
from backend.app.modules.matching.router import router as matching_router
from backend.app.modules.chat.router import router as chat_router

app = FastAPI(title="DoppleJa API", description="Two sides. Two Yes. One Match.", version="1.0.0")
app.include_router(auth_router)
app.include_router(workers_router)
app.include_router(employers_router)
app.include_router(jobs_router)
app.include_router(swipes_router)
app.include_router(matching_router)
app.include_router(chat_router)

@app.get('/api/health', tags=['System'])
def health_check():
    return {'status': 'ok', 'app': 'DoppleJa', 'version': '1.0.0'}
