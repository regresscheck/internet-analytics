from worker.parsing.activity_extractor_base import ActivityExtractorBase


class ActivityExtractorFactory:
    def __init__(self) -> None:
        self._extractors = {}

    def register_extractor(self, extractor):
        assert issubclass(extractor, ActivityExtractorBase)
        domain = extractor.get_supported_domain()
        assert domain not in self._extractors
        self._extractors[domain] = extractor

    def get_extractor(self, entity):
        domain = entity.domain
        assert domain in self._extractors

        extractor_class = self._extractors[domain]
        return extractor_class(entity)


extractor_factory = ActivityExtractorFactory()
