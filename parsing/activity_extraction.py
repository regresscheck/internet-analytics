from parsing.activity_extractor_factory import extractor_factory
from parsing.sites.tjournal import TJournalActivityExtractor


extractor_factory.register_extractor(TJournalActivityExtractor)


def extract_entity_activities(entity):
    extractor = extractor_factory.get_extractor(entity)
    return extractor.get_activities()
