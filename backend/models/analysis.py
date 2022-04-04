from enum import unique
from models.base import BaseModel
from peewee import BigAutoField, ForeignKeyField, BooleanField, DoubleField

from models.entity import Entity


class Analysis(BaseModel):
    id = BigAutoField(primary_key=True)
    owner = ForeignKeyField(Entity, backref='activites', unique=True)
    is_bot = BooleanField(default=False)
    activity_score = DoubleField(default=0.0)
