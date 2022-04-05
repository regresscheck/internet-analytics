import abc
from common.database_helpers import session
from common.models.activity import Activity


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

    def _get_last_activity(self):
        return session.query(Activity).filter(Activity.owner == self.entity).order_by(
            Activity.creation_time.desc()).first()
