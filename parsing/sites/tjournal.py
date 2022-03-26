from bs4 import BeautifulSoup
from models.entity import Entity, EntityType
from parsing.entity_extractor_base import EntityExtractorBase


class TJournalEntityExtractor(EntityExtractorBase):
    def get_entities(self):
        page = self._get_page()
        soup = BeautifulSoup(page)
        comment_authors = soup.find_all("a", {"class": "comment__author"})
        urls = [tag.get('href') for tag in comment_authors]
        entities = []
        for url in set(urls):
            entity = Entity(entity_type=EntityType.USER, url=url)
            entities.append(entity)
        return entities

    def get_supported_domain():
        return 'tjournal.ru'
