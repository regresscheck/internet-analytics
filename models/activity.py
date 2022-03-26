from peewee import BigAutoField, ForeignKeyField

from models.entity import Entity
from models.base import BaseModel


class Activity(BaseModel):
    id = BigAutoField(primary_key=True)
    owner = ForeignKeyField(Entity, backref='activites')
    parent = ForeignKeyField('self', backref='children', null=True)
