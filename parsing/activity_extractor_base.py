import abc

from parsing.activity_extractor_factory import extractor_factory


class ActivityExtractorBase(abc.ABC):
    def __init__(self, entity) -> None:
        self.entity = entity

    @abc.abstractmethod
    def get_activities(self):
        pass

    @abc.abstractmethod
    def get_supported_domain():
        pass

    @classmethod
    def _register_extractor(cls):
        domain = cls.get_supported_domain()
        extractor_factory.register_extractor(domain, cls)
