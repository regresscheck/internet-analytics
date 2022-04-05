from datetime import datetime
import json
from bs4 import BeautifulSoup
from worker.consts import OLD_TIMES
from worker.database_helpers import get_or_create, session
from worker.models.activity import Activity
from worker.models.entity import Entity, EntityType
from worker.parsing.activity_extractor_base import ActivityExtractorBase
from worker.parsing.entity_extractor_base import EntityExtractorBase
from urllib.parse import urlparse
from worker.parsing.page_loader import PageLoader
import re

SUPPORTED_DOMAIN = 'tjournal.ru'

pattern = re.compile("^([A-Z][0-9]+)+$")


class TJournalEntityExtractor(EntityExtractorBase):
    def get_entities(self):
        page = self._get_page()
        soup = BeautifulSoup(page, features="lxml")
        comment_authors = soup.find_all("a", {"class": "comment__author"})
        urls = [tag.get('href') for tag in comment_authors]
        entities = []
        for url in set(urls):
            domain = urlparse(url).netloc
            entity, _ = get_or_create(session, Entity,
                                      url=url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                                         'last_updated': OLD_TIMES})
            entities.append(entity)
        return entities

    @staticmethod
    def get_supported_domain():
        return SUPPORTED_DOMAIN


_url_pattern = re.compile('^https://tjournal.ru/u/[^/]*$')


class TJournalActivityExtractor(ActivityExtractorBase):
    def get_activities_from_page(self, soup):
        comment_tags = urls = soup.find_all(
            "div", {"class": "profile_comment_favorite"})
        activities = []
        for tag in comment_tags:
            p_tag = tag.find("span", {
                "class": "profile_comment_favorite__text__full"}).p
            # Gifs don't have any "p" tag(and any text)
            text = p_tag.text if p_tag else None
            creation_time = datetime.fromtimestamp(
                int(tag.find('time', {"class": "time"})['data-date']))
            url = tag.find("a", {"class": "profile_comment_favorite__date"})[
                'href']
            # TODO: set parent to post
            domain = urlparse(url).netloc
            activity, created = get_or_create(session, Activity, url=url, defaults={'text': text, 'owner': self.entity,
                                                                                    'creation_time': creation_time, 'domain': domain})
            if created:
                activities.append(activity)
        return activities

    def get_activities(self):
        url = self.entity.url.rstrip('/')
        assert _url_pattern.match(url)
        comments_url = url + '/comments'
        page = PageLoader().get_url(comments_url)
        soup = BeautifulSoup(page, features="lxml")

        last_activity = self._get_last_activity()
        last_creation_time = last_activity.creation_time if last_activity else OLD_TIMES

        activities = self.get_activities_from_page(soup)
        if len(activities) == 0:
            return []

        feed_tag = soup.find("div", {"class": "feed"})
        last_sorting_value = feed_tag['data-feed-last-sorting-value']
        last_id = feed_tag['data-feed-last-id']
        page_count = 2
        more_comments_url = comments_url + '/more'
        while activities[-1].creation_time > last_creation_time:
            # Manually construct URL to properly encode whitespace
            full_url = more_comments_url + \
                f'?%20%20%20%20last_id={last_id}&'\
                + f'%20%20%20%20last_sorting_value={last_sorting_value}&'\
                + f'%20%20%20%20page={page_count}&'\
                + f'%20%20%20%20exclude_ids=[]&'\
                + f'mode=raw'
            page = PageLoader().get_url(full_url)
            try:
                data = json.loads(page)
            except json.decoder.JSONDecodeError:
                # TODO: proper handling? verify possible cause
                break
            # TODO: proper error handling
            assert data['rc'] == 200
            if data['data']['items_html'] == None:
                break
            soup = BeautifulSoup(data['data']['items_html'], features="lxml")
            activities.extend(self.get_activities_from_page(soup))

            last_sorting_value = data['data']['last_sorting_value']
            last_id = data['data']['last_id']
            page_count += 1

        return activities

    @ staticmethod
    def get_supported_domain():
        return SUPPORTED_DOMAIN
