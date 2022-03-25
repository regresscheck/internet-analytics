import abc
from parsing.page_loader import PageLoader
from parsing.entity_extractor_factory import extractor_factory


class EntityExtractorBase(abc.ABC):
    def __init__(self, url) -> None:
        self.url = url

    @abc.abstractmethod
    def get_entities(self):
        pass

    @abc.abstractmethod
    def get_supported_domain():
        pass

    @classmethod
    def _register_extractor(cls):
        domain = cls.get_supported_domain()
        extractor_factory.register_extractor(domain, cls)

    def _get_page(self):
        return PageLoader().get_url(self.url)
