from peewee import BigAutoField, ForeignKeyField, DateTimeField, TextField

from models.entity import Entity
from models.base import BaseModel


class Activity(BaseModel):
    id = BigAutoField(primary_key=True)
    owner = ForeignKeyField(Entity, backref='activites')
    parent = ForeignKeyField('self', backref='children', null=True)
    url = TextField(unique=True, index=True)
    domain = TextField()
    text = TextField(null=True)
    creation_time = DateTimeField()


Activity.add_index(Activity.owner, Activity.creation_time.desc())
