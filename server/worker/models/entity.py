from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from enum import IntEnum
from worker.models.base import Base


class EntityType(IntEnum):
    USER = 1


class Entity(Base):
    __tablename__ = 'entity'

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(Enum(EntityType))
    url = Column(String, nullable=False, unique=True, index=True)
    domain = Column(String, nullable=False)
    last_updated = Column(DateTime)
    is_analyzed = Column(Boolean, default=False, index=True)
    activities = relationship("Activity", back_populates="owner")
    analysis = relationship("Analysis", back_populates="owner", uselist=False)
