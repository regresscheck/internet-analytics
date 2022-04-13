from datetime import datetime, timedelta
from worker.parsing.crawler import Crawler
from common.models import Activity, Analysis, Entity
from common.database_helpers import create_db, get_or_create, session
from datetime import datetime
from worker.logging_utils import setup_logging


setup_logging()


def analyze_entity(entity):
    analysis, _ = get_or_create(session, Analysis, owner=entity)

    activities = session.query(Activity).filter(
        Activity.owner == entity).all()

    recent_activities_window_days = 30
    recent_activities_date = datetime.now(
    ) - timedelta(days=recent_activities_window_days)
    recent_activities = list(filter(
        lambda activity: activity.creation_time > recent_activities_date, activities))
    analysis.activity_score = len(
        recent_activities) / recent_activities_window_days
    entity.is_analyzed = True
    session.commit()


def do_analysis():
    entities_to_analyze = session.query(Entity).filter(
        Entity.is_analyzed == False)
    for entity in entities_to_analyze:
        analyze_entity(entity)


def crawl():
    urls = ['https://pikabu.ru/best']
    crawler = Crawler()
    crawler.crawl(urls)


def main():
    create_db()
    crawl()
    # do_analysis()
