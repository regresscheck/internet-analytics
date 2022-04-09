import abc
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from worker.parsing.page_loader import PageLoader


class EntityExtractorBase(abc.ABC):
    def __init__(self, url, soup=None) -> None:
        domain = urlparse(url).netloc
        assert domain == self.get_supported_domain()
        self.url = url
        self._soup = soup

    @abc.abstractmethod
    def get_entities(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def get_supported_domain():
        pass

    def get_soup(self):
        if not self._soup:
            text = PageLoader().get_url(self.url)
            self._soup = BeautifulSoup(text, features="lxml")
        return self._soup
