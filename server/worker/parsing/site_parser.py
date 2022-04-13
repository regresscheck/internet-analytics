import abc
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class SiteParser(abc.ABC):
    def __init__(self, driver):
        domain = urlparse(driver.current_url).netloc
        assert domain == self.get_supported_domain()
        self.driver = driver

        self.total_entities = 0
        self.total_activities = 0

    @staticmethod
    @abc.abstractmethod
    def get_supported_domain():
        pass

    @abc.abstractmethod
    def parse(self):
        pass

    def log_results(self):
        logger.info(
            f"URL {self.driver.current_url} was parsed. Found {self.total_entities} entities, {self.total_activities} activites.")
