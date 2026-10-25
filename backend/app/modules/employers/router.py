from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import EmployerProfile, User
from backend.app.modules.auth.router import current_user
from backend.app.modules.employers.schemas import EmployerProfileInput, EmployerProfileOut

router = APIRouter(prefix="/api/employers", tags=["Employer Profiles"])


def require_employer(user: User = Depends(current_user)) -> User:
    if user.role != "employer":
        raise HTTPException(status_code=403, detail="Employer account required")
    return user


@router.get("/me", response_model=EmployerProfileOut)
def get_my_profile(
    user: User = Depends(require_employer), db: Session = Depends(get_db)
):
    profile = db.get(EmployerProfile, user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Complete your employer profile")
    return profile


@router.put("/me", response_model=EmployerProfileOut)
def save_my_profile(
    body: EmployerProfileInput,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
):
    profile = db.get(EmployerProfile, user.id)
    if profile is None:
        profile = EmployerProfile(user_id=user.id, **body.model_dump(exclude={"photo_url"}))
        db.add(profile)
    else:
        for key, value in body.model_dump(exclude={"photo_url"}).items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile
