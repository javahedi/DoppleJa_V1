"""Serve the same-origin vanilla-JS frontend alongside FastAPI APIs.

The frontend directory is a Docker read-only bind mount in local development.
Production will use a built image or nginx with the same paths.
"""
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parents[4] / 'frontend'
router = APIRouter(include_in_schema=False)

@router.get('/')
@router.get('/app')
def frontend_index():
    return FileResponse(BASE / 'index.html')

assets = StaticFiles(directory=str(BASE), check_dir=True)
