from urllib.parse import urlparse
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from common.models import Entity, Analysis
from common.database import SessionLocal
from common.consts import OLD_TIMES
from common.models.entity import EntityType

app = FastAPI()


def get_db():
    return SessionLocal()


@app.get('/analytics/')
async def get_analytics(entity_url: str = "", db: Session = Depends(get_db)):
    # TODO: normalize url here, it can be something meaningless
    try:
        entity = db.query(Entity).where(Entity.url == entity_url).first()
        if entity is None:
            # TODO: verify that link is actual entity link
            domain = urlparse(entity_url).netloc
            entity = Entity(url=entity_url, entity_type=EntityType.USER, domain=domain,
                            last_updated=OLD_TIMES)
            db.add(entity)
            db.commit()
            return {
                "found": "no",
                "message": "No data found for valid Entity. Adding it for feature analysis"
            }
        if entity.is_analyzed:
            analysis = entity.analysis
            return {
                "id": analysis.id,
                "owner_id": analysis.owner_id,
                "is_bot": analysis.is_bot,
                "activity_score": analysis.activity_score
            }
        else:
            return {
                "found": "no",
                "message": "No analysis found for given Entity"
            }
    except Exception as e:
        # TODO: proper error handling
        return {
            "found": "no",
            "exception": str(e)
        }
