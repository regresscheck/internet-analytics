from datetime import datetime
from worker.parsing.site_parser import SiteParser
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, MoveTargetOutOfBoundsException
from selenium.webdriver.common.action_chains import ActionChains
from common.consts import OLD_TIMES
from common.database_helpers import get_or_create, session
from common.models.activity import Activity
from common.models.entity import Entity, EntityType
from urllib.parse import urlparse


SUPPORTED_DOMAIN = 'pikabu.ru'


class PikabuParser(SiteParser):
    @staticmethod
    def get_supported_domain():
        return SUPPORTED_DOMAIN

    def _close_popups(self):
        elements = self.driver.find_elements(
            By.XPATH, "//div[contains(@class, 'story__top-close')]")
        for element in elements:
            ActionChains(self.driver).move_to_element(
                element).click(element).perform()

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

    def _expand_comments(self):
        element = self.driver.find_element(
            By.CLASS_NAME, 'comments__more-button')
        if element.is_displayed():
            ActionChains(self.driver).move_to_element(
                element).click(element).perform()
        self._close_popups()
        # Load all top comments
        total_failures = 0
        while True:
            try:
                element = self.driver.find_element(
                    By.CLASS_NAME, 'comment__more')
                ActionChains(self.driver).move_to_element(
                    element).click(element).perform()
            except MoveTargetOutOfBoundsException:
                total_failures += 1
                print("WARNING: EXPAND CLICK FAILURE")
                if total_failures >= 10:
                    print("ERROR: CANNOT EXPAND ALL COMMENTS")
                    break
            except NoSuchElementException:
                break

        # Expand each comment subtree, may take multiple iterations
        expanded = True
        total_failures = 0
        while expanded:
            expanded = False
            buttons = self.driver.find_elements(By.CLASS_NAME, 'comment-toggle-children__label') + \
                self.driver.find_elements(
                    By.CLASS_NAME, 'comment-hidden-group__toggle')
            try:
                for button in buttons:
                    if button.is_displayed():
                        ActionChains(self.driver).move_to_element(
                            button).click(button).perform()
                        expanded = True
            except MoveTargetOutOfBoundsException:
                total_failures += 1
                expanded = True
                print("WARNING: EXPAND CLICK FAILURE")
                if total_failures >= 10:
                    print("ERROR: CANNOT EXPAND ALL COMMENTS")
                    break

    def _get_entity_from_comment(self, comment):
        try:
            entity_url = comment.find_element(
                By.XPATH, ".//a[contains(@class, 'user')]").get_attribute('href')
        except NoSuchElementException as e:
            # User is banned/deleted
            return None
        domain = urlparse(entity_url).netloc
        # TODO: insert all entities with a single commit
        entity, _ = get_or_create(session, Entity,
                                  url=entity_url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                                            'last_updated': OLD_TIMES})
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
            return

        if len(text) == 0:
            print("WARNING: empty comment text")
            return

        domain = urlparse(activity_url).netloc
        # TODO: same, single commit
        _ = get_or_create(session, Activity, url=activity_url, defaults={'text': text, 'owner': entity,
                                                                         'creation_time': creation_time, 'domain': domain})

    def parse(self):
        self._close_popups()
        self._get_post_author_entities()
        if not self._is_post_url():
            return
        self._expand_comments()

        comments = self.driver.find_elements(By.CLASS_NAME, 'comment__body')
        for comment in comments:
            entity = self._get_entity_from_comment(comment)

            if entity is not None:
                _ = self._get_activity_from_comment(comment, entity)
