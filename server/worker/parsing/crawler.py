from queue import Queue
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from worker.parsing.site_parser_utils import NoSuitableParserException, get_suitable_parser

# TODO: implement caching. Maybe through proxy?


class Crawler:
    def __init__(self):
        self.queue = Queue()
        self.current = set()
        self.processed = set()
        # TODO: driver.close() on exit
        # TODO: use env variable
        chrome_options = Options()
        chrome_options.add_argument('enable-automation')
        chrome_options.add_argument('start-maximized')
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--dns-prefetch-disable")
        self.driver = webdriver.Chrome(
            '/home/regresscheck/Downloads/chromedriver', options=chrome_options)
        self.driver.implicitly_wait(2)
        self.driver.set_page_load_timeout(30)

    def _get_next_urls(self):
        current_domain = '{uri.scheme}://{uri.netloc}/'.format(
            uri=urlparse(self.driver.current_url))
        links = set()
        for element in self.driver.find_elements(By.TAG_NAME, 'a'):
            url = element.get_attribute('href')
            parsed_url = urlparse(url)
            if parsed_url.scheme in ['http', 'https'] and len(parsed_url.netloc) > 0:
                next_url = parsed_url._replace(
                    fragment="", query="").geturl()
                links.add(next_url)
        return list(links)

    def _mark_as_done(self, url):
        self.processed.add(url)
        self.current.remove(url)

    def _process_one(self):
        url = self.queue.get()
        if url in self.current or url in self.processed:
            return
        self.current.add(url)
        print(f"Processing {url}")
        try:
            self.driver.get(url)
        except TimeoutException as e:
            # Retry once
            self.driver.navigate().refresh()
            self.driver.get(url)
        try:
            parser = get_suitable_parser(self.driver)
        except NoSuitableParserException as e:
            print(e)
            self._mark_as_done(url)
            return
        parser.parse()

        next_urls = self._get_next_urls()
        for next_url in next_urls:
            if next_url not in self.current and next_url not in self.processed:
                self.queue.put(next_url)
        self._mark_as_done(url)

    def crawl(self, starting_urls):
        for url in starting_urls:
            self.queue.put(url)
        while self.queue.qsize() > 0:
            self._process_one()
            # TODO: wait time based on last request to given domain
            time.sleep(2)
