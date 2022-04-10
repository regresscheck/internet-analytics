import abc
from urllib.parse import urlparse


class SiteParser(abc.ABC):
    def __init__(self, driver):
        domain = urlparse(driver.current_url).netloc
        assert domain == self.get_supported_domain()
        self.driver = driver

    @staticmethod
    @abc.abstractmethod
    def get_supported_domain():
        pass

    @abc.abstractmethod
    def parse(self):
        pass
