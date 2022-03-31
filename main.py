from datetime import datetime
from urllib.parse import urlparse
from consts import OLD_TIMES
from database_helpers import create_db
from models.activity import Activity
from models.analysis import Analysis
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

    entity.last_updated = datetime.now()
    if len(activities) > 0:
        entity.is_analyzed = False
    entity.save()


def fetch_activities():
    update_threshold = datetime.now() - timedelta(days=1)
    entities_to_update = Entity.select().where(
        Entity.last_updated < update_threshold)
    for entity in entities_to_update:
        fetch_entity_activities(entity)


def analyze_entity(entity):
    analysis, _ = Analysis.get_or_create(
        owner=entity, defaults={'is_bot': False})

    activities = list(Activity.select().where(Activity.owner == entity))

    # TODO: do proper analysis
    analysis.is_bot = len(activities) == 1337
    analysis.save()

    entity.is_analyzed = True
    entity.save()


def do_analysis():
    entities_to_analyze = Entity.select().where(Entity.is_analyzed == False)
    for entity in entities_to_analyze:
        analyze_entity(entity)


def create_test_entity():
    url = 'https://tjournal.ru/u/469012-puhlyy-belyash'
    domain = urlparse(url).netloc
    _ = Entity.get_or_create(
        url=url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                           'last_updated': OLD_TIMES})


def require_analysis_for_test():
    entities_to_analyze = Entity.select().where(Entity.is_analyzed == True)
    for entity in entities_to_analyze:
        entity.is_analyzed = False
        entity.save()


if __name__ == '__main__':
    create_db()
    # fetch_page_entities()
    create_test_entity()
    fetch_activities()
    require_analysis_for_test()
    do_analysis()
