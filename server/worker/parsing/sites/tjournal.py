from datetime import datetime
from worker.parsing.site_parser import SiteParser
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from common.consts import OLD_TIMES
from common.database_helpers import create_or_update, session
from common.models.activity import Activity
from common.models.entity import Entity, EntityType
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

SUPPORTED_DOMAIN = 'tjournal.ru'


class TJournalParser(SiteParser):
    @staticmethod
    def get_supported_domain():
        return SUPPORTED_DOMAIN

    def _is_post_url(self):
        try:
            self.driver.find_element(By.CLASS_NAME, 'page--entry')
            return True
        except NoSuchElementException:
            return False

    def _expand_comments(self):
        self.driver.execute_script(
            "const button = document.querySelector('.comments__content_wrapper__button > .ui-button'); if (button !== null) { button.click(); }")
        self.driver.execute_script(
            "async function run() { while (true) { const button = document.querySelector('.comment__load-more.comment__inline-action'); if (button === null) { break; } if (!button.classList.contains('comment__load-more-waiting')) { button.click(); } await new Promise(resolve => setTimeout(resolve, 300));}} run()")
        try:
            _ = WebDriverWait(self.driver, 60).until_not(
                EC.presence_of_element_located((By.CLASS_NAME, 'comment__load-more')))
        except TimeoutException:
            logger.warning("Timed out while waiting for all comments to load")

    def _get_entity_from_comment(self, comment):
        try:
            entity_url = comment.find_element(
                By.CSS_SELECTOR, "a.comment__author").get_attribute('href')
        except NoSuchElementException:
            # Anonymous user
            return None
        domain = urlparse(entity_url).netloc
        # TODO: insert all entities with a single commit
        entity, _ = create_or_update(session, Entity,
                                     url=entity_url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                                               'last_updated': OLD_TIMES})
        self.total_entities += 1
        return entity

    def _get_activity_from_comment(self, comment, entity, parent):
        activity_url = comment.find_element(
            By.CSS_SELECTOR, "a.comment__detail").get_attribute('href')
        creation_time_str = comment.find_element(
            By.CSS_SELECTOR, "a.comment__detail > time").get_attribute('data-date')
        creation_time = datetime.fromtimestamp(int(creation_time_str))
        try:
            text = comment.find_element(
                By.CSS_SELECTOR, "div.comment__text").get_attribute('innerHTML').strip()
        except NoSuchElementException:
            # no text(e.g. just a pic)
            text = ""

        domain = urlparse(activity_url).netloc
        defaults = {'text': text, 'owner': entity,
                    'creation_time': creation_time, 'domain': domain}
        if parent is not None:
            defaults['parent'] = parent
        activity, _ = create_or_update(
            session, Activity, url=activity_url, defaults=defaults)
        self.total_activities += 1
        return activity

    def _extract_post_activity(self):
        main_story = self.driver.find_element(
            By.CSS_SELECTOR, "div.l-entry")
        try:
            author = main_story.find_element(
                By.CSS_SELECTOR, '.content-header-author')
        except NoSuchElementException:
            # TODO: verify if it's possible
            logger.warning('Failed to extract post author')
            return None

        entity_url = author.get_attribute('href')
        domain = urlparse(entity_url).netloc
        entity, _ = create_or_update(session, Entity,
                                     url=entity_url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                                               'last_updated': OLD_TIMES})
        self.total_entities += 1

        link_element = main_story.find_element(
            By.CSS_SELECTOR, 'div[data-io-article-url]')
        activity_url = link_element.get_attribute('data-io-article-url')
        domain = urlparse(activity_url).netloc

        creation_time_str = main_story.find_element(
            By.CSS_SELECTOR, 'div.content-header__item time.time').get_attribute('data-date')
        creation_time = datetime.fromtimestamp(int(creation_time_str))

        try:
            title = main_story.find_element(
                By.CSS_SELECTOR, 'h1.content-title').get_attribute('innerHTML').strip()
        except NoSuchElementException:
            title = ""
        inner_text = main_story.find_element(
            By.CSS_SELECTOR, 'div.content--full').get_attribute('innerHTML').strip()
        text = title + "\n" + inner_text

        activity, _ = create_or_update(session, Activity, url=activity_url, defaults={'text': text, 'owner': entity,
                                                                                      'creation_time': creation_time, 'domain': domain})
        self.total_activities += 1
        return activity

    def _extract_comments_recursive(self, parent_id, parent_activity):
        # TODO: this approach is very slow. Better idea - fetch all comments and build the graph
        comments = self.driver.find_elements(
            By.CSS_SELECTOR, f'div.comment[data-reply_to="{parent_id}"]')
        for comment in comments:
            comment_id = comment.get_attribute('data-id')
            entity = self._get_entity_from_comment(comment)
            if entity is not None:
                activity = self._get_activity_from_comment(
                    comment, entity, parent_activity)
            else:
                activity = None
            # TODO: if comment was left by anonymous user, context of child comments is completely lost
            self._extract_comments_recursive(comment_id, activity)

    def parse(self):
        if not self._is_post_url():
            return
        self._expand_comments()

        post_activity = self._extract_post_activity()

        self._extract_comments_recursive(0, post_activity)
