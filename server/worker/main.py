from datetime import datetime
from urllib.parse import urlparse
from common.consts import OLD_TIMES
from common.database_helpers import create_db, get_or_create, session
from common.models import Activity, Analysis, Entity, EntityType
from worker.parsing.activity_extraction import extract_entity_activities
from worker.parsing.entity_extraction import extract_entities
from datetime import datetime, timedelta


def fetch_page_entities():
    request_url = 'https://tjournal.ru/flood/567408-mechty-o-budushchem'

    entities = extract_entities(request_url)


def fetch_entity_activities(entity):
    print(entity.url)
    activities = extract_entity_activities(entity)

    entity.last_updated = datetime.now()
    if len(activities) > 0:
        entity.is_analyzed = False
    session.commit()


def fetch_activities():
    update_threshold = datetime.now() - timedelta(days=1)
    entities_to_update = session.query(Entity).filter(
        Entity.last_updated < update_threshold)
    for entity in entities_to_update:
        fetch_entity_activities(entity)


def analyze_entity(entity):
    analysis, _ = get_or_create(session, Analysis, owner=entity)

    activities = session.query(Activity).filter(
        Activity.owner == entity).all()

    recent_activities_window_days = 30
    recent_activities_date = datetime.now(
    ) - timedelta(days=recent_activities_window_days)
    recent_activities = filter(
        lambda activity: activity.creation_time > recent_activities_date, activities)
    analysis.activity_score = len(activities) / recent_activities_window_days
    entity.is_analyzed = True
    session.commit()


def do_analysis():
    entities_to_analyze = session.query(Entity).filter(
        Entity.is_analyzed == False)
    for entity in entities_to_analyze:
        analyze_entity(entity)


def create_test_entity():
    url = 'https://tjournal.ru/u/469012-puhlyy-belyash'
    domain = urlparse(url).netloc
    _ = get_or_create(session, Entity,
                      url=url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                         'last_updated': OLD_TIMES})


def require_analysis_for_test():
    entities_to_analyze = session.query(
        Entity).filter(Entity.is_analyzed == True)
    for entity in entities_to_analyze:
        entity.is_analyzed = False
    session.commit()


def main():
    create_db()
    # fetch_page_entities()
    create_test_entity()
    fetch_activities()
    require_analysis_for_test()
    do_analysis()
