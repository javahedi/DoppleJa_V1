"""Idempotent local overlay integration. Run from DoppleJa_V1 repository root."""
from pathlib import Path
p = Path('backend/app/main.py')
s = p.read_text()
import_line = 'from backend.app.modules.frontend.router import router as frontend_router, assets as frontend_assets'
if import_line not in s:
    s = import_line + '\n' + s
if 'app.include_router(frontend_router)' not in s:
    s += '\n# DoppleJa mobile-first frontend (same origin as cookie-based API)\napp.include_router(frontend_router)\napp.mount("/app-assets", frontend_assets, name="app-assets")\n'
p.write_text(s)
p = Path('compose.yaml'); s = p.read_text()
if './frontend:/code/frontend:ro' not in s:
    anchor = '      - ./backend:/code/backend'
    if anchor not in s:
        raise SystemExit('Expected backend bind mount not found in compose.yaml. Add - ./frontend:/code/frontend:ro to api.volumes manually.')
    s = s.replace(anchor,anchor+'\n      - ./frontend:/code/frontend:ro',1)
    p.write_text(s)
print('Installed routes and Docker frontend volume. Existing services unchanged.')
