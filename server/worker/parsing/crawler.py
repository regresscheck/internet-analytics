from queue import Queue
from urllib.parse import urlparse

from worker.parsing.entity_extraction import get_extractor

# TODO: make it async to save a lot of time


class Crawler:
    def __init__(self):
        self.queue = Queue()
        self.current = set()
        self.processed = set()

    def _get_next_urls(self, current_url, soup):
        current_domain = '{uri.scheme}://{uri.netloc}/'.format(
            uri=urlparse(current_url))
        links = set()
        for link in soup.find_all("a"):
            if link.has_attr('href'):
                url = link['href']
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

        extractor = get_extractor(url)
        _ = extractor.get_entities()

        soup = extractor.get_soup()
        next_urls = self._get_next_urls(url, soup)
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
