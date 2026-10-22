"""Add Likes router to the existing main.py; safe to run repeatedly."""
from pathlib import Path
main=Path('backend/app/main.py')
source=main.read_text()
import_line='from backend.app.modules.likes.router import router as likes_router'
include_line='app.include_router(likes_router)'
if import_line not in source:
    anchor='app = FastAPI('
    assert anchor in source, 'Cannot find FastAPI app; inspect main.py first.'
    source=source.replace(anchor, import_line+'\n\n'+anchor, 1)
if include_line not in source:
    anchor='app.include_router(auth_router)'
    assert anchor in source, 'Cannot find router registration; inspect main.py first.'
    source=source.replace(anchor, anchor+'\n'+include_line, 1)
main.write_text(source)
print('Likes router registered in backend/app/main.py')
