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
from urllib.parse import urlparse, unquote

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
        try:
            _ = WebDriverWait(self.driver, 30).until_not(
                EC.presence_of_element_located((By.CLASS_NAME, 'comment__placeholder')))
        except:
            logger.warning("Failed to expand comments in time")

    def _get_entity_from_comment(self, comment):
        try:
            entity_url = comment.find_element(
                By.CSS_SELECTOR, "a.user").get_attribute('href')
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
        entity, _ = get_or_create(session, Entity,
                                  url=entity_url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                                            'last_updated': OLD_TIMES})
        self.total_entities += 1
        return entity

    def _parse_pikabu_time(self, time_str):
        # 2022-04-10T06:31:03+03:00
        # Python does not like colon in timezone, drop it
        if time_str[-3:-2] == ':':
            time_str = time_str[:-3] + time_str[-2:]
        return datetime.strptime(
            time_str, '%Y-%m-%dT%H:%M:%S%z')

    def _get_activity_from_comment(self, comment, entity, parent):
        activity_url = comment.find_element(
            By.CSS_SELECTOR, 'a.comment__tool[data-role="link"]').get_attribute('href')
        creation_time_str = comment.find_element(
            By.CSS_SELECTOR, "time.comment__datetime").get_attribute('datetime')
        creation_time = self._parse_pikabu_time(creation_time_str)
        try:
            tags = comment.find_elements(
                By.CSS_SELECTOR, "div.comment__content")
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
        defaults = {'text': text, 'owner': entity,
                    'creation_time': creation_time, 'domain': domain}
        if parent is not None:
            defaults['parent'] = parent
        activity, _ = get_or_create(
            session, Activity, url=activity_url, defaults=defaults)
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

    def _extract_post_activity(self):
        main_story = self.driver.find_element(
            By.CSS_SELECTOR, "div.story__main")
        try:
            author = main_story.find_element(
                By.CSS_SELECTOR, "a.story__user-link")
        except NoSuchElementException:
            # Author is banned/deleted
            # TODO: allow creating activities without entities to save full context
            return None
        entity_url = author.get_attribute('href')
        domain = urlparse(entity_url).netloc
        entity, _ = get_or_create(session, Entity,
                                  url=entity_url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                                            'last_updated': OLD_TIMES})
        self.total_entities += 1

        link_element = main_story.find_element(
            By.CSS_SELECTOR, "span.story__copy-link[data-url]")
        activity_url = furl(unquote(link_element.get_attribute(
            'data-url'))).remove(fragment=True, args=True).url
        domain = urlparse(activity_url).netloc

        date_element = main_story.find_element(
            By.CSS_SELECTOR, "time.story__datetime")
        creation_time = self._parse_pikabu_time(
            date_element.get_attribute('datetime'))
        title = main_story.find_element(
            By.CSS_SELECTOR, "span.story__title-link").get_attribute('innerHTML').strip()
        inner_text = main_story.find_element(
            By.CSS_SELECTOR, "div.story__content-inner").get_attribute('innerHTML').strip()
        text = title + "\n" + inner_text

        activity, _ = get_or_create(session, Activity, url=activity_url, defaults={'text': text, 'owner': entity,
                                                                                   'creation_time': creation_time, 'domain': domain})
        self.total_activities += 1
        return activity

    def _extract_comments_recursive(self, level_element, parent_activity):
        elements = level_element.find_elements(
            By.CSS_SELECTOR, ":scope > div.comment")
        for element in elements:
            body = element.find_element(
                By.CSS_SELECTOR, ":scope > div.comment__body")
            entity = self._get_entity_from_comment(body)
            if entity is None:
                logger.warning("Failed to extract entity from comment")
                continue
            activity = self._get_activity_from_comment(
                body, entity, parent_activity)
            try:
                children_level = element.find_element(
                    By.CSS_SELECTOR, ":scope > div.comment__children")
            except NoSuchElementException:
                continue
            self._extract_comments_recursive(children_level, activity)

    def parse(self):
        if not self._is_post_url():
            return
        self._expand_comments()

        activity = self._extract_post_activity()

        try:
            root_level = self.driver.find_element(
                By.CLASS_NAME, 'comments__container')
        except NoSuchElementException:
            # It's likely https://pikabu.ru/story/.../author page, but let's log to verify
            logger.warning("Failed to find top level layer for comments")
            return
        self._extract_comments_recursive(root_level, activity)
