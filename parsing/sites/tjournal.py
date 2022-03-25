from bs4 import BeautifulSoup
from parsing.entity_extractor_base import EntityExtractorBase


class TJournalEntityExtractor(EntityExtractorBase):
    def get_entities(self):
        page = self._get_page()
        soup = BeautifulSoup(page)
        comment_authors = soup.find_all("a", {"class": "comment__author"})
        return [tag.get('href') for tag in comment_authors]

    def get_supported_domain():
        return 'tjournal.ru'
