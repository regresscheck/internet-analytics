from database import db
from models.activity import Activity
from models.analysis import Analysis
from models.entity import Entity


def create_db():
    db.create_tables([Entity, Activity, Analysis])
