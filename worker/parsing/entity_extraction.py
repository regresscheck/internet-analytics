from worker.parsing.entity_extractor_factory import extractor_factory
from worker.parsing.sites.tjournal import TJournalEntityExtractor

extractor_factory.register_extractor(TJournalEntityExtractor)


def extract_entities(url):
    extractor = extractor_factory.get_extractor(url)
    return extractor.get_entities()
