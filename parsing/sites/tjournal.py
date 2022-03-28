from datetime import datetime
import json
from bs4 import BeautifulSoup
from models.activity import Activity
from models.entity import Entity, EntityType
from parsing.activity_extractor_base import ActivityExtractorBase
from parsing.entity_extractor_base import EntityExtractorBase
from urllib.parse import urlparse
from parsing.page_loader import PageLoader
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
            entity, created = Entity.get_or_create(
                url=url, defaults={'entity_type': EntityType.USER, 'domain': domain,
                                   'last_updated': datetime(2000, 1, 1)})
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
            activity = Activity.get_or_create(url=url, defaults={'text': text, 'owner': self.entity,
                                                                 'creation_time': creation_time, 'domain': domain})
            activities.append(activity)
        return activities

    def get_activities(self):
        # TODO: get time
        url = self.entity.url.rstrip('/')
        assert _url_pattern.match(url)
        comments_url = url + '/comments'
        page = PageLoader().get_url(comments_url)
        soup = BeautifulSoup(page, features="lxml")
        activities = self.get_activities_from_page(soup)

        feed_tag = soup.find("div", {"class": "feed"})
        last_sorting_value = feed_tag['data-feed-last-sorting-value']
        last_id = feed_tag['data-feed-last-id']
        page_count = 2

        more_comments_url = url + '/more'
        while page_count <= 5:
            params = {
                '    last_id': last_id,
                '    last_sorting_value': last_sorting_value,
                '    page': page_count,
                '    exclude_ids': '[]',
                'mode': 'raw'
            }
            page = PageLoader().get_url(more_comments_url, params=params)
            try:
                data = json.loads(page)
            except json.decoder.JSONDecodeError:
                # TODO: proper handling? verify possible cause
                break
            # TODO: proper error handling
            assert data['rc'] == 200
            if data['data']['items_html'] == None:
                break
            soup = BeautifulSoup(page, features="lxml")
            activities.extend(self.get_activities_from_page(soup))

            last_sorting_value = data['data']['last_sorting_value']
            last_id = data['data']['last_id']
            page_count += 1

        return activities

    @ staticmethod
    def get_supported_domain():
        return SUPPORTED_DOMAIN
