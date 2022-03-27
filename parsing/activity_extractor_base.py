import abc


class ActivityExtractorBase(abc.ABC):
    def __init__(self, entity) -> None:
        assert entity.domain == self.get_supported_domain()
        self.entity = entity

    @abc.abstractmethod
    def get_activities(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def get_supported_domain():
        pass
