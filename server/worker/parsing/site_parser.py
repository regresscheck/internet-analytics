import abc
from furl import furl
import logging
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


class SiteParser(abc.ABC):
    def __init__(self, driver):
        domain = furl(driver.current_url).netloc
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

    def _strip_next_url(self, url):
        return furl(url).remove(args=True, fragment=True).url

    def _get_next_urls(self):
        links = set()
        for element in self.driver.find_elements(By.TAG_NAME, 'a'):
            url = element.get_attribute('href')
            try:
                f = furl(url)
            except ValueError:
                # Not a valid URL
                continue
            if f.scheme not in ['http', 'https'] or len(f.netloc) == 0:
                continue
            links.add(self._strip_next_url(url))
        return list(links)

    def log_results(self):
        logger.info(
            f"URL {self.driver.current_url} was parsed. Found {self.total_entities} entities, {self.total_activities} activites.")
