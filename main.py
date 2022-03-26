from datetime import datetime
from database_helpers import create_db
from models.entity import Entity
from parsing.entity_extraction import extract_entities
from datetime import datetime, timedelta


def fetch_page_entities():
    request_url = 'https://tjournal.ru/flood/567408-mechty-o-budushchem'

    entities = extract_entities(request_url)


def fetch_entity_activities(entity):
    # TODO: do actual fetch
    print(entity)

    #entity.last_updated = datetime.now()
    # entity.save()


def fetch_activities():
    update_threshold = datetime.now() - timedelta(days=1)
    entities_to_update = Entity.select().where(
        Entity.last_updated < update_threshold)
    for entity in entities_to_update:
        fetch_entity_activities(entity)


if __name__ == '__main__':
    create_db()
    fetch_page_entities()
    fetch_activities()
