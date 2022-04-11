from datetime import datetime
from worker.parsing.site_parser import SiteParser
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from common.consts import OLD_TIMES
from common.database_helpers import get_or_create, session
from common.models.activity import Activity
from common.models.entity import Entity, EntityType
from urllib.parse import urlparse
import re

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
        # Sometimes it takes time to load comments
        try:
            element = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'comments__content_wrapper__button')]/div")))
        except TimeoutException:
            print("WARNING: No expand button was found")
            return
        if element.is_displayed():
            ActionChains(self.driver).move_to_element(
                element).click(element).perform()

    def _get_entity_from_comment(self, comment):
        try:
            entity_url = comment.find_element(
                By.XPATH, ".//a[contains(@class, 'comment__author')]").get_attribute('href')
        except NoSuchElementException:
            # Anonymous user
            return None
        domain = urlparse(entity_url).netloc
        # TODO: insert all entities with a single commit
        entity, _ = get_or_create(session, Entity,
                                  url=entity_url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                                            'last_updated': OLD_TIMES})
        return entity

    def _get_activity_from_comment(self, comment, entity):
        activity_url = comment.find_element(
            By.XPATH, ".//a[contains(@class, 'comment__detail')]").get_attribute('href')
        creation_time_str = comment.find_element(
            By.XPATH, ".//a[contains(@class, 'comment__detail')]/time").get_attribute('data-date')
        creation_time = datetime.fromtimestamp(int(creation_time_str))
        try:
            text = comment.find_element(
                By.XPATH, "./div[contains(@class, 'comment__text')]").get_attribute('innerHTML')
        except NoSuchElementException:
            # no text(e.g. just a pic)
            text = ""

        domain = urlparse(activity_url).netloc
        # TODO: same, single commit
        _ = get_or_create(session, Activity, url=activity_url, defaults={'text': text, 'owner': entity,
                                                                         'creation_time': creation_time, 'domain': domain})

    def _get_post_author_entities(self):
        authors = self.driver.find_elements(
            By.CLASS_NAME, 'content-header-author--user')
        for author in authors:
            entity_url = author.get_attribute('href')
            domain = urlparse(entity_url).netloc
            _ = get_or_create(session, Entity,
                              url=entity_url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                                        'last_updated': OLD_TIMES})

    def parse(self):
        self._get_post_author_entities()
        if not self._is_post_url():
            return
        self._expand_comments()

        comments = self.driver.find_elements(By.CLASS_NAME, 'comment__content')
        for comment in comments:
            entity = self._get_entity_from_comment(comment)

            if entity is not None:
                _ = self._get_activity_from_comment(comment, entity)
