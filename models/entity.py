import datetime
from peewee import IntegerField, TextField, DateTimeField
from enum import IntEnum

from models.base import BaseModel


class EntityType(IntEnum):
    USER = 1


class EntityTypeField(IntegerField):
    def db_value(self, enum_value):
        if not isinstance(enum_value, EntityType):
            raise TypeError('Invalid type, expected EntityType')
        return super().db_value(enum_value.value)

    def python_value(self, value):
        return EntityType(value)


class Entity(BaseModel):
    entity_type = EntityTypeField()
    url = TextField(unique=True, index=True)
    domain = TextField()
    last_updated = DateTimeField()
