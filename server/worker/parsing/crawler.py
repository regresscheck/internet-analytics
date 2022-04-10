from queue import Queue
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from worker.parsing.site_parser_utils import get_suitable_parser

# TODO: implement caching. Maybe through proxy?


class Crawler:
    def __init__(self):
        self.queue = Queue()
        self.current = set()
        self.processed = set()
        # TODO: driver.close() on exit
        # TODO: use env variable
        self.driver = webdriver.Chrome(
            '/home/regresscheck/Downloads/chromedriver')

    def _get_next_urls(self):
        current_domain = '{uri.scheme}://{uri.netloc}/'.format(
            uri=urlparse(self.driver.current_url))
        links = set()
        for element in self.driver.find_elements(By.TAG_NAME, 'a'):
            url = element.get_attribute('href')
            parsed_url = urlparse(url)
            url_domain = '{uri.scheme}://{uri.netloc}/'.format(
                uri=parsed_url)
            if current_domain == url_domain:
                # Drop query parameters and fragment
                links.add(parsed_url._replace(
                    fragment="", query="").geturl())
        return list(links)

    def _process_one(self):
        url = self.queue.get()
        if url in self.current or url in self.processed:
            return
        self.current.add(url)
        print(f"Processing {url}")

        self.driver.get(url)

        parser = get_suitable_parser(self.driver)
        parser.parse()

        next_urls = self._get_next_urls()
        for next_url in next_urls:
            if next_url not in self.current and next_url not in self.processed:
                self.queue.put(next_url)

        self.processed.add(url)
        self.current.remove(url)

    def crawl(self, starting_urls):
        for url in starting_urls:
            self.queue.put(url)
        while self.queue.qsize() > 0:
            self._process_one()
            # TODO: wait time based on last request to given domain
            time.sleep(2)
