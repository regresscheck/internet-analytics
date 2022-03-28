from peewee import BigAutoField, ForeignKeyField, DateTimeField, TextField

from models.entity import Entity
from models.base import BaseModel


class Activity(BaseModel):
    id = BigAutoField(primary_key=True)
    owner = ForeignKeyField(Entity, backref='activites')
    parent = ForeignKeyField('self', backref='children', null=True)
    url = TextField(unique=True)
    domain = TextField()
    text = TextField(null=True)
    creation_time = DateTimeField()
