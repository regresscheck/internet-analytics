from datetime import datetime
from bs4 import BeautifulSoup
from models.entity import Entity, EntityType
from parsing.entity_extractor_base import EntityExtractorBase
from urllib.parse import urlparse


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

    def get_supported_domain():
        return 'tjournal.ru'
