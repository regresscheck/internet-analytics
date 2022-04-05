from sqlalchemy import Column, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from common.models.base import Base


class Analysis(Base):
    __tablename__ = 'analysis'

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('entity.id'), nullable=False)
    owner = relationship("Entity", back_populates="analysis")
    is_bot = Column(Boolean, default=False)
    activity_score = Column(Float, default=0.0)
