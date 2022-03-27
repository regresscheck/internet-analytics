import abc
from parsing.page_loader import PageLoader


class EntityExtractorBase(abc.ABC):
    def __init__(self, url) -> None:
        self.url = url

    @abc.abstractmethod
    def get_entities(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def get_supported_domain():
        pass

    def _get_page(self):
        return PageLoader().get_url(self.url)
