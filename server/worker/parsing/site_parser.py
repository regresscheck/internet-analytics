import abc
from urllib.parse import urlparse
import logging
from selenium.webdriver.common.by import By

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

    def _get_next_urls(self):
        links = set()
        for element in self.driver.find_elements(By.TAG_NAME, 'a'):
            url = element.get_attribute('href')
            parsed_url = urlparse(url)
            if parsed_url.scheme in ['http', 'https'] and len(parsed_url.netloc) > 0:
                next_url = parsed_url._replace(
                    fragment="", query="").geturl()
                links.add(next_url)
        return list(links)

    def log_results(self):
        logger.info(
            f"URL {self.driver.current_url} was parsed. Found {self.total_entities} entities, {self.total_activities} activites.")
