from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.intelligence import policy_playground

router = APIRouter(prefix="/api/playground")


@router.get("/simulate")
def simulate(threshold: float = 50, app_id: int | None = None, db: Session = Depends(get_db)):
    return policy_playground.simulate(db, threshold, app_id)


@router.get("/recommend")
def recommend(app_id: int | None = None, db: Session = Depends(get_db)):
    return policy_playground.recommend_threshold(db, app_id)


@router.get("/curve")
def curve(app_id: int | None = None, db: Session = Depends(get_db)):
    result = policy_playground.recommend_threshold(db, app_id)
    return result["candidates"]
