from datetime import datetime
from urllib.parse import urlparse
from consts import OLD_TIMES
from database_helpers import create_db
from models.entity import Entity, EntityType
from parsing.activity_extraction import extract_entity_activities
from parsing.entity_extraction import extract_entities
from datetime import datetime, timedelta


def fetch_page_entities():
    request_url = 'https://tjournal.ru/flood/567408-mechty-o-budushchem'

    entities = extract_entities(request_url)


def fetch_entity_activities(entity):
    print(entity.url)
    activities = extract_entity_activities(entity)
    print(activities)

    #entity.last_updated = datetime.now()
    # entity.save()


def fetch_activities():
    update_threshold = datetime.now() - timedelta(days=1)
    entities_to_update = Entity.select().where(
        Entity.last_updated < update_threshold)
    for entity in entities_to_update:
        fetch_entity_activities(entity)


def create_test_entity():
    url = 'https://tjournal.ru/u/469012-puhlyy-belyash'
    domain = urlparse(url).netloc
    _ = Entity.get_or_create(
        url=url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                           'last_updated': OLD_TIMES})


if __name__ == '__main__':
    create_db()
    fetch_page_entities()
    # create_test_entity()
    fetch_activities()
