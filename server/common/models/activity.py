from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship, backref
from common.models.base import Base


class Activity(Base):
    __tablename__ = 'activity'

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('entity.id'), nullable=False)
    owner = relationship("Entity", back_populates="activities")
    parent_id = Column(Integer, ForeignKey('activity.id'))
    parent = relationship("Activity", backref=backref(
        'children', remote_side=[id]))
    url = Column(String, nullable=False, unique=True, index=True)
    domain = Column(String, nullable=False)
    text = Column(String)
    creation_time = Column(DateTime(timezone=True))

    __table_args__ = (
        Index('owner_creation_time_desc_idx', owner_id, creation_time.desc()),
    )
