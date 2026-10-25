from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import User, WorkerProfile
from backend.app.modules.auth.router import current_user
from backend.app.modules.workers.schemas import WorkerProfileInput, WorkerProfileOut

router = APIRouter(prefix="/api/workers", tags=["Worker Profiles"])

def require_worker(user: User = Depends(current_user)) -> User:
    if user.role != "worker":
        raise HTTPException(status_code=403, detail="Worker account required")
    return user

@router.get("/me", response_model=WorkerProfileOut)
def get_my_profile(user: User = Depends(require_worker), db: Session = Depends(get_db)):
    profile = db.get(WorkerProfile, user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Complete your worker profile")
    return profile

@router.put("/me", response_model=WorkerProfileOut)
def save_my_profile(body: WorkerProfileInput, user: User = Depends(require_worker), db: Session = Depends(get_db)):
    profile = db.get(WorkerProfile, user.id)
    if profile is None:
        profile = WorkerProfile(user_id=user.id, **body.model_dump(exclude={"photo_url"}))
        db.add(profile)
    else:
        for key, value in body.model_dump(exclude={"photo_url"}).items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile
