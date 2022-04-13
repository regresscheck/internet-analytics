import logging
from datetime import datetime
from furl import furl
from worker.parsing.selenium_utils import last_element_changed
from worker.parsing.site_parser import SiteParser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from common.consts import OLD_TIMES
from common.database_helpers import get_or_create, session
from common.models.activity import Activity
from common.models.entity import Entity, EntityType
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


SUPPORTED_DOMAIN = 'pikabu.ru'


class PikabuParser(SiteParser):
    MAX_SCROLLS = 15

    @staticmethod
    def get_supported_domain():
        return SUPPORTED_DOMAIN

    def _is_post_url(self):
        if not self.driver.current_url.startswith('https://pikabu.ru/story/'):
            return False
        # Ignore sponsor/ad posts
        elements = self.driver.find_elements(By.CLASS_NAME, 'story__sponsor')
        return len(elements) == 0

    def _get_post_author_entities(self):
        authors = self.driver.find_elements(
            By.XPATH, "//a[contains(@class, 'story__user-link')]")
        for author in authors:
            entity_url = author.get_attribute('href')
            domain = urlparse(entity_url).netloc
            _ = get_or_create(session, Entity,
                              url=entity_url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                                        'last_updated': OLD_TIMES})
            self.total_entities += 1

    def _expand_comments(self):
        # First button has different class
        self.driver.execute_script(
            "const button = document.querySelector('.comments__more-button'); if (button !== null) { button.click(); }")
        self.driver.execute_script(
            "while (true) { const button = document.querySelector('.comment__more'); if (button === null) { break; } button.click(); }")
        # Expand each comment subtree, may take multiple iterations
        # TODO: verify it works on very deep trees
        self.driver.execute_script(
            "while (true) {const collapsed = document.querySelectorAll('.comment-toggle-children_collapse'); if (collapsed.length == 0) {break;} collapsed.forEach(element => element.click())}")
        _ = WebDriverWait(self.driver, 15).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, 'comment__placeholder')))

    def _get_entity_from_comment(self, comment):
        try:
            entity_url = comment.find_element(
                By.XPATH, ".//a[contains(@class, 'user')]").get_attribute('href')
        except NoSuchElementException as e:
            # User is banned/deleted
            return None
        except StaleElementReferenceException as e:
            # TODO: investigate why
            # Test link: https://pikabu.ru/story/surovaya_vzroslaya_zhizn_9004310
            logger.error(
                f"Stale element found while parsing URL {self.driver.current_url}")
            return None
        domain = urlparse(entity_url).netloc
        # TODO: insert all entities with a single commit
        entity, _ = get_or_create(session, Entity,
                                  url=entity_url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                                            'last_updated': OLD_TIMES})
        self.total_entities += 1
        return entity

    def _get_activity_from_comment(self, comment, entity):
        activity_url = comment.find_element(
            By.XPATH, ".//a[contains(@class, 'comment__tool') and contains(@data-role, 'link')]").get_attribute('href')
        creation_time_str = comment.find_element(
            By.XPATH, ".//time[contains(@class, 'comment__datetime')]").get_attribute('datetime')
        # 2022-04-10T06:31:03+03:00
        # Python does not like colon in timezone, drop it
        if creation_time_str[-3:-2] == ':':
            creation_time_str = creation_time_str[:-3] + creation_time_str[-2:]
        creation_time = datetime.strptime(
            creation_time_str, '%Y-%m-%dT%H:%M:%S%z')
        try:
            tags = comment.find_elements(
                By.XPATH, "./div[contains(@class, 'comment__content')]")
            # For some reason the site sometimes adds empty div. Skip it
            for tag in tags:
                text = tag.get_attribute('innerHTML').strip()
                if len(text) > 0:
                    break
        except NoSuchElementException:
            # likely post-answer, not really comment. Can be parsed separately on a different crawler call.
            # TODO: maybe parse it here?
            return None

        if len(text) == 0:
            logger.warning(
                f"Empty comment text was parsed when processing URL {self.driver.current_url}")
            return None

        domain = urlparse(activity_url).netloc
        # TODO: same, single commit
        activity, _ = get_or_create(session, Activity, url=activity_url, defaults={'text': text, 'owner': entity,
                                                                                   'creation_time': creation_time, 'domain': domain})
        self.total_activities += 1
        return activity

    def _strip_next_url(self, url):
        f = furl(url).remove(fragment=True)
        # Drop all the parameters except "page"
        params_to_drop = set(f.query.params.keys())
        params_to_drop.discard('page')
        return f.remove(args=params_to_drop).url

    def _scroll_for_more_posts(self):
        try:
            feed = self.driver.find_element(By.CLASS_NAME, 'stories-feed')
        except NoSuchElementException:
            return
        is_paginated = feed.get_attribute(
            'data-pagination-mode') == 'true'
        if is_paginated:
            return
        for _ in range(self.MAX_SCROLLS):
            try:
                _ = self.driver.find_element(
                    By.CLASS_NAME, 'stories-feed__spinner')
            except NoSuchElementException:
                return
            posts = self.driver.find_elements(By.TAG_NAME, 'article')
            if len(posts) == 0:
                return

            self.driver.execute_script(
                'window.scrollTo(0, document.body.scrollHeight);')
            try:
                WebDriverWait(self.driver, 10).until(
                    last_element_changed((By.TAG_NAME, 'article'), posts[-1]))
            except TimeoutException:
                return

    def _get_next_urls(self):
        self._scroll_for_more_posts()
        return super()._get_next_urls()

    def parse(self):
        self._get_post_author_entities()
        if not self._is_post_url():
            return
        self._expand_comments()

        comments = self.driver.find_elements(By.CLASS_NAME, 'comment__body')
        for comment in comments:
            entity = self._get_entity_from_comment(comment)

            if entity is not None:
                _ = self._get_activity_from_comment(comment, entity)
