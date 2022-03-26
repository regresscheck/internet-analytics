from database_helpers import create_db
from models.entity import Entity
from parsing.entity_extraction import extract_entities


if __name__ == '__main__':
    create_db()
    request_url = 'https://tjournal.ru/flood/567408-mechty-o-budushchem'

    entities = extract_entities(request_url)
    for entity in entities:
        old_exists = Entity.select().where(Entity.url == entity.url).exists()
        if not old_exists:
            entity.save()
