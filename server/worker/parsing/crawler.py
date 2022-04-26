import logging
from queue import Queue
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from worker.parsing.site_parser_utils import NoSuitableParserException, get_suitable_parser


logger = logging.getLogger(__name__)

# TODO: implement caching. Maybe through proxy?


class Crawler:
    def __init__(self):
        self.queue = Queue()
        self.current = set()
        self.processed = set()
        self._timeout_count = 0
        self.driver = None
        self._create_driver()

    def _create_driver(self):
        if self.driver is not None:
            self.driver.quit()
        options = Options()
        options.headless = True
        self.driver = webdriver.Firefox(options=options)
        self.driver.set_page_load_timeout(30)

    def _mark_as_done(self, url):
        self.processed.add(url)
        self.current.remove(url)

    def _cleanup_browser(self):
        logger.warning("Trying to clean up browser")
        self._create_driver()
        self.driver.delete_all_cookies()

    def _process_one(self):
        url = self.queue.get()
        if url in self.current or url in self.processed:
            return
        self.current.add(url)
        logger.info(f"Processing {url}")
        try:
            self.driver.get(url)
        except TimeoutException as e:
            logger.warning(f'Timed out fetching URL {url}')
            self._mark_as_done(url)
            self._timeout_count += 1
            if self._timeout_count >= 3:
                self._cleanup_browser()
                self._timeout_count = 0
            return
        except WebDriverException:
            # Easiest cause - unresolvable URL
            logger.warning("Received WebDriverError", exc_info=True)
            self._mark_as_done(url)
            return
        try:
            parser = get_suitable_parser(self.driver)
        except NoSuitableParserException as e:
            logger.info(f'No suitable parser found for URL {url}')
            self._mark_as_done(url)
            return
        parser.parse()
        parser.log_results()

        next_urls = parser._get_next_urls()
        for next_url in next_urls:
            if next_url not in self.current and next_url not in self.processed:
                self.queue.put(next_url)
        self._mark_as_done(url)
        # Also mark the resulting url, there could be redirects
        self.processed.add(self.driver.current_url)
        self._timeout_count = 0

    def crawl(self, starting_urls):
        for url in starting_urls:
            self.queue.put(url)
        try:
            while self.queue.qsize() > 0:
                self._process_one()
                # TODO: wait time based on last request to given domain
                time.sleep(2)
        except KeyboardInterrupt as e:
            logger.info("Stopping driver")
            self.driver.quit()
            raise e
