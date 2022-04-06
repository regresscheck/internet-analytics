from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from common.models import Entity, Analysis
from common.database import SessionLocal

app = FastAPI()


def get_db():
    return SessionLocal()


@app.get('/analytics/')
async def get_analytics(entity_url: str = "", db: Session = Depends(get_db)):
    # TODO: normalize url here, it can be something meaningless
    try:
        entity = db.query(Entity).where(Entity.url == entity_url).first()
        analysis = entity.analysis
        return {
            "id": analysis.id,
            "owner_id": analysis.owner_id,
            "is_bot": analysis.is_bot,
            "activity_score": analysis.activity_score
        }
    except Exception as e:
        # TODO: proper error handling
        return {
            "found": "no",
            "exception": str(e)
        }
