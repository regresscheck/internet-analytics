from urllib.parse import urlparse

from parsing.activity_extractor_base import ActivityExtractorBase


class ActivityExtractorFactory:
    def __init__(self) -> None:
        self._extractors = {}

    def register_extractor(self, domain, extractor):
        assert domain not in self._extractors
        assert isinstance(extractor, ActivityExtractorBase)
        self._extractors[domain] = extractor

    def get_extractor(self, url):
        domain = urlparse(url).netloc
        assert domain in self._extractors

        extractor_class = self._extractors[domain]
        return extractor_class(url)


extractor_factory = ActivityExtractorFactory()
