from datetime import datetime, timedelta
from worker.parsing.crawler import Crawler
from common.models import Activity, Analysis, Entity
from common.database_helpers import create_db, create_or_update, session
from datetime import datetime
from worker.logging_utils import setup_logging
import logging

setup_logging()

logger = logging.getLogger(__name__)


def analyze_entity(entity):
    analysis, _ = create_or_update(session, Analysis, owner=entity)

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
    urls = ['https://pikabu.ru/']
    crawler = Crawler()
    crawler.crawl(urls)


def main():
    try:
        create_db()
        crawl()
    except KeyboardInterrupt:
        logger.info("Stopping worker")
    except Exception as e:
        logger.exception("Unhandled exception")
        raise e
    # do_analysis()
